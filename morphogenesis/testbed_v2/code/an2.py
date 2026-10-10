"""analysis helpers for v2 (shape classification, orbit completeness, belief summaries)"""
import numpy as np, jax, jax.numpy as jnp
from shape import d_rigid, cell_types
from engine2 import *

ORBIT_GAP = float(np.log(9.0) / 4.0)   # DECLARED: mirror twins whose energy gap at the exact template state is below ln9/beta_max(4)=0.55 cannot be separated at belief 0.9 by any allowed beta

def orbits(tm, pi_c=float(np.exp(2)), pi_lam=float(np.exp(2)), gap=ORBIT_GAP):
    """Exchangeable places (orbits): mirror twins (k, m(k)) whose symmetric energy gap at the exact L template state is < gap.  Singletons otherwise."""
    S = tm.S; G = lambda k, j: 0.5 * (pi_c * ((tm.CL[:, k] - tm.CL[:, j]) ** 2).sum() + pi_lam * ((tm.LamL[:, k] - tm.LamL[:, j]) ** 2).sum())
    orb = -np.ones(S, int); nxt = 0
    for k in range(S):
        if orb[k] >= 0: continue
        m = int(tm.mirror[k]); orb[k] = nxt
        if m != k and G(k, m) < gap and G(m, k) < gap: orb[m] = nxt
        nxt += 1
    return orb

def classify_shape(tm, X, C, thr=0.4):
    """typed rigid distance (proper rotations) to L and R templates. returns label, dL, dR"""
    ct = cell_types(np.asarray(C).T)
    dL = d_rigid(np.asarray(X).T, ct, tm.Xs, tm.types[0]); dR = d_rigid(np.asarray(X).T, ct, tm.Xs, tm.types[1])
    lab = 'L' if dL < thr and dL < dR else ('R' if dR < thr else 'other')
    return lab, float(dL), float(dR)

def orbits_mirror(tm):
    """G2+ orbits (declared): every mirror pair (k, m(k)) whose codes are identical in both forms (non-body-row places) is exchangeable, because under unresolved handedness the pair is the image of itself under the form swap."""
    orb = -np.ones(tm.S, int); nxt = 0
    for k in range(tm.S):
        if orb[k] >= 0: continue
        m = int(tm.mirror[k]); orb[k] = nxt
        if m != k and np.allclose(tm.CL[:, k], tm.CL[:, m]) and np.allclose(tm.CR[:, k], tm.CR[:, m]): orb[m] = nxt
        nxt += 1
    return orb

def summarize(eng, fin, perm=None, pis=None, mirror_orbits=False):
    tm = eng.tm; X, C, D, MU, L = [np.array(a) for a in fin]
    q = np.array(jax.nn.softmax(jnp.array(MU), axis=1)); orb = orbits_mirror(tm) if mirror_orbits else orbits(tm, *(pis or ())); no = orb.max() + 1
    O = np.zeros((no, tm.S)); O[orb, np.arange(tm.S)] = 1; qo = q @ O.T
    okc = bool((np.bincount(qo.argmax(1), minlength=no) == np.bincount(orb, minlength=no)).all())
    lab, dL, dR = classify_shape(tm, X, C)
    rho = 1 / (1 + np.exp(-L))
    return dict(label=lab, dL=dL, dR=dR, orbit_complete=okc, min_orbit_bel=float(qo.max(1).min()), min_bel=float(q.max(1).min()), mean_rho=float(rho.mean()), min_rho=float(rho.min()), max_rho=float(rho.max()))
