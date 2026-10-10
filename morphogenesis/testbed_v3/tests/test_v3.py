import os, sys, numpy as np, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from engine3 import *
from an2 import classify_shape, orbits

DT = 0.0125
def _setup(noisy):
    tm = make_template2(); P = Params3(sig_x=.02, sig_c=.02, sig_mu=.02, sig_h=.4, sig_d=.02, sig_e=.02) if noisy else Params3()
    return tm, make_engine3(tm, P)

@pytest.mark.parametrize('noisy', [False, True])
def test_T4_structure_bit_identical_under_20_memory_interventions(noisy):
    tm, eng = _setup(noisy); st, perm = seeded_start3(tm, 0, 'a'); n = 24; key = jax.random.PRNGKey(7); rng = np.random.default_rng(1)
    k = int(30 / DT); sham = eng.run_ctl(st, 0.0, DT, k, key, zero_ctl(n), 5.0, 25.0, 5.0)
    for trial in range(20):
        kind = trial % 4; uM = np.zeros((n, 2)); mp = np.zeros((1, 2)); ma = np.zeros((1, 2)); mb = np.zeros(2); st0 = st
        if kind == 0: lit = rng.random(n) < 0.3; uM[lit, rng.integers(0, 2)] = rng.uniform(1, 20)
        elif kind == 1: mp = rng.uniform(-3, 3, (1, 2)); ma = rng.uniform(0, 30, (1, 2))
        elif kind == 2: mb = rng.uniform(0, 30, 2)
        else: Lk = np.array(st[3]) + rng.uniform(-6, 6, n); st0 = (st[0], st[1], st[2], jnp.array(Lk), st[4], st[5])
        ctl = (jnp.zeros((n, 4)), jnp.zeros((n, 4)), jnp.zeros(n), jnp.array(uM), jnp.ones(n), jnp.zeros((1, 2)), jnp.zeros((1, 4)), jnp.zeros(4), jnp.array(mp), jnp.array(ma), jnp.array(mb))
        out = eng.run_ctl(st0, 0.0, DT, k, key, ctl, 5.0, 25.0, 5.0)
        for a, b in zip(out[:3], sham[:3]): assert float(jnp.abs(a - b).max()) == 0.0
        if kind != 3: assert float(jnp.abs(out[3] - sham[3]).max()) > 0     # the intervention acted on memory

def test_reporter_target_formula_10_random_states():
    tm, eng = _setup(False); rng = np.random.default_rng(3); Sp, Sm = reporter_sets(tm)
    for _ in range(10):
        MU = rng.standard_normal((24, 24)) * 3; L = rng.standard_normal(24) * 2; st = (jnp.array(rng.standard_normal((24, 2)) * 3), jnp.array(rng.standard_normal((24, 4))), jnp.array(MU), jnp.array(L), jnp.array(rng.random((24, 2))), jnp.zeros(24))
        d = eng.diagnostics(st); q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True); rho = 1 / (1 + np.exp(-L))
        assert np.allclose(np.array(d['estar']), rho * q[:, Sp].sum(1) + (1 - rho) * q[:, Sm].sum(1), atol=1e-12)

def test_structure_has_no_h_and_isolated_cell_f_half():
    tm, eng = _setup(False); st, perm = seeded_start3(tm, 0, 'a'); e1 = make_engine3(tm, Params3(), N=1)
    s1 = (st[0][:1], st[1][:1], st[2][:1], st[3][:1], st[4][:1], st[5][:1]); d = e1.diagnostics(s1); assert abs(float(d['f'][0]) - 0.5) < 1e-12
    # structure drift independent of l, d, e
    f0 = eng.drift(st); st2 = (st[0], st[1], st[2], st[3] * -3.0, st[4][::-1], st[5] * 0); f1 = eng.drift(st2)
    for a, b in zip(f0[:3], f1[:3]): assert float(jnp.abs(a - b).max()) == 0.0

def test_seeded_start_complete_L():
    tm, eng = _setup(False); st, perm = seeded_start3(tm, 0, 'a'); fin = run_plain(eng, st, 0, 400, jax.random.PRNGKey(0))
    assert classify_shape(tm, fin[0], fin[1])[0] == 'L'

def test_mean_field_rho_fixed_point_matches_theory():
    tm, eng = _setup(False); st, perm = seeded_start3(tm, 0, 'a', lstar=1.0); fin = run_plain(eng, st, 0, 1500, jax.random.PRNGKey(0))
    ls = 2 * np.arccosh(np.sqrt(0.6 / 0.2)); assert abs(float(np.mean(np.array(fin[3]))) - ls) < 0.1
