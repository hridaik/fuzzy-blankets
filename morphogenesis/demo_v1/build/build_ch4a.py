"""Chapters 4.1 (five lights, seed 5001 a and its b clone), 4.2 mini-clips (equal dose: body centre vs the tail end), 4.3 (seed 6007 four arms, from the sealed hidden logs), 4.4 worst clip (seed 6026)."""
import sys; sys.path.insert(0, '.')
from common import *
import lib as AL
from lib import make_dish, snap, restore, mk_action, rel_t
sg = lambda z: 1 / (1 + np.exp(-z))
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
def bodyxf(X, MU): R, tc, xc, asg = frame_map(X, MU); return (lambda P: to_body(P, R, tc, xc)), asg
def record(ex, T, acts, step=1.0):
    fr = []
    for _ in range(int(T / step)):
        ex.run_sched(step, acts, sham=False, obs_times=[]); w = ex.w; fr.append(dict(X=w.X.copy(), C=w.C.copy(), L=w.L.copy(), D=w.D.copy(), E=w.E.copy(), MU=w.MU.copy()))
    return fr
def ncomp(X): return int(connected_components(cdist(X, X) < 1.6, directed=False)[0])
# ---------------- 4.1
out41 = dict(rows={}, params=dict(amp=5.0, dur=10.0, ramp=2.5, t_on=20.0, radius=1.5, T=100))
lab_ch = dict(zip(['L1', 'L2', 'L3', 'L4', 'L5'], ['L1', 'L2', 'L3', 'L4', 'L5']))
for st in ('a', 'b'):
    ex = make_dish(5001, state=st); ex.run_sched(20.0, [], sham=False, obs_times=[]); s0 = snap(ex); X20 = ex.w.X.copy(); MU20 = ex.w.MU.copy(); tb, asg = bodyxf(X20, MU20); ctr = X20.mean(0)
    twin = record(ex, 100, []); rowc = []
    types = template()[2][asg]
    for lab in ['L1', 'L2', 'L3', 'L4', 'L5']:
        restore(ex, s0); acts = [mk_action(lab, {'type': 'disc', 'xy': ctr.tolist(), 'radius': 1.5}, 5.0, 20.0, 10.0, 2.5)]; fr = record(ex, 100, acts)
        rho = np.array([sg(f['L']).mean() for f in fr]); rho_tw = np.array([sg(f['L']).mean() for f in twin])
        dX = max(np.abs(a['X'] - b['X']).max() for a, b in zip(fr, twin)); dC = max(np.abs(a['C'] - b['C']).max() for a, b in zip(fr, twin)); nc = max(ncomp(f['X']) for f in fr)
        flipped = (rho[-1] < 0.5) != (rho_tw[-1] < 0.5)
        if flipped: verdict = 'state flipped'
        elif nc > 1 or dX > 2.0: verdict = 'damage'
        elif dC > 0.1: verdict = 'pattern only'
        else: verdict = 'no effect'
        print(st, lab, 'dX %.3f dC %.3f ncomp %d rho_end %.2f -> %s' % (dX, dC, nc, rho[-1], verdict))
        rowc.append(dict(label=lab, verdict=verdict, dX=float(dX), dC=float(dC), ncomp=int(nc), rho_end=float(rho[-1]), X=enc16(np.stack([tb(f['X']) for f in fr]), 1000), rho=enc16(np.stack([sg(f['L']) for f in fr]), 20000), disc=tb(ctr)[0].tolist()))
    out41['rows'][st] = dict(types=types.tolist(), clips=rowc, nc_twin=max(ncomp(f['X']) for f in twin))
write_js('c41', out41)
# ---------------- 4.2 mini-clips: equal dose, centre vs tail end (T5's '+p = 3 ("head")'), seed 5004 (dev, state a)
seed = 5004; ex = make_dish(seed); ex.run_sched(20.0, [], sham=False, obs_times=[]); s0 = snap(ex); X20 = ex.w.X.copy(); MU20 = ex.w.MU.copy(); tb, asg = bodyxf(X20, MU20)
R, tc, xc, _ = frame_map(X20, MU20); to_arena = lambda p: (R @ (np.atleast_2d(p) - tc).T).T + xc
disc = {'centre': to_arena([0.0, 0.0])[0], 'tail_end': to_arena([3.0, 0.0])[0]}
ncell = {k: int((np.linalg.norm(X20 - v, axis=1) <= 1.5).sum()) for k, v in disc.items()}; lab = 'L4' if sg(ex.w.L).mean() > 0.5 else 'L3'; start = 'a' if sg(ex.w.L).mean() > 0.5 else 'b'
exn = AL.Experiment4(start, seed=seed, noise=0.0, sig_h=0.0, private=dict(AL.PRIV), form_seed=seed); exn.t0 = s0['time'] - 20.0
def flips(amp_c, dur=20.0, ramp=5.0):
    restore(exn, s0); acts = [mk_action(lab, {'type': 'disc', 'xy': disc['centre'].tolist(), 'radius': 1.5}, amp_c, 20.0, dur, ramp)]; exn.run_sched(dur + 100, acts, sham=False, obs_times=[]); m = sg(exn.w.L).mean(); return (m < .5) if start == 'a' else (m > .5)
lo, hi = 0.2, 8.0
for _ in range(10):
    m = np.sqrt(lo * hi)
    if flips(m): hi = m
    else: lo = m
thr = hi; print('4.2: centre noise-free threshold amp (20 tu)', thr, 'cells', ncell)
clips = {}
for factor in (1.3, 1.6, 2.0):
    amp_c = factor * thr; dose = amp_c * 20 * ncell['centre']; amp_t = dose / (20 * ncell['tail_end']); res = {}
    for k, amp in (('centre', amp_c), ('tail_end', amp_t)):
        restore(ex, s0); acts = [mk_action(lab, {'type': 'disc', 'xy': disc[k].tolist(), 'radius': 1.5}, amp, 20.0, 20.0, 5.0)]; fr = record(ex, 120, acts); rho = np.stack([sg(f['L']) for f in fr])
        end_other = (rho[-1].mean() < .5) if start == 'a' else (rho[-1].mean() > .5); res[k] = dict(amp=float(amp), end_other=bool(end_other), rho_peak_dev=float(max((rho[:, :].mean(1) - rho[0].mean()) * (-1 if start == 'a' else 1))), fr=fr)
    print('factor', factor, 'dose', round(dose, 1), {k: (round(v['amp'], 2), v['end_other'], round(v['rho_peak_dev'], 2)) for k, v in res.items()})
    if res['centre']['end_other'] and not res['tail_end']['end_other']: clips = dict(factor=factor, dose=float(dose), res=res); break
assert clips, 'no equal-dose pair found'
res = clips['res']
write_js('c42clips', dict(seed=seed, start=start, label=lab, dose=clips['dose'], factor=clips['factor'], thr_amp_centre=float(thr), dur=20.0, ramp=5.0, t_on=20.0,
    clips={k: dict(amp=v['amp'], cells=ncell[k], end_other=v['end_other'], disc=tb(disc[k])[0].tolist(), X=enc16(np.stack([tb(f['X']) for f in v['fr']]), 1000), rho=enc16(np.stack([sg(f['L']) for f in v['fr']]), 20000)) for k, v in res.items()}, types=template()[2][asg].tolist()))
# ---------------- 4.3 / 4.4: sealed hidden logs of the held-out arms
R_ = [json.loads(l) for l in open(f'{T5}/logs/heldout_summary.jsonl')]
def arm_pack(seed, arm, xf, geo_base=None):
    r = next(x for x in R_ if x['seed'] == seed and x['arm'] == arm); eid = r['episode']; h = np.load(f'{SEALED}/episode_{eid:05d}/hidden.npz'); L = json.load(open(f'{T5}/episodes_heldout/ep_{eid:05d}.json')); T = len(h['t'])
    X = np.stack([xf(h['X'][k]) for k in range(T)]); rho = sg(h['L'])
    mon = L['frames']; acts = []; cum = 0.0
    for a in L['actions']:
        m = a['mask']; acts.append(dict(t=a['t'], dur=a['dur'], ramp=a['ramp'], amp=a['amp'], dose=a['dose'], cells=a['cells'], whole=(m['type'] == 'all'), xy=(None if m['type'] == 'all' else xf(np.array(m['xy']))[0].tolist()), r=m.get('radius', 0)))
    B = json.load(open(f'{T5}/MONITOR_CONFIG.json'))['bounds']
    geo = [max(f['mst_max'] / B['mst_max'], f['s1_rel'] / B['s1_rel'], f['s2_rel'] / B['s2_rel'], 1.0001 if (f['ncomp'] > 1 or f['n'] != 24) else 0) for f in mon]
    return dict(eid=eid, T=T, X=enc16(X, 1000), rho=enc16(rho, 20000), acts=acts, state=[f['state'] for f in mon], p_plus=[round(f['p_plus'], 4) for f in mon], V=[bool(f['V_body']) for f in mon], u0=[round(f['u'][0], 3) for f in mon], geo=[round(g, 3) for g in geo],
                decisions=[dict(t=d['t'], action=d['action'], reason=d.get('reason', '')) for d in L.get('decisions', [])], summary=dict(success=r['success'], dose=r['dose'], reason=r.get('reason')))
def xform_for(seed):
    r = next(x for x in R_ if x['seed'] == seed and x['arm'] == 'twin'); h = np.load(f'{SEALED}/episode_{r["episode"]:05d}/hidden.npz'); R, tc, xc, asg = frame_map(h['X'][20], h['MU'][20])
    return (lambda P: to_body(P, R, tc, xc)), template()[2][asg]
xf, types = xform_for(6007); arms = {a: arm_pack(6007, a, xf) for a in ('ctrl', 'random', 'whole_dm', 'twin')}
write_js('c43', dict(seed=6007, types=types.tolist(), start='a', arms=arms))
xf, types = xform_for(6026); write_js('c44worst', dict(seed=6026, types=types.tolist(), start='a', arm=arm_pack(6026, 'ctrl', xf)))
