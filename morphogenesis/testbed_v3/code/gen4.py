"""Package-v3 raw run generators (pickles in ../data/raw_v4/<family>/). Same families as v2; new bodies; finer sampling."""
import sys, os, json, time, pickle; sys.path.insert(0, ".")
import numpy as np
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw_v4')
SIGH = 0.4; NZ = 0.02; TAU_SLOW = 112.0; NAT_T = 50 * TAU_SLOW              # 5,600 tu
def _save(fam, name, obj):
    os.makedirs(os.path.join(RAW, fam), exist_ok=True); p = os.path.join(RAW, fam, name + '.pkl'); pickle.dump(obj, open(p, 'wb'), protocol=4); return p
def _ex(state, seed, private=None, noise=NZ):
    from world4 import Experiment4
    return Experiment4(state, seed=seed, noise=noise, sig_h=SIGH if noise else 0.0, private=private or {}, form_seed=seed)
def job_natural(state, seed, tag):
    from world4 import obs_schedule
    ex = _ex(state, seed); ex.run_sched(300.0, observe=False) if False else None
    ex.run(300.0, observe=False); ex.t0 = ex.w.time; ex.obs = []; ex.run_sched(NAT_T, obs_times=obs_schedule(NAT_T))
    return _save('natural', f'{state}_{tag}_{seed:04d}', dict(frames=ex.obs, hidden=ex.hidden(), state=state, seed=seed, tag=tag, interval=1.0))
def _axis(X):
    c = X.mean(0); u, s, vt = np.linalg.svd(X - c); return c, vt[0], vt[1]
def job_stress(scn, state, seed, T=600.0, t_ev=50.0):
    from world4 import obs_schedule, fuse3
    out = {}
    for arm in ('event', 'twin', 'sham'):
        ex = _ex(state, seed); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []; X0 = ex.w.X.copy(); acts = []
        if scn.startswith('fuse'):
            kind, st2, offs = scn.split('|'); off = [float(v) for v in offs.split(',')]; ex2 = _ex(st2, seed + 500); ex2.run(100.0, observe=False)
            w = fuse3(ex.w, ex2.w, off if arm == 'event' else [14.0, 14.0]); import jax; w.key = jax.random.PRNGKey(9000 + seed); ex.w = w; ex.t0 = w.time; ex.obs = []
            if arm == 'sham': ex.log.append(dict(t=float(w.time), kind='sham_fuse'))
            dense = (0.0, 100.0)
        else:
            c, u1, u2 = _axis(X0); i = int(np.argsort(np.linalg.norm(X0 - c, axis=1))[3 + seed % 5])
            if scn == 'replace3':
                idxs = [int(np.argsort(np.linalg.norm(X0 - c, axis=1))[k]) for k in (2 + seed % 4, 9, 17)]; acts = [dict(type='surgery', op='replace', pos=X0[j].tolist(), t=t_ev + 100 * q) for q, j in enumerate(idxs)]; dense = (t_ev - 20, t_ev + 200 + 100)
            elif scn == 'extrude':
                v = X0[i] - c; v = 8.0 * v / np.linalg.norm(v); acts = [dict(type='tweezers', pos=X0[i].tolist(), vec=v.tolist(), t=t_ev)]; dense = (t_ev - 20, t_ev + 100)
            else:
                n = u1 if scn == 'cutx' else u2; acts = [dict(type='surgery', op='cut', normal=n.tolist(), d=float(c @ n), vec=(7.0 * n).tolist(), t=t_ev)]; dense = (t_ev - 20, t_ev + 100)
        ex.run_sched(T, acts if arm != 'twin' else [], sham=(arm == 'sham'), obs_times=obs_schedule(T, dense)); out[arm] = dict(frames=ex.obs, hidden=ex.hidden(), n=ex.w.N, dense=dense)
    return _save('stress', f'{scn.replace("|", "_").replace(",", "x")}_{state}_{seed:04d}', dict(arms=out, scn=scn, state=state, seed=seed))
CH = {'MA': ('mem', 0), 'MB': ('mem', 1), 'SEC': ('sec', 0), 'RG': ('rg', 0), 'MIG': ('mig', 0)}
def job_switch(state, centre, dur, level, kind, seed, thr, far=None, T_after=100.0, t_on=40.0):
    from world4 import obs_schedule
    from world3 import Mask
    ch = 'MB' if state == 'a' else 'MA'; ex = _ex(state, seed, private={ch: CH[ch]}); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []
    place = centre if kind != 'wrong' else far; amp = level * thr; ramp = min(5.0, dur / 4); act = [dict(type='light', channel=ch, mask=Mask([('place', place, 1.5, 1.0)]), amp=amp, t_on=t_on, t_off=t_on + dur, ramp=ramp)]
    c0 = ex.place_in_arena(place); T = t_on + dur + T_after + 30.0
    ex.run_sched(T, act, sham=(kind == 'sham'), obs_times=obs_schedule(T, (t_on - 20.0, t_on + dur + T_after)))
    meta = dict(state=state, centre=centre, dur=dur, level=level, kind=kind, amp=amp, place=place, disc_xy0=c0.tolist(), radius=1.5, t_on=t_on, t_off=t_on + dur, ramp=ramp, channel=ch)
    return _save('switch', f'{state}_c{centre}_d{dur:.1f}_l{level}_{kind}_{seed}', dict(frames=ex.obs, hidden=ex.hidden(), meta=meta))
def job_decoy(state, kind, seed, T=200.0, t_on=40.0):
    from world4 import obs_schedule
    from world3 import Mask
    ch = {'sec': 'SEC', 'rg': 'RG', 'mig': 'MIG'}.get(kind); priv = {ch: CH[ch]} if ch else {}; ex = _ex(state, seed, private=priv); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []
    c = ex.place_in_arena(12); cen = ex.w.X.mean(0); t1 = t_on + 50.0
    if ch: acts = [dict(type='light', channel=ch, mask=Mask([('place', 12, 1.5, 1.0)]), amp={'sec': 0.8, 'rg': 0.3, 'mig': 0.5}[kind], t_on=t_on, t_off=t1, ramp=5)]
    elif kind == 'mbath_low': acts = [dict(type='mbath', ligand_index=1 if state == 'a' else 0, amp=0.4, t_on=t_on, t_off=T, ramp=5)]
    elif kind == 'mbath_high': acts = [dict(type='mbath', ligand_index=1 if state == 'a' else 0, amp=1.0, t_on=t_on, t_off=t1 + 10, ramp=5)]
    elif kind == 'mpipette': acts = [dict(type='mpipette', pos=cen.tolist(), ligand_index=1 if state == 'a' else 0, amp=6.0, t_on=t_on, t_off=t1, ramp=5)]
    elif kind == 'pipette': acts = [dict(type='pipette', pos=cen.tolist(), ligand_index=0, amp=1.0, t_on=t_on, t_off=t1, ramp=5)]
    elif kind == 'bath': acts = [dict(type='bath', ligand_index=0, amp=0.3, t_on=t_on, t_off=t1, ramp=5)]
    ex.run_sched(T, acts, obs_times=obs_schedule(T, (t_on - 20.0, t1 + 100.0)))
    meta = dict(state=state, kind=kind, channel=ch, centre=12, disc_xy0=c.tolist(), radius=1.5, acts=[{k: v for k, v in a.items() if k != 'mask'} for a in acts])
    return _save('decoy', f'{state}_{kind}_{seed}', dict(frames=ex.obs, hidden=ex.hidden(), meta=meta))
