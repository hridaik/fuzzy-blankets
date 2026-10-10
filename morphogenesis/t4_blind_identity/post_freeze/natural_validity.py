"""Reporting only (written after freeze; no change to the pipeline): validity pass rates on natural dishes at every level,
development calibration / development validation / held-out natural validation dishes (dish bootstrap CIs)."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from t4 import io, summ
cat = io.catalog(); rng = np.random.default_rng(3)
nat = [r for r in cat if r['condition'] == 'N0']
groups = {'dev_calibration': [r for r in nat if r['split'] == 'development' and r['body_id'] % 2 == 0],
          'dev_validation': [r for r in nat if r['split'] == 'development' and r['body_id'] % 2 == 1],
          'heldout_natural': [r for r in nat if r['split'] != 'development']}
res = {}
for g, rs in groups.items():
    res[g] = {}
    for lv in ['O1', 'O2', 'O3a', 'O3b']:
        V = []; Vc = []; axf = []; state_change = []; ood_end = []
        for r in rs:
            o = summ.load_out(f"outputs/{r['run']}.json.gz"); L = o['levels'][lv]
            f = summ.founders(L)[0]; info = L['organisms'][f]
            V.append(info['V']); Vc.append(info['V_conservative']); axf.append([info['axis_fail_any'][a] for a in ('material', 'count', 'cohesion', 'shape', 'pattern')])
            state_change.append(len(info['state_changes']) > 0); ood_end.append(info['state_last'] == -1)
        def ci(v):
            v = np.array(v, float); bs = [v[rng.integers(0, len(v), len(v))].mean() for _ in range(2000)]
            return [round(float(v.mean()), 3), round(float(np.quantile(bs, .025)), 3), round(float(np.quantile(bs, .975)), 3)]
        res[g][lv] = dict(n=len(rs), V=ci(V), V_conservative=ci(Vc), state_change_any=ci(state_change), ood_at_end=ci(ood_end),
                          axis_fail=dict(zip(('material', 'count', 'cohesion', 'shape', 'pattern'), [round(float(x), 3) for x in np.mean(axf, 0)])))
json.dump(res, open('results_heldout/natural_validity.json', 'w'), indent=1)
for g in res:
    for lv in res[g]: print(g, lv, res[g][lv]['n'], 'V', res[g][lv]['V'], 'Vc', res[g][lv]['V_conservative'], 'chg', res[g][lv]['state_change_any'][0])
