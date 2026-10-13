"""mean-field theory v4: l*, g_eff, bath critical value with the feedback term, per-cell phi_k."""
import numpy as np
from scipy.optimize import brentq
from dish import R_, BETA_E, D_k
def lstar(g, r=R_, c=0.0):
    """stable positive root of -2r sinh l + (g + c) tanh(l/2) = 0 (c = alpha*beta_E*Dbar); closed form 2 arccosh sqrt((g+c)/4r)"""
    ge = g + c; return 2 * np.arccosh(np.sqrt(ge / (4 * r))) if ge > 4 * r else 0.0
def W_of(tm):
    D = np.linalg.norm(tm.Xs[:, :, None] - tm.Xs[:, None, :], axis=0); w = np.exp(-D); np.fill_diagonal(w, 0.0); return w.sum(1)
def F(l, B, W, g, c, r=R_, eps=1e-3):
    rho = 1 / (1 + np.exp(-l)); f = (W * rho + eps / 2) / (W + B + eps); return -2 * r * np.sinh(l) + g * (2 * f - 1) + c * np.tanh(l / 2)
def stable_pos_root(B, W, g, c, r=R_):
    ls = np.linspace(0.02, 10, 20001); v = F(ls, B, W, g, c, r); out = []
    for i in range(len(ls) - 1):
        if v[i] * v[i + 1] < 0 and v[i] > 0: out.append(brentq(lambda x: F(x, B, W, g, c, r), ls[i], ls[i + 1]))
    return out
def Bc(W, g, c, r=R_, Bmax_factor=1e4):
    """smallest bath B (ligand B) at which the stable a-branch (root l>0) disappears; None if it persists up to Bmax_factor*W (no bath can switch: locked)"""
    if not stable_pos_root(Bmax_factor * W, W, g, c, r) == []: return None
    lo, hi = 0.0, Bmax_factor * W
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if stable_pos_root(mid, W, g, c, r): lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)
def phi_cells(tm, g, alpha): return alpha * BETA_E * D_k(tm) / g
