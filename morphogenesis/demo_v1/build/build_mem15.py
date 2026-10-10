"""Chapter 1.5: N = 1, 4, 24 cells cut from the settled body (protocol of testbed_v3/code/h2d.py), sigma_h = 0.7, state a, 600 tu, one stream per N.
Clip rule (declared before running): lowest seed s = 0,1,2,... such that the group of 4 first has mean l <= 0 between 150 and 450 tu and the 24-body never does."""
import sys; sys.path.insert(0, '.')
from common import *
import jax, jax.numpy as jnp
from an3 import *
from world3 import settled3
DT = 0.0125; NOISE = dict(sig_x=.02, sig_c=.02, sig_mu=.02, sig_d=.02, sig_e=.02); T = 600.0; REC = 2.0
def run(n, seed, sig_h=0.7, seed_place=10):
    arr, perm = settled3('a', 0); tm = make_template2(); Xp = tm.Xs[:, perm].T; cp = tm.Xs[:, seed_place]
    idx = np.argsort(np.linalg.norm(Xp - cp[None], axis=1))[:n]
    eng = make_engine3(tm, Params3(sig_h=sig_h, **NOISE), N=n); eng.dt = DT
    st = tuple(jnp.array(a[idx]) for a in arr); key = jax.random.PRNGKey(5000 + 97 * seed + n); k = int(round(REC / DT)); Xs = []; Ls = []
    Xs.append(np.array(st[0])); Ls.append(np.array(st[3]))
    for c in range(int(T / REC)):
        st = run_plain(eng, st, c * REC, REC, key, step0=c * k); Xs.append(np.array(st[0])); Ls.append(np.array(st[3]))
    return np.stack(Xs), np.stack(Ls)
def first_cross(L): m = L.mean(1); i = np.where(m <= 0)[0]; return None if len(i) == 0 else float(i[0] * REC)
for seed in range(0, 40):
    X4, L4 = run(4, seed); t4 = first_cross(L4)
    print('seed', seed, 'group-4 first sign change', t4, flush=True)
    if t4 is None or not (150 <= t4 <= 450): continue
    X24, L24 = run(24, seed); t24 = first_cross(L24)
    print('   24-body first sign change', t24, flush=True)
    if t24 is not None: continue
    X1, L1 = run(1, seed); t1 = first_cross(L1); print('   isolated first sign change', t1)
    sg = lambda z: 1 / (1 + np.exp(-z))
    def pack(X, L, n): Xc = X - X.mean(1, keepdims=True)[0:1].mean(0, keepdims=True); return dict(X=enc16(Xc - 0, 1000), rho=enc16(sg(L), 20000))
    out = dict(T=T, dt=REC, nf=X4.shape[0], seed=seed, sig_h=0.7, rule='lowest seed with group-4 sign change in [150,450] tu and 24-body never', t_cross=dict(n1=t1, n4=t4, n24=t24),
               n1=pack(X1, L1, 1), n4=pack(X4, L4, 4), n24=pack(X24, L24, 24))
    write_js('mem15', out); break
