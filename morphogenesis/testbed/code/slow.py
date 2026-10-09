"""slow-manifold plan dynamics: freeze (mu, zeta), relax the fast variables (x, c), read d(zeta_B - zeta_A)/dt"""
import sys; sys.path.insert(0,'.')
from mem import *
import dataclasses

def g_of_s(kappa_m, mem_amp, pim, pi_zeta, bias, s_list, T_relax=60.0, jit_x=0.0, extra=None):
    tm = make_body('AB', kappa_m=kappa_m, mem_amp=mem_amp); d = dict(pi_m=pim, pi_zeta=pi_zeta, bias=bias, kappa_m=kappa_m, mem_amp=mem_amp)
    if extra: d.update(extra)
    P, _ = mem_params(**d); eng = make_engine(tm, P); eng.dt, eng.rho = auto_dt(eng, tm)
    Pf = dataclasses.replace(P, k_mu=0.0, k_zeta=0.0); engf = make_engine(tm, Pf)     # frozen slow variables
    n = tm.n; out = []
    st0, perm = mem_start(tm, 0, jit_x=0.0, jit_mu=0.0)
    MU = st0[2]
    for s in s_list:
        w = 1 / (1 + np.exp(-s)); ZE = jnp.tile(jnp.array([0.0, s]), (n, 1))
        wz = np.array([1 - w, w])
        X = sum(wz[z] * tm.Xs[z][:, perm].T for z in range(2)); C = sum(wz[z] * tm.Cs[z][:, perm].T for z in range(2))
        st = (jnp.array(X), jnp.array(C), MU, ZE)
        fin = engf.run_final(st, 1e4, eng.dt, int(T_relax / eng.dt), jax.random.PRNGKey(0), None, 0)
        dr = eng.drift(fin, 1e4, jnp.zeros((n, tm.nc)))
        dz = np.array(dr[3]); g = float((dz[:, 1] - dz[:, 0]).mean())
        # per-cell spread and mean secretion of memory ligand
        out.append(dict(s=s, w=w, g=g, g_min=float((dz[:, 1] - dz[:, 0]).min()), g_max=float((dz[:, 1] - dz[:, 0]).max()), cm=float(np.array(fin[1])[:, 4].mean())))
    return out
