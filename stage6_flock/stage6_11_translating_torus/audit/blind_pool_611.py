"""Stage 6.11B item 4: blind (observable-geometry-only) exterior candidate
pool, as a comparator to `intervention_api_611.near_exterior` (which uses the
true interaction radius R and is preserved UNCHANGED, imported not
reimplemented, for reproduction of the original result only -- never called
from here to build a pool that feeds any decision).

Two blind rules, both built from positions alone (never R, FOV, or the true
live-neighbour graph):

  nearest_M_pool(members, r, L, M)      -- the M non-member birds nearest to
                                            ANY candidate member (count-based,
                                            same convention as
                                            predictive_boundary_611's own
                                            nearest-M_obs pool)
  radius_pool(members, r, L, k)         -- non-members within k * local_scale
                                            of any member (radius-based,
                                            k calibrated below)

PRIMARY = nearest_M_pool, M_probe=20. Chosen for computational-budget /
consistency-with-an-already-validated-design reasons, matching
`predictive_boundary_611.M_OBS_GRID`'s own larger value (12, 20) -- NOT by
maximizing true-causal-parent recall (that would violate the task brief's
explicit prohibition). M_probe=12 and 30 are reported as disclosed
sensitivity alternatives, same convention as M_OBS_GRID.

The secondary radius rule's k is calibrated purely to land near the same
MEDIAN pool size as the primary rule on uncontrolled development data (a
computational-budget matching exercise, not a recall-maximizing one) --
`calibrate_radius_k()` below.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

AUDIT_DIR = Path(__file__).resolve().parent
CODE_DIR = AUDIT_DIR.parent / "code"
sys.path.insert(0, str(AUDIT_DIR))
sys.path.insert(0, str(CODE_DIR))
import common_611  # noqa: E402,F401

from common_611 import DATA_DIR, L_BOX, dump_json  # noqa: E402
from flock_sim.model import UV4  # noqa: E402
from detect_69 import propose  # noqa: E402
from geometry_611 import torus_delta, local_scale  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402
from intervention_api_611 import near_exterior  # noqa: E402  (ORACLE, reproduction only)

M_PROBE_GRID = (12, 20, 30)
M_PROBE_PRIMARY = 20


def nearest_M_pool(members: np.ndarray, r: np.ndarray, L: float, M: int) -> list[int]:
    member_set = set(int(m) for m in members)
    non_members = np.array([i for i in range(len(r)) if i not in member_set])
    if len(non_members) == 0:
        return []
    d = torus_delta(r[members][:, None, :], r[non_members][None, :, :], L)
    D = np.sqrt((d ** 2).sum(-1)).min(axis=0)   # each non-member's distance to its NEAREST member
    order = np.argsort(D)[:M]
    return sorted(int(x) for x in non_members[order])


def radius_pool(members: np.ndarray, r: np.ndarray, L: float, k: float) -> list[int]:
    member_set = set(int(m) for m in members)
    non_members = np.array([i for i in range(len(r)) if i not in member_set])
    if len(non_members) == 0:
        return []
    radius = k * local_scale(r, L)
    d = torus_delta(r[members][:, None, :], r[non_members][None, :, :], L)
    D = np.sqrt((d ** 2).sum(-1))
    near = (D <= radius).any(axis=0)
    return sorted(int(x) for x in non_members[near])


def calibrate_radius_k(target_median: int = M_PROBE_PRIMARY, n_episodes: int = 6) -> dict:
    d = np.load(DATA_DIR / "observational_corpus_611__train.npz")
    episodes = [dict(r_hist=d["r_hist"][k], z_hist=d["z_hist"][k]) for k in range(n_episodes)]
    candidates_snaps = []
    for ep in episodes:
        r_hist, z_hist = ep["r_hist"], ep["z_hist"]
        z_window = []
        for t in range(0, r_hist.shape[0], 10):
            z_window.append(z_hist[t])
            if len(z_window) > 6:
                z_window.pop(0)
            if len(z_window) < 2:
                continue
            cands = propose(r_hist[t], z_window, L_BOX)
            if cands:
                candidates_snaps.append((cands[0], r_hist[t]))

    results = {}
    for k in (5, 10, 20, 40, 60, 80, 100):
        sizes = [len(radius_pool(members, r, L_BOX, k)) for members, r in candidates_snaps]
        results[k] = float(np.median(sizes))
    best_k = min(results, key=lambda k: abs(results[k] - target_median))
    return dict(grid=results, chosen_k=best_k, chosen_k_median_pool_size=results[best_k],
                 target_median=target_median, n_snapshots=len(candidates_snaps))


def recall_report(members: np.ndarray, r: np.ndarray, z: np.ndarray, mf, L: float) -> dict:
    n_exterior = len(z) - len(members)
    B_D_true = set(int(x) for x in mf.oracle_B_D(r, z, members))
    out = dict(n_exterior=n_exterior, n_true_direct_parents_total=len(B_D_true))
    for M in M_PROBE_GRID:
        pool = nearest_M_pool(members, r, L, M)
        inter = len(set(pool) & B_D_true)
        out[f"nearest_M{M}"] = dict(n_pool=len(pool),
                                       n_true_parents_in_pool=inter,
                                       max_attainable_recall=(inter / len(B_D_true)) if B_D_true else 1.0)
    oracle_pool = near_exterior(mf, r, members, radius_factor=3.0)   # reproduction only, not used downstream
    inter_o = len(set(oracle_pool) & B_D_true)
    out["oracle_near_exterior_3R_reproduction_only"] = dict(
        n_pool=len(oracle_pool), n_true_parents_in_pool=inter_o,
        max_attainable_recall=(inter_o / len(B_D_true)) if B_D_true else 1.0)
    return out


def main():
    print("[blind_pool] calibrating radius rule's k on uncontrolled dev data...", flush=True)
    k_cal = calibrate_radius_k()
    print(f"  {k_cal}", flush=True)

    print("[blind_pool] recall report: dev snapshots + all 5 online seeds' control-window snapshots", flush=True)
    mf = ROC.make_flock()
    reports = []

    d = np.load(DATA_DIR / "observational_corpus_611__val.npz")
    for k in range(6):
        r_hist, z_hist = d["r_hist"][k], d["z_hist"][k]
        t0 = 90
        z_window = [z_hist[max(0, t0 - i)] for i in range(5, -1, -1)]
        cands = propose(r_hist[t0], z_window, L_BOX)
        if not cands:
            continue
        rep = recall_report(cands[0], r_hist[t0], z_hist[t0], mf, L_BOX)
        rep.update(source=f"dev_val_ep{k}_t{t0}")
        reports.append(rep)

    for seed in (500, 501, 502, 503, 504):
        viz = json.load(open(DATA_DIR / f"viz_bundle_611__seed{seed}.json"))
        control_frames = [f for f in viz["frames"] if f["phase"] == "control"]
        for frame in control_frames[::4]:   # every 4th control-phase frame, tractability
            r = np.array(frame["r"]); z = np.array(frame["z"], dtype=int)
            interior = np.array(frame["interior"], dtype=int)
            if len(interior) == 0:
                continue
            rep = recall_report(interior, r, z, mf, L_BOX)
            rep.update(source=f"seed{seed}_t{frame['t']}")
            reports.append(rep)

    def agg(key_path):
        vals = [r[key_path]["max_attainable_recall"] for r in reports if key_path in r]
        return float(np.mean(vals)) if vals else None

    summary = dict(
        radius_rule_calibration=k_cal,
        n_snapshots=len(reports),
        mean_max_attainable_recall=dict(
            nearest_M12=agg("nearest_M12"), nearest_M20=agg("nearest_M20"), nearest_M30=agg("nearest_M30"),
            oracle_3R_reproduction=agg("oracle_near_exterior_3R_reproduction_only")),
        mean_pool_size=dict(
            nearest_M12=float(np.mean([r["nearest_M12"]["n_pool"] for r in reports])),
            nearest_M20=float(np.mean([r["nearest_M20"]["n_pool"] for r in reports])),
            nearest_M30=float(np.mean([r["nearest_M30"]["n_pool"] for r in reports])),
            oracle_3R=float(np.mean([r["oracle_near_exterior_3R_reproduction_only"]["n_pool"] for r in reports]))),
    )
    dump_json(dict(summary=summary, reports=reports), AUDIT_DIR / "blind_pool_611.json")
    print(json.dumps(summary, indent=1, default=str))


if __name__ == "__main__":
    main()
