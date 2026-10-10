"""Body-frame descriptors of an organism (single frame). Translation/rotation invariant by construction.
Reflection: p = coordinate along signed major axis e1, q = coordinate along e2 = rot90(e1) (right-handed).
A reflection flips q only. 'sens' features are odd in q; 'inv' features are even in q."""
import numpy as np
from .geom import mst_max_edge, components


def _third_masks(p):
    lo, hi = np.quantile(p, [1 / 3, 2 / 3])
    return p <= lo, p >= hi


def describe(xy, lev, ch, bf, r_coh):
    n = len(xy)
    d = {}
    x = xy - bf['centroid']
    p = x @ bf['e1']; q = x @ bf['e2']
    s1 = max(p.std(), 1e-6); s2 = max(q.std(), 1e-6)
    d['n'] = float(n)
    d['mst_max'] = mst_max_edge(xy)
    lab = components(xy, r_coh)
    d['ncomp_coh'] = float(lab.max() + 1)
    d['s1'] = float(s1); d['s2'] = float(s2); d['rg'] = float(np.sqrt((x ** 2).sum(1).mean()))
    d['skew_p_inv'] = float(((p / s1) ** 3).mean())
    d['pqq_inv'] = float((p * q ** 2).mean() / (s1 * s2 ** 2))
    d['q3_sens'] = float(((q / s2) ** 3).mean())
    d['ppq_sens'] = float((p ** 2 * q).mean() / (s1 ** 2 * s2))
    d['pq_cov_sens'] = float((p * q).mean() / (s1 * s2))
    lo, hi = _third_masks(p)
    for j, c in enumerate(ch):
        y = lev[:, j]
        yc = y - y.mean()
        d[f'{c}_mean'] = float(y.mean())
        d[f'{c}_slope_p'] = float((p * yc).mean() / s1 ** 2)
        d[f'{c}_dq_sens'] = float((q * yc).mean() / s2)
        d[f'{c}_dabsq_inv'] = float((np.abs(q) * yc).mean() / s2)
        d[f'{c}_tailhead'] = float(y[hi].mean() - y[lo].mean()) if lo.any() and hi.any() else 0.0
    return d


def feature_names(ch):
    names = ['n', 'mst_max', 'ncomp_coh', 's1', 's2', 'rg', 'skew_p_inv', 'pqq_inv', 'q3_sens', 'ppq_sens', 'pq_cov_sens']
    for c in ch:
        names += [f'{c}_mean', f'{c}_slope_p', f'{c}_dq_sens', f'{c}_dabsq_inv', f'{c}_tailhead']
    return names


def pattern_names(ch):
    """Channel-pattern features used for the C2 'pattern' axis and the state descriptors."""
    out = []
    for c in ch:
        out += [f'{c}_mean', f'{c}_slope_p', f'{c}_dq_sens', f'{c}_dabsq_inv', f'{c}_tailhead']
    return out
