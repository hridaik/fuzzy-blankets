"""Chapter 3.1 (rebuilt): ONE package-v3 run with a cut, seen at four levels, with the outline(s) that the blind pipelines' own grouping code produce.
O1/O2: T4 pipeline (process_points: single linkage r_link 1.6, hysteresis, >=3 cells, forward organism tracker; O2 ids from T4's cell tracker).
O3a (glow): T4 pipeline's O3 front end (foreground of the smoothed c6 field, connected components, forward organism tracker) -> organism = foreground pixel set.
O3c (cell markers): T5's spot detection (gaussian smooth + local maxima, a_track.o3c_eval) followed by the SAME linking/tracker rule (T4 OrganismTracker; ids from the position-only CellTracker)."""
import sys, os, json, base64
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
sys.path.insert(0, MORPH + '/t4_blind_identity')
from t4 import io, o3 as T4o3, segment
from t4.orgtrack import OrganismTracker
from t4.pipeline import load_geometry, process_points
from t4.celltrack import CellTracker
from t4.describe import describe
from scipy.ndimage import gaussian_filter, maximum_filter
io.DATA = PKG; geo = load_geometry()
RUN = sys.argv[1] if len(sys.argv) > 1 else 'run_00283'; T0, T1 = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (30, 150); OUTNAME = sys.argv[4] if len(sys.argv) > 4 else 'c31'
row = next(r for r in csv.DictReader(open(PKG + '/catalog.csv')) if r['run'] == RUN) if False else None
import csv
row = next(r for r in csv.DictReader(open(PKG + '/catalog.csv')) if r['run'] == RUN); fov = float(row['fov']); fovc = float(row['fov_c'])
out = dict(run=RUN, fov=fov, fovc=fovc, onset=50, t0=T0, t1=T1)
ts = list(range(T0, T1 + 1)); out['ts'] = ts
# ---- O1 and O2 by the T4 pipeline (whole run, causal)
for lev in ('O1', 'O2'):
    R = process_points(RUN, lev, geo); fr = {int(round(f['t'] * 2)): f for f in R['frames'] if abs(f['t'] - round(f['t'])) < 1e-6}
    pts = io.point_frames(RUN, lev); pm = {int(round(p['t'] * 2)): p for p in pts}
    XY, LAB, ID, C6, ORG = [], [], [], [], []
    for T in ts:
        f = fr[2 * T]; xy = np.array(f['cells']['xy']); ids = np.array(f['cells']['ids']); lab = -np.ones(len(ids), int)
        orgs = []
        for o in f['orgs']:
            for m in o['members']: lab[ids == m] = o['org']
            orgs.append([o['org'], o['n'], round(o['centroid'][0], 3), round(o['centroid'][1], 3), round(o['e1'][0], 3), round(o['e1'][1], 3)])
        XY.append(enc16(xy, 1000)); LAB.append(lab.tolist()); ID.append(ids.tolist()); ORG.append(orgs)
        if lev == 'O1': C6.append(enc16(pm[2 * T]['lev'][:, 6], 1000))
    out[lev] = dict(xy=XY, lab=LAB, id=ID, org=ORG)
    if lev == 'O1': out[lev]['c6'] = C6
    print(lev, 'n orgs at t=40/60/100/150', [len(ORG[min(T - T0, len(ORG) - 1)]) for T in (40, 60, 100, 150)])
# ---- O3a: T4 front end + forward tracker, record foreground label image
ta, imgs = io.image_frames(RUN, 'O3a'); px = 2 * fov / 64; m_px = max(3, int(round(geo['m_min'] / px ** 2)))
ot = OrganismTracker(io.CHANNELS['O3a'], 1.0, m_px, geo['margin'], None); LI, IM, NO = [], [], []
tmap = {int(round(t)): k for k, t in enumerate(ta) if abs(t - round(t)) < 1e-6}
for k, t in enumerate(ta):
    if t < T0 or t > T1: continue
    fp = T4o3.frame_points(imgs[k], fov, geo); orgs, ev = ot.step(float(t), fp['xy'], fp['lev'], fp['ids'], lab=fp['lab'], compute_frame=False)
    L = np.zeros(64 * 64, np.uint8)
    for o in orgs: L[fp['ids'][o['idx']]] = o['org'] + 1
    L = L.reshape(64, 64)[::-1].copy()      # rows top = +y
    if abs(t - round(t)) < 1e-6 and int(round(t)) in range(T0, T1 + 1): LI.append((int(round(t)), L, [[o['org'], int(len(o['idx']))] for o in orgs], k))
LI = {a[0]: a for a in LI}
out['O3a'] = dict(lab=[enc8(LI[T][1]) for T in ts], org=[LI[T][2] for T in ts], img=[enc8(np.asarray(imgs[LI[T][3]]).astype('u1').transpose(1, 2, 0)[::-1].copy()) for T in ts])
print('O3a orgs', [len(LI[min(T, T1)][2]) for T in (40, 60, 100, 150)])
# ---- O3c: T5 spot detection then the same linking rule
tc = io.load(RUN, 'O3c'); tcs = tc['t']; ci = {int(round(t)): k for k, t in enumerate(tcs) if abs(t - round(t)) < 1e-6}
ct = CellTracker([]); ot3 = OrganismTracker([], geo['r_link'], geo['m_min'], geo['margin'], geo['r_hold']); XY, LAB, ORG, SP, IMG = [], [], [], [], []
hh = 2 * fovc / 128
for k in range(len(tcs)):
    t = tcs[k]
    if t > T1 or abs(t - round(t)) > 1e-6: continue
    im = tc['image'][k, 0].astype(float) / tc['scale'][0]
    if t < T0:  # keep trackers warm from the start of the fine window only
        continue
    g = gaussian_filter(im, 1.0); pk = (g == maximum_filter(g, size=5)) & (g > 0.35); iy, ix = np.nonzero(pk); xy = np.c_[-fovc + (ix + 0.5) * hh, -fovc + (iy + 0.5) * hh]
    ids, _ = ct.step(xy, np.zeros((len(xy), 0))); orgs, ev = ot3.step(float(t), xy, np.zeros((len(xy), 0)), ids, compute_frame=False)
    lab = -np.ones(len(xy), int)
    for o in orgs: lab[o['idx']] = o['org']
    XY.append((int(round(t)), enc16(xy, 1000), lab.tolist(), [[o['org'], int(len(o['idx']))] for o in orgs], enc8(np.asarray(tc['image'][k, 0])[::-1].copy())))
M_ = {a[0]: a for a in XY}
out['O3c'] = dict(xy=[M_[T][1] for T in ts], lab=[M_[T][2] for T in ts], org=[M_[T][3] for T in ts], img=[M_[T][4] for T in ts], scale=float(tc['scale'][0]))
print('O3c orgs', [len(M_[min(T, T1)][3]) for T in (40, 60, 100, 150)], 'spots', [len(M_[min(T, T1)][2]) for T in (40, 60, 100, 150)])
# statistic over the cut runs (for notes): does the glow image split at once?
write_js(OUTNAME, out)
