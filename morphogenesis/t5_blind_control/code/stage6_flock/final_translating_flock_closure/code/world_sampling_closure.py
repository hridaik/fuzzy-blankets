"""Final-closure fresh state sampling. Reuses the SAME qualification rule as
Stage 6.12/6.12B/6.12C unmodified (material lineage, size in [20,80], dwell
persistence with no split/merge flag, minimum torus-aware displacement,
h_star = ROT_CCW[bearing_to_cardinal(...)]). Logic reproduced (not imported)
from world_sampling_612c.try_world, only the module docstring says so
because that source is itself a __main__-style script, not a library.

Fresh seed range 64200+, disjoint from 500-504, 61200-61399 (6.12),
62200-62399 (6.12B), 63000-63499 (6.12C pilot+confirm).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_closure as C  # noqa: E402

SEED_START = 64200
SEED_END = 64800
N_STATES = 8

DWELL_WINDOW = 20
QUALIFY_SIZE_RANGE = (20, 80)
QUALIFY_MIN_DISPLACEMENT_R = 3.0
NT_MAX_UNCONTROLLED_WORLD = 180
POOL_M = 20
K_MAX = 1


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
    C.DATA_DIR.mkdir(parents=True, exist_ok=True)
    C.LOG_DIR.mkdir(parents=True, exist_ok=True)
    timing_log = C.LOG_DIR / "world_sampling_closure.log"

    rule, frozen = C.load_frozen_rule()
    states = []
    seed = SEED_START
    n_tried = 0
    t0_run = time.time()
    while len(states) < N_STATES and seed < SEED_END:
        n_tried += 1
        t0 = time.time()
        result = try_world(seed, rule)
        dt = time.time() - t0
        status = "QUALIFIED" if result else "no-qualify"
        print(f"seed={seed}: {status} ({dt:.1f}s)", flush=True)
        with open(timing_log, "a") as f:
            f.write(f"seed={seed} status={status} dt={dt:.2f}s\n")
        if result:
            result["state_id"] = f"sclosure_{len(states):02d}_seed{seed}"
            states.append(result)
        seed += 1
    total_dt = time.time() - t0_run
    print(f"Sampled {len(states)} states from {n_tried} seeds tried in {total_dt:.1f}s")

    manifest = dict(
        seed_range=[SEED_START, SEED_END], n_states_requested=N_STATES,
        dwell_window=DWELL_WINDOW, qualify_size_range=list(QUALIFY_SIZE_RANGE),
        qualify_min_displacement_r=QUALIFY_MIN_DISPLACEMENT_R,
        nt_max_uncontrolled_world=NT_MAX_UNCONTROLLED_WORLD, pool_m=POOL_M,
        frozen_rule=frozen, n_seeds_tried=n_tried, wall_time_s=total_dt,
        states=states,
        disjoint_from=dict(seed_500_504="stage6_11", seed_61200_61399="stage6_12",
                            seed_62200_62399="stage6_12B", seed_63000_63499="stage6_12C"),
    )
    out_path = C.DATA_DIR / "state_manifest_closure.json"
    json.dump(manifest, open(out_path, "w"), indent=1)
    print("wrote", out_path)


if __name__ == "__main__":
    main()
