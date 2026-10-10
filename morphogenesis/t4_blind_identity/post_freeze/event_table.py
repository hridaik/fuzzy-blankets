"""Reporting only: event-flag rates by opaque condition/arm at O1/O2/O3b and natural false-flag rates."""
import sys, json, collections; sys.path.insert(0, '.')
import numpy as np
from t4 import io, summ
cat = io.catalog(); res = {}
for lv in ('O1', 'O2', 'O3b'):
    by = collections.defaultdict(list)
    for r in cat:
        o = summ.load_out(f"outputs/{r['run']}.json.gz"); ev = o['levels'][lv]['summary']['events']
        key = ('N0' if r['condition'] == 'N0' else r['condition'], r['arm'], 'dev' if r['split'] == 'development' else 'heldout')
        row = {t: (ev[t]['n'] > 0 if t in ev else False) for t in ('SPLIT', 'MERGE', 'EXTRUSION', 'ARRIVAL', 'LOSS')}
        row['delay'] = {t: (ev[t]['first_t'] - r['onset']) for t in ('SPLIT', 'MERGE', 'EXTRUSION', 'ARRIVAL', 'LOSS') if t in ev and r['onset'] is not None and r['onset'] > 0}
        by[key].append(row)
    tab = {}
    for k, v in sorted(by.items()):
        d = {t: round(float(np.mean([x[t] for x in v])), 3) for t in ('SPLIT', 'MERGE', 'EXTRUSION', 'ARRIVAL', 'LOSS')}
        d['n_runs'] = len(v)
        dl = {t: [x['delay'][t] for x in v if t in x['delay']] for t in ('SPLIT', 'MERGE', 'EXTRUSION', 'ARRIVAL', 'LOSS')}
        d['median_delay_from_onset'] = {t: float(np.median(a)) for t, a in dl.items() if a}
        tab['|'.join(k)] = d
    res[lv] = tab
json.dump(res, open('results_heldout/event_table.json', 'w'), indent=1)
for lv in ('O1', 'O2', 'O3b'):
    print('==', lv)
    for k, d in res[lv].items():
        if k.startswith('N0') or 'treated' in k.split('|')[1] and 'sham' not in k or k.split('|')[0] in ('P01', 'P04', 'T3a', 'Xmig') :
            print('%-30s n=%3d SPLIT %.2f MERGE %.2f EXTR %.2f ARR %.2f LOSS %.2f  delay %s' % (k, d['n_runs'], d['SPLIT'], d['MERGE'], d['EXTRUSION'], d['ARRIVAL'], d['LOSS'], d['median_delay_from_onset']))
