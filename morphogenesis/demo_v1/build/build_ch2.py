"""Chapters 2.1 / 2.2 / 3.1 assets from package v3 (observables) + its hidden tier (truth view). Declared exemplar rules:
undisturbed = lowest-id natural run (run_00011); cut = lowest-id x-cut treated run (run_00263); fusion = lowest-id fusion run (run_00640);
light pulse = lowest-id light run that truly switched (run_01105, T4b, level 1.4); link-slider merge dish = lowest-id fuse offset (6,0) run (run_00702)."""
import sys; sys.path.insert(0, '.')
from common import *
RUNS = f'{PKG}/runs'; HID = f'{V3}/data/blind_v3_hidden'
def o1(run, ts):
    z = np.load(f'{RUNS}/{run}_O1.npz'); t = z['t']; fp = z['frame_ptr']; out = []
    for T in ts:
        k = int(np.argmin(np.abs(t - T)));
        if abs(t[k] - T) > 1e-6: raise ValueError((run, T, t[k]))
        a, b = fp[k], fp[k + 1]; out.append(dict(id=z['cell_id'][a:b].tolist(), xy=z['xy'][a:b], lev=z['level'][a:b]))
    return out
def pack_xy(frames): return [enc16(f['xy'], 1000) for f in frames]
def thumb(run, t0, t1, tag, extra=None):
    ts = list(range(t0, t1 + 1)); fr = o1(run, ts); n = len(fr[0]['id']); return dict(run=run, tag=tag, t0=t0, ts=ts, n=n, xy=pack_xy(fr), **(extra or {}))
import csv
cat = {r['run']: r for r in csv.DictReader(open(f'{PKG}/catalog.csv'))}
tr = json.load(open(f'{PKG}/treatments.json'))
light = tr['run_01105'][0]
out21 = dict(thumbs=[thumb('run_00011', 100, 140, 'Undisturbed'), thumb('run_00263', 40, 100, 'Cut', dict(onset=50)), thumb('run_00640', 1, 60, 'Fusion'), thumb('run_01105', 30, 100, 'Light pulse', dict(light=dict(xy=light['disc_xy'], r=light['radius'], t_on=light['t_on'], t_off=light['t_off'], ramp=light['ramp'], device=light['device'], amp=light['amplitude'])))],
             dish=dict(run='run_01105', t=30, xy=enc16(o1('run_01105', [30])[0]['xy'], 1000)))
write_js('c21', out21)
# ---------------- 2.2: one clip, four observation levels + hidden truth (window [36,66], 1 tu)
run = 'run_01105'; T0, T1 = 36, 66; ts = list(range(T0, T1 + 1))
z1 = np.load(f'{RUNS}/{run}_O1.npz'); z2 = np.load(f'{RUNS}/{run}_O2.npz'); za = np.load(f'{RUNS}/{run}_O3a.npz'); zc = np.load(f'{RUNS}/{run}_O3c.npz'); h = np.load(f'{HID}/{run}_hid.npz'); meta = json.load(open(f'{HID}/{run}.json'))
def fr_idx(z, T): k = np.where(np.abs(z['t'] - T) < 1e-6)[0]; assert len(k) == 1, (T, k); return int(k[0])
O1 = []; O2 = []; IA = []; IC = []; HT = []
amax = np.maximum.reduce([za['image'][fr_idx(za, T)].astype(float).max(axis=(1, 2)) for T in ts])
for T in ts:
    k = fr_idx(z1, T); a, b = z1['frame_ptr'][k], z1['frame_ptr'][k + 1]; O1.append((z1['cell_id'][a:b], z1['xy'][a:b]))
    k2 = fr_idx(z2, T); a, b = z2['frame_ptr'][k2], z2['frame_ptr'][k2 + 1]; O2.append(z2['xy'][a:b])
    im = za['image'][fr_idx(za, T)].astype(float); im = np.clip(im / amax[:, None, None], 0, 1); IA.append(np.flipud(np.round(255 * im).astype('u1').transpose(1, 2, 0)))     # (64,64,3) rows top = +y
    ic = zc['image'][fr_idx(zc, T)][0]; IC.append(np.flipud(ic))
    kh = fr_idx(dict(t=h['t']), T); q = softmax(np.log(np.maximum(h['q'][kh], 1e-9)) * 0 + h['q'][kh]) if False else h['q'][kh]
    HT.append(dict(X=h['X'][kh], rho=1 / (1 + np.exp(-h['l'][kh])), place=q.argmax(1), e=h['e'][kh], id=h['cell_id'][kh]))
tm, XS, CT = template()
write_js('c22', dict(run=run, ts=ts, fovO1=10.0, fovA=12.0, fovC=10.0, n=24,
    O1=dict(id=[o[0].tolist() for o in O1], xy=[enc16(o[1], 1000) for o in O1]), O2=[enc16(x, 1000) for x in O2],
    O3a=[enc8(i) for i in IA], O3c=[enc8(i) for i in IC], hid=dict(X=[enc16(t['X'], 1000) for t in HT], rho=[enc16(t['rho'], 20000) for t in HT], place=[t['place'].tolist() for t in HT], e=[enc16(t['e'], 20000) for t in HT], id=[t['id'].tolist() for t in HT], tmplType=CT.tolist(), tmplXY=XS.tolist()),
    light=dict(xy=light['disc_xy'], r=light['radius'], t_on=light['t_on'], t_off=light['t_off'], ramp=light['ramp'])))
# ---------------- 3.1: link-radius dishes
def one(run, T): f = o1(run, [T])[0]; return dict(id=f['id'], xy=enc16(f['xy'], 1000), lev6=enc16(f['lev'][:, 6], 1000), n=len(f['id']))
write_js('c31', dict(single=one('run_01105', 36), merge=one('run_00702', 30), mergeNote='dish-merge run: two 24-cell bodies brought together at offset (6.0, 0.0) (package run_00702, t = 30)',
    singleH=dict(X=enc16(h['X'][fr_idx(dict(t=h['t']), 36)], 1000))))
