import pickle, glob, json, os, numpy as np, sys
sys.path.insert(0, '.')
rows = []
for pk in sorted(glob.glob('../data/stress_raw/*.pkl')):
    b = os.path.basename(pk)[:-4].split('_'); seed = int(b[-1]); kind = b[-2]; scn = '_'.join(b[:-2])
    d = pickle.load(open(pk, 'rb')); ev = d['event']['hidden']['events']; T = [e['t'] - 1e4 for e in ev if e['kind'] in ('remove', 'insert', 'extrude', 'cut')]
    onset = min(T) if T else 0.0
    def diff(a, b_, pre=None):
        fa, fb = d[a]['frames'], d[b_]['frames']; m = 0.0
        for x, y in zip(fa, fb):
            if pre is not None and x['t'] - fa[0]['t'] >= pre: break
            m = max(m, float(np.abs(x['X'] - y['X']).max()))
        return m
    last = d['event']['frames'][-1]; lt = d['twin']['frames'][-1]
    rows.append(dict(scn=scn, kind=kind, seed=seed, onset=onset, pre_onset_event_vs_twin=diff('event', 'twin', pre=onset if onset > 0 else None) if not scn.startswith('fuse') else None, sham_vs_twin=diff('sham', 'twin'), post_event_vs_twin_final=float(np.abs(last['X'] - lt['X']).max()) if last['X'].shape == lt['X'].shape else None))
json.dump(rows, open('../data/stress_check.json', 'w'), indent=1)
import collections
for scn in sorted(set(r['scn'] for r in rows)):
    r = [x for x in rows if x['scn'] == scn]; print(scn, 'n', len(r), 'max pre-onset event-vs-twin', max([x['pre_onset_event_vs_twin'] or 0 for x in r]), 'max sham-vs-twin', max(x['sham_vs_twin'] for x in r), 'median post-event divergence', np.median([x['post_event_vs_twin_final'] for x in r if x['post_event_vs_twin_final'] is not None]) if any(x['post_event_vs_twin_final'] is not None for x in r) else None)
