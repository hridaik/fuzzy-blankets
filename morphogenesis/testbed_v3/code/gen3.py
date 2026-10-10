"""H5 raw run generators (pickles in ../data/raw_v3/<family>/). Observation frames are stored with full state; the packager renders O1-O3 and hidden tiers."""
import sys, os, json, time, pickle; sys.path.insert(0, ".")
import numpy as np
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw_v3')
SPACING = 100.0; NB = 8; SIGH = 0.4; NZ = 0.02
def _save(fam, name, obj):
    os.makedirs(os.path.join(RAW, fam), exist_ok=True); p = os.path.join(RAW, fam, name + '.pkl'); pickle.dump(obj, open(p, 'wb'), protocol=4); return p
def _ex(state, seed, private=None, noise=NZ):
    import world3
    from world3 import Experiment3
    return Experiment3(state, seed=seed, noise=noise, sig_h=SIGH if noise else 0.0, private=private or {}, form_seed=seed)

def job_natural(state, seed, tag):
    ex = _ex(state, seed); ex.run(150.0, observe=False); ex.t0 = ex.w.time; ex.obs = []
    for k in range(NB): ex.run(SPACING, observe=False); ex._observe()
    return _save('natural', f'{state}_{tag}_{seed:03d}', dict(frames=ex.obs, hidden=ex.hidden(), state=state, seed=seed, tag=tag, interval=SPACING))

def _axis(X):
    c = X.mean(0); u, s, vt = np.linalg.svd(X - c); return c, vt[0], vt[1]
def job_stress(scn, state, seed, T=600.0, t_ev=50.0):
    import world3, numpy as np_
    from world3 import Experiment3, fuse3
    out = {}
    for arm in ('event', 'twin', 'sham'):
        world3.OBS_EVERY = 5.0; ex = _ex(state, seed); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []; X0 = ex.w.X.copy(); acts = []
        if scn.startswith('fuse'):
            kind, st2, offs = scn.split('|'); off = [float(v) for v in offs.split(',')]; ex2 = _ex(st2, seed + 500, noise=NZ); ex2.run(100.0, observe=False)
            if arm == 'event': w = fuse3(ex.w, ex2.w, off)
            else: w = fuse3(ex.w, ex2.w, [25.0, 25.0])            # twin / sham: the two bodies are in the dish but far apart (no event)
            w.key = jax_key(seed); ex.w = w; ex.t0 = w.time; ex.obs = []
            if arm == 'sham': ex.log.append(dict(t=float(w.time), kind='sham_fuse'))
        else:
            c, u1, u2 = _axis(X0); i = int(np_.argsort(np_.linalg.norm(X0 - c, axis=1))[3 + seed % 5])
            if scn == 'replace3':
                idxs = [int(np_.argsort(np_.linalg.norm(X0 - c, axis=1))[k]) for k in (2 + seed % 4, 9, 17)]
                acts = [dict(type='surgery', op='replace', pos=X0[j].tolist(), t=t_ev + 100 * q) for q, j in enumerate(idxs)]
            elif scn == 'extrude':
                v = X0[i] - c; v = 8.0 * v / np_.linalg.norm(v); acts = [dict(type='tweezers', pos=X0[i].tolist(), vec=v.tolist(), t=t_ev)]
            elif scn in ('cutx', 'cuty'):
                n = u1 if scn == 'cutx' else u2; acts = [dict(type='surgery', op='cut', normal=n.tolist(), d=float(c @ n), vec=(7.0 * n).tolist(), t=t_ev)]
        ex.run(T, acts if arm != 'twin' else [], sham=(arm == 'sham')); out[arm] = dict(frames=ex.obs, hidden=ex.hidden(), n=ex.w.N)     # twin: no operation at all
    return _save('stress', f'{scn.replace("|", "_").replace(",", "x")}_{state}_{seed:03d}', dict(arms=out, scn=scn, state=state, seed=seed))
def jax_key(s):
    import jax; return jax.random.PRNGKey(9000 + s)

CH = {'MA': ('mem', 0), 'MB': ('mem', 1), 'SEC': ('sec', 0), 'RG': ('rg', 0), 'MIG': ('mig', 0)}
def job_switch(state, centre, dur, level, kind, seed, thr, far=None, T_after=100.0, t_on=10.0):
    """kind: 'on' (disc on place `centre`, amplitude level*thr), 'wrong' (disc on place `far`, same amplitude), 'sham' (on-target but amplitude 0)"""
    import world3
    from world3 import Mask
    world3.OBS_EVERY = 2.0; ch = 'MB' if state == 'a' else 'MA'; ex = _ex(state, seed, private={ch: CH[ch]}); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []
    place = centre if kind != 'wrong' else far; amp = level * thr; ramp = min(5.0, dur / 4)
    act = [dict(type='light', channel=ch, mask=Mask([('place', place, 1.5, 1.0)]), amp=amp, t_on=t_on, t_off=t_on + dur, ramp=ramp)]
    c0 = ex.place_in_arena(place)
    ex.run(t_on + dur + T_after, act, sham=(kind == 'sham'))
    meta = dict(state=state, centre=centre, dur=dur, level=level, kind=kind, amp=amp, place=place, disc_xy0=c0.tolist(), radius=1.5, t_on=t_on, t_off=t_on + dur, ramp=ramp, channel=ch)
    return _save('switch', f'{state}_c{centre}_d{dur:.1f}_l{level}_{kind}_{seed}', dict(frames=ex.obs, hidden=ex.hidden(), meta=meta))

def job_decoy(state, kind, seed, T=160.0):
    import world3
    from world3 import Mask
    world3.OBS_EVERY = 2.0; ch = {'sec': 'SEC', 'rg': 'RG', 'mig': 'MIG'}.get(kind); priv = {ch: CH[ch]} if ch else {}; ex = _ex(state, seed, private=priv); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []
    c = ex.place_in_arena(12); X = ex.w.X; cen = X.mean(0)
    if ch: acts = [dict(type='light', channel=ch, mask=Mask([('place', 12, 1.5, 1.0)]), amp={'sec': 0.8, 'rg': 0.3, 'mig': 0.5}[kind], t_on=10, t_off=60, ramp=5)]
    elif kind == 'mbath_low': acts = [dict(type='mbath', ligand_index=1 if state == 'a' else 0, amp=0.4, t_on=10, t_off=T, ramp=5)]
    elif kind == 'mbath_high': acts = [dict(type='mbath', ligand_index=1 if state == 'a' else 0, amp=1.0, t_on=10, t_off=70, ramp=5)]
    elif kind == 'mpipette': acts = [dict(type='mpipette', pos=cen.tolist(), ligand_index=1 if state == 'a' else 0, amp=6.0, t_on=10, t_off=60, ramp=5)]
    elif kind == 'pipette': acts = [dict(type='pipette', pos=cen.tolist(), ligand_index=0, amp=1.0, t_on=10, t_off=60, ramp=5)]
    elif kind == 'bath': acts = [dict(type='bath', ligand_index=0, amp=0.3, t_on=10, t_off=60, ramp=5)]
    ex.run(T, acts); meta = dict(state=state, kind=kind, channel=ch, centre=12, disc_xy0=c.tolist(), radius=1.5, acts=[{k: v for k, v in a.items() if k != 'mask'} for a in acts])
    return _save('decoy', f'{state}_{kind}_{seed}', dict(frames=ex.obs, hidden=ex.hidden(), meta=meta))
