"""Per-run truth tables from the hidden tier. Groups: 'all' (all alive cells), 'b0'/'b1' (original bodies; dish-merge runs only)."""
import sys, os, pickle, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from an3 import *            # v3 code (read-only): make_template2, classify_shape, orbits, PI_C, PI_L
from world2 import component_labels
from scipy.sparse.csgraph import minimum_spanning_tree
from scipy.spatial.distance import cdist
TM = make_template2(); SP, SM = np.array(TM.Xs[1] > 0), None
BR = np.where((TM.CL != TM.CR).any(0))[0]; SPL = BR[TM.Xs[1, BR] > 0]; SMI = BR[TM.Xs[1, BR] < 0]; ORB = orbits(TM, PI_C, PI_L); NORB = ORB.max() + 1
def procrustes_frame(X, place):
    """proper rotation R with (X - mean) ~ R (Xs[:, place] - mean); returns R, centroid"""
    A = TM.Xs[:, place].T; A = A - A.mean(0); B = X - X.mean(0); U, S, Vt = np.linalg.svd(A.T @ B); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    return R, X.mean(0)
def group_row(fr, idx, f0=None, shape=False):
    X = fr['X'][idx]; C = fr['C'][idx]; MU = fr['MU'][idx]; L = fr['L'][idx]; E = fr['E'][idx]; D = fr['D'][idx]; n = len(idx)
    q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True); place = q.argmax(1); r = rho(L)
    comp = component_labels(X, CFG['r_link']); nc = int((np.bincount(comp) >= CFG['m_min']).sum()) if n else 0
    Dm = cdist(X, X); mst = float(minimum_spanning_tree(Dm + 1e-9).toarray().max()) if n > 1 else 0.0
    row = dict(n=n, mean_rho=float(r.mean()), frac_a=float((r > 0.5).mean()), ncomp=nc, n_comp_all=int(comp.max() + 1) if n else 0, mst_max=mst, centroid=X.mean(0).tolist())
    ep = float((E * q[:, SPL].sum(1)).sum() / max(q[:, SPL].sum(), 1e-9)); em = float((E * q[:, SMI].sum(1)).sum() / max(q[:, SMI].sum(), 1e-9)); row.update(rep_plus=ep, rep_minus=em, rep_contrast=ep - em)
    row['dA'] = float(D[:, 0].mean()); row['dB'] = float(D[:, 1].mean())
    if n >= 12:
        R, c = procrustes_frame(X, place); row.update(e1=R[:, 0].tolist(), e2=R[:, 1].tolist(), place=place.tolist())
        ocnt = np.bincount(ORB[place], minlength=NORB); row['orbit_ok'] = bool((ocnt == np.bincount(ORB, minlength=NORB)).all()) if n == 24 else False
        if shape and n == 24:
            lab, dL, dR = classify_shape(TM, X, C); row.update(shape=lab, dL=float(dL))
    return row
def build(run, shape_every=4):
    frs, hidden = raw(run); m = META[run]; out = dict(run=run, t=[fr['t'] for fr in frs], groups={'all': [], 'b0': [], 'b1': []}, per_cell=[])
    fuse = m['family'] == 'stress' and m['scn'].startswith('fuse')
    for k, fr in enumerate(frs):
        a = np.where(fr['alive'])[0]; out['groups']['all'].append(group_row(fr, a, shape=(k % shape_every == 0)))
        ids = fr['cell_id']
        if fuse:
            out['groups']['b0'].append(group_row(fr, a[ids[a] < 24], shape=(k % shape_every == 0))); out['groups']['b1'].append(group_row(fr, a[ids[a] >= 24], shape=(k % shape_every == 0)))
        out['per_cell'].append(dict(id=ids[a].tolist(), rho=rho(fr['L'][a]).round(4).tolist(), X=fr['X'][a].round(4).tolist()))
    out['hidden_events'] = hidden['events']; out['pose'] = hidden['pose']; out['meta'] = m; out['onset'] = onset_abs(run)
    return out
def job(run):
    p = os.path.join(AUD, 'data', 'truth', run + '.pkl'); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p): pickle.dump(build(run), open(p, 'wb'))
    return run
if __name__ == "__main__":
    from par import run_jobs; import time; t0 = time.time()
    run_jobs(job, [(r['run'],) for r in CAT], workers=8, label='truth'); print('wall', time.time() - t0)
