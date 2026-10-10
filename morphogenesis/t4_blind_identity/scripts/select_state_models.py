"""Pick, per level, the descriptor family (pattern / inv / sens) with the highest half-split stability at its k*, on the
calibration dishes with ARI measured on the development-validation dishes. Writes calibration/state_models.pkl."""
import sys; sys.path.insert(0, "."); import json, pickle
import numpy as np
from t4 import io, states
fam = ['pattern', 'inv', 'sens']
R = {f: json.load(open(f'calibration/states_{f}.json')) for f in fam}
M = {f: pickle.load(open(f'calibration/state_models_{f}.pkl', 'rb')) for f in fam}
cat = io.catalog()
val = [r for r in cat if r['condition'] == 'N0' and r['split'] == 'development' and r['body_id'] % 2 == 1]
cal = [r for r in cat if r['condition'] == 'N0' and r['split'] == 'development' and r['body_id'] % 2 == 0]
def feats(lv, names, rs):
    out = []
    for r in rs:
        rec = pickle.load(open(f"cache/dev/{r['run']}_{lv}.pkl", 'rb'))
        for f in rec['frames']:
            o = max(f['orgs'], key=lambda o: o['n']); out.append([o['desc'][n] for n in names])
    return np.array(out)
def med_gain(lv, f):
    m = M[f][lv]; Zc = m['pre'].transform(feats(lv, m['names'], cal)); Zv = m['pre'].transform(feats(lv, m['names'], val))
    if m['k'] == 1: return 0.0, 0.0
    d = m['gmm'].loglik(Zv) - states.GMM(1).fit(Zc).loglik(Zv)
    return float(np.median(d)), float((d > 0).mean())
sel = {}; models = {}
for lv in ['O1', 'O2', 'O3a', 'O3b']:
    rows = []
    for f in fam:
        r = R[f][lv]; k = r['k_star']
        stab = 1.0 if k == 1 else r['stability_ari'][str(k)]
        mg, fp = med_gain(lv, f)
        rows.append((f, k, stab, r['val_ll'][str(k)] - r['val_ll']['1'], mg, fp))
    # a family must show k>=2 with stability>=0.8; choose highest stability, ties -> fewer states
    ok = [x for x in rows if x[1] >= 2 and x[2] >= 0.8 and x[4] > 0]
    pick = max(ok, key=lambda x: (round(x[2], 2), -x[1])) if ok else ('pattern', R['pattern'][lv]['k_star'], None, None, None, None)
    sel[lv] = dict(chosen=pick[0], k=pick[1], stability=pick[2], table=[dict(family=a, k=b, stability=c, val_ll_gain_mean=d, val_ll_gain_median=e, val_frac_frames_improved=g) for a, b, c, d, e, g in rows])
    models[lv] = M[pick[0]][lv]; models[lv]['family'] = pick[0]
    print(lv, sel[lv]['chosen'], pick[1], pick[2])
json.dump(sel, open('calibration/states_selection.json', 'w'), indent=1)
pickle.dump(models, open('calibration/state_models.pkl', 'wb'))
