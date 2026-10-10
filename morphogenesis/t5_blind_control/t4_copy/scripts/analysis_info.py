"""Part G: information-theoretic structure on NATURAL dishes (level O1 variables). usage: analysis_info.py SPLIT(development|heldout) OUTJSON [CACHE_TAG]
Variables: 7 channels x 3 body-frame regions (terciles of p along the signed major axis) = 21 variables per dish-frame."""
import sys, json, pickle, itertools; sys.path.insert(0, '.')
import numpy as np
from t4 import io
from t4.louvain import louvain
SPLIT, OUTJ = sys.argv[1], sys.argv[2]
TAG = sys.argv[3] if len(sys.argv) > 3 else ('dev' if SPLIT == 'development' else 'held')
rng = np.random.default_rng(11)
SHR = 0.2; RIDGE = 1.0; NPERM = 1000; NPERM_G3 = 200
CH = io.CHANNELS['O1']
cat = io.catalog()
runs = [r for r in cat if r['condition'] == 'N0' and (r['split'] == 'development') == (SPLIT == 'development')]

def build():
    X = np.zeros((len(runs), 8, 21))
    for i, r in enumerate(runs):
        rec = pickle.load(open(f"cache/{TAG}/{r['run']}_O1.pkl", 'rb')); raw = io.point_frames(r['run'], 'O1')
        for k, f in enumerate(raw):
            o = rec['frames'][k]['orgs'][0]
            mem = {c: j for j, c in enumerate(f['ids'])}
            idx = np.array([mem[c] for c in o['members']])
            p = (f['xy'][idx] - np.array(o['centroid'])) @ np.array(o['e1'])
            lo, hi = np.quantile(p, [1 / 3, 2 / 3])
            for g, m in enumerate([p <= lo, (p > lo) & (p < hi), p >= hi]):
                X[i, k, g * 7:(g + 1) * 7] = f['lev'][idx][m].mean(0)
    return X
X = build()                                    # dishes x 8 x 21
names = [f'{c}@{["head","mid","tail"][g]}' for g in range(3) for c in CH]
nd, T, D = X.shape
# ---------------- decorrelation / effective sample size
Xc = X - X.mean(1, keepdims=True)
rho_raw = float(np.nanmean([np.corrcoef(Xc[:, :-1, j].ravel(), Xc[:, 1:, j].ravel())[0, 1] for j in range(D) if Xc[:, :, j].std() > 1e-9]))
rho_corr = rho_raw + 1.0 / (T - 1)            # bias of dish-mean removal with T frames
icc = []
for j in range(D):
    m = X[:, :, j]; sb = m.mean(1).var(ddof=1); sw = m.var(1, ddof=1).mean()
    icc.append(max(0.0, (sb - sw / T) / max(sb + sw * (T - 1) / T, 1e-12)))
icc = float(np.mean(icc))
deff = 1 + (T - 1) * icc
n_eff = float(nd * T / deff)
S = (X - X.reshape(-1, D).mean(0)) / np.maximum(X.reshape(-1, D).std(0), 1e-9)
Z1 = S[np.arange(nd), rng.integers(0, T, nd)]  # one random frame per dish (independent samples)
samp = dict(n_dishes=nd, frames_per_dish=T, dim=D, lag1_residual_autocorr_raw=rho_raw, lag1_residual_autocorr_bias_corrected=rho_corr,
            icc_dish=icc, design_effect=float(deff), n_eff_all_frames=n_eff, n_one_frame_per_dish=nd, n_over_dim_one_frame=nd / D,
            n_eff_over_dim=n_eff / D, requirement='n_eff >= 5*dim', requirement_met_one_frame=bool(nd >= 5 * D), requirement_met_all_frames=bool(n_eff >= 5 * D))

# ---------------- Gaussian CMI leakage
def logdet(M):
    s, ld = np.linalg.slogdet(M); return ld if s > 0 else np.nan
def L_leak(Z, I, B, E, shr=SHR):
    p = Z.shape[1]; S_ = np.cov(Z.T)
    S_ = (1 - shr) * S_ + shr * np.trace(S_) / p * np.eye(p)
    def cc(ix, cond):
        if not cond: return S_[np.ix_(ix, ix)]
        return S_[np.ix_(ix, ix)] - S_[np.ix_(ix, cond)] @ np.linalg.inv(S_[np.ix_(cond, cond)]) @ S_[np.ix_(cond, ix)]
    return 0.5 * (logdet(cc(I, B)) + logdet(cc(E, B)) - logdet(cc(I + E, B)))

# ---------------- ridge lag predictors, dish-clustered CV
folds = np.arange(nd) % 5; rng.shuffle(folds)
def cv_loss(Y, Xreg, fold_ids=folds, per_dish=False):
    """Y: (nd, T-1, q) targets at t+1; Xreg: (nd, T-1, r) regressors at t. returns mean squared error per dish (nd,)."""
    nd_, Tm, q = Y.shape
    out = np.zeros(nd_)
    for f in range(5):
        tr = fold_ids != f; te = ~tr
        A = Xreg[tr].reshape(-1, Xreg.shape[2]); A = np.c_[A, np.ones(len(A))]; y = Y[tr].reshape(-1, q)
        W = np.linalg.solve(A.T @ A + RIDGE * np.eye(A.shape[1]), A.T @ y)
        At = np.c_[Xreg[te].reshape(-1, Xreg.shape[2]), np.ones(te.sum() * Tm)]
        err = ((At @ W - Y[te].reshape(-1, q)) ** 2).sum(1).reshape(te.sum(), Tm).mean(1)
        out[te] = err
    return out
def delta_group(Aidx, Bidx, Xs=S, A_override=None):
    """held-out loss difference: predict B_{t+1} from B_t vs from (B_t, A_t). Returns per-dish improvement (nd,) and baseline loss."""
    Y = Xs[:, 1:, :][:, :, Bidx]; Bt = Xs[:, :-1, :][:, :, Bidx]
    At = (Xs if A_override is None else A_override)[:, :-1, :][:, :, Aidx]
    base = cv_loss(Y, Bt); aug = cv_loss(Y, np.concatenate([Bt, At], 2))
    return base - aug, base

# ---------------- variable-level influence matrix (for Louvain)
Winf = np.zeros((D, D))
for j in range(D):
    for i in range(D):
        if i == j: continue
        d, b = delta_group([i], [j]); Winf[i, j] = d.mean() / max(b.mean(), 1e-9)
Wsym = np.maximum(Winf, 0) + np.maximum(Winf, 0).T
comm = louvain(Wsym)
# ---------------- candidate partitions
partitions = {}
chan_groups = {'type(c0-c3)': [g * 7 + c for g in range(3) for c in range(4)], 'graded(c6)': [g * 7 + 6 for g in range(3)], 'dish(c4,c5)': [g * 7 + c for g in range(3) for c in (4, 5)]}
for perm in itertools.permutations(chan_groups):
    partitions['chan:I=' + perm[0] + ',B=' + perm[1] + ',E=' + perm[2]] = (chan_groups[perm[0]], chan_groups[perm[1]], chan_groups[perm[2]])
reg_groups = {'head': list(range(0, 7)), 'mid': list(range(7, 14)), 'tail': list(range(14, 21))}
for perm in itertools.permutations(reg_groups):
    partitions['region:I=' + perm[0] + ',B=' + perm[1] + ',E=' + perm[2]] = (reg_groups[perm[0]], reg_groups[perm[1]], reg_groups[perm[2]])
# Louvain-derived roles (deterministic rule): merge to <=3 communities by largest inter-community weight; B = community with the largest
# weight to the other two combined; I = the larger of the remaining two by internal weight.
labs = comm.copy()
def merge_to(labs, k):
    labs = labs.copy()
    while len(np.unique(labs)) > k:
        u = np.unique(labs); best = None
        for a, b in itertools.combinations(u, 2):
            w = Wsym[np.ix_(labs == a, labs == b)].sum()
            if best is None or w > best[0]: best = (w, a, b)
        labs[labs == best[2]] = best[1]
    return labs
labs3 = merge_to(labs, 3); u = np.unique(labs3)
lou = dict(n_communities_raw=int(len(np.unique(comm))), n_after_merge=int(len(u)), sizes=[int((labs3 == c).sum()) for c in u],
           members=[[names[i] for i in np.where(labs3 == c)[0]] for c in u])
if len(u) == 3:
    cross = {c: sum(Wsym[np.ix_(labs3 == c, labs3 == o)].sum() for o in u if o != c) for c in u}
    Bc = max(cross, key=cross.get); rest = [c for c in u if c != Bc]
    internal = {c: Wsym[np.ix_(labs3 == c, labs3 == c)].sum() for c in rest}
    Ic = max(rest, key=internal.get); Ec = [c for c in rest if c != Ic][0]
    partitions['louvain'] = (list(np.where(labs3 == Ic)[0]), list(np.where(labs3 == Bc)[0]), list(np.where(labs3 == Ec)[0]))
elif len(u) == 2:
    partitions['louvain'] = (list(np.where(labs3 == u[0])[0]), [], list(np.where(labs3 == u[1])[0]))
# ---------------- evaluate partitions
def null_L(sizes, Z, n=NPERM):
    out = []
    for _ in range(n):
        perm = rng.permutation(D); a, b, c = sizes
        I = list(perm[:a]); B = list(perm[a:a + b]); E = list(perm[a + b:a + b + c])
        out.append(L_leak(Z, I, B, E))
    return np.array(out)
res = dict(sampling=samp, louvain=lou, partitions={})
for name, (I, B, E) in partitions.items():
    sizes = (len(I), len(B), len(E))
    row = dict(sizes=sizes, dim_used=sum(sizes))
    for tag, Z in (('one_frame_per_dish', Z1), ('all_frames', S.reshape(-1, D))):
        L = L_leak(Z, list(I), list(B), list(E)); nl = null_L(sizes, Z, NPERM if tag == 'one_frame_per_dish' else 300)
        row[tag] = dict(n=int(len(Z)), L=float(L), null_median=float(np.nanmedian(nl)), null_q05=float(np.nanquantile(nl, .05)), null_q95=float(np.nanquantile(nl, .95)),
                        percentile_in_null=float(np.nanmean(nl <= L)), ratio_to_null_median=float(L / np.nanmedian(nl)))
    # directed held-out contributions between groups
    G = dict(I=list(I), B=list(B), E=list(E)); dg = {}
    for a_, b_ in itertools.permutations('IBE', 2):
        if not G[a_] or not G[b_]: continue
        d, base = delta_group(G[a_], G[b_])
        rel = d / np.maximum(base, 1e-9)
        bs = [rel[rng.integers(0, nd, nd)].mean() for _ in range(1000)]
        nullm = []
        for _ in range(NPERM_G3):
            sh = S.copy(); perm = rng.permutation(nd); sh = S[perm]                     # whole-dish block permutation of the source history
            dd, _ = delta_group(G[a_], G[b_], A_override=sh); nullm.append((dd / np.maximum(base, 1e-9)).mean())
        dg[f'{a_}->{b_}'] = dict(rel_gain=float(rel.mean()), ci=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))],
                                 null_q95=float(np.quantile(nullm, .95)), exceeds_null=bool(rel.mean() > np.quantile(nullm, .95)))
    row['directed'] = dg
    asym = {}
    for a_, b_ in itertools.combinations('IBE', 2):
        if f'{a_}->{b_}' in dg and f'{b_}->{a_}' in dg:
            asym[f'{a_}->{b_} minus {b_}->{a_}'] = dg[f'{a_}->{b_}']['rel_gain'] - dg[f'{b_}->{a_}']['rel_gain']
    row['asymmetry'] = asym
    res['partitions'][name] = row
res['influence_matrix_rel_gain'] = Winf.round(5).tolist(); res['variable_names'] = names
json.dump(res, open(OUTJ, 'w'), indent=1)
print(json.dumps(samp, indent=1))
tab = sorted(res['partitions'].items(), key=lambda kv: kv[1]['one_frame_per_dish']['ratio_to_null_median'])
for n_, r_ in tab[:6] + tab[-3:]:
    print(n_, r_['sizes'], 'L=%.3f null_med=%.3f pct=%.3f' % (r_['one_frame_per_dish']['L'], r_['one_frame_per_dish']['null_median'], r_['one_frame_per_dish']['percentile_in_null']))
print('louvain', lou['sizes'], 'raw communities', lou['n_communities_raw'])
