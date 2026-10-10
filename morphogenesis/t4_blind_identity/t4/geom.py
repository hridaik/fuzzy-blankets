"""Geometry: detection (single-linkage), body frame with observable sign resolution, descriptors."""
import math
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components, minimum_spanning_tree


def components(xy, r):
    if len(xy) == 0:
        return np.zeros(0, int)
    return connected_components(cdist(xy, xy) < r, directed=False)[1]


def mst_max_edge(xy):
    if len(xy) < 2:
        return 0.0
    return float(minimum_spanning_tree(cdist(xy, xy)).toarray().max())


def body_frame(xy, lev, ch, prev_e1=None, conf_min=0.9):
    """Centroid, principal axes (e1 major), orientation sign from the 'c6' level gradient along e1.
    Returns dict(centroid, e1, e2, axis_conf, sign_conf, sign_src, aspect). e2 = rot90(e1): right-handed,
    so reflections are NOT absorbed into the frame."""
    n = len(xy)
    c = xy.mean(0)
    if n < 3:
        return dict(centroid=c, e1=np.array([1., 0.]), e2=np.array([0., 1.]), axis_conf=0., sign_conf=0.,
                    sign_src='none', aspect=1.)
    x = xy - c
    w, v = np.linalg.eigh(x.T @ x / n)
    e1 = v[:, 1].copy()
    axis_conf = float(1 - w[0] / max(w[1], 1e-12))
    sc, src = 0.0, 'none'
    if 'c6' in ch:
        y = lev[:, ch.index('c6')]
        p = x @ e1
        pc = p - p.mean()
        sxx = (pc ** 2).sum()
        if sxx > 1e-9:
            b = (pc * (y - y.mean())).sum() / sxx
            res = y - y.mean() - b * pc
            se = math.sqrt(max((res ** 2).sum() / max(n - 2, 1), 1e-18) / sxx)
            z = b / se
            sc = math.erf(abs(z) / math.sqrt(2))
            if sc >= conf_min:
                if b < 0:
                    e1 = -e1
                src = 'observable'
            else:
                src = 'weak'
                if b < 0:
                    e1 = -e1
    if src != 'observable' and prev_e1 is not None:
        if e1 @ prev_e1 < 0:
            e1 = -e1
        src = 'continuity'
    e2 = np.array([-e1[1], e1[0]])
    return dict(centroid=c, e1=e1, e2=e2, axis_conf=axis_conf, sign_conf=float(sc), sign_src=src,
                aspect=float(math.sqrt(w[1] / max(w[0], 1e-12))))


def procrustes(A, B, allow_reflection):
    """Shape distance between corresponding point sets (translation, rotation [, reflection] removed;
    scale NOT removed). RMS residual."""
    A = A - A.mean(0); B = B - B.mean(0)
    H = A.T @ B
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.eye(2)
    if not allow_reflection and d < 0:
        D[1, 1] = -1
    R = U @ D @ Vt
    return float(np.sqrt(((A @ R - B) ** 2).sum(1).mean()))
