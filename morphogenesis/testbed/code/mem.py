"""T2c body-plan memory harness"""
import sys; sys.path.insert(0,'.')
from asm import *

DEF = dict(mem_amp=0.25, kappa_m=0.35, pi_m=float(np.exp(2)), pi_zeta=1.0, bias=1.0, k_a=0.4, k_mu=1.4, k_zeta=1.0, lp=-10.0, pi_s=3.0)

def mem_params(**kw):
    d = dict(DEF); d.update(kw)
    ps = float(np.exp(d['pi_s']))
    P = Params(k_mu=d['k_mu'], k_a=d['k_a'], pi_prior=float(np.exp(d['lp'])), pi_a_x=0.0, pi_a_c=0.0, pos_on=False,
               pi_x=ps, pi_c=ps, pi_l=ps, pi_ref=ps, pi_act=1.5 * ps / np.e,
               pi_c_vec=(ps,) * 4 + (ps,), pi_l_vec=(ps,) * 4 + (d['pi_m'],),
               pi_zeta=d['pi_zeta'], zeta0=(d['bias'], 0.0), k_zeta=d['k_zeta'])
    return P, d

def mem_start(tmpl, plan, k=0, a=8.0, s=4.0, jit_x=0.3, jit_mu=0.3, jit_z=0.0, bias=1.0):
    n = tmpl.n; rng = np.random.default_rng(777 + k); perm = rng.permutation(n)
    MU = np.zeros((n, n)); MU[np.arange(n), perm] = a; MU += jit_mu * rng.standard_normal((n, n))
    w = np.array([s, 0.0]) if plan == 0 else np.array([0.0, s])
    ZE = np.tile(w, (n, 1)) + jit_z * rng.standard_normal((n, 2))
    # plan mixture weights -> positions and secretions from the mixture
    wz = np.exp(ZE) / np.exp(ZE).sum(1, keepdims=True)
    X = np.einsum('iz,zdn,in->id', wz, tmpl.Xs, np.eye(n)[perm][:, :]) if False else sum(wz[:, [z]] * tmpl.Xs[z][:, perm].T for z in range(tmpl.K))
    C = sum(wz[:, [z]] * tmpl.Cs[z][:, perm].T for z in range(tmpl.K))
    X = X + jit_x * rng.standard_normal((n, 2))
    return (jnp.array(X), jnp.array(C), jnp.array(MU), jnp.array(ZE)), perm

def wB(fin):
    return np.array(jax.nn.softmax(fin[3], axis=1))[:, 1]

def plan_state(eng, tmpl, fin):
    """classify adult as A/B by type pattern + geometry distance to each plan (reflection allowed), return dict"""
    n = tmpl.n; X, C, MU, ZE = [np.array(a) for a in fin]
    ct = cell_types(C.T); out = {}
    for z, nm in enumerate('AB'):
        out['d_' + nm] = d_rigid(X.T, ct, tmpl.Xs[z], type_vector(tmpl, z), reflection=True)
    out['wB_mean'] = float(wB(fin).mean()); out['wB_min'] = float(wB(fin).min()); out['wB_max'] = float(wB(fin).max())
    p = np.array(jax.nn.softmax(jnp.array(MU), axis=1)); out['min_maxbel'] = float(p.max(1).min())
    out['plan'] = 'A' if out['d_A'] < out['d_B'] and out['d_A'] < 0.4 else ('B' if out['d_B'] < 0.4 else '?')
    return out
