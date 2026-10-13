import sys; sys.path.insert(0,'.')
from lib4 import *
def job(seed, state, kg, T=3000.0):
    d = dict(seed=-1, kappa_g=kg, g=4*R_*kg, gamma_factor=1.0); e = get_engine(d, 'phi04', noise=True, gamma_on=False); arr, perm = settled(d, 'phi04', state); st = tuple(jnp.array(a) for a in arr); key = jax.random.PRNGKey(777+seed)
    nstrict = 0; norb = 0; n = 0; step = 0
    for c in range(int(T)):
        st = run_plain(e, st, c*1.0, 1.0, key, step0=step); step += 80
        MU = np.array(st[2]); q = np.array(jax.nn.softmax(jnp.array(MU), 1)); pl = q.argmax(1); okS = len(set(pl.tolist())) == 24; okO, _ = place_fill(TM, q); n += 1; nstrict += (not okS); norb += (not okO)
    return dict(seed=seed, state=state, kg=kg, frames=n, strict_fail=nstrict, orbit_fail=norb)
if __name__ == "__main__":
    from par4 import run_jobs
    res = run_jobs(job, [(0, 'a', 2.449), (1, 'b', 2.449), (2, 'a', 1.5), (3, 'a', 4.0)], workers=4, label='strict'); print(res)
