"""A4: T5's blind dose map (centre / side / tail / head, duration curve) vs the true per-place thresholds (SWITCH_V3 h3_bisect.json) and the connectivity rule.
Where do T5's discs fall in the TRUE body frame (template coordinates, true cell types)?"""
import sys, os, json, numpy as np, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truth import *
from lib import *
from scipy.optimize import linear_sum_assignment
from scipy.stats import spearmanr
sys.path.insert(0, os.path.join(V3, '..', 'testbed_v2', 'code'))
from engine2 import make_template2
from shape import cell_types
TM = make_template2(); XS = TM.Xs.T.copy(); CT_TEMPLATE = cell_types(TM.CL); TYPE_NAME = {1: 'head', 2: 'trunk', 3: 'limb', 4: 'tail'}
def softmax(M): e = np.exp(M - M.max(1, keepdims=True)); return e / e.sum(1, keepdims=True)
def frame_map(X, MU):
    """true body frame: cell->place by Hungarian on place beliefs, proper Procrustes of the template onto the cells. Returns a function arena->template and the assignment"""
    q = softmax(MU); r, c = linear_sum_assignment(-np.log(q + 1e-12)); P = XS[c]                 # place coordinates of each cell
    a = P - P.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    to_arena = lambda p: (R @ (np.atleast_2d(p) - P.mean(0)).T).T + X.mean(0); to_tpl = lambda x: (R.T @ (np.atleast_2d(x) - X.mean(0)).T).T + P.mean(0)
    return to_tpl, to_arena, c, float(np.sqrt(((to_arena(P) - X) ** 2).sum(1).mean()))
# ---- T5 blind map
B2 = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'b2_results.jsonl'))]
blind = collections.defaultdict(list)
for r in B2:
    if r['dose_star'] is not None: blind[(r['loc'], r['dur'])].append(r['dose_star'])
gm = lambda v: float(np.exp(np.mean(np.log(v))))
BM = {f'{k[0]}|{k[1]}': dict(n=len(v), dose_gm=gm(v), doses=v) for k, v in blind.items()}
ctr = {d: BM[f'C|{d}']['dose_gm'] for d in (10.0, 20.0, 40.0)}
rel = {f'{loc}|{d}': BM[f'{loc}|{d}']['dose_gm'] / ctr[d] for loc in ('C', 'side', 'tail', 'head', 'whole') for d in (10.0, 20.0, 40.0) if f'{loc}|{d}' in BM}
# per-dish relative dose (same dish) for 20-40 tu
per_dish = collections.defaultdict(dict)
for r in B2:
    if r['dose_star'] is not None: per_dish[(r['seed'], r['label'], r['dur'])][r['loc']] = r['dose_star']
rel_dish = collections.defaultdict(list)
for k, v in per_dish.items():
    if 'C' in v and k[2] >= 20:
        for loc, ds in v.items(): rel_dish[loc].append(ds / v['C'])
rel_dish = {loc: dict(n=len(v), gm=gm(v), min=float(min(v)), max=float(max(v))) for loc, v in rel_dish.items()}
# ---- placement of T5 discs in the true body frame
place = {}
for seed in (5001, 5002, 5004, 5005):
    # one B2 trial per location
    ex = make_dish(seed); ex.run_sched(20.0, [], sham=False, obs_times=[]); X = ex.w.X.copy(); MU = ex.w.MU.copy(); to_tpl, to_arena, assign, rms = frame_map(X, MU)
    ct_cells = np.array([CT_TEMPLATE[assign[i]] for i in range(24)])
    for loc in ('C', 'side', 'tail', 'head'):
        tr = next(r for r in B2 if r['seed'] == seed and r['loc'] == loc and r['dur'] == 20.0); La = load_ep(tr['trials'][0]['episode'], 'dev')['actions'][0]
        xy = np.array(La['mask']['xy']); rad = La['mask']['radius']; lit = np.where(np.linalg.norm(X - xy, axis=1) <= rad)[0]
        ctr_t = to_tpl(xy)[0]; place[(seed, loc)] = dict(centre_template=ctr_t.tolist(), body_frame_T5=La['body_frame'], n_lit=int(len(lit)), places_lit=sorted(int(assign[i]) for i in lit), types_lit=dict(collections.Counter(TYPE_NAME[int(ct_cells[i])] for i in lit)), frame_rms=rms)
agg = {}
for loc in ('C', 'side', 'tail', 'head'):
    cs = np.array([place[(s, loc)]['centre_template'] for s in (5001, 5002, 5004, 5005)]); agg[loc] = dict(mean_centre_template_xy=cs.mean(0).tolist(), sd=cs.std(0).tolist(), n_lit=[place[(s, loc)]['n_lit'] for s in (5001, 5002, 5004, 5005)],
        places_lit=[place[(s, loc)]['places_lit'] for s in (5001, 5002, 5004, 5005)], types_lit=[place[(s, loc)]['types_lit'] for s in (5001, 5002, 5004, 5005)])
# controller discs of the 60 held-out dishes
R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'heldout_summary.jsonl'))]
ctrl = [r for r in R if r['arm'] == 'ctrl' and r['reason'] not in ('quota_skip', 'baseline_not_clean')]
cc = []
for r in ctrl:
    h, e = load_hidden(r['episode']); k = 20; to_tpl, to_arena, assign, rms = frame_map(h['X'][k], h['MU'][k]); La = load_ep(r['episode'])['actions'][0]
    xy = np.array(La['mask']['xy']); lit = np.where(np.linalg.norm(h['X'][k] - xy, axis=1) <= La['mask']['radius'])[0]
    cc.append(dict(seed=r['seed'], centre_template=to_tpl(xy)[0].tolist(), places_lit=sorted(int(assign[i]) for i in lit), n_lit=int(len(lit)), types_lit=dict(collections.Counter(TYPE_NAME[int(CT_TEMPLATE[assign[i]])] for i in lit))))
cc_mean = np.mean([c['centre_template'] for c in cc], 0)
place_freq = collections.Counter(p for c in cc for p in c['places_lit'])
# ---- true per-place thresholds (SWITCH_V3) and connectivity
H3 = json.load(open(os.path.join(V3, 'data', 'h3_bisect.json')))
W = np.exp(-np.linalg.norm(XS[:, None] - XS[None], axis=-1)); np.fill_diagonal(W, 0)
def lit_set(c, rad=1.5): return np.where(np.linalg.norm(XS - c, axis=1) <= rad)[0]
def connectivity(L): m = np.zeros(24, bool); m[L] = True; return float(W[np.ix_(m, ~m)].sum())
truth = {}
for dur_key, dur in (('4g', 6.6667), ('16g', 26.6667)):
    rows = []
    for x in H3:
        if x['state'] == 'a' and x['centre'] >= 0 and abs(x['dur'] - dur) < 0.01 and x.get('thr'):
            L = lit_set(XS[x['centre']]); rows.append(dict(centre=x['centre'], thr_amp=x['thr'], dose=x['dose'], n_lit=x['n_lit'], conn=connectivity(L), xy=XS[x['centre']].tolist(), type=TYPE_NAME[int(CT_TEMPLATE[x['centre']])]))
    sp_amp = spearmanr([r['conn'] for r in rows], [r['thr_amp'] for r in rows])[0]; sp_dose = spearmanr([r['conn'] for r in rows], [r['dose'] for r in rows])[0]
    # power law fit log thr_amp = a + b log conn
    b, a = np.polyfit(np.log([r['conn'] for r in rows]), np.log([r['thr_amp'] for r in rows]), 1)
    truth[dur_key] = dict(rows=rows, spearman_conn_amp=float(sp_amp), spearman_conn_dose=float(sp_dose), fit_loga=float(a), fit_b=float(b))
# T5 discs: nearest-place threshold and connectivity prediction (at 16/g ~ 26.7 tu is nearest to T5's 20-40 tu)
pred = {}
for loc in ('C', 'side', 'tail', 'head'):
    c = np.array(agg[loc]['mean_centre_template_xy']); L = lit_set(c); cn = connectivity(L)
    nearest = int(np.argmin(np.linalg.norm(XS - c, axis=1))); row = next(r for r in truth['16g']['rows'] if r['centre'] == nearest)
    a, b = truth['16g']['fit_loga'], truth['16g']['fit_b']; amp_pred = float(np.exp(a + b * np.log(cn)))
    pred[loc] = dict(centre_template=c.tolist(), n_lit_template=int(len(L)), conn=cn, nearest_place=nearest, nearest_place_dose_16g=row['dose'], nearest_place_thr_amp_16g=row['thr_amp'], conn_rule_amp=amp_pred, conn_rule_dose=amp_pred * 26.667 * len(L))
rel_true = {loc: pred[loc]['nearest_place_dose_16g'] / pred['C']['nearest_place_dose_16g'] for loc in pred}; rel_rule = {loc: pred[loc]['conn_rule_dose'] / pred['C']['conn_rule_dose'] for loc in pred}
out = dict(T5_blind_map=BM, T5_relative_dose_vs_centre=rel, T5_relative_dose_same_dish=rel_dish, T5_discs_in_true_frame=agg, controller_disc=dict(mean_centre_template_xy=cc_mean.tolist(), n_lit_median=float(np.median([c['n_lit'] for c in cc])), place_freq={int(k): v for k, v in sorted(place_freq.items())}, per_dish=cc),
    true_switch_v3=truth, T5_discs_predicted=pred, relative_dose_true_nearest_place=rel_true, relative_dose_connectivity_rule=rel_rule, template=dict(xy=XS.tolist(), type=[TYPE_NAME[int(t)] for t in CT_TEMPLATE]))
json.dump(out, open('../data/a4_location.json', 'w'), indent=1, default=float)
print('T5 rel dose (same dish, >=20tu):', rel_dish); print('rel by loc/dur', {k: round(v, 2) for k, v in rel.items()})
for loc in agg: print(loc, 'template centre', np.round(agg[loc]['mean_centre_template_xy'], 2), 'sd', np.round(agg[loc]['sd'], 2), 'lit', agg[loc]['n_lit'], agg[loc]['types_lit'][0], 'places', agg[loc]['places_lit'][0])
print('controller disc centre (template)', cc_mean, 'places freq', dict(place_freq))
print('spearman conn-amp', {k: (round(v['spearman_conn_amp'], 3), round(v['spearman_conn_dose'], 3)) for k, v in truth.items()})
print('pred', {k: (v['nearest_place'], round(v['conn'], 2), round(v['nearest_place_dose_16g'], 0)) for k, v in pred.items()}); print('rel true nearest', {k: round(v, 2) for k, v in rel_true.items()}, 'rule', {k: round(v, 2) for k, v in rel_rule.items()})
