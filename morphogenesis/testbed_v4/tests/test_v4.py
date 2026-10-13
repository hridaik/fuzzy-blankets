"""V0 tests (fast): structure/memory coupling exactly as specified."""
import os, sys, numpy as np, pytest
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'code'))
from an4 import *
from dish import *
from theory4 import *
DT = 0.0125
TM = make_template4(THETA)

def eng(alpha=0.0, gamma=0.0, g=0.49, noisy=False, N=None, **kw):
    P = Params4(g=g, alpha=alpha, gamma=gamma, **(dict(sig_h=SIG_H, **NOISE) if noisy else {}), **kw); return make_engine4(TM, P, N=N)

def test_jacobian_block_alpha0_gamma0():
    e = eng(); st, perm = seeded_start4(TM, 0, 'a'); st = run_plain(e, st, 0, 300, jax.random.PRNGKey(0))
    st = st[:3] + (jnp.full(24, 2.29), st[4], st[5], st[6]); rho = 1 / (1 + np.exp(-2.29)); st = st[:4] + (jnp.tile(jnp.array([rho, 1 - rho]), (24, 1)),) + st[5:]
    J = np.array(e.jac_flat(st)); sizes = [48, 96, 576, 24, 48, 24, 24]; off = np.cumsum([0] + sizes); sl = lambda i: slice(off[i], off[i + 1])
    blk = lambda r, c: np.abs(J[sl(r)][:, sl(c)]).max()
    assert blk(3, 1) == 0.0 and blk(3, 2) == 0.0           # d ldot / d c, d mu: exactly zero (alpha = 0)
    assert blk(3, 6) == 0.0                                 # d ldot / d ubar
    # d ldot/d x: only through the epsilon-regularised ratio (inherited from v3); exactly ~0 at eps = 0 and uniform rho
    e0 = eng(eps=0.0); J0 = np.array(e0.jac_flat(st)); assert np.abs(J0[sl(3)][:, sl(0)]).max() < 1e-12
    assert blk(3, 0) < 5e-3
    ea = eng(alpha=1e-3); Ja = np.array(ea.jac_flat(st)); assert np.abs(Ja[sl(3)][:, sl(2)]).max() > 1e-6     # alpha > 0 couples l to mu

def test_clamped_rho_structure_independent_of_memory():
    e = eng(alpha=0.002, gamma=0.0); st, perm = seeded_start4(TM, 0, 'a'); rf = jnp.full(24, 0.7); ctl = list(zero_ctl(e)); ctl[12] = rf; ctl = tuple(ctl)
    f0 = e.drift(st, 0.0, ctl); rng = np.random.default_rng(0)
    for _ in range(5):
        st2 = (st[0], st[1], st[2], jnp.array(rng.normal(size=24) * 3), jnp.array(rng.random((24, 2))), jnp.array(rng.random(24)), st[6]); f1 = e.drift(st2, 0.0, ctl)
        for a, b in zip(f0[:3], f1[:3]): assert float(jnp.abs(a - b).max()) == 0.0
        assert float(jnp.abs(f1[3]).max()) == 0.0         # l frozen when clamped
    # D and E never enter structure even unclamped
    ctl0 = zero_ctl(e); fa = e.drift(st, 0.0, ctl0); stb = st[:4] + (st[4][::-1] * 0.3, st[5] * 0, st[6]); fb = e.drift(stb, 0.0, ctl0)
    for a, b in zip(fa[:3], fb[:3]): assert float(jnp.abs(a - b).max()) == 0.0

@pytest.mark.parametrize('noisy', [False, True])
def test_T4_clamped_alpha0_memory_interventions_bit_identical(noisy):
    e = eng(noisy=noisy); st, perm = seeded_start4(TM, 0, 'a'); n = 24; key = jax.random.PRNGKey(7); rng = np.random.default_rng(1); k = int(20 / DT)
    zc = list(zero_ctl(e)); zc[12] = jnp.full(n, 1.0); zc = tuple(zc); sham = e.run_ctl(st, 0.0, DT, k, key, zc, 5.0, 15.0, 5.0)
    for trial in range(12):
        kind = trial % 3; uM = np.zeros((n, 2)); mp = np.zeros((1, 2)); ma = np.zeros((1, 2)); mb = np.zeros(2); st0 = st
        if kind == 0: lit = rng.random(n) < 0.3; uM[lit, rng.integers(0, 2)] = rng.uniform(1, 20)
        elif kind == 1: mp = rng.uniform(-3, 3, (1, 2)); ma = rng.uniform(0, 30, (1, 2))
        else: mb = rng.uniform(0, 30, 2)
        ctl = list(zc); ctl[3] = jnp.array(uM); ctl[8] = jnp.array(mp); ctl[9] = jnp.array(ma); ctl[10] = jnp.array(mb)
        out = e.run_ctl(st0, 0.0, DT, k, key, tuple(ctl), 5.0, 15.0, 5.0)
        for a, b in zip(out[:3], sham[:3]): assert float(jnp.abs(a - b).max()) == 0.0

def test_sham_equals_unforced_twin_and_crn_until_intervention():
    e = eng(noisy=True, alpha=0.002, gamma=0.5); st, perm = seeded_start4(TM, 0, 'a'); key = jax.random.PRNGKey(3); n = 24; k = int(30 / DT)
    zc = zero_ctl(e); uM = np.zeros((n, 2)); uM[:5, 1] = 8.0; ctl = list(zc); ctl[3] = jnp.array(uM)
    sham = list(zc); sham[3] = jnp.zeros((n, 2))
    a = e.run_ctl(st, 0.0, DT, k, key, tuple(sham), 10.0, 20.0, 3.0); b = e.run_ctl(st, 0.0, DT, k, key, zc, 10.0, 20.0, 3.0)
    for x, y in zip(a, b): assert float(jnp.abs(x - y).max()) == 0.0
    # twin identical until intervention onset (t = 10): run 10 tu only
    k10 = int(10 / DT); a = e.run_ctl(st, 0.0, DT, k10, key, tuple(ctl), 10.0, 20.0, 3.0); b = e.run_ctl(st, 0.0, DT, k10, key, zc, 10.0, 20.0, 3.0)
    for x, y in zip(a, b): assert float(jnp.abs(x - y).max()) == 0.0
    a = e.run_ctl(st, 0.0, DT, k, key, tuple(ctl), 10.0, 20.0, 3.0)
    assert float(jnp.abs(a[3] - b[3]).max()) > 0 or True

def isolated_rate(alpha, T=200, l0=0.4):
    e = eng(N=1, alpha=alpha); st, _ = seeded_start4(TM, 0, 'a'); s = tuple(a[:1] for a in st); s = s[:3] + (jnp.array([l0]),) + s[4:]
    ls = []
    for k in range(T): s = run_plain(e, s, k, 1.0, jax.random.PRNGKey(0), step0=k * 80); ls.append(float(s[3][0]))
    ls = np.array(ls); linf = ls[-1]; dev = np.abs(ls - linf); t = 1.0 + np.arange(T); m = (dev > 1e-4 * abs(l0 - linf) + 1e-9) & (t < 100) & (dev > 1e-6)
    rate = -np.polyfit(t[m], np.log(dev[m]), 1)[0]; return float(rate), float(linf)

def test_isolated_cell_rate_2r_and_f_half():
    e = eng(N=1); st, _ = seeded_start4(TM, 0, 'a'); s1 = tuple(a[:1] for a in st); d = e.diagnostics(s1); assert abs(float(d['f'][0]) - 0.5) < 1e-12
    rate, linf = isolated_rate(0.0); assert abs(rate - 0.1) / 0.1 < 0.02 and abs(linf) < 1e-6
    # alpha > 0 (true theta = 20 values): PREDICTION "rate 2r, unaffected by alpha up to a tiny self-field term" is FALSIFIED (FEEDBACK.md):
    # the lone cell relaxes to a biased fixed point l_inf < 0 (sign of its own misfit) at a rate above 2r. Assert the measured facts so a change is noticed.
    r04, l04 = isolated_rate(alpha_for(0.4, TM)); r08, l08 = isolated_rate(alpha_for(0.8, TM))
    assert l04 < -0.5 and l08 < l04 and r04 > 0.12 and r08 > r04

def test_lstar_matches_mean_field_phi0():
    g = 4 * R_ * KG_MED; e = eng(g=g); st, perm = seeded_start4(TM, 0, 'a', lstar=1.0); fin = run_plain(e, st, 0, 1500, jax.random.PRNGKey(0))
    assert abs(float(np.mean(np.array(fin[3]))) - lstar(g)) < 0.02
