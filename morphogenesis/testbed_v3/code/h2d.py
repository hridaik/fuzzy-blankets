"""H2(d) finite groups: n cells cut out of the settled body (n nearest places to a central place), memory lifetime = first time mean l <= 0 (from state a)."""
import sys, json, time; sys.path.insert(0, '.')
from an3 import *
from theory3 import dU
DT = 0.0125; NOISE = dict(sig_x=.02, sig_c=.02, sig_mu=.02, sig_d=.02, sig_e=.02)
def job_group(n, sig_h, seed, T=10000.0, chunk=25.0, seed_place=10):
    from world3 import settled3
    arr, perm = settled3('a', 0); tm = make_template2(); Xp = tm.Xs[:, perm].T; cp = tm.Xs[:, seed_place]
    order = np.argsort(np.linalg.norm(Xp - cp[None], axis=1)); idx = order[:n]
    eng = make_engine3(tm, Params3(sig_h=sig_h, **NOISE), N=n); eng.dt = DT
    st = tuple(jnp.array(a[idx]) for a in arr); key = jax.random.PRNGKey(5000 + 97 * seed + n); k = int(round(chunk / DT)); tl = None; mls = []; spread = []
    for c in range(int(T / chunk)):
        st = run_plain(eng, st, c * chunk, chunk, key, step0=c * k); ml = float(np.array(st[3]).mean()); mls.append(ml)
        if tl is None and ml <= 0: tl = (c + 1) * chunk
        if tl is not None and c * chunk > tl + 200: break
        X = np.array(st[0]); D = np.linalg.norm(X[:, None] - X[None], axis=-1) + 99 * np.eye(n); spread.append(float(D.min(1).max()) if n > 1 else 0.0)
    return dict(n=n, sig_h=sig_h, seed=seed, lifetime=tl, censored=tl is None, T=T, max_nn=float(max(spread)), final_mean_l=mls[-1], min_mean_l=float(min(mls)))
if __name__ == "__main__":
    from par import run_jobs; t0 = time.time()
    args = [(n, sh, s) for sh in (0.4, 0.7, 1.0) for n in (2, 4, 8, 12, 24) for s in range(12)]
    res = run_jobs(job_group, args, workers=8, label='H2d'); json.dump(res, open('../data/h2d_groups.json', 'w')); print('wall', time.time() - t0)
