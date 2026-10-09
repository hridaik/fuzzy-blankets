"""S3/S4 shared: operating-point engine, adult L/R states, body-frame patterns, outcome classifier."""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import *
from exports import component_labels
import chiral as CH

OP = dict(lp=-8.0, ls=2.0)           # S1 operating point (see SITUS_CALIBRATION.md)
T_ON = 1e4

def op_params(sig=0.0, smu=0.0, **kw):
    ps = float(np.exp(OP['ls']))
    return tb_params(pi_prior=float(np.exp(OP['lp'])), pi_x=ps, pi_c=ps, pi_l=ps, pi_ref=ps, pi_act=1.5 * ps / np.e, sig_x=sig, sig_c=sig, sig_mu=smu, **kw)

def setup(sig=0.0, smu=0.0, **kw):
    t = make_body('chiral'); eng = make_engine(t, op_params(sig, smu, **kw)); eng.dt = 0.02
    return t, eng

def adult(t, eng, k=0, mirror=False, settle=100.0):
    """settled adult state of form L (mirror False) or R, cell->slot permutation perm (cell i holds slot perm[i])"""
    st = CH.start(t, k, mirror); rng = np.random.default_rng(777 + k); perm = rng.permutation(t.n)
    fin = eng.run_final(st, 0.0, eng.dt, int((100.0 + settle) / eng.dt), jax.random.PRNGKey(0), None, 0)
    return fin, perm

def body_frame_xy(t, perm):
    """template (body-frame) coordinates of the slot held by each cell (observer-independent ground truth)"""
    return t.Xs[0][:, perm].T

def masks(t, perm):
    T = body_frame_xy(t, perm); n = t.n; M = {}
    for nm, (cx, cy) in dict(head=(-2.7, 0.0), trunkP=(0.0, 1.0), trunkM=(0.0, -1.0), tail=(2.7, 0.0), mid=(0.9, 0.0)).items():
        M['disc_' + nm] = (np.linalg.norm(T - np.array([cx, cy]), axis=1) <= 1.5).astype(float)
    M['two_discs'] = (np.linalg.norm(T - np.array([0.0, 1.0]), axis=1) <= 1.5).astype(float) - (np.linalg.norm(T - np.array([0.0, -1.0]), axis=1) <= 1.5).astype(float)
    M['half_plus'] = (T[:, 1] > 0.1).astype(float); M['half_minus'] = (T[:, 1] < -0.1).astype(float)
    return M

def classify_state(t, eng, fin, perm=None):
    """L / R / DEFECT / OTHER with reasons. DEFECT = fragmentation (>1 component at r=1.6), extrusion (isolated cell), or incomplete slots/types."""
    X, C, MU, ZE = [np.array(a) for a in fin]; n = t.n
    if not np.isfinite(X).all(): return 'DEFECT', dict(reason='nan')
    comp = component_labels(X, 1.6); ncomp = int(comp.max() + 1)
    D = np.linalg.norm(X[:, None] - X[None], axis=-1) + 9 * np.eye(n); extr = int((D.min(1) > 1.6).sum())
    r = analyse(eng, t, fin, 0)
    lab, dL, dR = CH.classify(t, X, C)
    info = dict(dL=float(dL), dR=float(dR), ncomp=ncomp, extruded=extr, orbit_complete=bool(r['orbit_complete']), min_orbit_maxbel=r['min_orbit_maxbel'], type_ok=int(r['type_ok']))
    if ncomp > 1 or extr > 0 or not r['orbit_complete'] or not r['type_ok']:
        info['reason'] = 'fragmentation' if ncomp > 1 else ('extrusion' if extr else 'incomplete'); return 'DEFECT', info
    if lab == 'L': return 'L', info
    if lab == 'R': return 'R', info
    return 'OTHER', info

def target_R(t, perm, fin):
    """R target for each cell: the cell keeps its place; under the pure-fate-exchange correspondence it adopts the type of the mirror slot.
    returns (pos_target (n,2) = current-form positions aligned into the arena by Kabsch against slot positions, code_target (n,nc))"""
    X = np.array(fin[0]); T = body_frame_xy(t, perm)           # body-frame coords of the slot each cell holds
    a = T - T.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); Rm = Vt.T @ U.T
    if np.linalg.det(Rm) < 0: Vt[-1] *= -1; Rm = Vt.T @ U.T
    Tm = T * np.array([1, -1])                                    # mirror slot position (same set of positions): find the slot at that position
    Xs = t.Xs[0].T; j = np.array([np.argmin(np.linalg.norm(Xs - tm, axis=1)) for tm in Tm])   # slot at the mirrored position
    # R: the cell at body position p takes the TYPE/code of L slot at the mirrored position (reflection of the type pattern)
    code = t.Cs[0].T[j]; return X.copy(), code
