import os, sys, json, numpy as np, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from asm import *
from exports import load_tier

def test_oracle_fixed_point_matches():
    """T1.4(a): engine adult state from oracle initial beliefs matches the oracle reference phenotype, d_pair < 0.01"""
    t = vanilla8(); eng = make_engine(t, Params(k_mu=1.4, k_a=1.2)); o = oracle_run('primary_0000')
    fin = eng.run_final(eng.init_from_mu(o['v0'].T), 0.0, 0.02, int(400 / 0.02), jax.random.PRNGKey(0), None, 0)
    ref = json.load(open(os.path.join(M2A, 'sealed', 'reference_phenotype_v2.json')))
    assert d_pair(np.array(fin[0]).T, np.array(fin[1]).T, np.array(ref['pos']), np.array(ref['sec'])) < 0.01

def test_rk4_order_about_four():
    t = vanilla8(); eng = make_engine(t, Params(k_mu=1.4, k_a=1.2)); o = oracle_run('primary_0000'); st = eng.init_from_mu(o['v0'].T); key = jax.random.PRNGKey(0)
    ref = eng.run_final(st, 0.0, 0.00125, int(round(10 / 0.00125)), key, None, 0)
    err = {}
    for dt in (0.02, 0.01, 0.005):
        f = eng.run_final(st, 0.0, dt, int(round(10 / dt)), key, None, 0); err[dt] = max(float(jnp.abs(a - b).max()) for a, b in zip(f[:3], ref[:3]))
    assert np.log2(err[0.01] / err[0.005]) > 3.0

def test_crn_twins_identical_until_intervention():
    t = make_body('A'); eng = make_engine(t, tb_params(sig_x=0.02, sig_c=0.02)); dt = 0.02; key = jax.random.PRNGKey(3); st = seeded_start(t, 0, jit_x=0.0, jit_mu=0.0)
    amp = np.zeros((24, 4)); amp[:4, 2] = 5.0
    a = eng.run_final(st, 0.0, dt, 1500, key, None, 0); b = eng.run_final(st, 0.0, dt, 1500, key, (jnp.array(amp), 40.0, 50.0), 0)   # t_on = 40 > 30 = end
    assert max(float(jnp.abs(x - y).max()) for x, y in zip(a, b)) < 1e-12
    c = eng.run_final(st, 0.0, dt, 3000, key, None, 0); d = eng.run_final(st, 0.0, dt, 3000, key, (jnp.array(amp), 40.0, 50.0), 0)
    assert max(float(jnp.abs(x - y).max()) for x, y in zip(c, d)) > 1e-3

def test_hidden_tier_requires_audit():
    p = os.path.join(TB, 'data', 'natural', 'A_train_00')
    load_tier(p, 'obs')
    with pytest.raises(PermissionError): load_tier(p, 'hid')
    load_tier(p, 'hid', audit=True)

def test_plan_B_recodes_one_third_of_slots():
    A = make_body('A'); B = make_body('B'); ra = np.where((np.abs(A.Xs[0] - B.Xs[0]).max(0) > 1e-9) | (type_vector(A) != type_vector(B)))[0]
    assert 0.25 <= len(ra) / 24 <= 0.40 and (A.Xs[0].shape == B.Xs[0].shape == (2, 24))

def test_observable_html_has_no_audit_fields():
    p = os.path.join(MORPH, 'viz', 'output', 'testbed', 'observable', 't2d_mirror_forms.html'); s = open(p).read()
    assert '"target"' not in s and '"planB"' not in s and '"role"' not in s
