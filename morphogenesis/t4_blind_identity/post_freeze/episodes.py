"""Reporting only (post-freeze corrective measure; the frozen `state_changes` list repeats an OOD change every frame):
number of label TRANSITIONS (consecutive filtered labels that differ, -2 excluded) per founder, treated - twin paired, pooled."""
import sys, json; sys.path.insert(0, '.')
import numpy as np
from t4 import io, summ
cat = io.catalog(); rng = np.random.default_rng(2)
def trans(run, lv):
    o = summ.load_out(f'outputs/{run}.json.gz'); L = o['levels'][lv]; tot = 0
    for oid in summ.founders(L):
        lab = [x['C3']['label'] for f in L['frames'] for x in f['organisms'] if str(x['id']) == oid]
        lab = [l for l in lab if l != -2]
        tot += sum(1 for a, b in zip(lab[:-1], lab[1:]) if a != b)
    return tot
res = {}
for sp, sel in (('development', lambda r: r['split'] == 'development'), ('heldout', lambda r: r['split'] != 'development')):
    g = {}
    for r in cat:
        if r['condition'].startswith('P') and sel(r): g.setdefault(r['group'], {})[r['arm']] = r['run']
    g = {k: v for k, v in g.items() if len(v) == 3}
    for lv in ('O1', 'O2'):
        a = np.array([trans(v['treated'], lv) - trans(v['untreated_control'], lv) for v in g.values()], float)
        b = np.array([trans(v['sham_treated'], lv) - trans(v['untreated_control'], lv) for v in g.values()], float)
        def ci(x): bs = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(2000)]; return [round(float(x.mean()), 2), round(float(np.quantile(bs, .025)), 2), round(float(np.quantile(bs, .975)), 2)]
        res[f'{sp}|{lv}'] = dict(n_triplets=len(g), treated_minus_twin=ci(a), sham_minus_twin=ci(b))
        print(sp, lv, len(g), 'treated-twin', ci(a), 'sham-twin', ci(b))
json.dump(res, open('results_heldout/state_transition_pairs.json', 'w'), indent=1)
