"""T1.4 (c) sustained DH, (d) linearization vs SKELETON D1, (e) speed."""
import sys, time, dataclasses; sys.path.insert(0,'.')
from common import *
KMU, KA, DT = 1.4, 1.2, 0.02
P0 = Params(k_mu=KMU, k_a=KA)
t = vanilla8(); key = jax.random.PRNGKey(0)
out = {}

def state_of(nm):
    o = oracle_run(nm)
    return (jnp.array(o['pos'][:, :, -1].T), jnp.array(o['sec'][:, :, -1].T), jnp.array(o['v'][:, :, -1].T), jnp.zeros((8, 1)))

# ---- (c) sustained DH / DT families from class-0 adult (continuation, absolute clock)
st0 = state_of('primary_0000'); c = []
for sgn, nm in ((1.0, 'DH'), (-1.0, 'DT')):
    for eps in (0.1, 0.2, 0.3, 0.35, 0.4, 0.5, 0.7, 1.0):
        eng = make_engine(t, dataclasses.replace(P0, warp_eps=eps, warp_sgn=sgn))
        dt = 0.005 if eps > 0.5 else 0.01
        per = int(round(2 / dt)); fin, tr = eng.run(st0, 1e4, dt, int(1000 / dt), key, None, 0, save_every=per)
        X = np.array(tr[0]); sp = [float(np.abs(X[k] - X[k - 1]).max()) for k in range(1, len(X))]
        d = eng.drift(fin, 1e4, jnp.zeros((8, 4))); res = max(float(jnp.abs(a).max()) for a in d)
        J = np.array(eng.jac_flat(fin, 1e4)); ev = np.linalg.eigvals(J); ev = ev[np.abs(ev) > 1e-9]
        c.append(dict(kind=nm, eps=eps, dt=dt, end_speed=sp[-1], p2=float(np.abs(X[-1] - X[-3]).max()), resid=res, max_re=float(ev.real.max()),
                      fixed=bool(res < 1e-8 and ev.real.max() < 0)))
        print(c[-1], flush=True)
out['c'] = c

# ---- (d) linearization at class-0 and class-1 adult fixed points
def block_weights(V, n=8):
    # state layout: X(16), C(32), MU(64), ZE(8)
    sl = dict(pos=slice(0, 16), sec=slice(16, 48), belief=slice(48, 112))
    return {k: float((np.abs(V[s]) ** 2).sum() / (np.abs(V[:112]) ** 2).sum()) for k, s in sl.items()}
d = {}
eng = make_engine(t, P0)
for nm in ('primary_0000', 'secondary_0005'):
    s = state_of(nm)
    # relax engine from the oracle end state to the engine's own fixed point first
    fin = eng.run_final(s, 1e4, DT, int(300 / DT), key, None, 0)
    res = max(float(jnp.abs(a).max()) for a in eng.drift(fin, 1e4, jnp.zeros((8, 4))))
    J = np.array(eng.jac_flat(fin, 1e4))[:112, :112]  # drop plan block (K=1)
    w, V = np.linalg.eig(J)
    idx = np.argsort(-w.real)[:10]
    d[nm] = dict(resid=res, slowest=[(float(w[i].real), float(w[i].imag), block_weights(V[:, i])) for i in idx],
                 relax_time=float(-1 / w.real.max()), n_unstable=int((w.real > 1e-9).sum()), spectral_radius=float(np.abs(w).max()))
    print(nm, d[nm]['relax_time'], [round(x[0], 3) for x in d[nm]['slowest']], d[nm]['slowest'][0][2])
out['d'] = d

# ---- (e) speed: runs/hour for a 500-time-unit run at dt=0.02 (25000 RK4 steps)
def rand_template(n, seed=0):
    rng = np.random.default_rng(seed); X = rng.uniform(-1, 1, (2, n)) * np.sqrt(n) * 0.6; Cc = (rng.uniform(size=(4, n)) > 0.5).astype(float); Cc[0] = 1
    return make_template(X, Cc, 1.0)
e = {}
NS = 25000
for n in (8, 24, 48):
    tt = vanilla8() if n == 8 else rand_template(n)
    eng_n = make_engine(tt, P0)
    MU0 = np.random.default_rng(1).standard_normal((n, n)) / 8
    st = eng_n.init_from_mu(MU0)
    fn = jax.jit(lambda s: eng_n.run_final(s, 0.0, DT, NS, key, None, 0)); fn(st)[0].block_until_ready()
    t0 = time.time(); fn(st)[0].block_until_ready(); ts = time.time() - t0
    B = 32
    stB = jax.tree_util.tree_map(lambda a: jnp.broadcast_to(a, (B,) + a.shape), st)
    stB = (stB[0], stB[1], stB[2] + jnp.asarray(np.random.default_rng(2).standard_normal((B, n, n)) / 8), stB[3])
    fb = jax.jit(jax.vmap(lambda s: eng_n.run_final(s, 0.0, DT, NS, key, None, 0))); fb(stB)[0].block_until_ready()
    t0 = time.time(); fb(stB)[0].block_until_ready(); tb = time.time() - t0
    e[n] = dict(single_s=ts, runs_per_hour_single=3600 / ts, batch=B, batch_s=tb, runs_per_hour_batched=3600 * B / tb)
    print(n, e[n], flush=True)
out['e'] = e
json.dump(out, open(os.path.join(TB, 'data', 't14_cde.json'), 'w'), indent=1, default=float)
