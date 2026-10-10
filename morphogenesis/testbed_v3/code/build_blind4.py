"""Package v3: OBSERVABLE tier (O1, O2, O3a, O3b, O3c) at fine resolution; opaque labels identical to package v2; hidden tier + mapping outside the package."""
import sys, os, json, glob, pickle, csv; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import build_blind3 as B3                                    # coding constants (column permutation, light labels, reagents): identical opaque labels
from build_blind3 import COL_PERM, LIGHT_LABELS, REAGENT, O2_COLS, O3A, O3B, levels, lnoise, POS_NOISE, PSF_SIGMA, SNR, IMG_PX, pack1, pack2, obs_actions
from world3 import component_labels
from scipy.ndimage import gaussian_filter
HERE = os.path.dirname(os.path.abspath(__file__)); TB = os.path.dirname(HERE); MORPH = os.path.dirname(TB)
PKG = os.path.join(MORPH, 'testbed_blind_v3'); HID = os.path.join(TB, 'data', 'blind_v3_hidden'); RAW = os.path.join(TB, 'data', 'raw_v4')
V2MAP = json.load(open(os.path.join(TB, 'data', 'blind_v2_hidden', 'mapping.json'))); SCN_CODES = V2MAP['scn_codes']
MARK_SD = 0.25; MARK_NOISE = 0.05; FOV_C = 10.0; PX_C = 128; FOV_F = 24.0; PX_F = 256                      # O3c: marker sd 0.25 = 0.28 x nearest-neighbour spacing (0.9), noise sd 0.05 (peak 1 -> SNR 20)
C_SCALE = np.array([255.0, 40.0, 40.0, 40.0])                                                                  # uint8 scale of the four O3c channels: marker, then the three field channels of O3a (value = uint8 / scale)
def c_channels(f, fov, px_n, rng):
    a = f['alive']; Xc = f['X'][a]; g = np.linspace(-fov, fov, px_n); GX, GY = np.meshgrid(g, g); P = np.stack([GX.ravel(), GY.ravel()], 1); px = 2 * fov / px_n
    d2 = ((P[:, None, :] - Xc[None]) ** 2).sum(-1); marker = np.exp(-d2 / (2 * MARK_SD ** 2)).sum(1).reshape(px_n, px_n); marker = marker + MARK_NOISE * rng.standard_normal(marker.shape)
    d = np.exp(-np.sqrt(d2)); Lv = levels(f)[a][:, COL_PERM]; chans = [marker]
    for c in O3A:
        im = gaussian_filter((d @ Lv[:, c]).reshape(px_n, px_n), PSF_SIGMA / px); pk = max(im.max(), 1e-6); chans.append(im + rng.standard_normal(im.shape) * pk / SNR)
    arr = np.stack(chans); q = np.clip(np.round(arr * C_SCALE[:, None, None] * np.array([1.0, 1, 1, 1])[:, None, None]), 0, 255).astype(np.uint8); return q
def render_frames(frames, rng, keep3, fov3, cfov, cpx, keepc):
    o1, o2, t3, o3a, o3b, tc, o3c = [], [], [], [], [], [], []; g = np.linspace(-fov3, fov3, IMG_PX); GX, GY = np.meshgrid(g, g); P = np.stack([GX.ravel(), GY.ravel()], 1); px = 2 * fov3 / IMG_PX
    for f in frames:
        a = f['alive']; X = f['X'][a] + POS_NOISE * rng.standard_normal((a.sum(), 2)); Lv = lnoise(rng, levels(f)[a])[:, COL_PERM]
        o1.append(dict(t=f['t'], id=f['cell_id'][a], xy=X, level=Lv)); p = rng.permutation(len(X)); o2.append(dict(t=f['t'], xy=X[p], level=Lv[p][:, O2_COLS]))
        if keep3(f['t']):
            d = np.exp(-np.linalg.norm(P[:, None, :] - f['X'][a][None], axis=-1)); LvT = levels(f)[a][:, COL_PERM]
            def img(cols):
                im = np.stack([(d @ LvT[:, c]).reshape(IMG_PX, IMG_PX) for c in cols]); im = np.stack([gaussian_filter(m, PSF_SIGMA / px) for m in im]); pk = np.maximum(im.max(axis=(1, 2), keepdims=True), 1e-6)
                return np.clip(im + rng.standard_normal(im.shape) * pk / SNR, 0, None).astype(np.float16)
            t3.append(f['t']); o3a.append(img(O3A)); o3b.append(img(O3B))
        if keepc(f['t']): tc.append(f['t']); o3c.append(c_channels(f, cfov, cpx, rng))
    return o1, o2, t3, o3a, o3b, tc, o3c
def index_runs():
    """(family, path, arm, condition, group, split, body_id, fov spec) for every package run, deterministic order"""
    specs = []
    for p in sorted(glob.glob(f'{RAW}/natural/*.pkl')): specs.append(dict(fam='natural', path=p))
    for p in sorted(glob.glob(f'{RAW}/stress/*.pkl')):
        for arm in ('event', 'twin', 'sham'): specs.append(dict(fam='stress', path=p, arm=arm))
    for p in sorted(glob.glob(f'{RAW}/switch/*.pkl')): specs.append(dict(fam='switch', path=p))
    for p in sorted(glob.glob(f'{RAW}/decoy/*.pkl')): specs.append(dict(fam='decoy', path=p))
    rng = np.random.default_rng(20261011)
    for i, s in enumerate(specs): s['name'] = 'run_%05d' % ((i + 1) * 7 + int(rng.integers(0, 7))); s['obs_seed'] = int(rng.integers(0, 2 ** 31))
    return specs
def render_job(s):
    d = pickle.load(open(s['path'], 'rb')); fam = s['fam']; name = s['name']; os.makedirs(f'{PKG}/runs', exist_ok=True); os.makedirs(HID, exist_ok=True)
    if fam == 'natural': frames, hidden, meta = d['frames'], d['hidden'], dict(family='natural', state=d['state'], seed=d['seed'], tag=d['tag']); keep3 = lambda t: (round(t) % 2 == 0); dense = None
    elif fam == 'stress': a = d['arms'][s['arm']]; frames, hidden, meta = a['frames'], a['hidden'], dict(family='stress', scn=d['scn'], arm=s['arm'], state=d['state'], seed=d['seed']); dense = a['dense']
    else: frames, hidden, meta = d['frames'], d['hidden'], dict(d['meta'], family=fam); dense = None
    if fam == 'stress': keep3 = (lambda t, dn=dense: (abs(t - round(t)) < 1e-6) if (dn[0] <= t <= dn[1]) else (round(t) % 2 == 0 and abs(t - round(t)) < 1e-6))
    elif fam != 'natural': keep3 = lambda t: True
    fuse = fam == 'stress' and d['scn'].startswith('fuse'); cfov, cpx = (FOV_F, PX_F) if fuse else (FOV_C, PX_C)
    keepc = (lambda t: keep3(t) and (round(t) % 4 == 0)) if fuse else keep3
    rng = np.random.default_rng(s['obs_seed']); o1, o2, t3, o3a, o3b, tc, o3c = render_frames(frames, rng, keep3, 30.0 if fuse else 12.0, cfov, cpx, keepc)
    np.savez_compressed(f'{PKG}/runs/{name}_O1.npz', **pack1(o1)); np.savez_compressed(f'{PKG}/runs/{name}_O2.npz', **pack2(o2))
    np.savez_compressed(f'{PKG}/runs/{name}_O3a.npz', t=np.array(t3), image=np.stack(o3a)); np.savez_compressed(f'{PKG}/runs/{name}_O3b.npz', t=np.array(t3), image=np.stack(o3b)); np.savez_compressed(f'{PKG}/runs/{name}_O3c.npz', t=np.array(tc), image=np.stack(o3c), scale=C_SCALE)
    N = hidden_n(frames); hd = B3.hidden_diag(frames, N, hidden); np.savez_compressed(f'{HID}/{name}_hid.npz', **hd); json.dump(dict(meta=meta, events=hidden['events'], pose=hidden['pose'], private=hidden['private']), open(f'{HID}/{name}.json', 'w'), default=str)
    acts = []
    if fam == 'switch': m = meta; acts = [dict(device=LIGHT_LABELS[m['channel']], disc_xy=[round(x, 3) for x in m['disc_xy0']], radius=m['radius'], amplitude=round(m['amp'], 4), t_on=m['t_on'], t_off=m['t_off'], ramp=m['ramp'])]
    elif fam == 'decoy':
        for a in meta['acts']:
            if a['type'] == 'light': acts.append(dict(device=LIGHT_LABELS[a['channel']], disc_xy=[round(x, 3) for x in meta['disc_xy0']], radius=meta['radius'], amplitude=a['amp'], t_on=a['t_on'], t_off=a['t_off'], ramp=a['ramp']))
            else: acts += obs_actions([a], None, LIGHT_LABELS)
    elif fam == 'stress' and s['arm'] != 'twin': acts = [dict(device=dict(replace3='surgery-replace', extrude='tweezers', cutx='surgery-cut', cuty='surgery-cut').get(d['scn'], 'dish-merge'), onset='sham' if s['arm'] == 'sham' else None)]
    return dict(name=name, meta=meta, n_frames=len(frames), frame_t=[frames[0]['t'], frames[-1]['t']], n_o3=len(t3), n_o3c=len(tc), fov=30.0 if fuse else 12.0, fov_c=cfov, px_c=cpx, actions=acts, N=N, interval=float(np.median(np.diff([f['t'] for f in frames[:50]]))))
def hidden_n(frames): return int(len(frames[0]['alive']))

def ess(x, maxlag=600):
    x = np.asarray(x, float) - np.mean(x); n = len(x); v = (x ** 2).mean()
    if v < 1e-18: return float(n)
    acf = [(x[:n - k] * x[k:]).mean() / v for k in range(min(maxlag, n // 2))]; s = 0.0
    for k in range(1, len(acf) - 1, 2):
        pr = acf[k] + acf[k + 1]
        if pr < 0: break
        s += pr
    return float(n / max(1.0, 1 + 2 * s))
def obs_series(name):
    z = np.load(f'{PKG}/runs/{name}_O1.npz'); d = {k: z[k] for k in z.files}; ptr = d['frame_ptr']; ser = {}
    sh = []; mean_lv = []
    for k in range(len(ptr) - 1):
        xy = d['xy'][ptr[k]:ptr[k + 1]]; lv = d['level'][ptr[k]:ptr[k + 1]]; w = np.sort(np.linalg.eigvalsh(np.cov((xy - xy.mean(0)).T))); sh.append(np.log(w[1] / w[0])); mean_lv.append(lv.mean(0))
    mean_lv = np.array(mean_lv); ser['shape_logratio'] = np.array(sh)
    for j in range(7): ser[f'level_mean_c{j}'] = mean_lv[:, j]
    return ser
def main():
    from par import run_jobs
    specs = index_runs(); os.makedirs(PKG + '/runs', exist_ok=True); os.makedirs(HID, exist_ok=True)
    res = run_jobs(render_job, [(s,) for s in specs], workers=8, label='render4'); rows = []; treat = {}; hidmap = {}; gid = {}
    for s, r in zip(specs, res):
        m = r['meta']; fam = m['family']; name = r['name']; hidmap[name] = m
        if fam == 'natural': group = 'N%04d' % m['seed']; cond = 'N0'; arm = 'untreated'; split = 'development' if m['tag'] == 'cal' else 'heldout_bodies'; body = m['seed']; onset = ''; fine = ''
        elif fam == 'stress':
            key = (m['scn'], m['state'], m['seed']); group = gid.setdefault(key, 'G%03d' % (len(gid) + 1)); cond = SCN_CODES[m['scn']]; arm = dict(event='treated', twin='untreated_control', sham='sham_treated')[m['arm']]; body = m['seed']
            split = 'heldout_conditions' if m['scn'] == 'fuse|b|5.0,0.0' else ('heldout_bodies' if body % 3 == 0 else 'development'); evs = [e for e in json.load(open(f'{HID}/{name}.json'))['events'] if e['kind'] in ('remove', 'insert', 'extrude', 'cut', 'fuse', 'replace')]
            onset = (min(e['t'] for e in evs) - 1e4 - 100.0) if (evs and m['arm'] != 'twin') else ''; fine = ''
        elif fam == 'switch':
            lab = LIGHT_LABELS[m['channel']]; group = 'W%04d' % (len(rows) + 1); cond = 'T' + lab[1:] + ('b' if m['dur'] > 10 else 'a'); arm = 'sham_treated' if m['kind'] == 'sham' else 'treated'; body = int(os.path.basename(s['path']).split('_')[-1][:-4])
            split = 'heldout_locations' if m['centre'] in (5, 21) else ('heldout_bodies' if body % 3 == 0 else 'development'); onset = m['t_on']; fine = f"{m['t_on'] - 20.0}-{m['t_off'] + 100.0}"
        else:
            group = 'D%04d' % (len(rows) + 1); cond = 'X' + m['kind']; arm = 'treated'; body = int(os.path.basename(s['path']).split('_')[-1][:-4]); split = 'heldout_conditions' if m['kind'] in ('mbath_low', 'bath') else 'development'; onset = 40.0; fine = '20.0-190.0'
        if fam == 'stress': fine = '%s-%s' % tuple(__import__('pickle').load(open(s['path'], 'rb'))['arms'][m['arm']]['dense'])
        rows.append(dict(run=name, group=group, condition=cond, arm=arm, n_cells=int(r['N']) if fam != 'stress' or not m['scn'].startswith('fuse') or m['arm'] == 'event' else int(r['N']), n_frames=r['n_frames'], frame_interval=1.0, fine_window=fine if fam != 'natural' else '', fine_interval=0.5 if fam != 'natural' else '',
                         fov=r['fov'], fov_c=r['fov_c'], px_c=r['px_c'], onset=onset, split=split, body_id=body, noise_level='n1')); treat[name] = r['actions']
    keys = ['run', 'group', 'condition', 'arm', 'n_cells', 'n_frames', 'frame_interval', 'fine_window', 'fine_interval', 'fov', 'fov_c', 'px_c', 'onset', 'split', 'body_id', 'noise_level']
    with open(f'{PKG}/catalog.csv', 'w', newline='') as fh: w = csv.DictWriter(fh, keys); w.writeheader(); [w.writerow({k: c.get(k, '') for k in keys}) for c in rows]
    json.dump(treat, open(f'{PKG}/treatments.json', 'w'), default=str)
    json.dump(dict(policy=dict(development='bodies with body_id % 3 != 0 and calibration dishes; all conditions except those listed as held out; all light locations except the held-out ones', heldout_bodies='operation, light and device runs with body_id % 3 == 0, and the natural validation dishes (ids 2400-2405)', heldout_conditions='all runs of the listed condition codes', heldout_locations='light runs whose disc is centred on one of two places of the cluster'), runs={c['run']: c['split'] for c in rows}), open(f'{PKG}/split_manifest.json', 'w'), indent=1)
    json.dump(dict(col_perm=[int(x) for x in COL_PERM], light_labels=LIGHT_LABELS, reagent={str(k): v for k, v in REAGENT.items()}, scn_codes=SCN_CODES, o2_cols=O2_COLS, o3a=O3A, o3b=O3B, runs=hidmap), open(f'{HID}/mapping.json', 'w'), default=str, indent=1)
    ess_step(rows)
def ess_step(rows):
    nat = [r for r in rows if r['condition'] == 'N0']; out = {}
    for sp in ('development', 'heldout_bodies'):
        per = {}
        for r in nat:
            if r['split'] != sp: continue
            for k, v in obs_series(r['run']).items(): per.setdefault(k, []).append((len(v), ess(v)))
        out[sp] = {k: dict(runs=len(v), frames=int(sum(a for a, b in v)), ess_total=float(sum(b for a, b in v)), ess_per_run_median=float(np.median([b for a, b in v]))) for k, v in per.items()}
    json.dump(out, open(os.path.join(TB, 'data', 'ess_observable.json'), 'w'), indent=1); print(len(rows), 'runs written'); print(json.dumps({sp: {k: round(v['ess_total']) for k, v in d.items()} for sp, d in out.items()}))
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'ess': ess_step(list(csv.DictReader(open(f'{PKG}/catalog.csv'))))
    else: main()
