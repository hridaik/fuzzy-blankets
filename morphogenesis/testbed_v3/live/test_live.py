"""Tests of the sealed live environment (server in a separate process; client uses only the client library)."""
import os, sys, re, json, time, subprocess, glob
import numpy as np, pytest
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.dont_write_bytecode = True
from live_client import Dish, DishError
FORBID = [r'memory', r'handed', r'chiral', r'situs', r'lateral', r'reporter', r'slot', r'belief', r'\bplans?\b', r'\bfate', r'template', r'mirror', r'\bstates?\b', r'mechanism', r'latent', r'hidden', r'posterior', r'logit', r'\brho\b', r'ligand', r'orbit', r'\bq\b', r'\bl\b']
@pytest.fixture(scope='module')
def env(tmp_path_factory):
    d = tmp_path_factory.mktemp('live'); ready = str(d / 'ready.json'); sealed = str(d / 'sealed'); budget = json.dumps(dict(ep_time=60.0, total_time=400.0, ep_dose=3000.0, ep_actions=3, total_episodes=12))
    p = subprocess.Popen([sys.executable, os.path.join(HERE, 'live_server.py'), '--ready', ready, '--sealed', sealed, '--budget', budget], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for _ in range(200):
        if os.path.exists(ready): break
        time.sleep(0.1)
    cl = Dish(ready); yield cl, sealed; cl.shutdown(); p.wait(timeout=20)
def scan(obj, path='root'):
    """no forbidden vocabulary in keys or string values; only json scalars / lists / dicts"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert not any(re.search(p, str(k), re.I) for p in FORBID), f'key {k} at {path}'; scan(v, path + '/' + str(k))
    elif isinstance(obj, (list, tuple)):
        for v in obj[:5]: scan(v, path + '[]')
    elif isinstance(obj, str):
        if len(obj) < 200: assert not any(re.search(p, obj, re.I) for p in FORBID), f'string {obj} at {path}'
    else: assert isinstance(obj, (int, float, bool, type(None), np.ndarray, np.generic)), f'type {type(obj)} at {path}'
def test_api_surface_exposes_no_internal_quantity(env):
    cl, sealed = env; raw = []
    s = cl.status(); raw.append(s); r = cl.reset('development', seed=5001); raw.append(r); ep = r['episode']
    for lv in ('O1', 'O2', 'O3a', 'O3b', 'O3c'):
        o = cl.observe(ep, lv); raw.append({k: v for k, v in o.items() if k != 'image'}); assert 't' in o
    o1 = cl.observe(ep, 'O1'); assert o1['level_values'].shape[1] == 7 and set(o1) == {'level', 't', 'id', 'xy', 'level_values', 'budget'}
    o2 = cl.observe(ep, 'O2'); assert o2['level_values'].shape[1] == 5 and 'id' not in o2
    assert cl.observe(ep, 'O3c')['image'].shape == (4, 128, 128) and cl.observe(ep, 'O3a')['image'].shape == (3, 64, 64) and cl.observe(ep, 'O3b')['image'].shape == (4, 64, 64)
    a = cl.act(ep, 'L3', dict(type='disc', xy=[0.0, 0.0], radius=2.0), 1.0, 5.0, 1.0); raw.append(a); raw.append(cl.step(ep, 1.0)); raw.append(cl.end_episode(ep))
    for x in raw: scan(x)
    # repeated observation at the same time is identical (observation noise is a function of episode and time only)
    r2 = cl.reset('development', seed=5002); e2 = r2['episode']; a1 = cl.observe(e2, 'O1'); a2 = cl.observe(e2, 'O1'); assert np.array_equal(a1['xy'], a2['xy']) and np.array_equal(a1['level_values'], a2['level_values']); cl.end_episode(e2)
def test_live_bit_identical_to_offline_engine_run(env):
    cl, sealed = env; r = cl.reset('development', seed=5001); ep = r['episode']; cl.step(ep, 4.0); cl.act(ep, 'L4', dict(type='disc', xy=[1.0, 0.5], radius=1.5), 5.0, 6.0, 1.5); cl.step(ep, 5.0); cl.step(ep, 7.5); cl.end_episode(ep)
    hid = np.load(os.path.join(sealed, f'episode_{ep:05d}', 'hidden.npz')); meta = json.load(open(os.path.join(sealed, f'episode_{ep:05d}', 'episode.json')))
    sys.path.insert(0, os.path.join(V3, 'code')); from world4 import Experiment4; from world3 import Mask
    st = meta['state0']; ex = Experiment4(st, seed=5001, noise=0.02, sig_h=0.4, private={'MB': ('mem', 1), 'MA': ('mem', 0), 'SEC': ('sec', 0), 'RG': ('rg', 0), 'MIG': ('mig', 0)}, form_seed=5001); ex.run(100.0, observe=False); ex.t0 = ex.w.time
    import build_blind3 as B3; chan = {v: k for k, v in B3.LIGHT_LABELS.items()}['L4']; act = dict(type='light', channel=chan, mask=Mask([('disc', 1.0, 0.5, 1.5, 1.0)]), amp=5.0, t_on=4.0, t_off=10.0, ramp=1.5)
    ex.run_sched(4.0, [], obs_times=[]); X0 = ex.w.X.copy(); ex.run_sched(12.5, [act], obs_times=[])                       # same total time; the server stepped 4 + 5 + 7.5
    assert np.array_equal(hid['L'][-1], ex.w.L) and np.array_equal(hid['X'][-1], ex.w.X) and np.array_equal(hid['MU'][-1], ex.w.MU) and np.array_equal(hid['E'][-1], ex.w.E)
def test_sham_equals_twin_bit_identical(env):
    cl, sealed = env; tw = cl.reset('development', seed=5002)['episode']; cl.step(tw, 10.0); cl.end_episode(tw)
    sh = cl.reset(sham_of=tw)['episode']; cl.act(sh, 'L3', dict(type='disc', xy=[0.0, 0.0], radius=3.0), 50.0, 8.0, 2.0); cl.step(sh, 10.0); cl.end_episode(sh)
    a = np.load(os.path.join(sealed, f'episode_{tw:05d}', 'hidden.npz')); b = np.load(os.path.join(sealed, f'episode_{sh:05d}', 'hidden.npz'))
    for k in ('X', 'C', 'MU', 'L', 'D', 'E'): assert np.array_equal(a[k], b[k]), k
def test_heldout_pool_locked_until_freeze(env):
    cl, sealed = env
    with pytest.raises(DishError, match='locked'): cl.reset('heldout')
    with pytest.raises(DishError): cl.freeze('abc')
    assert cl.freeze('frozen-config-sha256-0123456789')['heldout_unlocked']
    r = cl.reset('heldout', seed=6001); assert r['seed_pool'] == 'heldout'; cl.end_episode(r['episode'])
    with pytest.raises(DishError, match='already'): cl.freeze('another-hash-value-xxxxxxxx')
    assert json.load(open(os.path.join(sealed, 'freeze.json')))['hash'] == 'frozen-config-sha256-0123456789'
def test_budget_accounting_and_enforcement(env):
    cl, sealed = env; r = cl.reset('development', seed=5001); ep = r['episode']; assert r['budget']['episode_time_max'] == 60.0
    a = cl.act(ep, 'L3', dict(type='disc', xy=[0.0, 0.0], radius=2.0), 2.0, 5.0, 1.0); assert a['dose'] == pytest.approx(2.0 * 5.0 * a['cells_in_mask']) and a['budget']['episode_dose_used'] == pytest.approx(a['dose'])
    cl.step(ep, 30.0)
    with pytest.raises(DishError, match='time budget'): cl.step(ep, 40.0)
    with pytest.raises(DishError, match='dt'): cl.step(ep, 0.3)
    with pytest.raises(DishError, match='dose'): cl.act(ep, 'L4', dict(type='all'), 400.0, 20.0, 2.0)
    for _ in range(2): cl.act(ep, 'L1', dict(type='disc', xy=[9.0, 9.0], radius=0.5), 0.1, 2.0, 0.5)
    with pytest.raises(DishError, match='action budget'): cl.act(ep, 'L1', dict(type='disc', xy=[9.0, 9.0], radius=0.5), 0.1, 2.0, 0.5)
    cl.end_episode(ep)
    e3 = cl.reset('development', seed=5002)['episode']
    with pytest.raises(DishError, match='unknown channel'): cl.act(e3, 'L9', dict(type='all'), 1.0, 2.0, 0.5)
    with pytest.raises(DishError, match='invalid'): cl.act(e3, 'L3', dict(type='all'), 1.0, 2.0, 1.5)
    cl.end_episode(e3)
def test_hidden_state_only_in_sealed_dir_and_docs_clean(env):
    cl, sealed = env; assert oct(os.stat(sealed).st_mode & 0o777) == '0o700' and glob.glob(os.path.join(sealed, 'episode_*', 'hidden.npz'))
    assert not glob.glob(os.path.join(HERE, '**', 'hidden*'), recursive=True)
    txt = open(os.path.join(HERE, 'CLIENT_API.md')).read() + open(os.path.join(HERE, 'live_client.py')).read()
    for p in [r'memory', r'handed', r'chiral', r'situs', r'lateral', r'reporter', r'\bslot', r'belief', r'template', r'mirror', r'mechanism', r'latent', r'posterior', r'ligand']: assert not re.search(p, txt, re.I), p
