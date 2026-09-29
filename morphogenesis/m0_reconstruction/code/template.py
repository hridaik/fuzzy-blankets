"""Template decoding for the L=2 (8-cell) target morphology.

Direct transcription of DEM_morphogenesis.m lines 44-87 (SPM12 GitHub mirror,
commit 03ac9473c). See MODEL_SPEC.md section 1.

ESTABLISHED: transcribed 1:1 from source, no reinterpretation.
"""
import numpy as np

# T matrix, DEM_morphogenesis.m lines 46-51 (L=2 branch). Row/col order kept
# exactly as MATLAB source (row index -> y before detrend, col index -> x).
T_L2 = np.array([
    [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0, 4, 0, 4, 0, 3],
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
], dtype=float)

# T matrix, DEM_morphogenesis.m lines 54-66 (L=4 branch, "larger template").
# Dead code in the shipped script (L is hard-coded to 2) but transcribed here
# 1:1 to close MODEL_SPEC.md sec 1's NOT DONE item.
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


def spm_detrend_columns(x: np.ndarray) -> np.ndarray:
    """Port of spm_detrend for order-0 (mean removal only), applied per column.

    MATLAB: spm_detrend([x(:) y(:)]) with default order removes only the
    column mean (order 0 polynomial). x: (n, 2) -> mean-centered (n, 2).
    """
    return x - x.mean(axis=0, keepdims=True)


def decode_template(T: np.ndarray = T_L2):
    """Returns P.x (2,n), P.s (m,n) exactly as DEM_morphogenesis.m lines 69-86.

    p[:,:,0] = T > 0            (existence)
    p[:,:,1] = (T==2) | (T==1)
    p[:,:,2] = (T==3) | (T==1)
    p[:,:,3] = (T==4)
    """
    p0 = T > 0
    p1 = (T == 2) | (T == 1)
    p2 = (T == 3) | (T == 1)
    p3 = (T == 4)
    p = np.stack([p0, p1, p2, p3], axis=-1)  # (rows, cols, m=4)

    # [y,x] = find(p(:,:,1)) in MATLAB traverses in column-major order: for
    # each column left-to-right, rows top-to-bottom. Verified explicitly
    # against a hand-computed reference ordering (see MODEL_SPEC.md sec 1).
    rows, cols = np.nonzero(p0)
    order = np.lexsort((rows, cols))  # primary key: cols, secondary: rows
    rows_idx = rows[order]
    cols_idx = cols[order]
    y_coords = rows_idx  # MATLAB 'y' = row subscript
    x_coords = cols_idx  # MATLAB 'x' = column subscript
    n = len(y_coords)

    xy = np.stack([x_coords.astype(float), y_coords.astype(float)], axis=1)  # (n,2)
    xy = spm_detrend_columns(xy)
    P_x = xy.T / 2.0  # (2, n)

    m = p.shape[-1]
    P_s = np.zeros((m, n))
    for i in range(m):
        P_s[i, :] = p[..., i][rows_idx, cols_idx]
    return P_x, P_s, n, m


def cell_type_summary(T: np.ndarray = T_L2):
    vals = T[T > 0]
    uniq, counts = np.unique(vals, return_counts=True)
    return dict(zip(uniq.astype(int).tolist(), counts.tolist()))
