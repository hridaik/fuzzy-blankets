"""Stage 6.12B fresh state sampling. Same qualification rule as Stage
6.12 (`world_sampling_612.py`, reused not reimplemented for the core
qualification logic) -- material lineage exists, size in [20,80], dwell
persistence with no split/merge flag, minimum torus-aware displacement,
h_star = ROT_CCW[bearing_to_cardinal(...)]. NEW seed range, never
overlapping Stage 6.12's 61200-61399 or seeds 500-504.

DISCLOSED REDUCTION from the task brief's practical target (>=12 dev,
>=6 holdout): given Stage 6.12's measured cost and Stage 6.12B's much
larger per-state workload (exhaustive K=1/K=2 search, S6.12B-A; refresh
strategy comparison, S6.12B-B), this run uses N_DEV=3, N_HOLDOUT=2 (5
states total). See EXPERIMENT_SPEC.md's compute plan for the runtime
benchmarking that motivated this number -- exhaustive set coverage and the
q/strategy grid structure are preserved in full; STATE COUNT is what is
cut, exactly as Stage 6.12's own precedent.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C  # noqa: E402

SEED_START = 62200
SEED_END = 62400
N_DEV = 3
N_HOLDOUT = 2
DWELL_WINDOW = 20
QUALIFY_SIZE_RANGE = (20, 80)
QUALIFY_MIN_DISPLACEMENT_R = 3.0
NT_MAX_UNCONTROLLED_WORLD = 180
POOL_M = 20
K_MAX = 8

OUT_PATH = C.DATA_DIR / "state_manifest_612b.json"
TIMING_LOG = C.LOG_DIR / "timing_612b.txt"


def try_world(seed: int, rule):
    mf = C.make_flock()
    rng = np.random.default_rng(seed)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)

    z_window: list[np.ndarray] = []
    ring: list = []
    tr = None
    seed_t = None

    for t in range(NT_MAX_UNCONTROLLED_WORLD):
        z_window.append(z.copy())
        if len(z_window) > C.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = C.detect_propose(r, z_window, C.L_BOX) if len(z_window) >= 2 else []
        cands = [frozenset(int(x) for x in c) for c in cands]

        if tr is None and cands:
            tr = C.ForwardMaterialTrace611(rule)
            tr.start(t, cands[0])
            seed_t = t
        elif tr is not None:
            d = tr.step(t, cands)
            if d.status == "dead":
                tr = None

        ring.append((t, r.copy(), z.copy(), (tr.accepted if tr else None)))
        if len(ring) > DWELL_WINDOW + C.AFFINITY_WINDOW + 2:
            ring.pop(0)

        if tr is not None and tr.status == "continuing" and seed_t is not None and (t - seed_t) >= DWELL_WINDOW - 1:
            window = tr.history[-DWELL_WINDOW:]
            sizes_ok = all(QUALIFY_SIZE_RANGE[0] <= len(h.accepted_members) <= QUALIFY_SIZE_RANGE[1] for h in window)
            statuses_ok = all(h.status == "continuing" and not h.split_flag and not h.merge_flag for h in window)
            if sizes_ok and statuses_ok:
                t_start_dwell = window[0].t
                ring_at_start = next((e for e in ring if e[0] == t_start_dwell), None)
                if ring_at_start is not None:
                    _, r_start, _, members_start = ring_at_start
                    members_now = tr.accepted
                    common = members_start & members_now if members_start else members_now
                    if len(common) >= 5:
                        cen_start = C.bulk_centroid(r_start, common, C.L_BOX)
                        cen_now = C.bulk_centroid(r, common, C.L_BOX)
                        delta = C.torus_delta(cen_now[None, :], cen_start[None, :], C.L_BOX)[0]
                        disp = float(np.hypot(*delta))
                        if disp >= QUALIFY_MIN_DISPLACEMENT_R * C.R_PRIMARY:
                            cur_dir = C.bearing_to_cardinal(delta)
                            h_star = int(C.ROT_CCW[cur_dir])
                            interior0 = sorted(int(x) for x in members_now)
                            pool20 = C.nearest_M_pool(np.array(interior0), r, C.L_BOX, POOL_M)
                            if len(pool20) >= K_MAX:
                                ctx_start_t = max(0, t - C.AFFINITY_WINDOW + 1)
                                z_context = [e[2] for e in ring if ctx_start_t <= e[0] < t]
                                return dict(
                                    seed=seed, t0=t, interior0=interior0, h_star=h_star,
                                    cur_dir=int(cur_dir), displacement=disp,
                                    r0=r.tolist(), z0=z.tolist(), pool20=pool20,
                                    z_context=[zc.tolist() for zc in z_context],
                                )
        r, z, _ = mf.step(r, z, rng)
    return None


def main():
    rule, frozen = C.load_frozen_rule()
    states = []
    seed = SEED_START
    n_tried = 0
    import time
    t0_run = time.time()
    while len(states) < (N_DEV + N_HOLDOUT) and seed < SEED_END:
        n_tried += 1
        t0 = time.time()
        result = try_world(seed, rule)
        dt = time.time() - t0
        status = "QUALIFIED" if result else "no-qualify"
        print(f"seed={seed}: {status} ({dt:.1f}s)", flush=True)
        with open(TIMING_LOG, "a") as f:
            f.write(f"seed={seed} status={status} dt={dt:.2f}s\n")
        if result:
            role = "development" if len(states) < N_DEV else "holdout"
            result["state_id"] = f"s612b_{len(states):02d}_seed{seed}"
            result["role"] = role
            states.append(result)
        seed += 1
    total_dt = time.time() - t0_run
    print(f"Sampled {len(states)} states from {n_tried} seeds in {total_dt:.1f}s")

    manifest = dict(frozen_rule=frozen, seed_range=[SEED_START, SEED_END], n_dev=N_DEV, n_holdout=N_HOLDOUT,
                     dwell_window=DWELL_WINDOW, qualify_size_range=list(QUALIFY_SIZE_RANGE),
                     qualify_min_displacement_r=QUALIFY_MIN_DISPLACEMENT_R,
                     nt_max_uncontrolled_world=NT_MAX_UNCONTROLLED_WORLD, pool_m=POOL_M,
                     n_seeds_tried=n_tried, wall_time_s=total_dt, states=states)
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(manifest, open(OUT_PATH, "w"), indent=1)
    print("wrote", OUT_PATH)


if __name__ == "__main__":
    main()
