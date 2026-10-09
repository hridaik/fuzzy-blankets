"""T3.6 blind package v1: OBSERVABLE tier only (levels O1-O3), opaque labels, split manifest. Hidden mapping is written OUTSIDE the package (testbed/data/blind_v1_hidden/)."""
import sys, os, json, glob, pickle, hashlib; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from interface import render_O1, render_O2, render_O3, OBS_EVERY, IMG_PX, FOV, PSF_SIGMA, SNR, POS_NOISE, LEVEL_NOISE
HERE = os.path.dirname(os.path.abspath(__file__)); TB = os.path.dirname(HERE); MORPH = os.path.dirname(TB)
PKG = os.path.join(MORPH, 'testbed_blind_v1'); HID = os.path.join(TB, 'data', 'blind_v1_hidden')
rng_master = np.random.default_rng(20261008)
CH_PERM = rng_master.permutation(4)                       # opaque ordering of the four secreted levels, fixed for the package

def pack_O1(o1):
    ptr = np.cumsum([0] + [len(f['id']) for f in o1]); return dict(t=np.array([f['t'] for f in o1]), frame_ptr=ptr, cell_id=np.concatenate([f['id'] for f in o1]), xy=np.concatenate([f['xy'] for f in o1]).astype(np.float32), level=np.concatenate([f['level'] for f in o1]).astype(np.float32))
def pack_O2(o2):
    ptr = np.cumsum([0] + [len(f['xy']) for f in o2]); return dict(t=np.array([f['t'] for f in o2]), frame_ptr=ptr, xy=np.concatenate([f['xy'] for f in o2]).astype(np.float32), level=np.concatenate([f['level'] for f in o2]).astype(np.float32))
def pack_O3(o3, every=1):
    sel = o3[::every]; return dict(t=np.array([f['t'] for f in sel]), image=np.stack([f['img'] for f in sel]).astype(np.float16))

def write_run(name, frames, seed_obs, o3_every, extra_meta, hidden_meta):
    rng = np.random.default_rng(seed_obs)
    o1 = render_O1(frames, rng, CH_PERM); o2 = render_O2(frames, rng, CH_PERM); o3 = render_O3(frames, rng, CH_PERM)
    os.makedirs(f'{PKG}/runs', exist_ok=True)
    np.savez_compressed(f'{PKG}/runs/{name}_O1.npz', **pack_O1(o1)); np.savez_compressed(f'{PKG}/runs/{name}_O2.npz', **pack_O2(o2)); np.savez_compressed(f'{PKG}/runs/{name}_O3.npz', **pack_O3(o3, o3_every))
    hidden_meta = dict(hidden_meta, run=name); os.makedirs(HID, exist_ok=True); json.dump(hidden_meta, open(f'{HID}/{name}.json', 'w'), default=str)
    return dict(run=name, n_frames=len(frames), **extra_meta)

def main():
    import csv
    os.makedirs(PKG, exist_ok=True); cat = []; hidden_map = {}
    strain = {'L': 'S1', 'R': 'S2'} if rng_master.random() < 0.5 else {'L': 'S2', 'R': 'S1'}
    scn_codes = dict(zip(['replace1', 'replace6', 'extrude', 'cut', 'fuse_LL', 'fuse_LR'], ['P%d' % (i + 1) for i in rng_master.permutation(6)]))
    run_id = [0]
    def new_name():
        run_id[0] += 1; return 'run_%04d' % (run_id[0] * 7 + int(rng_master.integers(0, 7)))
    # ---------------- natural ensembles (observation frames spaced by the decorrelation time)
    man = json.load(open(f'{TB}/data/natural_v1/manifest.json')); spacing = man['spacing']
    for f in sorted(man['files']):
        base = os.path.basename(f); kind, tag, seed = base.split('.')[0].split('_'); seed = int(seed); d = np.load(f'{TB}/data/natural_v1/{base}')
        X, C = d['X'], d['C']; frames = [dict(t=float(k * spacing), X=X[k], C=C[k], alive=np.ones(len(X[k]), bool), cell_id=d['cell_id']) for k in range(len(X))]
        nm = new_name(); split = 'development' if tag == 'cal' else 'heldout_bodies'
        cat.append(write_run(nm, frames, seed, 2, dict(group='natural', condition='N0', strain_code=strain[kind], arm='untreated', onset='', event_xy='', frame_interval=spacing, split=split, body_seed=seed, noise_level='n1', treatment=''), dict(kind=kind, tag=tag, seed=seed, scenario='natural')))
    # ---------------- identity-stress
    for pk in sorted(glob.glob(f'{TB}/data/stress_raw/*.pkl')):
        scn, kind, seed = os.path.basename(pk)[:-4].rsplit('_', 2) if scn_split(pk) else (None, None, None)
        scn, kind, seed = parse(pk); out = pickle.load(open(pk, 'rb')); gid = 'G%03d' % (len(hidden_map) + 1); hidden_map[gid] = dict(scn=scn, kind=kind, seed=seed)
        evs = [e for e in out['event']['hidden']['events'] if e['kind'] in ('remove', 'insert', 'extrude', 'cut', 'fuse')]
        onset = min([e['t'] for e in evs]) - 1e4 if evs and scn != 'fuse_LL' and scn != 'fuse_LR' else 0.0
        ev_xy = ''
        acts = out['event']['hidden'].get('events', [])
        for arm, role in (('event', 'treated'), ('twin', 'untreated_control'), ('sham', 'sham_treated')):
            fr = out[arm]['frames']; frames = [dict(t=f['t'], X=f['X'], C=f['C'], alive=f['alive'], cell_id=f['cell_id']) for f in fr]
            held = (seed % 3 == 0); split = 'heldout_bodies' if held else 'development'
            if scn in ('fuse_LL', 'fuse_LR'): split = 'heldout_conditions'
            nm = new_name()
            cat.append(write_run(nm, frames, seed * 3 + 1, 2, dict(group=gid, condition=scn_codes[scn], strain_code=strain[kind], arm=role, onset=onset if role != 'untreated_control' else '', event_xy=ev_xy, frame_interval=5.0, split=split, body_seed=seed, noise_level='n1', treatment=scn_codes[scn] if role != 'untreated_control' else ''), dict(scn=scn, arm=arm, kind=kind, seed=seed, group=gid, events=out[arm]['hidden']['events'], pose=out[arm]['pose'])))
    json.dump(dict(strain=strain, scenarios=scn_codes, channel_perm=[int(x) for x in CH_PERM], groups=hidden_map), open(f'{HID}/mapping.json', 'w'), indent=1)
    keys = ['run', 'group', 'condition', 'strain_code', 'arm', 'treatment', 'onset', 'event_xy', 'n_frames', 'frame_interval', 'split', 'body_seed', 'noise_level']
    with open(f'{PKG}/catalog.csv', 'w', newline='') as fh:
        w = csv.DictWriter(fh, keys); w.writeheader(); [w.writerow({k: c.get(k, '') for k in keys}) for c in cat]
    split_manifest = dict(
        policy=dict(development='bodies with body_seed % 3 != 0 (stress) and calibration bodies (natural); everything available for fitting', heldout_bodies='bodies with body_seed % 3 == 0 (stress) and the natural validation bodies (disjoint seeds)',
                    heldout_conditions='treatment codes whose runs are all held out', heldout_locations='n/a in this package (no actuator-location dataset)'),
        runs={c['run']: c['split'] for c in cat}); json.dump(split_manifest, open(f'{PKG}/split_manifest.json', 'w'), indent=1)
    print(len(cat), 'runs written')

def parse(pk):
    b = os.path.basename(pk)[:-4]; parts = b.split('_')
    seed = int(parts[-1]); kind = parts[-2]; scn = '_'.join(parts[:-2]); return scn, kind, seed
def scn_split(pk): return False

if __name__ == '__main__': main()
