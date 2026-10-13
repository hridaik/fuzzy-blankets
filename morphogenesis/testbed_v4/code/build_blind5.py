"""Package v4 (testbed_blind_v4): OBSERVABLE tier O1, O2, O3a, O3b, O3c at fine time resolution, opaque labels (same coding as v2/v3), split manifest. Hidden tier + mapping written OUTSIDE the package (testbed_v4/data/blind_v4_hidden/).
Reuses v3 rendering helpers read-only (testbed_v3/code/build_blind3.py, build_blind4.py)."""
import sys, os, json, glob, pickle, csv
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
V3C = os.path.join(HERE, '..', '..', 'testbed_v3', 'code'); sys.path.insert(0, V3C)
import numpy as np
import build_blind3 as B3
import build_blind4 as B4
from lib4 import *
TB = os.path.dirname(HERE); MORPH = os.path.dirname(TB)
PKG = os.path.join(MORPH, 'testbed_blind_v4'); HID = os.path.join(TB, 'data', 'blind_v4_hidden'); RAW = os.path.join(TB, 'data', 'raw_v5')
B4.PKG = PKG
LIGHT_LABELS = B3.LIGHT_LABELS; levels = B3.levels
def hidden_diag(frames, hidden, N):
    from engine4 import make_engine4
    dish = hidden['dish']; e = get_engine(dish, hidden['variant'], noise=False, gamma_on=True, N=(None if N == 24 else N)); out = dict(t=[], l=[], rho=[], f=[], q=[], Ea=[], Eb=[], Delta=[], ubar=[], d=[], e=[], X=[], alive=[], cell_id=[], angle=[])
    for f in frames:
        st = tuple(jnp.array(f[k]) for k in ('X', 'C', 'MU', 'L', 'D', 'E', 'U')); dg = e.diagnostics(st); q = np.array(dg['q'])
        out['t'].append(f['t']); out['l'].append(f['L']); out['rho'].append(np.array(dg['rho'])); out['f'].append(np.array(dg['f'])); out['q'].append(q.astype(np.float16)); out['Ea'].append(np.array(dg['Ea'], dtype=np.float16)); out['Eb'].append(np.array(dg['Eb'], dtype=np.float16))
        out['Delta'].append(np.array(dg['Delta'])); out['ubar'].append(f['U']); out['d'].append(f['D']); out['e'].append(f['E']); out['X'].append(f['X']); out['alive'].append(f['alive']); out['cell_id'].append(f['cell_id'])
        a = f['alive']; out['angle'].append(tail_angle(TM, f['X'][a], q[a].argmax(1)) if a.sum() == 24 else np.nan)
    d = {k: np.array(v) for k, v in out.items()}; d['intact'] = np.array(hidden['intact'], dtype=bool); return d
def obs_actions_v4(acts):
    return B3.obs_actions(acts, None, LIGHT_LABELS)
def index_runs():
    specs = []
    for p in sorted(glob.glob(f'{RAW}/natural/*.pkl')): specs.append(dict(fam='natural', path=p))
    for p in sorted(glob.glob(f'{RAW}/stress/*.pkl')):
        for arm in ('event', 'twin', 'sham'): specs.append(dict(fam='stress', path=p, arm=arm))
    for p in sorted(glob.glob(f'{RAW}/damage/*.pkl')):
        for arm in ('event', 'twin', 'sham'): specs.append(dict(fam='damage', path=p, arm=arm))
    for p in sorted(glob.glob(f'{RAW}/switch/*.pkl')): specs.append(dict(fam='switch', path=p))
    rng = np.random.default_rng(20261012)
    for i, s in enumerate(specs): s['name'] = 'run_%05d' % ((i + 1) * 7 + int(rng.integers(0, 7))); s['obs_seed'] = int(rng.integers(0, 2 ** 31))
    return specs
def render_job(s):
    d = pickle.load(open(s['path'], 'rb')); fam = s['fam']; name = s['name']; os.makedirs(f'{PKG}/runs', exist_ok=True); os.makedirs(HID, exist_ok=True); dense = None
    if fam == 'natural': frames, hidden, meta = d['frames'], d['hidden'], dict(family='natural', state=d['state'], seed=d['seed'], tag=d['tag']); keep3 = lambda t: (round(t) % 5 == 0 and abs(t - round(t)) < 1e-6)
    elif fam in ('stress', 'damage'):
        a = d['arms'][s['arm']]; frames, hidden = a['frames'], a['hidden']; meta = dict(family=fam, arm=s['arm'], state=d.get('state', d.get('meta', {}).get('state')), seed=d.get('seed', d.get('meta', {}).get('dseed')))
        if fam == 'stress': meta['scn'] = d['scn']; dense = a['dense']
        else: meta.update(d['meta']); dense = (meta['t_on'] - 20.0, meta['t_off'] + 100.0)
        keep3 = (lambda t, dn=dense: (abs(t - round(t)) < 1e-6) if (dn[0] <= t <= dn[1]) else (round(t) % 2 == 0 and abs(t - round(t)) < 1e-6))
    else: frames, hidden, meta = d['frames'], d['hidden'], dict(d['meta'], family='switch'); keep3 = lambda t: True
    fuse = fam == 'stress' and d['scn'].startswith('fuse'); cfov, cpx = (B4.FOV_F, B4.PX_F) if fuse else (B4.FOV_C, B4.PX_C); keepc = (lambda t: keep3(t) and (round(t) % 4 == 0)) if fuse else keep3
    rng = np.random.default_rng(s['obs_seed']); o1, o2, t3, o3a, o3b, tc, o3c = B4.render_frames(frames, rng, keep3, 30.0 if fuse else 12.0, cfov, cpx, keepc)
    np.savez_compressed(f'{PKG}/runs/{name}_O1.npz', **B3.pack1(o1)); np.savez_compressed(f'{PKG}/runs/{name}_O2.npz', **B3.pack2(o2))
    np.savez_compressed(f'{PKG}/runs/{name}_O3a.npz', t=np.array(t3), image=np.stack(o3a)); np.savez_compressed(f'{PKG}/runs/{name}_O3b.npz', t=np.array(t3), image=np.stack(o3b)); np.savez_compressed(f'{PKG}/runs/{name}_O3c.npz', t=np.array(tc), image=np.stack(o3c), scale=B4.C_SCALE)
    N = int(len(frames[0]['alive'])); hd = hidden_diag(frames, hidden, N); np.savez_compressed(f'{HID}/{name}_hid.npz', **hd)
    json.dump(dict(meta=meta, events=hidden['events'], pose=hidden['pose'], private=hidden['private'], dish=hidden['dish'], variant=hidden['variant'], tau_J=hidden['tau_J'], dose=hidden['dose']), open(f'{HID}/{name}.json', 'w'), default=str)
    acts = []
    if fam == 'switch': acts = [dict(device=LIGHT_LABELS[meta['channel']], disc_xy=[round(x, 3) for x in meta['disc_xy0']], radius=meta['radius'], amplitude=round(meta['amp'], 4), t_on=meta['t_on'], t_off=meta['t_off'], ramp=meta['ramp'])]
    elif fam == 'damage' and s['arm'] != 'twin': acts = [dict(device=LIGHT_LABELS[meta['light']], disc_xy=[round(x, 3) for x in meta['disc_xy0']], radius=meta['radius'], amplitude=round(meta['amp'], 4), t_on=meta['t_on'], t_off=meta['t_off'], ramp=meta['ramp'], delivered=(s['arm'] == 'event'))]
    elif fam == 'stress' and s['arm'] != 'twin': acts = [dict(device=dict(replace3='surgery-replace', extrude='tweezers', cutx='surgery-cut', cuty='surgery-cut').get(d['scn'], 'dish-merge'), onset='sham' if s['arm'] == 'sham' else None)]
    return dict(name=name, meta=meta, n_frames=len(frames), n_o3=len(t3), n_o3c=len(tc), fov=30.0 if fuse else 12.0, fov_c=cfov, px_c=cpx, actions=acts, N=N, dense=dense, intact_frac=float(np.mean(hd['intact'])))
def main():
    from par4 import run_jobs
    specs = index_runs(); os.makedirs(PKG + '/runs', exist_ok=True); os.makedirs(HID, exist_ok=True)
    res = run_jobs(render_job, [(s,) for s in specs], workers=8, label='render5'); rows = []; treat = {}; hidmap = {}; codes = {}; gid = {}
    def code(key, prefix): return codes.setdefault(key, prefix + '%02d' % (len(codes) + 1))
    for s, r in zip(specs, res):
        m = r['meta']; fam = m['family']; name = r['name']; hidmap[name] = m; fine = ''; onset = ''
        if fam == 'natural': group = 'N%05d' % m['seed']; cond = 'N0'; arm = 'untreated'; split = 'heldout_bodies' if m['tag'] == 'val' else 'development'; body = m['seed']
        elif fam == 'stress':
            key = (m['scn'], m['state'], m['seed']); group = gid.setdefault(key, 'G%03d' % (len(gid) + 1)); cond = code(('scn', m['scn']), 'P'); arm = dict(event='treated', twin='untreated_control', sham='sham_treated')[m['arm']]; body = m['seed']
            split = 'heldout_conditions' if m['scn'] == 'fuse|b|5.0,0.0' else ('heldout_bodies' if body % 3 == 0 else 'development'); evs = [e for e in json.load(open(f'{HID}/{name}.json'))['events'] if e['kind'] in ('remove', 'insert', 'extrude', 'cut', 'fuse', 'replace')]
            onset = (min(e['t'] for e in evs) - 1e4 - 100.0) if (evs and m['arm'] != 'twin') else ''; fine = '%s-%s' % tuple(r['dense'])
        elif fam == 'damage':
            key = ('dmg', m['light'], m['dseed'], m['centre'], m['dm']); group = gid.setdefault(key, 'D%03d' % (len(gid) + 1)); lab = LIGHT_LABELS[m['light']]; cond = 'T' + lab[1:] + ('b' if m['dm'] >= 8 else 'a'); arm = dict(event='treated', twin='untreated_control', sham='sham_treated')[m['arm']]; body = abs(m['dseed'])
            split = 'heldout_locations' if m['centre'] == 'tail_end' else ('heldout_bodies' if body % 3 == 0 else 'development'); onset = m['t_on']; fine = '%s-%s' % tuple(r['dense'])
        else:
            lab = LIGHT_LABELS[m['channel']]; group = 'W%04d' % (len(rows) + 1); cond = 'T' + lab[1:] + ('b' if m['dm'] >= 8 else 'a'); arm = 'sham_treated' if m['kind'] == 'sham' else 'treated'; body = m['dseed']
            split = 'heldout_locations' if m['centre'] == 'tail_end' else ('heldout_bodies' if body % 3 == 0 else 'development'); onset = m['t_on']; fine = f"{m['t_on'] - 20.0}-{m['t_off'] + 100.0}"
        rows.append(dict(run=name, group=group, condition=cond, arm=arm, n_cells=int(r['N']), n_frames=r['n_frames'], frame_interval=1.0, fine_window=fine, fine_interval=0.5 if fine else '', fov=r['fov'], fov_c=r['fov_c'], px_c=r['px_c'], onset=onset, split=split, body_id=body, noise_level='n1')); treat[name] = r['actions']
    keys = ['run', 'group', 'condition', 'arm', 'n_cells', 'n_frames', 'frame_interval', 'fine_window', 'fine_interval', 'fov', 'fov_c', 'px_c', 'onset', 'split', 'body_id', 'noise_level']
    with open(f'{PKG}/catalog.csv', 'w', newline='') as fh: w = csv.DictWriter(fh, keys); w.writeheader(); [w.writerow({k: c.get(k, '') for k in keys}) for c in rows]
    json.dump(treat, open(f'{PKG}/treatments.json', 'w'), default=str)
    json.dump(dict(policy=dict(development='dishes with body_id % 3 != 0 and the calibration dishes; all conditions except those listed as held out; all light locations except the held-out ones', heldout_bodies='operation and light runs with body_id % 3 == 0, and the natural validation dishes (ids 3000-3007)', heldout_conditions='all runs of the dish-merge condition listed', heldout_locations='light runs whose disc is centred on the far end of the cluster'), runs={c['run']: c['split'] for c in rows}), open(f'{PKG}/split_manifest.json', 'w'), indent=1)
    json.dump(dict(col_perm=[int(x) for x in B3.COL_PERM], light_labels=LIGHT_LABELS, reagent={str(k): v for k, v in B3.REAGENT.items()}, scn_codes={k[1]: v for k, v in codes.items()}, runs=hidmap), open(f'{HID}/mapping.json', 'w'), default=str, indent=1)
    B4.ess_step(rows) if False else ess_step(rows)
def ess_step(rows):
    nat = [r for r in rows if r['condition'] == 'N0']; out = {}
    for sp in ('development', 'heldout_bodies'):
        per = {}
        for r in nat:
            if r['split'] != sp: continue
            for k, v in B4.obs_series(r['run']).items(): per.setdefault(k, []).append((len(v), B4.ess(v)))
        out[sp] = {k: dict(runs=len(v), frames=int(sum(a for a, b in v)), ess_total=float(sum(b for a, b in v)), ess_per_run_median=float(np.median([b for a, b in v]))) for k, v in per.items()}
    json.dump(out, open(os.path.join(PKG, 'ess_observable.json'), 'w'), indent=1); print(len(rows), 'runs written'); print(json.dumps({sp: {k: round(v['ess_total']) for k, v in d.items()} for sp, d in out.items()}))
if __name__ == '__main__': main()
