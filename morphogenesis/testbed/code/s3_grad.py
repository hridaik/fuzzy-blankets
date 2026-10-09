"""S3 primary search: gradient-based (JAX autodiff through forcing + release) over amplitudes of each family x pattern x duration, deterministic, S1 operating point.
loss = mean |C_final - C_R-target|^2 (secreted codes -> R fates) + w_d * mean (D_final - D_0)^2 (shape kept; rigid-invariant pairwise distances) + lam * dose."""
import sys, json, time; sys.path.insert(0, '.')
from par import run_jobs
RAMP = 5.0; REL = 100.0
AMAX = dict(sec=4.0, rg=0.8, mig=3.0)

def job(kind, pat, dur, iters=10, lam=0.02):
    from s3common import np, jax, jnp, setup, adult, masks, classify_state, target_R, T_ON
    t, eng = setup(); n, nc, S = t.n, t.nc, t.n
    fin, perm = adult(t, eng, 0); M = masks(t, perm)[pat]; Mj = jnp.array(M)
    X0, Ctar = target_R(t, perm, fin); Ctar = jnp.array(Ctar); D0 = jnp.sqrt(jnp.sum((jnp.array(X0)[:, None] - jnp.array(X0)[None]) ** 2, axis=-1) + 1e-9)
    nth = {'sec': nc, 'rg': nc, 'mig': 1}[kind]; amax = AMAX[kind]
    def amps_of(th):
        a = amax * jnp.tanh(th)
        z = jnp.zeros((n, nc)); zm = jnp.zeros((n,)); zb = jnp.zeros((n, S))
        if kind == 'sec': return (Mj[:, None] * a[None, :], z, zm, zb)
        if kind == 'rg': return (z, Mj[:, None] * a[None, :], zm, zb)
        return (z, z, Mj * a[0], zb)
    ns = int(round((dur + REL) / eng.dt))
    def loss_fn(th):
        out = eng.run_ctl(fin, T_ON, eng.dt, ns, jax.random.PRNGKey(0), amps_of(th), T_ON, T_ON + dur, RAMP, remat=True)
        Cf = out[1]; Xf = out[0]; D = jnp.sqrt(jnp.sum((Xf[:, None] - Xf[None]) ** 2, axis=-1) + 1e-9)
        lc = jnp.mean((Cf - Ctar) ** 2); ld = jnp.mean((D - D0) ** 2); dose = jnp.mean(jnp.tanh(th) ** 2)
        return lc + 2.0 * ld + lam * dose, (lc, ld)
    vg = jax.jit(jax.value_and_grad(loss_fn, has_aux=True))
    th = 0.3 * jnp.ones(nth) * (1 if kind != 'mig' else 0.5); m = jnp.zeros(nth); v = jnp.zeros(nth); trace = []
    t0 = time.time(); g0 = None
    for it in range(iters):
        (L, (lc, ld)), g = vg(th)
        if g0 is None: g0 = float(jnp.linalg.norm(g)); L0, lc0 = float(L), float(lc)
        trace.append((float(L), float(lc), float(ld), float(jnp.linalg.norm(g))))
        m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g ** 2; th = th - 0.3 * (m / (1 - 0.9 ** (it + 1))) / (jnp.sqrt(v / (1 - 0.999 ** (it + 1))) + 1e-12)
    out = eng.run_ctl(fin, T_ON, eng.dt, ns, jax.random.PRNGKey(0), amps_of(th), T_ON, T_ON + dur, RAMP)
    cls, info = classify_state(t, eng, out)
    return dict(kind=kind, pat=pat, dur=dur, loss0=L0, lc0=lc0, grad0=g0, loss_final=trace[-1][0], lc_final=trace[-1][1], ld_final=trace[-1][2], theta=[float(x) for x in amax * jnp.tanh(th)], cls=cls,
                dL=info.get('dL'), dR=info.get('dR'), reason=info.get('reason'), wall=time.time() - t0, trace=trace)

if __name__ == "__main__":
    pats = ['disc_head', 'disc_trunkP', 'disc_mid', 'two_discs', 'half_plus', 'half_minus']
    args = [(k, p, d) for k in ('sec', 'rg', 'mig') for p in pats for d in (20.0, 80.0)]
    res = run_jobs(job, args, workers=8, label='grad'); json.dump(res, open('../data/s3_grad.json', 'w'))
    for r in res: print(r['kind'], r['pat'], r['dur'], 'grad0 %.2e' % r['grad0'], 'lc %.4f -> %.4f' % (r['lc0'], r['lc_final']), r['cls'], 'wall %.0f' % r['wall'])
