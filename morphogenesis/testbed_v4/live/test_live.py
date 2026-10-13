"""Tests of the sealed live environment v4 (server in a separate process; client uses only the client library)."""
import os, sys, re, json, time, subprocess, glob
import numpy as np, pytest
HERE = os.path.dirname(os.path.abspath(__file__)); V4 = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.dont_write_bytecode = True
from live_client import Dish, DishError
FORBID = [r'memory', r'handed', r'chiral', r'situs', r'lateral', r'reporter', r'slot', r'belief', r'\bplans?\b', r'\bfate', r'template', r'mirror', r'\bstates?\b', r'mechanism', r'latent', r'hidden', r'posterior', r'logit', r'\brho\b', r'ligand', r'orbit', r'\bq\b', r'\bl\b',
          r'hinge', r'tail.?angle', r'\balpha\b', r'\bgamma\b', r'desensitis', r'desensitiz', r'feedback', r'variant', r'damage', r'intact', r'kappa', r'phi']
def start(tmp, name, budget=None, sealed=None):
    ready = str(tmp / f'ready_{name}.json'); sealed = sealed or str(tmp / 'sealed'); budget = json.dumps(budget or dict(ep_time=60.0, total_time=400.0, ep_dose=3000.0, ep_actions=3, total_episodes=20))
    if os.path.exists(ready): os.remove(ready)
    p = subprocess.Popen([sys.executable, os.path.join(HERE, 'live_server.py'), '--ready', ready, '--sealed', sealed, '--budget', budget], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    for _ in range(600):
        if os.path.exists(ready): break
        time.sleep(0.1)
    return p, Dish(ready), sealed
@pytest.fixture(scope='module')
def env(tmp_path_factory):
    d = tmp_path_factory.mktemp('live'); p, cl, sealed = start(d, 'main'); yield cl, sealed; cl.shutdown(); p.wait(timeout=30)
def scan(obj, path='root'):
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
    for msg in ('locked',):
        for pool in ('heldout', 'generalisation'):
            try: cl.reset(pool)
            except DishError as e: scan(str(e)); assert msg in str(e)
    r2 = cl.reset('development', seed=5002); e2 = r2['episode']; a1 = cl.observe(e2, 'O1'); a2 = cl.observe(e2, 'O1'); assert np.array_equal(a1['xy'], a2['xy']) and np.array_equal(a1['level_values'], a2['level_values']); cl.end_episode(e2)
def test_live_bit_identical_to_offline_engine_run(env):
    cl, sealed = env; r = cl.reset('development', seed=5001); ep = r['episode']; cl.step(ep, 4.0); cl.act(ep, 'L4', dict(type='disc', xy=[1.0, 0.5], radius=1.5), 5.0, 6.0, 1.5); cl.step(ep, 5.0); cl.step(ep, 7.5); cl.end_episode(ep)
    hid = np.load(os.path.join(sealed, f'episode_{ep:05d}', 'hidden.npz')); meta = json.load(open(os.path.join(sealed, f'episode_{ep:05d}', 'episode.json')))
    sys.path.insert(0, os.path.join(V4, 'code')); import live_server as LS
    from interface4 import Experiment4, Mask, CH
    d, variant, st = LS.episode_setup('development', 5001); assert st == meta['state0'] and variant == meta['variant']
    ex = Experiment4(st, seed=5001, noise=True, dish=d, variant=variant, private=dict(CH), form_seed=5001 % 7); ex.run(100.0, observe=False); ex.t0 = ex.w.time
    chan = {v: k for k, v in LS.B3.LIGHT_LABELS.items()}['L4']; act = dict(type='light', channel=chan, mask=Mask([('disc', 1.0, 0.5, 1.5, 1.0)]), amp=5.0, t_on=4.0, t_off=10.0, ramp=1.5)
    ex.run_sched(4.0, [], obs_times=[]); ex.run_sched(12.5, [act], obs_times=[])
    # NB: the server calls run_sched(dt, actions) per step with t_on = time of the act call: t_on = 4.0 as above
    for k, ref in (('L', ex.w.L), ('X', ex.w.X), ('MU', ex.w.MU), ('E', ex.w.E), ('U', ex.w.U)): assert np.array_equal(hid[k][-1], ref), k
def test_sham_equals_twin_bit_identical(env):
    cl, sealed = env; tw = cl.reset('development', seed=5002)['episode']; cl.step(tw, 10.0); cl.end_episode(tw)
    sh = cl.reset(sham_of=tw)['episode']; cl.act(sh, 'L3', dict(type='disc', xy=[0.0, 0.0], radius=3.0), 50.0, 8.0, 2.0); cl.step(sh, 10.0); cl.end_episode(sh)
    a = np.load(os.path.join(sealed, f'episode_{tw:05d}', 'hidden.npz')); b = np.load(os.path.join(sealed, f'episode_{sh:05d}', 'hidden.npz'))
    for k in ('X', 'C', 'MU', 'L', 'D', 'E', 'U'): assert np.array_equal(a[k], b[k]), k
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
def test_sealed_ledger_records_organism_intact_flag(env):
    cl, sealed = env; led = [json.loads(l) for l in open(os.path.join(sealed, 'ledger.jsonl'))]; assert len(led) >= 3
    assert all(isinstance(x['organism_intact'], bool) and 0.0 <= x['min_jaccard'] <= 1.0 for x in led)
    ep = sorted(glob.glob(os.path.join(sealed, 'episode_*')))[0]; m = json.load(open(os.path.join(ep, 'episode.json'))); assert 'organism_intact' in m and len(m['intact_series']) >= 2 and 'dish' in m and 'variant' in m
def test_hidden_state_only_in_sealed_dir_and_docs_clean(env):
    cl, sealed = env; assert oct(os.stat(sealed).st_mode & 0o777) == '0o700' and glob.glob(os.path.join(sealed, 'episode_*', 'hidden.npz'))
    assert not glob.glob(os.path.join(HERE, '**', 'hidden*'), recursive=True)
    txt = open(os.path.join(HERE, 'CLIENT_API.md')).read() + open(os.path.join(HERE, 'live_client.py')).read()
    for p in FORBID[:6] + [r'belief', r'mirror', r'mechanism', r'latent', r'posterior', r'ligand', r'hinge', r'feedback', r'variant', r'damage', r'desensitis']: assert not re.search(p, txt, re.I), p
def test_locks_hold_across_restart_and_generalisation_cannot_be_reset_before_freeze(tmp_path):
    p, cl, sealed = start(tmp_path, 'r1')
    try:
        for pool in ('heldout', 'generalisation'):
            with pytest.raises(DishError, match='locked'): cl.reset(pool)
            with pytest.raises(DishError, match='locked'): cl.reset(pool, seed=(6001 if pool == 'heldout' else 7001))
        assert cl.status()['frozen'] is False
    finally: cl.shutdown(); p.wait(timeout=30)
    p, cl, sealed = start(tmp_path, 'r2', sealed=sealed)                         # restart: still locked
    try:
        for pool in ('heldout', 'generalisation'):
            with pytest.raises(DishError, match='locked'): cl.reset(pool)
        with pytest.raises(DishError): cl.freeze('abc')
        assert cl.freeze('frozen-config-sha256-0123456789')['heldout_unlocked']
        with pytest.raises(DishError, match='already'): cl.freeze('another-hash-value-xxxxxxxx')
    finally: cl.shutdown(); p.wait(timeout=30)
    p, cl, sealed = start(tmp_path, 'r3', sealed=sealed)                         # restart: stays frozen, pools open, cannot be re-frozen
    try:
        assert cl.status()['frozen'] is True
        with pytest.raises(DishError, match='already'): cl.freeze('yet-another-hash-xxxxxxxxx')
        r = cl.reset('generalisation', seed=7001); assert r['seed_pool'] == 'generalisation'; scan(r); cl.end_episode(r['episode'])
        r = cl.reset('heldout', seed=6001); assert r['seed_pool'] == 'heldout'; cl.end_episode(r['episode'])
        assert json.load(open(os.path.join(sealed, 'freeze.json')))['hash'] == 'frozen-config-sha256-0123456789'
        led = [json.loads(l) for l in open(os.path.join(sealed, 'ledger.jsonl'))]; assert {x['pool'] for x in led} == {'generalisation', 'heldout'}
        meta = json.load(open(glob.glob(os.path.join(sealed, 'episode_*', 'episode.json'))[0])); assert meta['variant'] in ('phi0', 'phi04', 'phi08')
        # generalisation dishes are drawn from the phi0 / phi08 variants only (sealed)
        gen = [json.load(open(f)) for f in glob.glob(os.path.join(sealed, 'episode_*', 'episode.json')) if json.load(open(f))['pool'] == 'generalisation']; assert all(g['variant'] in ('phi0', 'phi08') for g in gen) and gen
    finally: cl.shutdown(); p.wait(timeout=30)
