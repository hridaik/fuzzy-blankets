"""Chapter 2.2 (new): one short clip per tool, truth view (shape colours = true cell type of the place the cell believes it is in).
Clips are existing package-v3 runs (observed positions, hidden tier for types)."""
import sys, os
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
import csv
RUNS = f'{PKG}/runs'; HID = f'{V3}/data/blind_v3_hidden'
TR = json.load(open(f'{PKG}/treatments.json'))
tm, XS, CT = template()           # CT[place] = type 1..4 (head, trunk, limb, tail)
def clip(run, t0, t1, step=1):
    z = np.load(f'{RUNS}/{run}_O1.npz'); h = np.load(f'{HID}/{run}_hid.npz'); meta = json.load(open(f'{HID}/{run}.json'))
    ts = [float(t) for t in np.arange(t0, t1 + 1e-9, step)]; frames = []
    for T in ts:
        k = int(np.argmin(np.abs(z['t'] - T))); assert abs(z['t'][k] - T) < 1e-6, (run, T)
        a, b = z['frame_ptr'][k], z['frame_ptr'][k + 1]; ids = z['cell_id'][a:b]; xy = z['xy'][a:b]
        kh = int(np.argmin(np.abs(h['t'] - (T + (h['t'][0] - z['t'][0]) if False else h['t'][0] + T - 0)))) if False else k
        q = h['q'][kh]; cid = h['cell_id'][kh]; row = {int(c): i for i, c in enumerate(cid)}
        typ = []
        for c in ids:
            qq = q[row[int(c)]]; typ.append(int(CT[int(qq.argmax())]) if qq.max() > 0.3 else 0)
        frames.append(dict(ids=ids.astype(int).tolist(), xy=enc16(xy, 1000), typ=typ, _xy=xy))
    return ts, frames, meta, z
out = {}
# --- Cut: run_00283 (same dish as 3.1)
ts, fr, meta, z = clip('run_00283', 40, 70); ev = meta['events'][0]; moved = set(ev['cells']); vec = np.array(ev['vec']); onset = 50
k49 = ts.index(49.0); ids = fr[k49]['ids']; P = fr[k49]['_xy']; v = vec / np.linalg.norm(vec)
# the moved side is the one whose cells are the 12 listed *hidden slots*; map slot->cell id via hidden cell_id (slot index == cell id at t0)
mv = np.array([i in moved for i in ids]); pr = P @ v
sgn = 1 if pr[mv].mean() > pr[~mv].mean() else -1
lo = (pr[~mv] * sgn).max(); hi = (pr[mv] * sgn).min(); s = (lo + hi) / 2 * sgn
c0 = v * s; nrm = np.array([-v[1], v[0]])
out['cut'] = dict(run='run_00283', ts=ts, onset=onset, frames=[{k: f[k] for k in ('ids', 'xy', 'typ')} for f in fr], line=[(c0 - 5.5 * nrm).tolist(), (c0 + 5.5 * nrm).tolist()], moved=sorted(moved), vec=vec.tolist(), vlen=float(np.linalg.norm(vec)), clean_gap=float(hi - lo))
print('cut: |vec|', np.linalg.norm(vec), 'gap between sides before cut', hi - lo, 'n moved', mv.sum())
# --- Pull out a cell (tweezers): run_00515
ts, fr, meta, z = clip('run_00515', 40, 70); ev = meta['events'][0]
out['pull'] = dict(run='run_00515', ts=ts, onset=50, frames=[{k: f[k] for k in ('ids', 'xy', 'typ')} for f in fr], cell=int(ev['cell_id']), vec=ev['vec'], vlen=float(np.linalg.norm(ev['vec'])))
print('pull |vec|', np.linalg.norm(ev['vec']), 'cell', ev['cell_id'])
# --- Replace a cell: run_00953 (first of its replacements, t = 50)
ts, fr, meta, z = clip('run_00953', 40, 80); ev = [e for e in meta['events'] if e['kind'] == 'insert'][0]
out['replace'] = dict(run='run_00953', ts=ts, onset=50, frames=[{k: f[k] for k in ('ids', 'xy', 'typ')} for f in fr], old=int(ev['replaces']), new=int(ev['cell_id']), pos=ev['pos'], all_events=[(e['t'] - 10100, e['kind']) for e in meta['events']][:12])
print('replace: new id', ev['cell_id'], 'first event times', out['replace']['all_events'][:6])
# --- Merge two organisms: run_00640 (t = 0..30)
ts, fr, meta, z = clip('run_00640', 1, 31); ev = meta['events'][0]
out['merge'] = dict(run='run_00640', ts=ts, frames=[{k: f[k] for k in ('ids', 'xy', 'typ')} for f in fr], offset=ev['offset'], n1=ev['n1'], n2=ev['n2'])
# --- Light: run_01105 (t = 30..80), disc from treatments.json
L = TR['run_01105'][0]
ts, fr, meta, z = clip('run_01105', 30, 80)
out['light'] = dict(run='run_01105', ts=ts, frames=[{k: f[k] for k in ('ids', 'xy', 'typ')} for f in fr], disc=L['disc_xy'], r=L['radius'], t_on=L['t_on'], t_off=L['t_off'], ramp=L['ramp'])
# --- Bath: run_01924
Bt = TR['run_01924'][0]; print('bath treatment keys', {k: Bt[k] for k in Bt if k != 'xy'})
ts, fr, meta, z = clip('run_01924', 30, 100)
out['bath'] = dict(run='run_01924', ts=ts, frames=[{k: f[k] for k in ('ids', 'xy', 'typ')} for f in fr], t_on=Bt.get('t_on', 40.0), t_off=Bt.get('t_off', 90.0), ramp=Bt.get('ramp', 5.0))
write_js('c22b', out)
