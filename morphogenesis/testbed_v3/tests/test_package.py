import os, csv, json, glob, numpy as np
HERE = os.path.dirname(__file__); PKG = os.path.join(HERE, '..', '..', 'testbed_blind_v2')
def test_package_files_and_split():
    rows = list(csv.DictReader(open(os.path.join(PKG, 'catalog.csv')))); assert len(rows) == 513
    for r in rows[::25]:
        for lvl in ('O1', 'O2', 'O3a', 'O3b'): assert os.path.exists(os.path.join(PKG, 'runs', f"{r['run']}_{lvl}.npz"))
    man = json.load(open(os.path.join(PKG, 'split_manifest.json')))['runs']; assert set(man) == {r['run'] for r in rows}
    assert not glob.glob(os.path.join(PKG, '**', '*hid*'), recursive=True)
def test_leak_check_passes_and_o2_has_no_ids():
    assert 'PASS' in open(os.path.join(PKG, 'LEAK_CHECK.md')).read()
    r = list(csv.DictReader(open(os.path.join(PKG, 'catalog.csv'))))[0]['run']; assert 'cell_id' not in np.load(os.path.join(PKG, 'runs', r + '_O2.npz')).files
def test_sham_bit_identical_in_packaged_triplets_hidden_tier():
    hid = os.path.join(HERE, '..', 'data', 'blind_v2_hidden'); m = json.load(open(os.path.join(hid, 'mapping.json')))['runs']
    ev = {k: v for k, v in m.items() if v.get('family') == 'stress' and v.get('arm') in ('twin', 'sham') and v.get('scn') == 'cutx' and v.get('seed') == 700 and v.get('state') == 'a'}
    assert len(ev) == 2; a, b = [np.load(os.path.join(hid, k + '_hid.npz')) for k in ev]
    for k in ('l', 'e', 'd', 'X'): assert np.abs(a[k] - b[k]).max() == 0.0
