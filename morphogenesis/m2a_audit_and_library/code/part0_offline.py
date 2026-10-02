"""Part 0 analyses that need only saved M1 rollouts: 0.1a (census injection),
0.1b (kicks), 0.3a/b (merging, stationarity), 0.4 (role maps), 0.5 (near-miss)."""
import json, os, sys, glob
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from m2a_common import *
from analysis import P_X, P_S, softmax_cols, d_target
from scipy.optimize import linear_sum_assignment

OUT = os.path.join(DATA, "part0"); os.makedirs(OUT, exist_ok=True)

def cen(k, i, N=512):
    p = f"{M1}/data/census/{k}_{i:04d}_N{N}.mat"
    if not os.path.exists(p): p = f"{M1}/data/census/{k}_{i:04d}_N2048.mat"
    return sio.loadmat(p)

def X(m, b): return m["positions"][:, b].reshape(8, 2).T          # (2,8)
def S_(m, b): return m["secretion"][:, b].reshape(4, 8, order="F")  # (4,8)
def V(m, b): return m["v_expect"][:, b].reshape(8, 8, order="F")    # (8 places, 8 cells)

def hung(A, B):
    C = np.linalg.norm(A[:, :, None] - B[:, None, :], axis=0)
    r, c = linear_sum_assignment(C); return C[r, c].mean()

def hung_joint(xa, sa, xb, sb, w=1.0):
    A = np.vstack([xa, w * sa]); B = np.vstack([xb, w * sb]); return hung(A, B)

def part_0_1a():
    ids = [("primary", i) for i in range(5)] + [("secondary", i) for i in range(5)]
    rows = []; pos0 = {}
    for k, i in ids:
        m = cen(k, i)
        v0 = draw_v0_octave(i) if k == "primary" else secondary_v0(i)
        a0 = P_X @ softmax_cols(v0)   # expected initial position from the injected draw
        s0 = P_S @ softmax_cols(v0)
        pos0[(k, i)] = X(m, 0)
        rows.append(dict(id=f"{k}_{i:04d}", v0_std=float(v0.std()),
            pos_bin0_max_abs_vs_draw=float(np.abs(X(m, 0) - a0).max()),
            pos_bin1_max_abs_vs_draw=float(np.abs(X(m, 1) - a0).max()),
            sec_bin0_max_abs_vs_draw=float(np.abs(S_(m, 0) - s0).max()),
            pos_bin0_norm=float(np.linalg.norm(X(m, 0))), pos_bin1_norm=float(np.linalg.norm(X(m, 1))),
            sec_bin0_norm=float(np.linalg.norm(S_(m, 0))), sec_bin1_norm=float(np.linalg.norm(S_(m, 1))),
            vexp_bin0_maxlogit=float(V(m, 0).max()), vexp_bin1_maxlogit=float(V(m, 1).max()),
            vexp_bin0_vs_v0_maxabs=float(np.abs(V(m, 0) - v0).max()),
            vexp_bin1_vs_v0_maxabs=float(np.abs(V(m, 1) - v0).max()),
            pos_bin0_sample=np.round(X(m, 0)[:, :3], 3).tolist(),
            v0_draw_first_col=np.round(v0[:, 0], 3).tolist(), vexp_bin0_first_col=np.round(V(m, 0)[:, 0], 3).tolist()))
    # do the bin-0 states differ across individuals? permutation-invariant (and index-wise) pairwise
    ks = list(pos0); n = len(ks)
    D = np.array([[hung(pos0[a], pos0[b]) for b in ks] for a in ks])
    off = D[~np.eye(n, dtype=bool)]
    return dict(rows=rows, pairwise_bin0_hungarian_min=float(off.min()), median=float(np.median(off)), max=float(off.max()))

def intended_kick(kind, idx):
    from run_kicks import apply_kick, load_final_state
    a_x, a_s, v = load_final_state(f"{M1}/data/census/primary_{idx:04d}_N512.mat")
    return (a_x, a_s, v), apply_kick(kind, a_x, a_s, v, idx, idx)

def part_0_1b(n_per=5):
    kinds = ["K1_sigma0.5", "K1_sigma1.5", "K2", "K3", "K4"]
    rng = np.random.default_rng(20261001)
    rows = []
    for kind in kinds:
        picks = sorted(rng.choice(20, n_per, replace=False).tolist())
        for idx in picks:
            pre = cen("primary", idx)
            kk = sio.loadmat(f"{M1}/data/kicks/primary_{idx:04d}_{kind}_N512.mat")
            (ax, as_, v), (ax2, as2, v2, log) = intended_kick(kind, idx)
            pre_x, pre_s, pre_v = X(pre, -1), S_(pre, -1), V(pre, -1)
            # state right after the kick = bin 0 of the kicked run
            post_x, post_s, post_v = X(kk, 0), S_(kk, 0), V(kk, 0)
            rows.append(dict(kind=kind, ind=idx,
                intended_dx=float(np.linalg.norm(ax2 - ax)), measured_dx_bin0=float(np.linalg.norm(post_x - pre_x)),
                intended_ds=float(np.linalg.norm(as2 - as_)), measured_ds_bin0=float(np.linalg.norm(post_s - pre_s)),
                intended_dv=float(np.linalg.norm(v2 - v)), measured_dv_bin0=float(np.linalg.norm(post_v - pre_v)),
                max_dx_cell=float(np.linalg.norm(post_x - pre_x, axis=0).max())))
    return rows

def part_0_3a():
    ids = [("primary", i) for i in range(6)] + [("secondary", i) for i in range(4)]
    M = [cen(k, i) for k, i in ids]
    N = 512
    ts = list(range(0, N, 8)) + [N - 1]
    out = {}
    for name, w in (("geom", 0.0), ("joint_pos_sec", 1.0)):
        maxd, meand = [], []
        for b in ts:
            ds = [hung_joint(X(M[a], b), S_(M[a], b), X(M[c], b), S_(M[c], b), w)
                  for a in range(len(M)) for c in range(a + 1, len(M))]
            maxd.append(float(np.max(ds))); meand.append(float(np.mean(ds)))
        out[name] = dict(bins=ts, max=maxd, mean=meand)
    return out

def stationarity_metric(m):
    pos, sec = m["positions"], m["secretion"]
    dx = np.linalg.norm(np.diff(pos, axis=1), axis=0); ds = np.linalg.norm(np.diff(sec, axis=1), axis=0)
    return dx, ds

def part_0_3b():
    ids = [("primary", i) for i in range(6)] + [("secondary", i) for i in range(4)]
    res = []
    for k, i in ids:
        m = cen(k, i)
        dx, ds = stationarity_metric(m)
        crit = np.maximum(dx, ds)
        st = is_stationary(m)[1]
        # alternative (declared) criterion: STATE-based -- distance to the
        # FINAL state of the same run (index-wise, same cells) < 1e-3, for all later bins
        fin = m["positions"][:, -1]; fins = m["secretion"][:, -1]
        dist = np.sqrt(((m["positions"] - fin[:, None]) ** 2).sum(0) + ((m["secretion"] - fins[:, None]) ** 2).sum(0))
        alt = int(np.where(dist >= 1e-3)[0].max() + 1)
        # velocity-only criterion with 10x looser threshold
        res.append(dict(id=f"{k}_{i:04d}", m1_bin=st, alt_state_dist_lt_1e3_bin=alt,
                        vel_at_bin=[float(crit[b]) for b in (32, 64, 128, 200, 246, 300, 400, 500)]))
    return res

def part_0_4():
    roles = []
    for k, n in (("primary", 200), ("secondary", 50)):
        for i in range(n):
            m = cen(k, i)
            d, rm, ft, mm = d_target(X(m, -1), S_(m, -1))
            roles.append((f"{k}_{i:04d}", tuple(int(x) for x in rm), float(d)))
    from collections import Counter
    c = Counter(r[1] for r in roles)
    # also raw argmax-belief role map
    return dict(n=len(roles), n_distinct_hungarian=len(c), max_count=max(c.values()), counts_top=sorted(c.values(), reverse=True)[:10],
                d_target_range=[min(r[2] for r in roles), max(r[2] for r in roles)],
                roles=[(a, list(b), c_) for a, b, c_ in roles])

def part_0_5():
    rows = []
    for k, i in [("primary", 0), ("primary", 1), ("secondary", 0), ("secondary", 1)]:
        m = cen(k, i)
        v = V(m, -1); p = softmax_cols(v); x = X(m, -1)
        pred = P_X @ p
        argm = P_X[:, p.argmax(0)]
        rows.append(dict(id=f"{k}_{i:04d}", max_belief=p.max(0).round(3).tolist(),
            dist_final_to_belief_pred=np.linalg.norm(x - pred, axis=0).round(4).tolist(),
            dist_final_to_argmax=np.linalg.norm(x - argm, axis=0).round(4).tolist(),
            dist_belief_pred_to_argmax=np.linalg.norm(pred - argm, axis=0).round(4).tolist(),
            argmax_slots=p.argmax(0).tolist()))
    return rows

if __name__ == "__main__":
    which = sys.argv[1:] or ["1a", "1b", "3a", "3b", "4", "5"]
    fn = dict(zip(["1a", "1b", "3a", "3b", "4", "5"], [part_0_1a, part_0_1b, part_0_3a, part_0_3b, part_0_4, part_0_5]))
    for w in which:
        r = fn[w](); json.dump(r, open(os.path.join(OUT, f"offline_{w}.json"), "w"), indent=1); print("done", w, flush=True)
