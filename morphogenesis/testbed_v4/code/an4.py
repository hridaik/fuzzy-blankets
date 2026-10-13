"""analysis helpers v4: tail angle, orbit completeness (theta=0 orbits, v3 pis), typed shape distance to the state templates, ORGANISM INTACT pieces."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine4 import *
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'testbed_v2', 'code'))
from an2 import orbits
from shape import d_rigid, cell_types
from world2 import component_labels
PI_C, PI_L = float(np.e), float(np.e ** 3)
_orb = {}
def orbit_ids(tm):
    if id(tm) not in _orb: _orb[id(tm)] = orbits(tm, PI_C, PI_L)
    return _orb[id(tm)]

def typed_dist(tm, X, C, which):
    ct = cell_types(np.asarray(C).T); Xs = tm.XsA if which == 'a' else tm.XsB
    return float(d_rigid(np.asarray(X).T, ct, Xs, tm.types[0]))

def place_fill(tm, q):
    """orbit-aware completeness: argmax-q counts per orbit equal orbit sizes"""
    orb = orbit_ids(tm); no = orb.max() + 1; O = np.zeros((no, tm.S)); O[orb, np.arange(tm.S)] = 1; qo = q @ O.T
    ok = bool((np.bincount(qo.argmax(1), minlength=no) == np.bincount(orb, minlength=no)).all()); return ok, float(qo.max(1).min())

def nbr_sets(X, alive=None, r=1.6):
    D = np.linalg.norm(X[:, None] - X[None], axis=-1); A = (D <= r) & ~np.eye(len(X), dtype=bool)
    if alive is not None: A &= alive[:, None] & alive[None]
    return A

def jaccard_mean(A0, A1, alive=None):
    inter = (A0 & A1).sum(1); uni = (A0 | A1).sum(1); j = np.where(uni > 0, inter / np.maximum(uni, 1), 1.0)
    return float(j[alive].mean() if alive is not None else j.mean())

def summarize4(eng, st, ctl=None):
    tm = eng.tm; X, C, MU, L, D, E, U = [np.array(a) for a in st]
    q = np.array(jax.nn.softmax(jnp.array(MU), axis=1)); ok, mb = place_fill(tm, q); pl = q.argmax(1); rho = 1 / (1 + np.exp(-L))
    ang = tail_angle(tm, X, pl) if len(np.unique(pl)) == 24 else tail_angle(tm, X, pl)
    comp = component_labels(X, 1.6)
    return dict(angle=ang, orbit_ok=ok, min_orbit_bel=mb, n_comp=int(comp.max() + 1), mean_rho=float(rho.mean()), min_rho=float(rho.min()), max_rho=float(rho.max()), mean_l=float(L.mean()), std_l=float(L.std()),
                dA=typed_dist(tm, X, C, 'a'), dB=typed_dist(tm, X, C, 'b'))
