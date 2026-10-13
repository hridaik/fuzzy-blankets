"""v4 state-dependent template: chiral v3 template with the 8 tail places rotated about a hinge H=(x_h,0) by +theta (state a) / -theta (state b).
Codes unchanged; Lambda*_k(h) = sum_j C*_j exp(-kappa |X*_k(h) - X*_j(h)|)."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'testbed_v2', 'code'))
from engine2 import make_template2


class Template4:
    pass


def make_template4(theta_deg=30.0, kappa=1.0):
    t2 = make_template2(); tm = Template4()
    for k in ('Xs', 'CL', 'CR', 'mirror', 'types', 'kappa', 'LamL', 'S', 'w', 'kappa_m'):
        setattr(tm, k, getattr(t2, k))
    ty = t2.types[0]; tail = np.where(ty == 4)[0]; body = np.where(ty != 4)[0]
    assert len(tail) == 8
    xh = 0.5 * (t2.Xs[0, body].max() + t2.Xs[0, tail].min()); H = np.array([xh, 0.0])
    th = np.radians(theta_deg)
    def rot(a):
        c, s = np.cos(a), np.sin(a); R = np.array([[c, -s], [s, c]]); X = t2.Xs.copy(); X[:, tail] = R @ (t2.Xs[:, tail] - H[:, None]) + H[:, None]; return X
    tm.theta = theta_deg; tm.hinge = H; tm.tail = tail; tm.body = body; tm.head = int(np.argmin(t2.Xs[0]))
    tm.XsA, tm.XsB = rot(+th), rot(-th)
    def lam(X):
        D = np.linalg.norm(X[:, :, None] - X[:, None, :], axis=0); return t2.CL @ np.exp(-kappa * D)
    tm.LamA, tm.LamB = lam(tm.XsA), lam(tm.XsB)
    return tm


def tail_angle(tm, X, perm_or_places, alive=None):
    """signed tail angle (deg) of an arena configuration. X (n,2) cell positions; places (n,) = place index of each cell (argmax q).
    Proper-rotation Procrustes of the BODY (non-tail) cells onto the undeformed body template gives the body frame; the head->hinge axis is +x there,
    the tail axis is hinge->tail centroid; positive toward +y (limb side)."""
    places = np.asarray(perm_or_places); sel = np.isin(places, tm.body)
    if sel.sum() < 4 or (~sel).sum() < 1: return np.nan
    T = tm.Xs[:, places[sel]].T; Y = X[sel]
    mt, my = T.mean(0), Y.mean(0); U, S, Vt = np.linalg.svd((T - mt).T @ (Y - my))
    d = np.sign(np.linalg.det(Vt.T @ U.T)); R = Vt.T @ np.diag([1, d]) @ U.T       # template -> arena (proper rotation)
    tailsel = np.isin(places, tm.tail)
    if tailsel.sum() == 0: return np.nan
    Hs = R @ (tm.hinge - mt) + my; tc = X[tailsel].mean(0) - Hs
    ang = np.arctan2(tc[1], tc[0]); ref = np.arctan2((R @ np.array([1.0, 0.0]))[1], (R @ np.array([1.0, 0.0]))[0])
    a = np.degrees(((ang - ref + np.pi) % (2 * np.pi)) - np.pi); return float(a)
