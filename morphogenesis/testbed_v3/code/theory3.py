"""mean-field theory T1-T5 (numbers)"""
import numpy as np
from scipy.optimize import brentq
R_, G_ = 0.05, 0.6
def lstar(g=G_, r=R_): return 2 * np.arccosh(np.sqrt(g / (4 * r))) if g > 4 * r else 0.0
def U(l, g=G_, r=R_): return 2 * r * np.cosh(l) - 2 * g * np.log(np.cosh(l / 2))
def dU(g=G_, r=R_): l = lstar(g, r); return float(U(0.0, g, r) - U(l, g, r))
def W_of(tm):
    D = np.linalg.norm(tm.Xs[:, :, None] - tm.Xs[:, None, :], axis=0); w = np.exp(-D); np.fill_diagonal(w, 0.0); return w.sum(1)   # W_i per place
def F(l, B, W, g=G_, r=R_, eps=1e-3, BA=0.0):
    rho = 1 / (1 + np.exp(-l)); f = (W * rho + BA + eps / 2) / (W + B + BA + eps); return -2 * r * np.sinh(l) + g * (2 * f - 1)
def roots(B, W, BA=0.0, g=G_, r=R_):
    ls = np.linspace(-8, 8, 16001); v = F(ls, B, W, g, r, BA=BA); out = []
    for i in range(len(ls) - 1):
        if v[i] == 0: out.append(ls[i])
        elif v[i] * v[i + 1] < 0: out.append(brentq(lambda x: F(x, B, W, g, r, BA=BA), ls[i], ls[i + 1]))
    return out
def Bc(W, g=G_, r=R_):
    """saddle-node of the a branch with bath B_B: smallest B at which the stable positive-l root disappears"""
    lo, hi = 0.0, 50.0 * W
    def has_a(B): return any((x > 0.3) and (-2 * r * np.cosh(x) + g * 2 * (W / (W + B + 1e-3)) * (1 / (1 + np.exp(x)))) < 0 for x in roots(B, W, g=g, r=r))
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if has_a(mid): lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)
