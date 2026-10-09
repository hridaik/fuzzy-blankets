import os, sys, json, numpy as np, scipy.io as sio
HERE = os.path.dirname(os.path.abspath(__file__))
TB = os.path.dirname(HERE)
MORPH = os.path.dirname(TB)
M2A = os.path.join(MORPH, "m2a_audit_and_library")
CENSUS = os.path.join(M2A, "data", "v2", "census")
sys.path.insert(0, HERE)
from engine import *
from scipy.optimize import linear_sum_assignment

def vanilla8():
    d = json.load(open(os.path.join(M2A, "sealed", "template_numbers.json")))["L2"]
    P_, S_ = np.array(d["P"]), np.array(d["S"])
    return make_template(P_, S_, 1.0)

def oracle_run(name):
    """oracle 512-bin trajectory. pos (2,8,T) sec (4,8,T) v (8slots,8cells,T) v0 (8 slots,8 cells)."""
    A = sio.loadmat(os.path.join(CENSUS, name + "_A.mat")); B = sio.loadmat(os.path.join(CENSUS, name + "_B.mat"))
    cat = lambda k: np.hstack([A[k], B[k]])
    T = cat("positions").shape[1]
    return dict(pos=cat("positions").reshape(2, 8, T, order="F"), sec=cat("secretion").reshape(4, 8, T, order="F"),
                v=cat("v_expect").reshape(8, 8, T, order="F"), v0=A["v_initial"], T=T)

def d_pair(xa, ca, xb, cb, pen=10.0):
    """permutation-invariant mean position distance, type-constrained when types given. xa (2,n)"""
    D = np.linalg.norm(xa[:, :, None] - xb[:, None, :], axis=0)
    ta = (ca > 0.5).astype(int) if ca is not None else None
    if ca is not None:
        code_a = (ca[1:4] > 0.5); code_b = (cb[1:4] > 0.5)
        mism = (code_a[:, :, None] != code_b[:, None, :]).any(0)
        D2 = D + pen * mism
    else:
        D2 = D
    r, c = linear_sum_assignment(D2)
    return float(D[r, c].mean())
