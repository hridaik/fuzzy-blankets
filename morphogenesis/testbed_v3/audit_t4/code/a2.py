"""A2: event flags vs truth. Truth events are computed from TRUE positions/ids with the analyst's declared geometric definitions (single-linkage r_link = 1.6, m_min = 3, no hysteresis)."""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
from world3 import component_labels
TYPES = ['SPLIT', 'MERGE', 'EXTRUSION', 'ARRIVAL', 'LOSS']
def comps(X): lab = component_labels(X, CFG['r_link']); cnt = np.bincount(lab); return lab, cnt
def comps_h(X, ids, prev_pairs):
    """single-linkage with hysteresis: link if d < r_link, or d < 1.3 r_link when the pair was linked in the previous frame"""
    from scipy.sparse.csgraph import connected_components
    from scipy.sparse import csr_matrix
    n = len(X); D = np.linalg.norm(X[:, None] - X[None], axis=-1); A = D < CFG['r_link']
    if prev_pairs:
        hold = D < 1.3 * CFG['r_link']
        for a, b in prev_pairs:
            ia = np.where(ids == a)[0]; ib = np.where(ids == b)[0]
            if len(ia) and len(ib) and hold[ia[0], ib[0]]: A[ia[0], ib[0]] = A[ib[0], ia[0]] = True
    np.fill_diagonal(A, False); nc, lab = connected_components(csr_matrix(A), directed=False); pairs = [(int(ids[i]), int(ids[j])) for i, j in zip(*np.where(np.triu(A)))]
    return lab, np.bincount(lab, minlength=nc), pairs
def truth_events(run):
    tr = pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb')); ev = collections.defaultdict(list); prev = None; pp = []
    for t, pc in zip(tr['t'], tr['per_cell']):
        ids = np.array(pc['id']); X = np.array(pc['X']); lab, cnt, pp = comps_h(X, ids, pp) if len(X) else (np.zeros(0, int), np.zeros(0), []); big = np.where(cnt >= CFG['m_min'])[0]; nc = len(big); free = int(np.sum(~np.isin(lab, big)))
        if prev is not None:
            if nc > prev['nc']: ev['SPLIT'].append(t)
            if nc < prev['nc']: ev['MERGE'].append(t)
            if free > prev['free']: ev['EXTRUSION'].append(t)
            if free < prev['free'] or (set(ids.tolist()) - set(prev['ids'])): ev['ARRIVAL'].append(t)
            if set(prev['ids']) - set(ids.tolist()): ev['LOSS'].append(t)
        prev = dict(nc=nc, free=free, ids=ids.tolist())
    return {k: sorted(set(v)) for k, v in ev.items()}, tr
def analyst_events(run, lv):
    ev = collections.defaultdict(list)
    for f in t4cache(run, lv)['frames']:
        for e in f['events']:
            if e['type'] in TYPES: ev[e['type']].append(f['t'])
    return {k: sorted(set(v)) for k, v in ev.items()}
def match(a, b, win):
    """one-to-one greedy matching of sorted time lists; returns matched pairs (t_a, t_b)"""
    used = set(); pairs = []
    for x in a:
        c = [(abs(x - y), j, y) for j, y in enumerate(b) if j not in used and abs(x - y) <= win]
        if c: d, j, y = min(c); used.add(j); pairs.append((x, y))
    return pairs
def main():
    ST = collections.defaultdict(lambda: dict(flags=0, tp=0, true=0, tp_true=0, err=[])); OP = collections.defaultdict(lambda: dict(n=0, hit=0, delay=[]))
    for r in CAT:
        run = r['run']; fam = META[run]['family']; dt = float(r['frame_interval']); win = CFG['event_match_window_frame_intervals'] * dt; te, tr = truth_events(run)
        grp = fam if fam != 'stress' else 'ops_' + r['arm']
        for lv in ('O1', 'O2', 'O3a', 'O3b'):
            ae = analyst_events(run, lv)
            for ty in TYPES:
                a = ae.get(ty, []); b = te.get(ty, []); p = match(a, b, win); s = ST[(lv, grp, ty)]; s['flags'] += len(a); s['tp'] += len(p); s['true'] += len(b); s['tp_true'] += len(p); s['err'] += [x - y for x, y in p]
        # operation-level recall (O1/O2/O3): cut->SPLIT, extrude->EXTRUSION, replace->ARRIVAL & LOSS (arm 'treated' only)
        if fam == 'stress' and r['arm'] == 'treated':
            ev = [e for e in tr['hidden_events'] if e['kind'] in ('cut', 'extrude', 'replace', 'fuse')]; scn = META[run]['scn']
            want = {'cutx': ['SPLIT'], 'cuty': ['SPLIT'], 'extrude': ['EXTRUSION'], 'replace3': ['ARRIVAL', 'LOSS']}.get(scn, ['MERGE', 'SPLIT'] if scn.startswith('fuse') else [])
            for lv in ('O1', 'O2', 'O3a', 'O3b'):
                ae = analyst_events(run, lv)
                for e in ev:
                    t_op = e['t'] - 1e4 - 100.0
                    if e['kind'] == 'fuse': continue
                    for ty in want:
                        o = OP[(lv, scn, ty)]; o['n'] += 1; c = [x for x in ae.get(ty, []) if t_op - 1e-9 <= x <= t_op + win]
                        if c: o['hit'] += 1; o['delay'].append(min(c) - t_op)
    out = {}
    for k, s in ST.items(): out['|'.join(k)] = dict(flags=s['flags'], supported=s['tp'], precision=(s['tp'] / s['flags'] if s['flags'] else None), true_events=s['true'], recall=(s['tp'] / s['true'] if s['true'] else None), timing_err_median=(float(np.median(s['err'])) if s['err'] else None))
    outop = {'|'.join(k): dict(n=o['n'], hit=o['hit'], recall=o['hit'] / o['n'], delay_median=(float(np.median(o['delay'])) if o['delay'] else None)) for k, o in OP.items()}
    json.dump(dict(flags=out, operations=outop), open(os.path.join(AUD, 'data', 'a2_events.json'), 'w'), indent=1)
    print('OPERATION recall by level / scenario / expected flag'); [print(k, v) for k, v in sorted(outop.items())]
    print('\nFLAG precision/recall (grouped over types)')
    for lv in ('O1', 'O2', 'O3a', 'O3b'):
        for grp in ('natural', 'ops_treated', 'ops_untreated_control', 'ops_sham_treated', 'switch', 'decoy'):
            f = sum(out[f'{lv}|{grp}|{ty}']['flags'] for ty in TYPES if f'{lv}|{grp}|{ty}' in out); s = sum(out[f'{lv}|{grp}|{ty}']['supported'] for ty in TYPES if f'{lv}|{grp}|{ty}' in out); t = sum(out[f'{lv}|{grp}|{ty}']['true_events'] for ty in TYPES if f'{lv}|{grp}|{ty}' in out)
            print(lv, grp, 'flags', f, 'supported', s, 'prec', round(s / f, 3) if f else None, 'true events', t, 'recall', round(s / t, 3) if t else None)
if __name__ == "__main__": main()
