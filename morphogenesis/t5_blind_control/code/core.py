"""
Shared population-level definitions for the 8-node graded-blanket benchmark.

This module reproduces (without re-running) the exact model construction verified
in benchmark.py Parts 1-10. It is duplicated here (not imported from benchmark.py)
so that benchmark.py remains completely untouched, per the stage-2 instructions.
A self-check at import time verifies this reconstruction is bit-for-bit identical
to the original, so any accidental drift is caught immediately rather than silently
propagating into the new statistical machinery.
"""
import itertools
import numpy as np

TOL = 1e-9  # population-level "exact zero" tolerance, unchanged from stage 1

N = 8
idx = {k: k - 1 for k in range(1, 9)}


def _add_edge(W, a, b, w):
    W[idx[a], idx[b]] += w
    W[idx[b], idx[a]] += w


def build_Omega0():
    W = np.zeros((N, N))
    for a, b in itertools.combinations([1, 2, 3], 2):
        _add_edge(W, a, b, 1.0)
    for a, b in itertools.combinations([6, 7, 8], 2):
        _add_edge(W, a, b, 1.0)
    for i in [1, 2, 3]:
        _add_edge(W, i, 4, 1.0)
        _add_edge(W, i, 5, 0.5)
    for j in [6, 7, 8]:
        _add_edge(W, 4, j, 1.0)
        _add_edge(W, 5, j, 0.5)
    D = np.diag(W.sum(axis=1))
    L = D - W
    return np.eye(N) + L


def build_Omega_amb():
    W = np.zeros((N, N))
    for a, b in itertools.combinations([1, 2, 3], 2):
        _add_edge(W, a, b, 1.0)
    for a, b in itertools.combinations([6, 7, 8], 2):
        _add_edge(W, a, b, 1.0)
    _add_edge(W, 3, 4, 1.0)
    _add_edge(W, 4, 6, 1.0)
    _add_edge(W, 2, 5, 0.5)
    _add_edge(W, 5, 7, 0.5)
    D = np.diag(W.sum(axis=1))
    L = D - W
    return np.eye(N) + L


Omega0 = build_Omega0()
Sigma0 = np.linalg.inv(Omega0)
Omega_amb = build_Omega_amb()

_Omega0_expected = np.array([
    [4.5, -1, -1, -1, -0.5, 0, 0, 0],
    [-1, 4.5, -1, -1, -0.5, 0, 0, 0],
    [-1, -1, 4.5, -1, -0.5, 0, 0, 0],
    [-1, -1, -1, 7, 0, -1, -1, -1],
    [-0.5, -0.5, -0.5, 0, 4, -0.5, -0.5, -0.5],
    [0, 0, 0, -1, -0.5, 4.5, -1, -1],
    [0, 0, 0, -1, -0.5, -1, 4.5, -1],
    [0, 0, 0, -1, -0.5, -1, -1, 4.5],
])
assert np.max(np.abs(Omega0 - _Omega0_expected)) < TOL, "core.py Omega0 drifted from stage-1 benchmark!"
assert np.all(np.linalg.eigvalsh(Omega0) > TOL), "core.py Omega0 not PD!"


def Omega_eps(eps):
    e3 = np.zeros(N); e3[idx[3]] = 1.0
    e6 = np.zeros(N); e6[idx[6]] = 1.0
    v = e3 - e6
    return Omega0 + eps * np.outer(v, v)


def logdet(M):
    if M.size == 0:
        return 0.0
    sign, ld = np.linalg.slogdet(M)
    if np.any(sign <= 0):
        raise np.linalg.LinAlgError(f"non-positive-definite matrix, sign={sign}")
    return ld


def L_cmi_precision(Omega, I_idx, B_idx, E_idx):
    """Exact population CMI from the precision matrix (Schur-complement form)."""
    IE = I_idx + E_idx
    K = Omega[np.ix_(IE, IE)]
    nI = len(I_idx)
    A = K[:nI, :nI]
    G = K[nI:, nI:]
    return 0.5 * (logdet(A) + logdet(G) - logdet(K))


def L_cmi_cov_joint(Sigma, I_idx, B_idx, E_idx):
    """Exact population CMI from joint covariance sub-blocks:
    L = 1/2[log|Sigma_IB| + log|Sigma_EB| - log|Sigma_B| - log|Sigma_IEB|].
    This is the *same formula* used for the finite-sample plug-in estimator in
    Part B, evaluated here at the population covariance as an independent check.
    """
    IB = I_idx + B_idx
    EB = E_idx + B_idx
    IEB = I_idx + E_idx + B_idx
    Sigma_IB = Sigma[np.ix_(IB, IB)]
    Sigma_EB = Sigma[np.ix_(EB, EB)]
    Sigma_B = Sigma[np.ix_(B_idx, B_idx)]
    Sigma_IEB = Sigma[np.ix_(IEB, IEB)]
    return 0.5 * (logdet(Sigma_IB) + logdet(Sigma_EB) - logdet(Sigma_B) - logdet(Sigma_IEB))


# cross-check the two population formulas agree, and match the stage-1 result
_I = [idx[n] for n in [1, 2, 3]]
_B = []
_E = [idx[n] for n in [4, 5, 6, 7, 8]]
_v1 = L_cmi_precision(Omega0, _I, _B, _E)
_v2 = L_cmi_cov_joint(Sigma0, _I, _B, _E)
_expected = 0.5 * np.log(211 / 142)
assert abs(_v1 - _expected) < 1e-9 and abs(_v2 - _expected) < 1e-9, "core.py CMI formulas drifted from stage-1!"

I_NODES = [1, 2, 3]
B45_NODES = [4, 5]
E678_NODES = [6, 7, 8]
REST_NODES = [4, 5, 6, 7, 8]
I_IDX = [idx[n] for n in I_NODES]
