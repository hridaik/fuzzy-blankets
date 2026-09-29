"""Template, field, generative model/process. Same equations as
m0_reconstruction (re-verified here, not re-derived), now used with
faithful forward-difference Jacobians instead of gradient-descent.
"""
import numpy as np

T_L2 = np.array([
    [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0, 4, 0, 4, 0, 3],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
], dtype=float)

T_L4 = np.array([
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,2,0,0,0,3,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,2,0,0,0,0,0,3,0,0,0,4,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,4,0,1,0,0],
    [0,0,0,2,0,0,0,0,0,3,0,0,0,4,0,0,0,0,0,0,0,1],
    [0,0,0,0,0,0,0,2,0,0,0,3,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
], dtype=float)


def decode_template(T: np.ndarray = T_L2):
    p0 = T > 0
    p1 = (T == 2) | (T == 1)
    p2 = (T == 3) | (T == 1)
    p3 = (T == 4)
    p = np.stack([p0, p1, p2, p3], axis=-1)
    rows, cols = np.nonzero(p0)
    order = np.lexsort((rows, cols))
    rows_idx, cols_idx = rows[order], cols[order]
    n = len(rows_idx)
    xy = np.stack([cols_idx.astype(float), rows_idx.astype(float)], axis=1)
    xy = xy - xy.mean(axis=0, keepdims=True)
    P_x = xy.T / 2.0
    m = p.shape[-1]
    P_s = np.zeros((m, n))
    for i in range(m):
        P_s[i, :] = p[..., i][rows_idx, cols_idx]
    return P_x, P_s, n, m


def field_concentration(x: np.ndarray, s: np.ndarray, y: np.ndarray = None) -> np.ndarray:
    if y is None:
        y = x
    diff = y[:, :, None] - x[:, None, :]
    d = np.sqrt(np.sum(diff ** 2, axis=0))
    weight = np.exp(-1.0 * d)
    return (weight @ s.T).T


def sensitivity(t: float) -> float:
    return 1.0 - np.exp(-2.0 * t)


def Mg(v_flat: np.ndarray, n: int, P_x, P_s, P_c, t: float) -> np.ndarray:
    """v_flat: (n*n,) column-major flattened v matrix. Returns g_flat
    (ny,) = [g.x (2n); g.s (4n); g.c (4n)] flattened cell-major (matching
    spm_vec's struct-field-then-column-major convention: field x fully
    flattened column-major, then field s, then field c)."""
    v = v_flat.reshape(n, n, order="F")
    s = sensitivity(t)
    p = np.exp(v - v.max(axis=0, keepdims=True))
    p = p / p.sum(axis=0, keepdims=True)
    g_x = P_x @ p
    g_s = P_s @ p
    g_c = s * (P_c @ p)
    return np.concatenate([g_x.ravel(order="F"), g_s.ravel(order="F"), g_c.ravel(order="F")])


def Gg(a_flat: np.ndarray, n: int, m: int, t: float) -> np.ndarray:
    """a_flat: (2n+4n,) = [a.x; a.s] flattened cell-major. Returns g_flat
    (2n+4n+4n,) = [g.x; g.s; g.c]."""
    a_x = a_flat[:2 * n].reshape(2, n, order="F")
    a_s = a_flat[2 * n:2 * n + m * n].reshape(m, n, order="F")
    s = sensitivity(t)
    g_x = a_x.copy()
    g_s = a_s.copy()
    g_c = s * field_concentration(a_x, a_s)
    return np.concatenate([g_x.ravel(order="F"), g_s.ravel(order="F"), g_c.ravel(order="F")])
