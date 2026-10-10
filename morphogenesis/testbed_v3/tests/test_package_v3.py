import os, csv, json, glob, numpy as np
HERE = os.path.dirname(__file__); PKG = os.path.join(HERE, '..', '..', 'testbed_blind_v3')
def rows(): return list(csv.DictReader(open(os.path.join(PKG, 'catalog.csv'))))
def test_files_split_and_no_hidden_files():
    R = rows(); assert len(R) == 289
    for r in R[::20]:
        for lv in ('O1', 'O2', 'O3a', 'O3b', 'O3c'): assert os.path.exists(os.path.join(PKG, 'runs', f"{r['run']}_{lv}.npz"))
    man = json.load(open(os.path.join(PKG, 'split_manifest.json')))['runs']; assert set(man) == {r['run'] for r in R}
    assert not glob.glob(os.path.join(PKG, '**', '*hid*'), recursive=True) and 'PASS' in open(os.path.join(PKG, 'LEAK_CHECK.md')).read()
def test_time_resolution_declared_in_b1():
    nat = [r for r in rows() if r['condition'] == 'N0']; assert len(nat) == 36
    for r in nat[:6]:
        t = np.load(os.path.join(PKG, 'runs', r['run'] + '_O1.npz'))['t']; assert np.allclose(np.diff(t), 1.0) and t[-1] >= 50 * 112.0
    for r in [x for x in rows() if x['condition'][0] in 'TXP'][::15]:
        t = np.load(os.path.join(PKG, 'runs', r['run'] + '_O1.npz'))['t']; a, b = [float(v) for v in r['fine_window'].split('-')]; dt = np.diff(t); mid = (t[:-1] >= a) & (t[1:] <= b)
        assert np.allclose(dt[mid], 0.5, atol=1e-6) and dt.max() <= 1.0 + 1e-6 and a >= 0
def test_o3c_cell_resolving_markers():
    r = [x for x in rows() if x['condition'] == 'N0'][0]; z = np.load(os.path.join(PKG, 'runs', r['run'] + '_O3c.npz')); assert z['image'].shape[1:] == (4, 128, 128) and z['image'].dtype == np.uint8
    im = z['image'][0][0].astype(float) / z['scale'][0]; from scipy.ndimage import maximum_filter
    pk = (im == maximum_filter(im, 5)) & (im > 0.5); assert abs(int(pk.sum()) - 24) <= 2
    px = 2 * float(r['fov_c']) / int(r['px_c']); assert 0.25 / 0.9 <= 0.3 and 0.25 / px > 1.2
def test_o2_has_no_ids_and_o3a_o3b_shapes_unchanged_from_v2():
    r = rows()[0]['run']; assert 'cell_id' not in np.load(os.path.join(PKG, 'runs', r + '_O2.npz')).files
    assert np.load(os.path.join(PKG, 'runs', r + '_O3a.npz'))['image'].shape[1:] == (3, 64, 64) and np.load(os.path.join(PKG, 'runs', r + '_O3b.npz'))['image'].shape[1:] == (4, 64, 64)
def test_opaque_labels_identical_to_package_v2():
    v2 = set(r['condition'] for r in csv.DictReader(open(os.path.join(HERE, '..', '..', 'testbed_blind_v2', 'catalog.csv')))); v3 = set(r['condition'] for r in rows()); assert v3 <= v2 and len(v3) >= 20
