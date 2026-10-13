"""OBSERVABLE builds: package data only (O1 tracked cells coloured by a selectable signal column). Run selection uses the owner-side hidden tier; nothing hidden is displayed."""
import sys, os, json, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from viewer4 import emit, _r
TB = os.path.dirname(HERE); PKG = os.path.join(os.path.dirname(TB), 'testbed_blind_v4'); HID = os.path.join(TB, 'data', 'blind_v4_hidden')
R = list(csv.DictReader(open(f'{PKG}/catalog.csv'))); meta = {r['run']: json.load(open(f'{HID}/{r["run"]}.json')) for r in R}
def panel(run, t_lo, t_hi, label, step=1):
    o1 = np.load(f'{PKG}/runs/{run}_O1.npz'); ptr = o1['frame_ptr']; t = o1['t']; ks = [k for k in range(len(t)) if t_lo <= t[k] <= t_hi][::step]
    return dict(label=label, t=[float(t[k] - t[ks[0]]) for k in ks], X=[_r(o1['xy'][ptr[k]:ptr[k + 1]], 3) for k in ks], lv=[_r(o1['level'][ptr[k]:ptr[k + 1]], 3) for k in ks])
def find(**kw):
    out = []
    for r in R:
        m = meta[r['run']]['meta']
        if all(m.get(k) == v for k, v in kw.items()): out.append(r)
    return out
if __name__ == "__main__":
    ds = json.load(open(f'{TB}/data/package_dishes.json')); med = ds[1]
    # 1. two natural dishes with opposite hidden orientation (selection uses the hidden tier; the page shows tracked cells only)
    nat = [r for r in R if r['condition'] == 'N0']; ang = {r['run']: float(np.nanmean(np.load(f'{HID}/{r["run"]}_hid.npz')['angle'])) for r in nat}
    pos = max(nat, key=lambda r: ang[r['run']]); neg = min(nat, key=lambda r: ang[r['run']])
    emit('natural_pair', 'v4 - two untreated dishes (package O1 data)', 'catalog runs ' + pos['run'] + ' and ' + neg['run'], [panel(pos['run'], 0, 300, 'dish ' + pos['run'], 2), panel(neg['run'], 0, 300, 'dish ' + neg['run'], 2)], build='observable', info='Tracked cells coloured by one signal column (select). The two clusters have different overall shapes.')
    # 2. a light run that works: at-threshold-and-above, middle disc, long pulse, median dish
    sw = [r for r in find(family='switch', dseed=med, centre='middle', dm=16, state='a') if meta[r['run']]['meta']['kind'] in ('at', 'above')]
    sw.sort(key=lambda r: meta[r['run']]['meta']['amp']); r = sw[-1]; m = meta[r['run']]['meta']
    emit('light_run', 'v4 - a light run (package O1 data)', f"run {r['run']}, catalog condition {r['condition']}", [panel(r['run'], m['t_on'] - 20, m['t_off'] + 100, f"light run {r['run']} (arm {r['arm']})")], build='observable', info='One light pulse on a disc; see treatments.json for the disc, amplitude and timing.')
    # 3. bright pulse vs gentle pulse at the same disc and dish (package: damage-set event run vs switch-set run)
    dm = [x for x in R if meta[x['run']]['meta'].get('family') == 'damage' and meta[x['run']]['meta'].get('arm') == 'event' and meta[x['run']]['meta'].get('dseed') == med and meta[x['run']]['meta'].get('light') == 'MB' and meta[x['run']]['meta'].get('centre') == 'middle'][0]
    md = meta[dm['run']]['meta']
    emit('bright_vs_gentle', 'v4 - a strong and a weak pulse at the same disc (package O1 data)', f"runs {dm['run']} and {r['run']}", [panel(dm['run'], md['t_on'] - 20, md['t_off'] + 250, f"stronger pulse: run {dm['run']}", 2), panel(r['run'], m['t_on'] - 20, m['t_off'] + 250, f"weaker pulse: run {r['run']}", 2)], build='observable', info='Same dish, same disc; amplitudes are in treatments.json.')
    # 4. one dish each at low / median / high coupling (light runs, same protocol)
    ps = []
    for d, nm in zip(ds, ('dish A', 'dish B', 'dish C')):
        c = sorted([x for x in find(family='switch', dseed=d, centre='middle', dm=16, state='a') if meta[x['run']]['meta']['kind'] == 'above'], key=lambda x: x['run'])[0]; mc = meta[c['run']]['meta']; ps.append(panel(c['run'], mc['t_on'] - 20, mc['t_off'] + 100, f"{nm}: run {c['run']}"))
    emit('three_dishes', 'v4 - three dishes, same protocol (package O1 data)', 'same disc and pulse length, amplitude scaled per dish', ps, build='observable')
