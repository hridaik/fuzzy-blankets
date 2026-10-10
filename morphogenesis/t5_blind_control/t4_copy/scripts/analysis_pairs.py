"""Part E: triplets (event / twin / sham), opaque-label summaries with cluster-bootstrap CIs. usage: analysis_pairs.py OUTDIR SPLITSEL RESULT_JSON
SPLITSEL: development | heldout"""
import sys, json, glob, os, collections; sys.path.insert(0, '.')
import numpy as np
from t4 import io, summ
OUT, SEL, RES = sys.argv[1], sys.argv[2], sys.argv[3]
LEVELS = ['O1', 'O2', 'O3a', 'O3b']
cat = {r['run']: r for r in io.catalog()}
rng = np.random.default_rng(7)
runs = [r for r in cat.values() if (r['split'] == 'development') == (SEL == 'development') and r['condition'] != 'N0']
M = {}
for r in runs:
    p = f"{OUT}/{r['run']}.json.gz"
    if not os.path.exists(p): continue
    o = summ.load_out(p)
    M[r['run']] = {lv: summ.run_metrics(o, lv) for lv in LEVELS}

def boot_prop(vals, clusters, B=2000):
    vals = np.asarray(vals, float); cl = np.asarray(clusters); u = np.unique(cl)
    if len(u) == 0: return [float('nan')] * 3
    idx = {c: np.where(cl == c)[0] for c in u}
    bs = []
    for _ in range(B):
        ch = rng.choice(u, len(u)); bs.append(np.concatenate([vals[idx[c]] for c in ch]).mean())
    return [float(vals.mean()), float(np.quantile(bs, .025)), float(np.quantile(bs, .975))]

res = dict(triplets={}, by_condition={}, dissociation={})
# ---- triplets (P*)
groups = collections.defaultdict(dict)
for r in runs:
    if r['run'] in M and r['condition'].startswith('P'): groups[r['group']][r['arm']] = r
for g, d in sorted(groups.items()):
    if len(d) < 3: continue
    row = dict(condition=d['treated']['condition'], body=d['treated']['body_id'], onset=d['treated']['onset'])
    for lv in LEVELS:
        ms = {a: M[d[a]['run']][lv] for a in ('treated', 'untreated_control', 'sham_treated')}
        def agg(m): return dict(V=float(np.mean(m['V'])), Vc=float(np.mean(m['Vc'])), minJ=float(np.min(m['minJ'])), max_shape=float(np.max(m['max_shape'])),
                                max_pattern=float(np.max(m['max_pattern'])), max_ndev=float(np.max(m['max_ndev'])), n_state_changes=m['n_state_changes'],
                                layers=[l for l in m['layers']], events={k: v for k, v in m['events'].items()})
        A = {a: agg(ms[a]) for a in ms}
        row[lv] = dict(arms=A,
                       paired_treated_minus_twin={k: A['treated'][k] - A['untreated_control'][k] for k in ('V', 'Vc', 'minJ', 'max_shape', 'max_pattern', 'max_ndev', 'n_state_changes')},
                       paired_sham_minus_twin={k: A['sham_treated'][k] - A['untreated_control'][k] for k in ('V', 'Vc', 'minJ', 'max_shape', 'max_pattern', 'max_ndev', 'n_state_changes')},
                       sham_matches_twin=bool(A['sham_treated']['V'] == A['untreated_control']['V'] and not A['sham_treated']['events'] and A['sham_treated']['n_state_changes'] == A['untreated_control']['n_state_changes']))
    res['triplets'][g] = row
# ---- by opaque condition & arm
for lv in LEVELS:
    by = collections.defaultdict(list)
    for r in runs:
        if r['run'] not in M: continue
        m = M[r['run']][lv]
        cluster = r['group'] if r['condition'].startswith('P') else r['body_id']
        for oid, lay in enumerate(m['layers']):
            by[(r['condition'], r['arm'])].append((cluster, m['V'][oid], m['Vc'][oid], lay))
    tab = {}
    for (cond, arm), v in sorted(by.items()):
        cl = [x[0] for x in v]
        t = dict(n_organisms=len(v), V=boot_prop([x[1] for x in v], cl), V_conservative=boot_prop([x[2] for x in v], cl))
        for layer in ('C1', 'C2', 'C3'):
            for c in ('persist', 'change', 'break'):
                t[f'{layer}_{c}'] = boot_prop([x[3][layer] == c for x in v], cl)
        tab[f'{cond}|{arm}'] = t
    res['by_condition'][lv] = tab
    # dissociation counts
    dis = collections.Counter()
    for (cond, arm), v in by.items():
        if arm == 'untreated_control' or arm == 'sham_treated': continue
        for x in v: dis[(x[3]['C1'], x[3]['C2'], x[3]['C3'])] += 1
    res['dissociation'][lv] = {'/'.join(k): n for k, n in sorted(dis.items(), key=lambda kv: -kv[1])}
json.dump(res, open(RES, 'w'), indent=1)
print('triplets', len(res['triplets']), 'conditions', len(res['by_condition']['O1']))
