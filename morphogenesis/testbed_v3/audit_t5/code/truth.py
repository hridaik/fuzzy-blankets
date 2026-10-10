"""Truth extraction for held-out episodes (white box): hidden.npz + episode.json of the sealed live directory, matched by environment episode id."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import SEALED, T5
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components, minimum_spanning_tree
AUD = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CFG = json.load(open(os.path.join(AUD, 'FROZEN_AUDIT_CONFIG.json')))
MB = json.load(open(os.path.join(T5, 'MONITOR_CONFIG.json')))['bounds']
def sig(x): return 1 / (1 + np.exp(-x))
def load_hidden(eid):
    d = os.path.join(SEALED, f'episode_{eid:05d}'); h = np.load(os.path.join(d, 'hidden.npz')); e = json.load(open(os.path.join(d, 'episode.json')))
    return {k: h[k] for k in h.files}, e
def load_ep(eid, pool='heldout'):
    return json.load(open(os.path.join(T5, 'episodes_heldout' if pool == 'heldout' else 'episodes', f'ep_{eid:05d}.json')))
def geom_series(X, alive, rlink=1.6):
    """per-step true (noise-free) geometry with the monitor's own definitions"""
    T = len(X); n = np.zeros(T, int); nc = np.zeros(T, int); mst = np.zeros(T); s1 = np.zeros(T); s2 = np.zeros(T)
    for k in range(T):
        x = X[k][alive[k]]; n[k] = len(x); D = cdist(x, x)
        nc[k] = connected_components(D < rlink, directed=False)[0]; mst[k] = minimum_spanning_tree(D).toarray().max()
        c = x - x.mean(0); w = np.linalg.eigvalsh(c.T @ c / len(c)); s1[k] = np.sqrt(w[1]); s2[k] = np.sqrt(max(w[0], 0))
    return dict(n=n, ncomp=nc, mst=mst, s1=s1, s2=s2)
def true_geometry_ok(g, nb=10):
    s1b = np.median(g['s1'][:nb]); s2b = np.median(g['s2'][:nb]); r1 = np.abs(g['s1'] / s1b - 1); r2 = np.abs(g['s2'] / s2b - 1)
    ok = (g['n'] == 24) & (g['ncomp'] == 1) & (g['mst'] <= MB['mst_max']) & (r1 <= MB['s1_rel']) & (r2 <= MB['s2_rel'])
    return ok, r1, r2
def summarise(eid, twin_eid=None):
    h, e = load_hidden(eid); t = h['t']; al = h['alive']; L = h['L']
    rho = np.array([sig(L[k][al[k]]).mean() for k in range(len(t))]); fa = np.array([(sig(L[k][al[k]]) > 0.5).mean() for k in range(len(t))])
    g = geom_series(h['X'], al); ok, r1, r2 = true_geometry_ok(g)
    out = dict(eid=eid, seed=e['seed'], t=t, rho=rho, frac_a=fa, geom=g, geom_ok_inst=ok, r1=r1, r2=r2, geom_ok_latched=np.cumprod(ok).astype(bool),
               members_ok=bool((al.all()) and (h['cell_id'] == h['cell_id'][0]).all()), hidden_events=e['hidden_events'], actions=e['actions'], state0=e['state0'])
    if twin_eid is not None:
        ht, _ = load_hidden(twin_eid); m = min(len(t), len(ht['t'])); out['dX_twin'] = float(np.abs(h['X'][:m] - ht['X'][:m]).max())
        out['dC_twin'] = float(np.abs(h['C'][:m] - ht['C'][:m]).max()); out['dMU_twin'] = float(np.abs(h['MU'][:m] - ht['MU'][:m]).max())
    return out
