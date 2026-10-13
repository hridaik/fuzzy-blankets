import os, csv, json, glob, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.join(HERE, '..', '..', 'testbed_blind_v4'); HID = os.path.join(HERE, '..', 'data', 'blind_v4_hidden')
def rows(): return list(csv.DictReader(open(os.path.join(PKG, 'catalog.csv'))))
def test_files_split_and_leak_check():
    R = rows(); assert len(R) > 300
    for r in R[::25]:
        for lv in ('O1', 'O2', 'O3a', 'O3b', 'O3c'): assert os.path.exists(os.path.join(PKG, 'runs', f"{r['run']}_{lv}.npz"))
    man = json.load(open(os.path.join(PKG, 'split_manifest.json')))['runs']; assert set(man) == {r['run'] for r in R}
    assert not glob.glob(os.path.join(PKG, '**', '*hid*'), recursive=True) and 'PASS' in open(os.path.join(PKG, 'LEAK_CHECK.md')).read()
    assert set(man.values()) == {'development', 'heldout_bodies', 'heldout_conditions', 'heldout_locations'}
def test_time_resolution():
    nat = [r for r in rows() if r['condition'] == 'N0']; assert len(nat) == 32
    for r in nat[:6]:
        t = np.load(os.path.join(PKG, 'runs', r['run'] + '_O1.npz'))['t']; assert np.allclose(np.diff(t), 1.0) and t[-1] >= 2990
    for r in [x for x in rows() if x['condition'][0] in 'TP'][::15]:
        t = np.load(os.path.join(PKG, 'runs', r['run'] + '_O1.npz'))['t']; a, b = [float(v) for v in r['fine_window'].split('-')]; dt = np.diff(t); mid = (t[:-1] >= a) & (t[1:] <= b)
        assert np.allclose(dt[mid], 0.5, atol=1e-6) and dt.max() <= 1.0 + 1e-6
def test_o3c_markers_o2_ids_shapes():
    r = [x for x in rows() if x['condition'] == 'N0'][0]; z = np.load(os.path.join(PKG, 'runs', r['run'] + '_O3c.npz')); assert z['image'].shape[1:] == (4, 128, 128) and z['image'].dtype == np.uint8
    im = z['image'][0][0].astype(float) / z['scale'][0]; from scipy.ndimage import maximum_filter
    pk = (im == maximum_filter(im, 5)) & (im > 0.5); assert abs(int(pk.sum()) - 24) <= 2
    assert 'cell_id' not in np.load(os.path.join(PKG, 'runs', r['run'] + '_O2.npz')).files
    assert np.load(os.path.join(PKG, 'runs', r['run'] + '_O3a.npz'))['image'].shape[1:] == (3, 64, 64) and np.load(os.path.join(PKG, 'runs', r['run'] + '_O3b.npz'))['image'].shape[1:] == (4, 64, 64)
def test_opaque_labels_same_coding_as_v2_v3_and_new_codes_opaque():
    import re; conds = {r['condition'] for r in rows()}; assert all(re.fullmatch(r'N0|P\d\d|T\d[ab]', c) for c in conds)
    v2 = json.load(open(os.path.join(HERE, '..', '..', 'testbed_v3', 'data', 'blind_v2_hidden', 'mapping.json'))); v4 = json.load(open(os.path.join(HID, 'mapping.json')))
    assert v4['light_labels'] == v2['light_labels'] and v4['col_perm'] == v2['col_perm'] and v4['reagent'] == v2['reagent']
    assert {int(c[1]) for c in conds if c[0] == 'T'} <= {1, 2, 3, 4, 5}
def test_twin_sham_crn_hidden_tier():
    """sham arm = twin arm bit-identical in the hidden tier (no operation delivered); event arm identical to the twin until the onset"""
    R = rows(); groups = {}
    for r in R: groups.setdefault(r['group'], {})[r['arm']] = r
    n = 0
    for g, d in groups.items():
        if {'treated', 'untreated_control', 'sham_treated'} <= set(d) and g.startswith('D'):
            a = np.load(os.path.join(HID, d['untreated_control']['run'] + '_hid.npz')); b = np.load(os.path.join(HID, d['sham_treated']['run'] + '_hid.npz')); c = np.load(os.path.join(HID, d['treated']['run'] + '_hid.npz'))
            for k in ('X', 'rho', 'l', 'ubar'): assert np.array_equal(a[k], b[k]), (g, k)
            on = float(d['treated']['onset']); pre = a['t'] < on - 1e-9; assert pre.sum() > 5
            for k in ('X', 'l'): assert np.array_equal(a[k][pre], c[k][pre]), (g, k, 'pre-onset')
            n += 1
    assert n >= 10
def test_hidden_tier_has_organism_intact_and_dish_params():
    R = rows(); r = [x for x in R if x['condition'][0] == 'T'][0]['run']; z = np.load(os.path.join(HID, r + '_hid.npz')); assert 'intact' in z.files and z['intact'].dtype == bool and len(z['intact']) == len(z['t'])
    m = json.load(open(os.path.join(HID, r + '.json'))); assert 'dish' in m and 'g' in m['dish'] and 'gamma_factor' in m['dish'] and 'variant' in m
