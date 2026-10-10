"""O3 segmentation: sparse Gaussian-blob fit to the c6 fluorescence field (greedy matching pursuit +
joint least-squares refinement), then per-cell amplitudes in all channels by linear least squares at the
fitted positions. The effective blob width S_EFF is an observation-model constant fitted on development
dishes (see CALIBRATION.md). Causal: one frame at a time."""
import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.optimize import least_squares

N = 64


def grid(fov):
    g = -fov + (np.arange(N) + 0.5) * 2 * fov / N
    return np.meshgrid(g, g)       # X varies along columns, Y along rows


def design(X, Y, xy, s):
    return np.exp(-((X.ravel()[:, None] - xy[None, :, 0]) ** 2 + (Y.ravel()[:, None] - xy[None, :, 1]) ** 2) / (2 * s * s))


def segment_frame(img6, fov, s_eff, kappa, max_cells=80, noise_floor=None):
    """img6: (64,64) c6 channel. Returns xy (n,2), amp (n,), noise estimate."""
    X, Y = grid(fov)
    px = 2 * fov / N
    far = np.hypot(X, Y) > 0.75 * fov
    sig = float(np.std(img6[far])) if noise_floor is None else noise_floor
    sig = max(sig, 1e-3)
    I = img6.ravel().astype(float)
    xy = np.zeros((0, 2)); amp = np.zeros(0)
    res = I.copy()
    thr = kappa * sig
    for it in range(max_cells):
        R = res.reshape(N, N)
        Rs = gaussian_filter(R, s_eff / px)       # matched-filter-like smoothing
        j = np.unravel_index(np.argmax(Rs), Rs.shape)
        if R[j] < thr and Rs[j] < thr * 0.7:
            break
        p0 = np.array([X[j], Y[j]])
        a0 = max(R[j], 0.1)
        xy = np.vstack([xy, p0]); amp = np.append(amp, a0)
        xy, amp = _refine(I, X, Y, xy, amp, s_eff, fov)
        res = I - design(X, Y, xy, s_eff) @ amp
    return xy, amp, sig


def _refine(I, X, Y, xy, amp, s, fov, nfev=12):
    n = len(amp)
    x0 = np.concatenate([xy.ravel(), amp])
    dx, dy = X.ravel(), Y.ravel()

    def f(p):
        P = p[:2 * n].reshape(n, 2); a = p[2 * n:]
        return design(X, Y, P, s) @ a - I

    def jac(p):
        P = p[:2 * n].reshape(n, 2); a = p[2 * n:]
        G = design(X, Y, P, s)
        J = np.zeros((len(I), 3 * n))
        gx = G * (dx[:, None] - P[None, :, 0]) / s ** 2 * a[None]
        gy = G * (dy[:, None] - P[None, :, 1]) / s ** 2 * a[None]
        J[:, 0:2 * n:2] = gx; J[:, 1:2 * n:2] = gy; J[:, 2 * n:] = G
        return J
    lb = np.concatenate([np.full(2 * n, -fov), np.zeros(n)])
    ub = np.concatenate([np.full(2 * n, fov), np.full(n, np.inf)])
    x0 = np.clip(x0, lb + 1e-6, np.where(np.isinf(ub), 1e9, ub - 1e-6))
    r = least_squares(f, x0, jac=jac, bounds=(lb, ub), max_nfev=nfev, method='trf')
    p = r.x
    return p[:2 * n].reshape(n, 2), p[2 * n:]


def channel_amps(imgs, fov, xy, s_eff):
    """Per-cell amplitudes in every channel (linear LSQ at fixed positions), imgs (C,64,64)."""
    X, Y = grid(fov)
    G = design(X, Y, xy, s_eff)
    out = []
    for c in range(imgs.shape[0]):
        a, *_ = np.linalg.lstsq(G, imgs[c].ravel().astype(float), rcond=None)
        out.append(np.clip(a, 0, None))
    return np.stack(out, 1)


# ---------------------------------------------------------------- v2: mass-count + Richardson-Lucy + weighted k-means
from scipy.signal import fftconvolve


def _kernel(s_pix, half=None):
    half = half or int(np.ceil(4 * s_pix))
    g = np.arange(-half, half + 1)
    k = np.exp(-(g[:, None] ** 2 + g[None, :] ** 2) / (2 * s_pix ** 2))
    return k / k.sum()


def rl_deconvolve(I, s_pix, iters):
    k = _kernel(s_pix)
    est = np.full_like(I, max(I.mean(), 1e-3))
    kf = k[::-1, ::-1]
    for _ in range(iters):
        conv = fftconvolve(est, k, mode='same') + 1e-6
        est = est * fftconvolve(I / conv, kf, mode='same')
    return est


def segment_frame2(img6, fov, s_eff, rl_iters, mass_per_cell, n_cap=100):
    """Count from integrated (background-subtracted) mass; positions from k-means on the RL-sharpened mass."""
    X, Y = grid(fov); px = 2 * fov / N
    far = np.hypot(X, Y) > 0.75 * fov
    bg = float(np.mean(img6[far]))
    I = np.clip(img6.astype(float) - bg, 0, None)
    mass = I.sum() * px * px
    n = int(np.clip(round(mass / mass_per_cell), 1, n_cap))
    fg = gaussian_filter(I, s_eff / px) > 0.12 * gaussian_filter(I, s_eff / px).max()
    R = rl_deconvolve(I, s_eff / px, rl_iters) * fg
    w = R.ravel(); w = w / max(w.sum(), 1e-12)
    P = np.c_[X.ravel(), Y.ravel()]
    # init: farthest-point seeding on mass-weighted pixels (deterministic)
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
    return cen, dict(n=n, mass=mass, bg=bg)
