"""Part D: state discovery on natural development dishes, per level."""
import sys, json, pickle; sys.path.insert(0, '.')
import numpy as np
from t4 import io, layers, states
from t4.describe import pattern_names
cat = io.catalog()
nat = [r for r in cat if r['condition'] == 'N0' and r['split'] == 'development']
cal = [r for r in nat if r['body_id'] % 2 == 0]; val = [r for r in nat if r['body_id'] % 2 == 1]
rng = np.random.default_rng(1)
FEATS = sys.argv[1] if len(sys.argv) > 1 else 'pattern'

def feats(ch, kind):
    pn = pattern_names(ch)
    if kind == 'pattern': return pn
    if kind == 'inv': return [n for n in pn if not n.endswith('_sens')]
    if kind == 'sens': return [n for n in pn if n.endswith('_sens')]
    if kind == 'means': return [n for n in pn if n.endswith('_mean')]
    if kind == 'nosens': return [n for n in pn if not n.endswith('_sens')]
    if kind == 'noC45': return [n for n in pn if not n.startswith(('c4_', 'c5_'))]

def collect(rs, lv, names):
    X = []; dish = []
    for i, r in enumerate(rs):
        rec = pickle.load(open(f"cache/dev/{r['run']}_{lv}.pkl", 'rb'))
        for f in rec['frames']:
            o = max(f['orgs'], key=lambda o: o['n'])
            X.append([o['desc'][n] for n in names]); dish.append(i)
    return np.array(X), np.array(dish)

res = {}; models = {}
for lv in ['O1', 'O2', 'O3a', 'O3b']:
    ch = io.CHANNELS[lv]; names = feats(ch, FEATS)
    Xc, dc = collect(cal, lv, names); Xv, dv = collect(val, lv, names)
    pre = states.Preproc().fit(Xc); Zc, Zv = pre.transform(Xc), pre.transform(Xv)
    K = [1, 2, 3, 4, 5]
    cv = {k: [] for k in K}
    folds = np.arange(len(cal)) % 5; rng.shuffle(folds)
    for k in K:
        per_dish = np.zeros(len(cal))
        for f in range(5):
            tr = np.isin(dc, np.where(folds != f)[0]); te = ~tr
            g = states.GMM(k, seed=f).fit(Zc[tr]); ll = g.loglik(Zc[te])
            for d_ in np.where(folds == f)[0]: per_dish[d_] = ll[dc[te] == d_].mean()
        cv[k] = per_dish
    full = {k: states.GMM(k).fit(Zc) for k in K}
    val_ll = {k: full[k].loglik(Zv) for k in K}
    # stability: half-split ARI on validation frames
    stab = {}
    for k in K[1:]:
        a = []
        for rep in range(15):
            perm = rng.permutation(len(cal)); h1, h2 = perm[:len(cal) // 2], perm[len(cal) // 2:]
            g1 = states.GMM(k, seed=rep, n_init=4).fit(Zc[np.isin(dc, h1)]); g2 = states.GMM(k, seed=100 + rep, n_init=4).fit(Zc[np.isin(dc, h2)])
            a.append(states.ari(g1.posterior(Zv).argmax(1), g2.posterior(Zv).argmax(1)))
        stab[k] = float(np.mean(a))
    dd = pre.d
    row = dict(dim=int(dd), n_cal_frames=int(len(Zc)), n_cal_dishes=len(cal), features=names)
    row['cv_ll'] = {k: float(cv[k].mean()) for k in K}
    row['cv_ll_se'] = {k: float(cv[k].std() / np.sqrt(len(cal))) for k in K}
    # paired difference vs k=1 with dish bootstrap CI
    row['cv_gain_vs_1'] = {}
    for k in K[1:]:
        diff = cv[k] - cv[1]; bs = [diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(2000)]
        row['cv_gain_vs_1'][k] = [float(diff.mean()), float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]
    row['val_ll'] = {k: float(val_ll[k].mean()) for k in K}
    row['bic_cal'] = {k: float(-2 * full[k].train_ll + full[k].n_params(dd) * np.log(len(Zc))) for k in K}
    row['stability_ari'] = stab
    # ---- declared selection rule (see STATES.md): S = {k>=2: dish-bootstrap CI of CV gain vs k=1 > 0, half-split ARI >= 0.8,
    # smallest state >= 3% of calibration frames}; k* = smallest k in S whose successor brings no significant CV gain; fallback argmax ARI in S; else 1.
    sizes_k = {}
    for k in K[1:]:
        lab_k = full[k].posterior(Zc).argmax(1); sizes_k[k] = float(np.bincount(lab_k, minlength=k).min() / len(lab_k))
    S = [k for k in K[1:] if row['cv_gain_vs_1'][k][1] > 0 and stab[k] >= 0.8 and sizes_k[k] >= 0.03]
    def sig_gain(k):
        if k + 1 > K[-1]: return False
        diff = cv[k + 1] - cv[k]; bs = [diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(2000)]
        return float(np.quantile(bs, .025)) > 0
    row['S_admissible'] = S; row['min_state_frac'] = sizes_k
    if not S: row['k_star'] = 1
    else:
        el = [k for k in S if not sig_gain(k)]
        row['k_star'] = min(el) if el else max(S, key=lambda k: stab[k])
    best = max(K, key=lambda k: row['cv_ll'][k]); thr = row['cv_ll'][best] - row['cv_ll_se'][best]
    row['k_best_cv'] = best; row['k_1se'] = min(k for k in K if row['cv_ll'][k] >= thr)
    # state sizes and within-dish constancy for k_1se
    k = row['k_star']; g = full[k]
    lab = g.posterior(Zc).argmax(1)
    row['sizes_cal'] = np.bincount(lab, minlength=k).tolist()
    same = np.mean([len(set(lab[dc == d_])) == 1 for d_ in range(len(cal))]); row['frac_dishes_single_label'] = float(same)
    labv = g.posterior(Zv).argmax(1); row['frac_val_dishes_single_label'] = float(np.mean([len(set(labv[dv == d_])) == 1 for d_ in range(len(val))]))
    row['mean_max_posterior_val'] = float(g.posterior(Zv).max(1).mean())
    res[lv] = row
    if True:
        thr_ood = float(np.quantile(full[row['k_star']].loglik(Zc), 0.005))
        models[lv] = dict(pre=pre, gmm=full[row['k_star']], ood=thr_ood, names=names, k=row['k_star'])
    print(lv, FEATS, 'dim', dd, 'cv', {k: round(v, 3) for k, v in row['cv_ll'].items()}, 'k*', row['k_star'], '1se', row['k_1se'], 'stab', {k: round(v, 2) for k, v in stab.items()}, 'sizes', row['sizes_cal'], 'single-label dishes', row['frac_dishes_single_label'])
json.dump(res, open(f'calibration/states_{FEATS}.json', 'w'), indent=1)

pickle.dump(models, open(f'calibration/state_models_{FEATS}.pkl', 'wb'))
