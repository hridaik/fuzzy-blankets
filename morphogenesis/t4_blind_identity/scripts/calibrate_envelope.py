"""Validity-envelope calibration on NATURAL development dishes: calibration subset (body_id even) -> bounds;
validation subset (body_id odd) -> check. Per level."""
import sys, json, pickle; sys.path.insert(0, '.')
import numpy as np
from t4 import io, layers
from t4.describe import pattern_names
cat = io.catalog()
nat = [r for r in cat if r['condition'] == 'N0' and r['split'] == 'development']
cal = [r for r in nat if r['body_id'] % 2 == 0]; val = [r for r in nat if r['body_id'] % 2 == 1]
TARGET = 0.90
rng = np.random.default_rng(0)

def load(r, lv): return pickle.load(open(f"cache/dev/{r['run']}_{lv}.pkl", 'rb'))

def main_lineage(rec):
    L, _ = layers.lineages(rec)
    k = max(L, key=lambda o: len(L[o]))
    return k, L[k]

out = {}
for lv in ['O1', 'O2', 'O3a', 'O3b']:
    recs_c = [load(r, lv) for r in cal]; recs_v = [load(r, lv) for r in val]
    pn = pattern_names(recs_c[0]['ch'])
    diffs = []
    for rec in recs_c:
        o, seq = main_lineage(rec)
        P = np.array([[s[1]['desc'][n] for n in pn] for s in seq]); diffs.append(P[1:] - P[0])
    pat_sd = np.maximum(np.concatenate(diffs).std(0), 1e-3)
    def axes(recs):
        res = []
        for rec in recs:
            o, seq = main_lineage(rec)
            ser = layers.layer_series(rec, o, layers.smooth_seq(rec, seq), pat_sd)
            res.append(layers.axis_values(ser)[1:])      # frames >= 1
        return res
    A_c, A_v = axes(recs_c), axes(recs_v)
    allc = np.concatenate(A_c)
    def bounds_for(alpha): return np.quantile(allc, 1 - alpha, axis=0)
    def pass_rate(A, b): return float(np.mean([np.all(a <= b + 1e-9) for a in A]))
    alphas = np.concatenate([np.geomspace(1e-5, 0.2, 200)])
    prs = [pass_rate(A_c, bounds_for(a)) for a in alphas]
    # alpha that gets closest to TARGET from above (pass >= target), the tightest such bounds
    ok = [i for i, p in enumerate(prs) if p >= TARGET]
    i = max(ok) if ok else int(np.argmax(prs)); alpha = float(alphas[i]); b = bounds_for(alpha)
    # dish bootstrap CI of validation pass rate
    pv = np.array([np.all(a <= b + 1e-9) for a in A_v], float)
    bs = [pv[rng.integers(0, len(pv), len(pv))].mean() for _ in range(2000)]
    # per-axis fail rates (dish level) cal / val
    fa_c = (np.array([(a > b + 1e-9).any(0) for a in A_c])).mean(0); fa_v = (np.array([(a > b + 1e-9).any(0) for a in A_v])).mean(0)
    out[lv] = dict(alpha=alpha, bounds=dict(zip(layers.AXES, map(float, b))), pat_sd=dict(zip(pn, map(float, pat_sd))),
                   cal_pass=float(prs[i]), val_pass=float(pv.mean()), val_pass_ci=[float(np.quantile(bs, .025)), float(np.quantile(bs, .975))],
                   axis_fail_cal=dict(zip(layers.AXES, map(float, fa_c))), axis_fail_val=dict(zip(layers.AXES, map(float, fa_v))),
                   n_cal=len(A_c), n_val=len(A_v))
    print(lv, json.dumps({k: v for k, v in out[lv].items() if k != 'pat_sd'}, indent=None))
json.dump(out, open('calibration/envelope.json', 'w'), indent=1)
