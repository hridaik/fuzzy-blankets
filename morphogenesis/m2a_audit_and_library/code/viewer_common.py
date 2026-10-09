"""Shared helpers for the M2a viewer builds (audit side). Reads v2 segments, assembles chains, computes role overlays, applies the declared exemplar rule."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "viz"))
from v2 import *
from outcomes import *
import build_viewer_m2a as BM
VIZ = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "viz")
OUT = os.path.join(VIZ, "output", "m2a")
def seg_arrays(m, n=8):
    N = m["positions"].shape[1]
    a_x = np.stack([m["positions"][:, b].reshape(n, 2).T for b in range(N)]); a_s = np.stack([m["secretion"][:, b].reshape(4, n, order="F") for b in range(N)])
    return a_x, a_s
def chain(paths, n=8):
    xs, ss = [], []
    for p in paths:
        a, s = seg_arrays(load(p), n); xs.append(a); ss.append(s)
    return np.concatenate(xs), np.concatenate(ss)
def role_labels(a_x, a_s, stride=1):
    out = []; last = None
    for b in range(a_x.shape[0]):
        if b % stride == 0 or last is None:
            sl, _ = slot_assignment(a_x[b], a_s[b]); last = [f"r{int(s)}" for s in sl]
        out.append(last)
    return out
def select_exemplars(metrics, seed):
    """declared rule: median, best, worst by the batch's hidden metric (ascending = best) + 2 uniformly random picks from the rest (seed recorded)."""
    ids = list(metrics); v = np.array([metrics[i] for i in ids]); o = np.argsort(v, kind="stable"); best, worst, med = ids[o[0]], ids[o[-1]], ids[o[len(o) // 2]]
    rest = [i for i in ids if i not in (best, worst, med)]; rng = np.random.default_rng(seed)
    rnd = [rest[i] for i in rng.choice(len(rest), size=min(2, len(rest)), replace=False)] if rest else []
    return dict(seed=seed, median=med, best=best, worst=worst, random=rnd, n_batch=len(ids))
def write_pair(name, rollouts_obs, rollouts_aud, title, banner, header_obs, header_aud, entries, tier_note=""):
    os.makedirs(os.path.join(OUT, "observable"), exist_ok=True); os.makedirs(os.path.join(OUT, "audit"), exist_ok=True)
    fo = os.path.join("output", "m2a", "observable", f"{name}_observable.html"); fa = os.path.join("output", "m2a", "audit", f"{name}_audit.html")
    BM.build_html(rollouts_obs, title, banner, "banner-validated", header_obs, False, os.path.join(VIZ, fo))
    BM.build_html(rollouts_aud, title + " [AUDIT]", banner + " | AUDIT TIER: contains role-map overlay / hidden-derived overlays", "banner-partial", header_aud, True, os.path.join(VIZ, fa))
    entries.append(dict(name=name, file_observable=fo, file_audit=fa, notes=tier_note))
