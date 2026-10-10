import os, sys, numpy as np, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from an2 import *
from g2cfg import FULL, G1, DT

def test_mirror_map_and_codes():
    tm = make_template2()
    assert sorted(tm.mirror.tolist()) == list(range(24)) and (tm.mirror[tm.mirror] == np.arange(24)).all()
    assert np.allclose(tm.Xs[:, tm.mirror], tm.Xs * np.array([[1], [-1]]))
    assert np.allclose(tm.CR, tm.CL[:, tm.mirror])
    changed = np.where((tm.CL != tm.CR).any(0))[0]
    assert len(changed) == 8 and set(tm.types[0][changed]) == {2, 3} and (tm.types[0][changed] != tm.types[1][changed]).all()
    assert (np.delete(tm.types[0], changed) == np.delete(tm.types[1], changed)).all()

def test_fixed_point_rho1_memory_off_matches_body_L():
    tm = make_template2(); eng = make_engine2(tm, Params2(fix_rho=1.0, **G1)); eng.dt = DT
    st, perm = seeded_start2(tm, 0, 'L'); fin = run_plain(eng, st, 0, 400, jax.random.PRNGKey(0))
    lab, dL, dR = classify_shape(tm, fin[0], fin[1]); assert lab == 'L' and dL < 0.1 and dR > 0.5

def test_crn_twins_bit_identical_until_intervention_and_sham():
    tm = make_template2(); P = Params2(sig_x=.02, sig_c=.02, sig_d=.02, sig_mu=.02, sig_h=.5, **FULL); eng = make_engine2(tm, P); eng.dt = DT
    st, _ = seeded_start2(tm, 0, 'L'); key = jax.random.PRNGKey(3); n = 24
    ext = np.zeros((n, 6)); ext[:4, 5] = 5.0
    zero = (jnp.zeros((n, 6)), jnp.zeros((n, 6)), jnp.zeros(n), jnp.zeros((n, 24)), jnp.ones(n)); act = (jnp.array(ext),) + zero[1:]
    k = int(20 / DT)
    a = eng.run_ctl(st, 0.0, DT, k, key, zero, 40.0, 60.0, 5.0); b = eng.run_ctl(st, 0.0, DT, k, key, act, 40.0, 60.0, 5.0)         # intervention window starts at 40 > 20
    assert max(float(jnp.abs(x - y).max()) for x, y in zip(a, b)) == 0.0
    c = eng.run_ctl(st, 0.0, DT, 2 * k, key, zero, 10.0, 30.0, 5.0); d = eng.run_ctl(st, 0.0, DT, 2 * k, key, act, 10.0, 30.0, 5.0)
    assert max(float(jnp.abs(x - y).max()) for x, y in zip(c, d)) > 1e-3
    s = eng.run_ctl(st, 0.0, DT, 2 * k, key, (jnp.zeros((n, 6)),) + zero[1:], 10.0, 30.0, 5.0)                                        # sham = amp 0, same code path
    assert max(float(jnp.abs(x - y).max()) for x, y in zip(c, s)) == 0.0

def test_events_unique_ids_and_naive_cell():
    from world2 import new_adult2
    w = new_adult2('L', capacity=24, noise=0)
    for i in (3, 3, 3): w.replace(i)
    assert len(set(w.cell_id.tolist())) == 24 and w.cell_id[3] == 26 and abs(w.rho()[3] - 0.5) < 1e-12 and np.abs(w.C[3]).max() == 0

def test_gradient_only_through_own_variables():
    """perturbing cell j's action variables changes cell i's drift only through sensations; cell i's drift does not depend on mu_j, l_j"""
    tm = make_template2(); eng = make_engine2(tm, Params2(**FULL)); st, _ = seeded_start2(tm, 0, 'L')
    f0 = eng.drift(st); MU2 = st[3].at[5].add(1.0); L2 = st[4].at[5].add(1.0); f1 = eng.drift((st[0], st[1], st[2], MU2, L2))
    assert max(float(jnp.abs(a[i] - b[i]).max()) for a, b in zip(f0, f1) for i in range(24) if i != 5) < 1e-12
