"""Faithful transliterations of the small SPM12 utility functions this model
needs. Each function cites its source file:line. Forward-difference step
size exp(-8) matches spm_diff.m line 37 exactly (not central differences).
"""
import math
import numpy as np
from scipy.linalg import expm

DX_STEP = np.exp(-8.0)  # spm_diff.m line 37: dx = exp(-8) (global default)


def spm_softmax_cols(x: np.ndarray) -> np.ndarray:
    """spm_softmax.m: softmax over columns, numerically stabilized."""
    x = x - x.max(axis=0, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=0, keepdims=True)


def spm_diff_jacobian(f, x0: np.ndarray, *args) -> np.ndarray:
    """Forward-difference Jacobian of f(x,*args) w.r.t. x, matching
    spm_diff.m's `dfdx = (f(x+dx)-f(x))/dx` with dx=exp(-8), applied
    independently per element of the flattened x (spm_diff perturbs each
    element of x{n} in turn using the same global step). Returns a matrix
    of shape (len(f(x0)), len(x0.ravel())), x0 flattened in the SAME
    column-major (Fortran) order MATLAB/Octave uses for `(:)`.
    """
    x_flat = x0.ravel(order="F")
    f0 = np.asarray(f(x0, *args)).ravel(order="F")
    J = np.zeros((f0.size, x_flat.size))
    for i in range(x_flat.size):
        xp = x_flat.copy()
        xp[i] += DX_STEP
        x_pert = xp.reshape(x0.shape, order="F")
        fp = np.asarray(f(x_pert, *args)).ravel(order="F")
        J[:, i] = (fp - f0) / DX_STEP
    return J


def spm_DEM_R(n: int, s: float) -> np.ndarray:
    """spm_DEM_R.m, 'Gaussian' branch: precision of n generalized temporal
    derivatives of a Gaussian process with smoothness s (s.d., in bins).
    Returns the (n x n) precision matrix R = inv(V)."""
    if n == 0:
        return np.zeros((0, 0))
    if s == 0:
        s = np.exp(-8.0)
    k = np.arange(n)
    x = np.sqrt(2.0) * s
    r = np.zeros(2 * n - 1)
    # r(1+2k) = cumprod(1-2k)/x^(2k)  (MATLAB 1-indexed -> r[2k] here, 0-indexed)
    cumprod_term = np.cumprod(np.where(k == 0, 1.0, 1 - 2 * k))
    r[2 * k] = cumprod_term / (x ** (2 * k))
    V = np.zeros((n, n))
    rr = r.copy()
    for i in range(n):
        V[i, :] = rr[i:i + n]
        rr = -rr
    R = np.linalg.inv(V)
    return R


def spm_DEM_embed(Y: np.ndarray, n: int, t: int, dt: float = 1.0, d=(0,)):
    """spm_DEM_embed.m: temporal embedding into n generalized derivatives.
    Y: (q, N) array. t: 1-indexed bin (as in MATLAB). Returns list of n
    (q,) arrays [y[0]=value, y[1]=1st deriv, ...]. Boundary-clamped exactly
    as the source (k<1 -> clamp to 1; k>N -> clamp to N).
    """
    q, N = Y.shape
    y = [np.zeros(q) for _ in range(n)]
    if q == 0:
        return y
    s = (t - d[0]) / dt
    k = np.arange(1, n + 1) + int(np.floor(s - (n + 1) / 2))
    x = s - k.min() + 1
    k = np.where(k < 1, 1, k)
    k = np.where(k > N, N, k)
    T = np.zeros((n, n))
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            T[i - 1, j - 1] = ((i - x) * dt) ** (j - 1) / math.factorial(j - 1)
    E = np.linalg.inv(T)
    Yk = Y[:, k - 1]  # (q, n)
    for i in range(n):
        y[i] = Yk @ E[i, :]
    return y


def spm_dx(dfdx: np.ndarray, f: np.ndarray, t: float = 1.0) -> np.ndarray:
    """spm_dx.m (dense path, n<=512, t scalar not a cell): local-linearization
    update dx = (expm(t*dfdx) - I) * inv(dfdx) * f, computed via the
    augmented-Jacobian matrix-exponential trick (source lines ~95-101):
        J = [0 0; t*f t*dfdx]; dx = expm(J)[:,0][1:]
    """
    n = f.shape[0]
    J = np.zeros((n + 1, n + 1))
    J[1:, 0] = t * f
    J[1:, 1:] = t * dfdx
    E = expm(J)
    dx = E[1:, 0]
    return np.real(dx)
