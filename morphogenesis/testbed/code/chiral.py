"""T2d chirality: single-plan chiral 24-cell body, relational (positional OFF), no memory variable.
 (i) both mirror forms stable and complete; (ii) disc-pulse bisection for a mirror switch (ext secretion of signal `ch` in a disc of template-frame radius r)."""
import sys, json; sys.path.insert(0, '.')
from par import run_jobs
KMU, KA = 1.4, 0.4

def mk():
    from asm import Params, np, make_engine, make_body, auto_dt, tb_params
    t = make_body('chiral'); P = tb_params()
    eng = make_engine(t, P); eng.dt, eng.rho = auto_dt(eng, t); return t, eng

def start(t, k, mirror, jit=0.3):
    from asm import seeded_start, jnp
    st = seeded_start(t, k, jit_x=jit); X = np_(st[0]); 
    if mirror:   # mirror image of the whole configuration (cells keep their slots; geometry reflected through y -> -y)
        rng = __import__('numpy').random.default_rng(777 + k); perm = rng.permutation(t.n)
        X = t.Xs[0][:, perm].T * __import__('numpy').array([1, -1]) + jit * rng.standard_normal((t.n, 2))
        st = (jnp.array(X),) + tuple(st[1:])
    return st

def np_(a):
    import numpy; return numpy.array(a)

def classify(t, X, C):
    from asm import d_rigid, cell_types, type_vector
    ty = type_vector(t); ct = cell_types(C.T)
    dL = d_rigid(X.T, ct, t.Xs[0], ty)                                   # proper rotations only
    dR = d_rigid(X.T, ct, t.Xs[0] * __import__('numpy').array([[1], [-1]]), ty)
    lab = 'L' if dL < 0.4 and dL < dR else ('R' if dR < 0.4 else 'defect')
    return lab, dL, dR

def forms_job(k, mirror):
    from asm import np, jax, analyse
    t, eng = mk(); st = start(t, k, mirror); fin = eng.run_final(st, 0.0, eng.dt, int(400 / eng.dt), jax.random.PRNGKey(0), None, 0)
    lab, dL, dR = classify(t, np.array(fin[0]), np.array(fin[1])); r = analyse(eng, t, fin, 0)
    ev = np.linalg.eigvals(np.array(eng.jac_flat(fin, 1e4))); ev = ev[np.abs(ev) > 1e-9]
    return dict(k=k, start='R' if mirror else 'L', label=lab, dL=dL, dR=dR, orbit_complete=r['orbit_complete'], min_orbit_maxbel=r['min_orbit_maxbel'], shape_speed=r['shape_speed'], max_re_eig=float(ev.real.max()),
                n_zero_modes=int((np.abs(ev.real) < 1e-7).sum()))

def pulse_job(center_slot, radius, amp, dur, ch, mirror=False, k=0, T_after=250.0):
    """disc = cells whose SLOT lies within `radius` of slot `center_slot`'s template position (body frame); pulse = extra secretion `amp` of signal ch for `dur`"""
    from asm import np, jax, jnp
    t, eng = mk(); st = start(t, k, mirror); n, nc = t.n, t.nc
    rng = np.random.default_rng(777 + k); perm = rng.permutation(n)               # cell i holds slot perm[i]
    c = t.Xs[0][:, center_slot]; disc = np.where(np.linalg.norm(t.Xs[0][:, perm].T - c, axis=1) <= radius)[0]
    a = np.zeros((n, nc)); a[disc, ch] = amp
    st = eng.run_final(st, 0.0, eng.dt, int(100 / eng.dt), jax.random.PRNGKey(0), None, 0)       # settle first
    t_on = 1e4; fin = eng.run_final(st, t_on, eng.dt, int((dur + T_after) / eng.dt), jax.random.PRNGKey(0), (jnp.array(a), t_on, t_on + dur), 0)
    lab, dL, dR = classify(t, np.array(fin[0]), np.array(fin[1]))
    return dict(center_slot=center_slot, radius=radius, amp=amp, dur=dur, ch=ch, start='R' if mirror else 'L', label=lab, dL=dL, dR=dR, n_cells=int(len(disc)))

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == 'forms':
        res = run_jobs(forms_job, [(k, m) for k in range(8) for m in (False, True)], workers=8, label='forms'); json.dump(res, open('../data/chiral_forms.json', 'w'))
        for r in res: print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    else:
        import numpy as np
        centers = {'head_tip': 0, 'trunk': 9, 'limb_side': 13}; amps = [0.5, 1, 2, 4, 8, 16, 32]
        args = [(cs, 1.6, a, 20.0, ch) for cs in centers.values() for a in amps for ch in (2, 3)]
        res = run_jobs(pulse_job, args, workers=8, label='pulse'); json.dump(res, open('../data/chiral_pulse_scan.json', 'w'))
        for r in res: print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
