"""Run: python3 -m pytest tests -q   (or python3 tests/test_t4.py)"""
import sys, os, copy, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
from t4 import io, geom, orgtrack, celltrack, pipeline, outputs, layers, states
from t4.louvain import louvain

GEO = None
def geo():
    global GEO
    GEO = GEO or pipeline.load_geometry(); return GEO

def test_components_and_mst():
    xy = np.array([[0, 0], [1, 0], [2, 0], [10, 0], [11, 0]], float)
    assert geom.components(xy, 1.5).max() == 1
    assert abs(geom.mst_max_edge(xy) - 8.0) < 1e-9

def test_procrustes_reflection():
    A = np.random.default_rng(0).normal(size=(10, 2))
    B = A * np.array([1, -1])                    # mirror image
    assert geom.procrustes(A, B, True) < 1e-9
    assert geom.procrustes(A, B, False) > 0.1    # rotation-only cannot undo a reflection

def test_body_frame_sign_from_observable():
    rng = np.random.default_rng(1)
    p = np.linspace(-3, 3, 24); xy = np.c_[p, 0.3 * rng.normal(size=24)]
    lev = (1.3 + 0.25 * p)[:, None] * (1 + 0.03 * rng.normal(size=(24, 1)))
    th = 0.7; R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    bf = geom.body_frame(xy @ R.T, lev, ['c6'])
    assert bf['e1'] @ (R @ np.array([1., 0.])) > 0.99 and bf['sign_conf'] > 0.99
    bf2 = geom.body_frame(xy @ R.T, lev[::-1].copy(), ['c6'])       # gradient reversed -> axis sign flips
    assert bf2['e1'] @ bf['e1'] < -0.99

def _blob(c, n=12, seed=0):
    r = np.random.default_rng(seed); g = np.array([[i % 4, i // 4] for i in range(n)], float) * 1.0
    return g + np.array(c) + 0.02 * r.normal(size=g.shape)

def test_split_merge_unresolved():
    g = geo(); ch = ['c6']
    ot = orgtrack.OrganismTracker(ch, g['r_link'], g['m_min'], g['margin'], g['r_hold'])
    A = _blob([0, 0], 12); ids = np.arange(12); lev = np.ones((12, 1))
    ot.step(0., A, lev, ids)
    B = A.copy(); B[:6] += [-10, 0]; B[6:] += [10, 0]                  # equal halves: SPLIT, ambiguous -> UNRESOLVED
    orgs, ev = ot.step(1., B, lev, ids)
    types = [e['type'] for e in ev]
    assert 'SPLIT' in types and any(o['unresolved'] for o in orgs)
    # back together -> MERGE
    orgs, ev = ot.step(2., A, lev, ids)
    assert 'MERGE' in [e['type'] for e in ev]

def test_extrusion_and_arrival():
    g = geo(); ch = ['c6']
    ot = orgtrack.OrganismTracker(ch, g['r_link'], g['m_min'], g['margin'], g['r_hold'])
    A = _blob([0, 0], 12); ids = np.arange(12); lev = np.ones((12, 1)); ot.step(0., A, lev, ids)
    B = A.copy(); B[0] += [-8, 0]
    _, ev = ot.step(1., B, lev, ids)
    assert [e['cell'] for e in ev if e['type'] == 'EXTRUSION'] == [0]
    C = np.vstack([A[1:], [[1.5, 1.5]]]); ids2 = np.r_[ids[1:], 99]
    _, ev = ot.step(2., C, np.ones((12, 1)), ids2)
    assert any(e['type'] == 'ARRIVAL' and e['cell'] == 99 for e in ev)

def test_celltracker_follows_shuffled_points():
    rng = np.random.default_rng(3); ch = ['c0', 'c1', 'c2', 'c3', 'c6']
    X = rng.uniform(0, 5, (24, 2)); X = X[np.argsort(X[:, 0])]
    L = np.c_[np.eye(4)[rng.integers(0, 4, 24)], rng.uniform(0.5, 2.3, 24)]
    ct = celltrack.CellTracker(ch); ids0, _ = ct.step(X, L)
    perm = rng.permutation(24); shift = np.array([0.4, -0.2])
    ids1, _ = ct.step(X[perm] + shift + 0.02 * rng.normal(size=(24, 2)), L[perm])
    assert (ids1 == ids0[perm]).all()

def test_louvain_deterministic():
    W = np.zeros((6, 6)); W[:3, :3] = 1; W[3:, 3:] = 1; np.fill_diagonal(W, 0); W[2, 3] = W[3, 2] = 0.1
    a, b = louvain(W), louvain(W)
    assert (a == b).all() and len(set(a[:3])) == 1 and len(set(a[3:])) == 1 and a[0] != a[3]

def test_gaussian_cmi_estimator_matches_population():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'flock_code'))
    import core
    X = np.random.default_rng(0).multivariate_normal(np.zeros(8), core.Sigma0, 40000)
    S = np.cov(X.T)
    def L(I, B, E):
        f = lambda ix, c: S[np.ix_(ix, ix)] - (S[np.ix_(ix, c)] @ np.linalg.inv(S[np.ix_(c, c)]) @ S[np.ix_(c, ix)] if c else 0)
        ld = lambda M: np.linalg.slogdet(M)[1]
        return 0.5 * (ld(f(I, B)) + ld(f(E, B)) - ld(f(I + E, B)))
    est = L(core.I_IDX, [], [3, 4, 5, 6, 7]); pop = core.L_cmi_precision(core.Omega0, core.I_IDX, [], [3, 4, 5, 6, 7])
    assert abs(est - pop) < 0.01

def _strip(o):
    return json.loads(json.dumps(o, default=lambda x: x.item() if hasattr(x, 'item') else str(x)))

def test_causality_stage1_and_stage2():
    """Output at frame k computed on a truncated recording equals the output computed on the full recording."""
    cal = outputs.Calib(); g = geo()
    for run, lv, K in (('run_01830', 'O1', 40), ('run_01830', 'O2', 40), ('run_02208', 'O1', 30)):
        full = pipeline.process(run, lv, g, 12.0)
        trunc = copy.deepcopy(full); trunc['frames'] = trunc['frames'][:K]
        # recompute truncated stage-1 by monkeypatching frame loader
        orig = io.point_frames
        io.point_frames = lambda r, l, orig=orig: orig(r, l)[:K]
        try:
            part = pipeline.process(run, lv, g, 12.0)
        finally:
            io.point_frames = orig
        for fa, fb in zip(full['frames'][:K], part['frames']):
            assert [o['members'] for o in fa['orgs']] == [o['members'] for o in fb['orgs']]
            assert _strip(fa['events']) == _strip(fb['events'])
        o_full = outputs.level_output(full, cal, cell_lookup=False); o_part = outputs.level_output(part, cal, cell_lookup=False)
        for fa, fb in zip(o_full['frames'][:K], o_part['frames']):
            for a, b in zip(fa['organisms'], fb['organisms']):
                assert a['C3'] == b['C3'] and a['C1'] == b['C1'] and a['axis_pass'] == b['axis_pass'] and a['V_running'] == b['V_running'], (run, lv, fa['k'])

def test_catalog_splits_disjoint_and_heldout_not_in_dev():
    cat = io.catalog(); m = io.run_split()
    assert all(m[r['run']] == r['split'] for r in cat)
    assert {r['split'] for r in cat} >= {'development', 'heldout_bodies'}

if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f(); print('ok', n)
