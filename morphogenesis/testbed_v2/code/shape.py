"""Rigid-motion-invariant, permutation-invariant, type-constrained shape distance and helpers (system-agnostic)."""
import numpy as np
from scipy.optimize import linear_sum_assignment

PEN = 10.0

def cell_types(C, codes=None):
    """nearest type code (vanilla four types) from secretion rows 0..3: returns int array in 1..4"""
    codes = codes if codes is not None else np.array([(1, 1, 1, 0), (1, 1, 0, 0), (1, 0, 1, 0), (1, 0, 0, 1)], float)
    d = ((C[:4].T[:, None, :] - codes[None]) ** 2).sum(-1)
    return d.argmin(1) + 1

def d_rigid(Xa, ta, Xb, tb, reflection=False, n_angles=48, iters=30, return_all=False):
    """min over rigid motions (rotation+translation; +reflection if allowed, with proper rotations otherwise) and permutations
    preserving type of mean distance. Xa,Xb (2,n); ta,tb int types (or None to ignore types)."""
    n = Xa.shape[1]
    A = Xa - Xa.mean(1, keepdims=True); B = Xb - Xb.mean(1, keepdims=True)
    best = (np.inf, None, None, None)
    variants = [False, True] if reflection else [False]
    for refl in variants:
        Ar = A.copy()
        if refl: Ar[1] *= -1
        for th in np.linspace(0, 2 * np.pi, n_angles, endpoint=False):
            c, s = np.cos(th), np.sin(th); R = np.array([[c, -s], [s, c]]); Rt = R; cur = Rt @ Ar
            prev = np.inf
            for _ in range(iters):
                D = np.linalg.norm(cur[:, :, None] - B[:, None, :], axis=0)
                cost = D + (PEN * (ta[:, None] != tb[None, :]) if ta is not None else 0)
                r, cc = linear_sum_assignment(cost)
                val = D[r, cc].mean()
                if val > prev - 1e-12: break
                prev = val
                # Procrustes (proper rotation) for assigned pairs
                P = Ar[:, r]; Q = B[:, cc]; H = P @ Q.T; U, S, Vt = np.linalg.svd(H)
                Rn = Vt.T @ np.diag([1, np.sign(np.linalg.det(Vt.T @ U.T))]) @ U.T
                Rt = Rn; cur = Rt @ Ar
            if prev < best[0]: best = (prev, Rt, refl, (r, cc))
    val, R, refl, (r, cc) = best
    if return_all:
        ang = float(np.degrees(np.arctan2(R[1, 0], R[0, 0])))
        return float(val), dict(angle_deg=ang, reflected=bool(refl), perm=(r, cc), R=R)
    return float(val)

def centroid_orient(X):
    """principal-axis angle (deg) of a cloud, modulo 180"""
    Y = X - X.mean(1, keepdims=True); w, v = np.linalg.eigh(Y @ Y.T); a = np.degrees(np.arctan2(v[1, 1], v[0, 1])); return a % 180

def nn_spacing(X):
    D = np.linalg.norm(X[:, :, None] - X[:, None, :], axis=0); np.fill_diagonal(D, np.inf); return D.min(1)
