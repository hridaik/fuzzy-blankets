"""Chapters 3.2 (frozen T5 monitor on three exemplars) and 3.3 (serial replacement, IDENTITY_EVENTS_V3 seed 0, regenerated)."""
import sys; sys.path.insert(0, '.')
from common import *
import build_blind3 as B3
sys.path.insert(0, f'{T5}/code'); from t5mon.monitor import OnlineMonitor
MON = json.load(open(f'{T5}/MONITOR_CONFIG.json')); B = MON['bounds']; CFGP = f'{T5}/MONITOR_CONFIG.json'
RUNS = f'{PKG}/runs'
def run_monitor(frames):
    """frames: list of (t, xy, lev(n,7), ids) -> list of monitor outputs (the frozen online monitor, causal)"""
    m = OnlineMonitor(CFGP); out = []
    for (t, xy, lev, ids) in frames: out.append(m.update(float(t), xy, lev, ids))
    return out
def traces(outs):
    t = [o['t'] for o in outs]
    mat = [1 - o['material_J'] for o in outs]; geo = []
    for o in outs:
        g = max(o['mst_max'] / B['mst_max'], o['s1_rel'] / B['s1_rel'], o['s2_rel'] / B['s2_rel'])
        if o['ncomp'] > 1 or o['n'] != 24: g = max(g, 1.0001 + 0.0)      # outside the band by definition
        geo.append(g)
    pat = [o['pat_dz'] / B['pat_dz'] for o in outs]; pplus = [o['p_plus'] for o in outs]
    return dict(t=t, material=mat, geometry=geo, pattern=pat, p_plus=pplus, state=[o['state'] for o in outs], V=[bool(o['V_body']) for o in outs], Vnow=[bool(o['V_body_now']) for o in outs], ev=[o['events'] for o in outs], ncomp=[o['ncomp'] for o in outs], n=[o['n'] for o in outs],
                geo_ok=[bool(o['geometry_ok']) for o in outs], mat_ok=[bool(o['material_ok']) for o in outs], u0=[o['u'][0] for o in outs], u1=[o['u'][1] for o in outs])
def package_frames(run, t0, t1):
    z = np.load(f'{RUNS}/{run}_O1.npz'); t = z['t']; fp = z['frame_ptr']; fr = []
    for T in range(t0, t1 + 1):
        k = np.where(np.abs(t - T) < 1e-6)[0]
        if len(k) != 1: continue
        k = int(k[0]); a, b = fp[k], fp[k + 1]; fr.append((T, z['xy'][a:b], z['level'][a:b], z['cell_id'][a:b]))
    return fr
def clip_pack(fr, o, extra=None):
    return dict(t=[f[0] for f in fr], xy=[enc16(f[1], 1000) for f in fr], ids=[f[3].tolist() for f in fr], tr=traces(o), **(extra or {}))
res = {}
# --- undisturbed (twin) and cut, from package v3 (body 2700, t = 1..150 at 1 tu; cut at t = 50)
for key, run in (('undisturbed', 'run_00266'), ('cut', 'run_00263')):
    fr = package_frames(run, 1, 150); o = run_monitor(fr); res[key] = clip_pack(fr, o, dict(run=run, onset=50 if key == 'cut' else None)); print(key, len(fr), 'V_body end', o[-1]['V_body'], 'events', sorted({e for x in o for e in x['events']}))
# --- light switch: T5 held-out controller episode seed 6007, O1 frames regenerated exactly as the live server (rng seeded by [seed, step*2, level index]) from the hidden per-step state
R = [json.loads(l) for l in open(f'{T5}/logs/heldout_summary.jsonl')]
ctrl = next(r for r in R if r['seed'] == 6007 and r['arm'] == 'ctrl'); eid = ctrl['episode']; hz = np.load(f'{SEALED}/episode_{eid:05d}/hidden.npz'); ep = json.load(open(f'{T5}/episodes_heldout/ep_{eid:05d}.json'))
fr = []; seed = 6007
for k, t in enumerate(hz['t']):
    f = dict(t=float(t), X=hz['X'][k], C=hz['C'][k], D=hz['D'][k], E=hz['E'][k], alive=hz['alive'][k], cell_id=hz['cell_id'][k]); a = f['alive']
    rng = np.random.default_rng([seed, int(round(t * 2)), 0]); X = f['X'][a] + B3.POS_NOISE * rng.standard_normal((a.sum(), 2)); Lv = B3.lnoise(rng, B3.levels(f)[a])[:, B3.COL_PERM]
    fr.append((float(t), X, Lv, f['cell_id'][a]))
o = run_monitor(fr)
# verify against the live log of T5 (same frozen monitor, same observations)
live = ep['frames']; mism = 0; maxd = 0.0
for a_, b_ in zip(live, o):
    maxd = max(maxd, abs(a_['mst_max'] - b_['mst_max']), abs(a_['u'][0] - b_['u'][0]), abs(a_['p_plus'] - b_['p_plus'])); mism += int(a_['state'] != b_['state'] or a_['V_body'] != b_['V_body'])
print('light switch: regenerated vs live T5 log: frames', len(live), len(o), 'state/V_body mismatches', mism, 'max abs diff', maxd)
acts = [dict(t=a['t'], xy=a['mask']['xy'], r=a['mask']['radius'], dur=a['dur'], ramp=a['ramp'], amp=a['amp'], label=a['label']) for a in ep['actions']]
sg = lambda z: 1 / (1 + np.exp(-z)); rho = [float(sg(hz['L'][k][hz['alive'][k]]).mean()) for k in range(len(hz['t']))]
res['light'] = clip_pack(fr, o, dict(run=f'T5 held-out seed 6007 controller (episode {eid})', onset=20, acts=acts, rho=rho, verify=dict(frames=len(live), state_vbody_mismatches=mism, max_abs_diff=maxd)))
res['bounds'] = B; res['bounds_cons'] = MON['bounds_conservative']
write_js('c32', res)
# ---------------- 3.3 serial replacement (seed 0), deterministic, every 1 tu
from world3 import *
w = new_adult3('a', capacity=24, noise=0.0, key=0); order = np.random.default_rng(0).permutation(24); X0 = w.X.copy(); frames = []; reps = []
def snapshot(): frames.append((w.time - 1e4, w.X.copy(), sg(w.L).copy(), w.cell_id.copy()))
snapshot()
for i in order:
    w.replace(int(i), seed=0); reps.append((float(w.time - 1e4), int(i)))
    for _ in range(100): w.run(1.0); snapshot()
for _ in range(400): w.run(1.0); snapshot()
tm, XS, CT = template(); R_, tc, xc, asg = frame_map(X0, np.zeros((24, 24)) + 0) if False else (None, None, None, None)
Xa = np.stack([f[1] for f in frames]); Ra = np.stack([f[2] for f in frames]); Ia = np.stack([f[3] for f in frames]); T_ = len(frames)
from scipy.sparse.csgraph import connected_components, minimum_spanning_tree
from scipy.spatial.distance import cdist
mst = []; nc = []; s1 = []; s2 = []
for k in range(T_):
    D = cdist(Xa[k], Xa[k]); nc.append(int(connected_components(D < 1.6, directed=False)[0])); mst.append(float(minimum_spanning_tree(D).toarray().max())); c = Xa[k] - Xa[k].mean(0); ev = np.linalg.eigvalsh(c.T @ c / 24); s1.append(float(np.sqrt(ev[1]))); s2.append(float(np.sqrt(ev[0])))
s1b, s2b = np.median(s1[:10]), np.median(s2[:10]); geo = [max(mst[k] / B['mst_max'], abs(s1[k] / s1b - 1) / B['s1_rel'], abs(s2[k] / s2b - 1) / B['s2_rel'], 1.0001 if nc[k] > 1 else 0) for k in range(T_)]
orig = [int((Ia[k] < 24).sum()) for k in range(T_)]
# types of the original places (for colouring original cells); newcomers drawn as neutral until they settle
XSC = 1000; Xa = np.clip(Xa, -32, 32); print('c33 X scale', XSC, 'max abs', np.abs(Xa).max())
write_js('c33', dict(T=T_, XS=XSC, X=enc16(Xa, XSC), rho=enc16(Ra, 20000), ids=Ia.astype(int).tolist() if False else enc16(Ia, 1), reps=reps, orig=orig, geo=geo, nc=nc, rho_mean=Ra.mean(1).tolist(), types0=CT[np.argsort(np.argsort(0)) if False else np.arange(24)].tolist(), perm0=w.perm0.tolist(), tmplType=CT.tolist(), seed=0, n_reps=len(reps)))
print('serial: final n components', nc[-1], 'orig left', orig[-1], 'mean rho end', Ra[-1].mean())
