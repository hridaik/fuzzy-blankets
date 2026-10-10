"""Sealed notes on package v3: per-state ESS (hidden state labels), frame-interval statistics, resolution of the memory lead, O3c marker check."""
import sys, json, csv, pickle, glob, os; sys.path.insert(0, '.')
import numpy as np
import build_blind4 as B4
from build_blind4 import ess, obs_series, PKG, HID, RAW
mp = json.load(open(f'{HID}/mapping.json'))['runs']; cat = list(csv.DictReader(open(f'{PKG}/catalog.csv'))); out = {}
# per-state ESS (natural)
agg = {}
for r in cat:
    if r['condition'] != 'N0': continue
    m = mp[r['run']]; s = obs_series(r['run'])
    for k, v in s.items(): agg.setdefault((m['state'], r['split'], k), []).append(ess(v))
out['ess_by_state'] = {f'{a}|{b}|{c}': dict(runs=len(v), ess_total=float(sum(v))) for (a, b, c), v in agg.items() if c in ('shape_logratio', 'level_mean_c0', 'level_mean_c4', 'level_mean_c6')}
# frame interval statistics
ints = {}
for r in cat:
    d = np.load(f'{PKG}/runs/{r["run"]}_O1.npz'); dt = np.diff(d['t']); fam = 'natural' if r['condition'] == 'N0' else ('switch' if r['condition'][0] == 'T' else ('device' if r['condition'][0] == 'X' else 'operation'))
    ints.setdefault(fam, []).append((len(d['t']), float(np.min(dt)), float(np.median(dt)), float(d['t'][-1])))
out['frames'] = {k: dict(runs=len(v), frames_median=int(np.median([x[0] for x in v])), min_dt=min(x[1] for x in v), median_dt=float(np.median([x[2] for x in v])), length_median=float(np.median([x[3] for x in v]))) for k, v in ints.items()}
# lead / lag at 0.5 tu in switch runs (hidden truth of the raw runs)
lags = []
for p in sorted(glob.glob(f'{RAW}/switch/*_on_*.pkl')):
    d = pickle.load(open(p, 'rb')); fr = d['frames']; t = np.array([f['t'] for f in fr]); L = np.array([f['L'] for f in fr]); D = np.array([f['D'] for f in fr]); E = np.array([f['E'] for f in fr]); MU = np.array([f['MU'] for f in fr])
    mr = (1 / (1 + np.exp(-L))).mean(1); a0 = mr[0] > 0.5; oth = (mr < 0.5) if a0 else (mr > 0.5)
    if not (oth[-int(0.2 * len(t)):].all() and oth.any()): continue
    from engine3 import make_template2, reporter_sets
    tm = make_template2(); Sp, Sm = reporter_sets(tm); q = np.exp(MU - MU.max(2, keepdims=True)); q /= q.sum(2, keepdims=True); Wp = q[:, :, Sp].sum(2); Wm = q[:, :, Sm].sum(2); ep = (E * Wp).sum(1) / Wp.sum(1); em = (E * Wm).sum(1) / Wm.sum(1); rc = ep - em
    dA = D[:, :, 0].mean(1); dB = D[:, :, 1].mean(1); f = lambda m: float(t[np.argmax(m)])
    lags.append((f(oth), f((dA < dB) if a0 else (dA > dB)), f((rc < 0) if a0 else (rc > 0))))
lags = np.array(lags); out['lead_at_half_tu'] = dict(n=len(lags), ligand_minus_rho=np.quantile(lags[:, 1] - lags[:, 0], [.1, .5, .9]).tolist(), reporter_minus_rho=np.quantile(lags[:, 2] - lags[:, 0], [.1, .5, .9]).tolist(), reporter_minus_ligand=np.quantile(lags[:, 2] - lags[:, 1], [.1, .5, .9]).tolist())
# O3c marker check
z = np.load(f'{PKG}/runs/{cat[0]["run"]}_O3c.npz'); im = z['image'][0][0].astype(float) / z['scale'][0]; px = 2 * B4.FOV_C / B4.PX_C; bg = np.median(im)
from scipy.ndimage import label, maximum_filter
pk = (im == maximum_filter(im, 5)) & (im > 0.5); out['o3c'] = dict(blobs_detected=int(pk.sum()), cells=int(cat[0]['n_cells']), marker_sd_units=B4.MARK_SD, nn_spacing_median=0.898, ratio=B4.MARK_SD / 0.898, pixel=px, sd_in_pixels=B4.MARK_SD / px, noise_sd=B4.MARK_NOISE, background_median=float(bg))
json.dump(out, open(os.path.join(B4.TB, 'data', 'pkg3_notes.json'), 'w'), indent=1); print(json.dumps(out, indent=1)[:2500])
