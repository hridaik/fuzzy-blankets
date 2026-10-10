"""O3 front end: foreground components of the c6 field, mass-based cell count, pseudo-cells (RL + weighted k-means),
per-channel amplitudes by NNLS. Organism members at O3 = foreground pixel ids (field-level, NOT cells)."""
import numpy as np
from scipy.ndimage import gaussian_filter, label
from scipy.optimize import nnls
from . import segment


def frame_points(imgs, fov, cfg):
    """imgs (C,64,64). Returns dict(xy, lev, ids, lab, I (smoothed c6), thr, bg)."""
    N = 64
    px = 2 * fov / N
    X, Y = segment.grid(fov)
    far = np.hypot(X, Y) > 0.75 * fov
    I6 = imgs[0].astype(float)
    Is = gaussian_filter(I6, 0.5)
    bg = float(Is[far].mean()); sd = float(Is[far].std())
    thr = bg + cfg['fg_sigma_mult'] * sd
    L, nl = label(Is > thr, structure=np.ones((3, 3)))
    keep = Is > thr
    ii = np.flatnonzero(keep.ravel())
    lab_full = L.ravel()
    xy = np.c_[X.ravel()[ii], Y.ravel()[ii]]
    lev = imgs.reshape(imgs.shape[0], -1)[:, ii].T.astype(float)
    return dict(xy=xy, lev=lev, ids=ii.astype(int), lab=lab_full[ii] - 1, bg=bg, sd=sd, thr=thr, px=px)


def regions(shape_n, org_pix_lists, fov, cfg):
    """Assign each pixel within 3*s_eff of an organism's foreground to its nearest organism (halo included)."""
    from scipy.ndimage import distance_transform_edt
    N = shape_n; px = 2 * fov / N
    L = np.zeros(N * N, int)
    for i, pix in enumerate(org_pix_lists):
        L[pix] = i + 1
    L = L.reshape(N, N)
    d, (ri, ci) = distance_transform_edt(L == 0, return_indices=True)
    near = L[ri, ci]
    ok = (d * px) < 4 * cfg['s_eff']
    return [np.flatnonzero(((near == i + 1) & ok).ravel()) for i in range(len(org_pix_lists))]


def pseudo_cells(imgs, fov, pix_idx, cfg):
    """Pseudo-cells for one organism (pixel index set)."""
    N = 64
    px = 2 * fov / N
    X, Y = segment.grid(fov)
    I6 = imgs[0].astype(float)
    far = np.hypot(X, Y) > 0.75 * fov
    bg = float(I6[far].mean())
    msk = np.zeros(N * N, bool); msk[pix_idx] = True
    I = np.clip(I6 - bg, 0, None).ravel() * msk
    mass = I.sum() * px * px
    n = int(np.clip(round(mass / cfg['mass_per_cell']), 1, 120))
    R = segment.rl_deconvolve(np.clip(I6 - bg, 0, None), cfg['s_eff'] / px, cfg['rl_iters']).ravel() * msk
    w = R / max(R.sum(), 1e-12)
    P = np.c_[X.ravel(), Y.ravel()]
    keep = w > w.max() * 0.02
    Pk, wk = P[keep], w[keep]
    cen = [Pk[np.argmax(wk)]]
    for _ in range(n - 1):
        d = np.min(((Pk[:, None, :] - np.array(cen)[None]) ** 2).sum(-1), 1)
        cen.append(Pk[np.argmax(d * wk ** 0.5)])
    cen = np.array(cen)
    for _ in range(25):
        lab = np.argmin(((Pk[:, None, :] - cen[None]) ** 2).sum(-1), 1)
        new = cen.copy()
        for c in range(n):
            m = lab == c
            if m.any():
                new[c] = (Pk[m] * wk[m, None]).sum(0) / wk[m].sum()
        if np.abs(new - cen).max() < 1e-4:
            break
        cen = new
    G = segment.design(X, Y, cen, cfg['s_eff'])[pix_idx]
    amps = np.zeros((n, imgs.shape[0]))
    for c in range(imgs.shape[0]):
        a, _ = nnls(G, imgs[c].ravel()[pix_idx].astype(float), maxiter=200)
        amps[:, c] = a
    return cen, amps, n, mass
