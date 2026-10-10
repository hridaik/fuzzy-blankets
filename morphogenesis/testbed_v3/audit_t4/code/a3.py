"""A3: identity layers vs truth (C1 material, C2 geometric vs pattern axes, light-run attribution)."""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
from truth2 import GROUPS
def t2(run): return pickle.load(open(os.path.join(AUD, 'data', 'truth2', run + '.pkl'), 'rb'))
def founder_fails(run, lv):
    o = t4out(run)['levels'][lv]; res = None
    for oid, org in o['organisms'].items():
        if org['origin'] == 'founder':
            f = org['axis_fail_any']; res = res or dict(material=False, count=False, cohesion=False, shape=False, pattern=False)
            for k in res: res[k] = res[k] or bool(f.get(k))
    return res
def main():
    nat = [r['run'] for r in CAT if META[r['run']]['family'] == 'natural']; S = {}
    for r in nat:
        s = t2(r); k = {'shape': np.nanmax(s['shape_dev']), 'mst': np.nanmax(s['mst'])}
        for g in GROUPS: k[g] = np.nanmax(s[f'pat_{g}'])
        for a, b in k.items(): S.setdefault(a, []).append(b)
    thr = {a: float(np.quantile(b, CFG['geometric_truth_natural_envelope_quantile'])) for a, b in S.items()}; print('truth thresholds (95% of natural per-dish max)', {a: round(b, 4) for a, b in thr.items()})
    rows = []
    for r in CAT:
        run = r['run']; m = META[run]; s = t2(run); fam = m['family']
        geo = bool((np.nanmax(s['shape_dev']) > thr['shape']) or (np.nanmax(s['mst']) > thr['mst']) or (s['ncomp'] != 1).any() or (np.abs(s['n'] - s['n'][0]) >= 1).any())
        pat = {g: bool(np.nanmax(s[f'pat_{g}']) > thr[g]) for g in GROUPS}
        cond = r['condition']; arm = r['arm']; memlight = fam == 'switch' and m['channel'] in ('MA', 'MB'); decoylight = fam == 'decoy' and m['channel'] is not None
        cls = 'natural' if fam == 'natural' else ('memory_light' if memlight else ('structural/other_light' if decoylight else ('device' if fam == 'decoy' else ('ops_' + arm))))
        if fam == 'switch' and m['kind'] == 'sham': cls = 'memory_light_sham'
        row = dict(run=run, cls=cls, cond=cond, arm=arm, true_geom=geo, **{f'true_pat_{g}': v for g, v in pat.items()}, split=r['split'])
        for lv in ('O1', 'O2', 'O3a', 'O3b'): row[lv] = founder_fails(run, lv)
        rows.append(row)
    json.dump(dict(thr=thr, rows=rows), open(os.path.join(AUD, 'data', 'a3_c2.json'), 'w'))
    for lv in ('O1', 'O2', 'O3a', 'O3b'):
        print('\n==', lv)
        for cls in ('natural', 'memory_light', 'memory_light_sham', 'structural/other_light', 'device', 'ops_treated', 'ops_untreated_control', 'ops_sham_treated'):
            R = [x for x in rows if x['cls'] == cls and x[lv]]
            if not R: continue
            geoF = np.array([any(x[lv][k] for k in ('count', 'cohesion', 'shape')) for x in R]); patF = np.array([x[lv]['pattern'] for x in R]); anyc2 = geoF | patF; tg = np.array([x['true_geom'] for x in R]); tp = np.array([x['true_pat_memory'] or x['true_pat_reporter'] or x['true_pat_structural'] for x in R])
            only_pat = int((patF & ~geoF).sum()); only_geo = int((geoF & ~patF).sum()); both = int((geoF & patF).sum())
            falsegeo = int((geoF & ~tg).sum())
            print(f'{cls:24s} n={len(R):3d} C2-changed={int(anyc2.sum()):3d} (pattern only {only_pat}, geometry only {only_geo}, both {both}) | true geom change {int(tg.sum())} | geometry flagged though truth geometry within natural: {falsegeo} | true pattern change {int(tp.sum())}; pattern flagged & truth {int((patF&tp).sum())} / pattern flagged & truth none {int((patF&~tp).sum())}')
if __name__ == "__main__": main()
