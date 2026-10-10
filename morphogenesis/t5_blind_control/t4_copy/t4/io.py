"""Data access: catalog, splits, frame iteration for O1/O2/O3a/O3b. Workspace-local data only."""
import csv, json, os
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')

# channel names (= O1 column index) per level, in file column order
CHANNELS = {
    'O1': ['c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6'],
    'O2': ['c0', 'c1', 'c2', 'c3', 'c6'],
    'O3a': ['c6', 'c2', 'c0'],
    'O3b': ['c6', 'c2', 'c0', 'c4'],
}


def catalog():
    rows = list(csv.DictReader(open(os.path.join(DATA, 'catalog.csv'))))
    for r in rows:
        r['n_cells'] = int(r['n_cells']); r['n_frames'] = int(r['n_frames'])
        r['frame_interval'] = float(r['frame_interval']); r['fov'] = float(r['fov'])
        r['body_id'] = int(r['body_id'])
        r['onset'] = float(r['onset']) if r['onset'] not in ('', None) else None
    return rows


def run_split(run=None):
    m = json.load(open(os.path.join(DATA, 'split_manifest.json')))['runs']
    return m if run is None else m[run]


def treatments():
    return json.load(open(os.path.join(DATA, 'treatments.json')))


def load(run, level):
    return np.load(os.path.join(DATA, 'runs', f'{run}_{level}.npz'))


def point_frames(run, level):
    """O1/O2: list of dict(t, xy, lev, ids|None) per frame."""
    d = load(run, level)
    fp = d['frame_ptr']
    out = []
    for i in range(len(fp) - 1):
        s = slice(fp[i], fp[i + 1])
        out.append(dict(t=float(d['t'][i]), xy=d['xy'][s].astype(float), lev=d['level'][s].astype(float),
                        ids=(d['cell_id'][s].astype(int) if 'cell_id' in d.files else None)))
    return out


def image_frames(run, level):
    d = load(run, level)
    return d['t'].astype(float), d['image'].astype(np.float32)
