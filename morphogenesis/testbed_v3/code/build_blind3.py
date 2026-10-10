"""H5 blind package v2: OBSERVABLE tier only (O1, O2, O3a, O3b), opaque labels, split manifest. Hidden mapping + hidden truth written OUTSIDE the package (testbed_v3/data/blind_v2_hidden/)."""
import sys, os, json, glob, pickle, csv, hashlib; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world3 import *
from scipy.ndimage import gaussian_filter
HERE = os.path.dirname(os.path.abspath(__file__)); TB = os.path.dirname(HERE); MORPH = os.path.dirname(TB)
PKG = os.path.join(MORPH, 'testbed_blind_v2'); HID = os.path.join(TB, 'data', 'blind_v2_hidden'); RAW = os.path.join(TB, 'data', 'raw_v3')
POS_NOISE = 0.02; LEVEL_NOISE = 0.03; IMG_PX = 64; PSF_SIGMA = 0.5; SNR = 20.0
rng_master = np.random.default_rng(20261009)
# hidden coding ----------------------------------------------------------------------------------
COL_PERM = rng_master.permutation(7)        # package column j of O1 shows hidden quantity COL_PERM[j] in [c0 c1 c2 c3 dA dB e]
LIGHT_LABELS = dict(zip(['MA', 'MB', 'SEC', 'RG', 'MIG'], ['L%d' % (i + 1) for i in rng_master.permutation(5)]))
REAGENT = dict(zip(range(6), ['R%d' % (i + 1) for i in rng_master.permutation(6)]))      # ligand index (c0..c3, dA, dB) -> reagent code
O1_COLS = list(range(7)); MEM_HID = {4, 5}
O2_COLS = [j for j in range(7) if COL_PERM[j] not in MEM_HID]                        # O2 keeps the five columns that are not memory ligands
REP_COL = int(np.where(COL_PERM == 6)[0][0]); STRUCT_COLS = [int(np.where(COL_PERM == k)[0][0]) for k in (0, 1)]; MEM_COL = int(np.where(COL_PERM == 4)[0][0])
O3A = STRUCT_COLS + [REP_COL]; O3B = O3A + [MEM_COL]
def levels(f): return np.concatenate([f['C'], f['D'], f['E'][:, None]], axis=1)               # hidden order c0..c3, dA, dB, e
def lnoise(rng, M): return M * (1 + LEVEL_NOISE * rng.standard_normal(M.shape))

def render(frames, rng, fov):
    o1, o2, o3a, o3b = [], [], [], []; g = np.linspace(-fov, fov, IMG_PX); GX, GY = np.meshgrid(g, g); P = np.stack([GX.ravel(), GY.ravel()], 1); px = 2 * fov / IMG_PX
    for f in frames:
        a = f['alive']; X = f['X'][a] + POS_NOISE * rng.standard_normal((a.sum(), 2)); Lv = lnoise(rng, levels(f)[a])[:, COL_PERM]
        o1.append(dict(t=f['t'], id=f['cell_id'][a], xy=X, level=Lv)); p = rng.permutation(len(X)); o2.append(dict(t=f['t'], xy=X[p], level=Lv[p][:, O2_COLS]))
        d = np.exp(-np.linalg.norm(P[:, None, :] - f['X'][a][None], axis=-1)); LvTrue = levels(f)[a][:, COL_PERM]
        def img(cols):
            im = np.stack([(d @ LvTrue[:, c]).reshape(IMG_PX, IMG_PX) for c in cols]); im = np.stack([gaussian_filter(m, PSF_SIGMA / px) for m in im]); pk = np.maximum(im.max(axis=(1, 2), keepdims=True), 1e-6)
            return np.clip(im + rng.standard_normal(im.shape) * pk / SNR, 0, None).astype(np.float16)
        o3a.append(dict(t=f['t'], img=img(O3A))); o3b.append(dict(t=f['t'], img=img(O3B)))
    return o1, o2, o3a, o3b
def pack1(o): ptr = np.cumsum([0] + [len(f['id']) for f in o]); return dict(t=np.array([f['t'] for f in o]), frame_ptr=ptr, cell_id=np.concatenate([f['id'] for f in o]), xy=np.concatenate([f['xy'] for f in o]).astype(np.float32), level=np.concatenate([f['level'] for f in o]).astype(np.float32))
def pack2(o): ptr = np.cumsum([0] + [len(f['xy']) for f in o]); return dict(t=np.array([f['t'] for f in o]), frame_ptr=ptr, xy=np.concatenate([f['xy'] for f in o]).astype(np.float32), level=np.concatenate([f['level'] for f in o]).astype(np.float32))
def pack3(o, every): sel = o[::every]; return dict(t=np.array([f['t'] for f in sel]), image=np.stack([f['img'] for f in sel]))

_eng = {}
def hidden_diag(frames, N, hidden):
    from engine3 import make_engine3, Params3
    if N not in _eng: _eng[N] = make_engine3(make_template2(), Params3(), N=N)
    eng = _eng[N]; out = dict(t=[], l=[], rho=[], f=[], q=[], E=[], d=[], e=[], X=[], alive=[], cell_id=[])
    for f in frames:
        st = tuple(jnp.array(f[k]) for k in ('X', 'C', 'MU', 'L', 'D', 'E')); dg = eng.diagnostics(st)
        out['t'].append(f['t']); out['l'].append(f['L']); out['rho'].append(np.array(dg['rho'])); out['f'].append(np.array(dg['f'])); out['q'].append(np.array(dg['q'], dtype=np.float16)); out['E'].append(np.array(dg['E'], dtype=np.float16))
        out['d'].append(f['D']); out['e'].append(f['E']); out['X'].append(f['X']); out['alive'].append(f['alive']); out['cell_id'].append(f['cell_id'])
    return {k: np.array(v) for k, v in out.items()}

def obs_actions(acts, private, light_names):
    """observable description of the treatment, opaque labels only"""
    out = []
    for a in acts:
        if a['type'] == 'light': out.append(dict(device=light_names[a['channel']], disc_xy=a.get('disc_xy'), radius=a.get('radius'), amplitude=float(a['amp']), t_on=float(a['t_on']), t_off=float(a['t_off']), ramp=float(a['ramp'])))
        elif a['type'] in ('pipette', 'mpipette'): out.append(dict(device='pipette', reagent=REAGENT[a['ligand_index'] + (4 if a['type'] == 'mpipette' else 0)], xy=[float(x) for x in a['pos']], amplitude=float(a['amp']), t_on=float(a['t_on']), t_off=float(a['t_off'])))
        elif a['type'] in ('bath', 'mbath'): out.append(dict(device='bath', reagent=REAGENT[a['ligand_index'] + (4 if a['type'] == 'mbath' else 0)], amplitude=float(a['amp']), t_on=float(a['t_on']), t_off=float(a['t_off'])))
    return out

def new_name(i): return 'run_%05d' % (i * 7 + int(rng_master.integers(0, 7)))
def main():
    os.makedirs(f'{PKG}/runs', exist_ok=True); os.makedirs(HID, exist_ok=True); cat = []; hid_map = {}; treat = {}; counter = [0]
    scn_codes = {}; cond_codes = {}
    def code(d, key, prefix):
        if key not in d: d[key] = prefix + '%02d' % (len(d) + 1)
        return d[key]
    def write_run(frames, hidden, meta, fov, o3_every, interval, group, cond, arm, split, body_id, actions, N, extra=None):
        counter[0] += 1; nm = new_name(counter[0]); obs_seed = int(rng_master.integers(0, 2 ** 31)); rng = np.random.default_rng(obs_seed); o1, o2, o3a, o3b = render(frames, rng, fov)
        np.savez_compressed(f'{PKG}/runs/{nm}_O1.npz', **pack1(o1)); np.savez_compressed(f'{PKG}/runs/{nm}_O2.npz', **pack2(o2)); np.savez_compressed(f'{PKG}/runs/{nm}_O3a.npz', **pack3(o3a, o3_every)); np.savez_compressed(f'{PKG}/runs/{nm}_O3b.npz', **pack3(o3b, o3_every))
        hd = hidden_diag(frames, N, hidden); np.savez_compressed(f'{HID}/{nm}_hid.npz', **hd); json.dump(dict(meta=meta, events=hidden['events'], pose=hidden['pose'], private=hidden['private']), open(f'{HID}/{nm}.json', 'w'), default=str)
        row = dict(run=nm, group=group, condition=cond, arm=arm, n_cells=int(frames[0]['alive'].sum()), n_frames=len(frames), frame_interval=interval, fov=fov, split=split, body_id=body_id, noise_level='n1')
        if extra: row.update(extra)
        cat.append(row); treat[nm] = actions; hid_map[nm] = meta; return nm
    # ---- natural ensembles
    for p in sorted(glob.glob(f'{RAW}/natural/*.pkl')):
        d = pickle.load(open(p, 'rb')); split = 'development' if d['tag'] == 'cal' else 'heldout_bodies'
        write_run(d['frames'], d['hidden'], dict(family='natural', state=d['state'], seed=d['seed'], tag=d['tag']), 12.0, 1, d['interval'], 'N%03d' % d['seed'], 'N0', 'untreated', split, d['seed'], [], 24)
    # ---- identity stress (CRN triplets)
    for p in sorted(glob.glob(f'{RAW}/stress/*.pkl')):
        d = pickle.load(open(p, 'rb')); scn = d['scn']; cc = code(scn_codes, scn, 'P'); gid = 'G%03d' % (len(set(r['group'] for r in cat if r['group'].startswith('G'))) + 1)
        fov = 30.0 if scn.startswith('fuse') else 12.0; split = 'heldout_conditions' if scn == 'fuse|b|5.0,0.0' else ('heldout_bodies' if d['seed'] % 3 == 0 else 'development')
        for arm, role in (('event', 'treated'), ('twin', 'untreated_control'), ('sham', 'sham_treated')):
            a = d['arms'][arm]; evs = [e for e in a['hidden']['events'] if e['kind'] in ('remove', 'insert', 'extrude', 'cut', 'fuse', 'replace')]
            onset = (min(e['t'] for e in evs) - 1e4 - 100.0) if evs else ''; desc = dict(scn=scn)
            acts = [] if arm == 'twin' else [dict(device=dict(replace3='surgery-replace', extrude='tweezers', cutx='surgery-cut', cuty='surgery-cut').get(scn, 'dish-merge'), onset=onset if arm == 'event' else 'sham')]
            write_run(a['frames'], a['hidden'], dict(family='stress', scn=scn, arm=arm, state=d['state'], seed=d['seed']), fov, 2, 5.0, gid, cc, role, split, d['seed'], acts, a['n'], extra=dict(onset=onset if arm != 'twin' else ''))
    # ---- switch dataset
    for p in sorted(glob.glob(f'{RAW}/switch/*.pkl')):
        d = pickle.load(open(p, 'rb')); m = d['meta']; cond = code(cond_codes, ('sw', m['state'], round(m['dur'], 2), m['centre']), 'C') if False else None
        lab = LIGHT_LABELS[m['channel']]; kind = m['kind']; split = 'heldout_locations' if m['centre'] in (5, 21) else ('heldout_bodies' if (d['hidden']['pose'] and int(os.path.basename(p).split('_')[-1][:-4]) % 3 == 0) else 'development')
        acts = [dict(device=lab, disc_xy=[round(x, 3) for x in m['disc_xy0']], radius=m['radius'], amplitude=round(m['amp'] if kind != 'sham' else m['amp'], 4), t_on=m['t_on'], t_off=m['t_off'], ramp=m['ramp'])]
        arm = 'sham_treated' if kind == 'sham' else 'treated'
        if kind == 'sham': acts[0]['amplitude_applied'] = 0.0
        write_run(d['frames'], d['hidden'], dict(m, family='switch'), 12.0, 1, 2.0, 'W%03d' % (len(cat) + 1), 'T' + lab[1:] + ('b' if m['dur'] > 10 else 'a'), arm, split, int(os.path.basename(p).split('_')[-1][:-4]), acts, 24, extra=dict(onset=m['t_on']))
    # ---- decoys / other actuators
    for p in sorted(glob.glob(f'{RAW}/decoy/*.pkl')):
        d = pickle.load(open(p, 'rb')); m = d['meta']; acts = []
        for a in m['acts']:
            if a['type'] == 'light': acts.append(dict(device=LIGHT_LABELS[a['channel']], disc_xy=[round(x, 3) for x in m['disc_xy0']], radius=m['radius'], amplitude=a['amp'], t_on=a['t_on'], t_off=a['t_off'], ramp=a['ramp']))
            else: acts += obs_actions([a], None, LIGHT_LABELS)
        write_run(d['frames'], d['hidden'], dict(m, family='decoy'), 12.0, 1, 2.0, 'D%03d' % (len(cat) + 1), 'X' + m['kind'], 'treated', 'heldout_conditions' if m['kind'] in ('mbath_low', 'bath') else 'development', int(os.path.basename(p).split('_')[-1][:-4]), acts, 24, extra=dict(onset=10.0))
    keys = ['run', 'group', 'condition', 'arm', 'n_cells', 'n_frames', 'frame_interval', 'fov', 'onset', 'split', 'body_id', 'noise_level']
    with open(f'{PKG}/catalog.csv', 'w', newline='') as fh: w = csv.DictWriter(fh, keys); w.writeheader(); [w.writerow({k: c.get(k, '') for k in keys}) for c in cat]
    json.dump(treat, open(f'{PKG}/treatments.json', 'w'), indent=0, default=str)
    json.dump(dict(policy=dict(development='bodies with body_id % 3 != 0 and calibration bodies; all conditions except those listed as held out; all actuator locations except the held-out ones',
                               heldout_bodies='stress and switch runs with body_id % 3 == 0, and the natural validation bodies (disjoint ids 400-429)', heldout_conditions='the treatment codes listed in heldout_conditions (all of their runs)',
                               heldout_locations='light runs whose disc is centred on one of two held-out places of the cluster'), runs={c['run']: c['split'] for c in cat}), open(f'{PKG}/split_manifest.json', 'w'), indent=1)
    json.dump(dict(col_perm=[int(x) for x in COL_PERM], light_labels=LIGHT_LABELS, reagent={str(k): v for k, v in REAGENT.items()}, scn_codes=scn_codes, o2_cols=O2_COLS, o3a=O3A, o3b=O3B, runs=hid_map), open(f'{HID}/mapping.json', 'w'), default=str, indent=1)
    print(len(cat), 'runs written')
if __name__ == '__main__': main()
