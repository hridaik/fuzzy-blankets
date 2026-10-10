"""Part B internal-consistency report: O2 / O3a / O3b versus O1 on runs that have all levels. usage: consistency.py CACHE_TAG SPLITSEL OUT.json"""
import sys, json, pickle, collections; sys.path.insert(0, '.')
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from multiprocessing import Pool
from t4 import io
TAG, SEL, OUTJ = sys.argv[1:4]
cat = [r for r in io.catalog() if (r['split'] == 'development') == (SEL == 'development')]

def one(r):
    L = {lv: pickle.load(open(f"cache/{TAG}/{r['run']}_{lv}.pkl", 'rb')) for lv in ('O1', 'O2', 'O3a', 'O3b')}
    o1 = L['O1']; res = {}
    ev1 = collections.defaultdict(list)
    for f in o1['frames']:
        for e in f['events']: ev1[e['type']].append(f['k'])
    raw1 = io.point_frames(r['run'], 'O1')
    for lv in ('O2', 'O3a', 'O3b'):
        rc = L[lv]; d = dict(frames=len(rc['frames']))
        ev = collections.defaultdict(list)
        # O3 images are subsampled in time for operation runs (every 2nd frame): align by time
        t1 = {f['t']: f for f in o1['frames']}
        same = []; cen = []; ang = []; sgn = []; cnt = []; segd = []
        for f in rc['frames']:
            for e in f['events']: ev[e['type']].append(f['t'])
            g = t1.get(f['t'])
            if g is None: continue
            same.append(len(f['orgs']) == len(g['orgs']))
            if f['orgs'] and g['orgs']:
                C1 = np.array([o['centroid'] for o in g['orgs']]); C2 = np.array([o['centroid'] for o in f['orgs']])
                D = cdist(C2, C1); rr, cc = linear_sum_assignment(D)
                for a, b in zip(rr, cc):
                    if D[a, b] < 3.0:
                        cen.append(D[a, b]); e2 = np.array(f['orgs'][a]['e1']); e1 = np.array(g['orgs'][b]['e1'])
                        c = float(e1 @ e2); ang.append(abs(c)); sgn.append(c > 0)
                        if lv != 'O2': cnt.append(f['orgs'][a]['desc']['n'] - g['orgs'][b]['desc']['n'])
                        else: cnt.append(f['orgs'][a]['n'] - g['orgs'][b]['n'])
        d.update(org_count_agree=float(np.mean(same)) if same else None, centroid_err_median=float(np.median(cen)) if cen else None,
                 axis_abs_cos_median=float(np.median(ang)) if ang else None, sign_agree=float(np.mean(sgn)) if sgn else None,
                 count_err_mean=float(np.mean(cnt)) if cnt else None, count_err_abs_mean=float(np.mean(np.abs(cnt))) if cnt else None)
        # event agreement: first time of SPLIT/MERGE in O1 vs this level (within 2 frame intervals)
        for et in ('SPLIT', 'MERGE'):
            t_o1 = [o1['frames'][k]['t'] for k in ev1.get(et, [])]
            dt_ = r['frame_interval'] * 2
            d[f'{et}_o1_n'] = len(t_o1); d[f'{et}_lvl_n'] = len(ev.get(et, []))
            d[f'{et}_matched'] = int(sum(any(abs(t - u) <= dt_ for u in ev.get(et, [])) for t in t_o1))
        res[lv] = d
    # O2 cell-link accuracy vs O1
    ct = None
    if True:
        o2 = io.point_frames(r['run'], 'O2'); rc = L['O2']
        ok = n = 0
        prev = None
        for a, b, f in zip(raw1, o2, rc['frames']):
            D = cdist(b['xy'], a['xy']); gt = a['ids'][D.argmin(1)]
            tid = np.array(f['cells']['ids'])
            if prev is not None:
                m0 = {g: i for i, g in zip(*prev)}
                ok += sum(m0.get(g, -9) == i for i, g in zip(tid, gt)); n += len(tid)
            prev = (tid, gt)
        res['O2']['cell_link_correct_frac'] = ok / max(n, 1)
    # O3 segmentation vs O1 (pseudo-cell matching distance; count from mass)
    for lv in ('O3a',):
        rc = L[lv]; md = []; ce = []
        t1 = {f['t']: i for i, f in enumerate(o1['frames'])}
        for f in rc['frames']:
            i = t1.get(f['t'])
            if i is None: continue
            xs = np.vstack([np.array(o['_pseudo']['xy']) for o in f['orgs']]) if f['orgs'] else np.zeros((0, 2))
            D = cdist(xs, raw1[i]['xy']); rr, cc = linear_sum_assignment(D)
            md.append(float(D[rr, cc].mean())); ce.append(len(xs) - len(raw1[i]['xy']))
        res['O3a']['seg_match_dist_mean'] = float(np.mean(md)); res['O3a']['seg_count_err_mean'] = float(np.mean(ce)); res['O3a']['seg_count_err_sd'] = float(np.std(ce))
    return r['run'], r['condition'], r['arm'], res

if __name__ == '__main__':
    with Pool(8) as P: out = P.map(one, cat, chunksize=4)
    agg = {}
    for lv in ('O2', 'O3a', 'O3b'):
        for grp in ('N0', 'ops', 'light_dev'):
            sel = [x for x in out if (x[1] == 'N0' if grp == 'N0' else (x[1].startswith('P') if grp == 'ops' else x[1][0] in 'TX'))]
            row = {}
            for k in sel[0][3][lv]:
                vals = [x[3][lv][k] for x in sel if x[3][lv].get(k) is not None]
                if k.endswith('_n') or k.endswith('_matched'): row[k] = int(np.sum(vals))
                elif k != 'frames': row[k] = float(np.mean(vals))
            row['n_runs'] = len(sel); agg[f'{lv}|{grp}'] = row
    for k, v in agg.items(): print(k, {a: round(b, 3) if isinstance(b, float) else b for a, b in v.items()})
    json.dump(dict(aggregate=agg, per_run={x[0]: x[3] for x in out}), open(OUTJ, 'w'))
