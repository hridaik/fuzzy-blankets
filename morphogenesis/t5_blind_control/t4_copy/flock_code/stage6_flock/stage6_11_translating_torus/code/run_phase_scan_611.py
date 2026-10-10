"""Stage 6.11 Section O -- uncontrolled-phenomenology (R, v, cohesion) screen
and Section P natural-emergence check.

EVALUATION-SIDE / PRIVILEGED. Implements exactly the procedure predeclared in
`logs/regime_selection_predeclared_611.txt`, written and committed before this
script was run. Every threshold used here is quoted from that file, not
invented inline.

Usage:
    python run_phase_scan_611.py --stage a   # coarse dev screen (Section 4a)
    python run_phase_scan_611.py --stage b --cells R,v,c [...]   # held-out confirmation (4b)
"""
from __future__ import annotations

import argparse
import itertools
import time

import numpy as np

from common_611 import (
    N_BIRDS, L_BOX, BETA_610, S_610, resolved_params, dump_json, DATA_DIR, LOG_DIR,
)
from moving_flock_611 import MovingFlock611
import phase_metrics_611 as pm611

# ---- predeclared constants (regime_selection_predeclared_611.txt) ----------
NT = 240
BURN_IN = 60
POL_THRESH, FRAC_THRESH, MIN_RUN = 0.90, 0.80, 20
SENSITIVITY = {
    "loose": (0.85, 0.75, 15),
    "primary": (POL_THRESH, FRAC_THRESH, MIN_RUN),
    "strict": (0.95, 0.85, 25),
}
DOM_MIN_DURATION = 30
DOM_SIZE_RANGE = (0.05, 0.50)
DOM_SIZE_FRAC_STEPS = 0.80
DOM_MIN_DISPLACEMENT_R = 3.0
MESO_FRAC_THRESH = 0.20
COLLAPSE_PROB_THRESH = 0.05

DEV_SEEDS = [0, 1, 2, 3]
HELDOUT_SEEDS = list(range(100, 120))

R_GRID = [0.7, 0.9, 1.1, 1.3]
V_GRID = [0.14, 0.28, 0.42]
COHESION_GRID = [0.0, 1.0, 2.0]


def wrap_delta(a: np.ndarray, b: np.ndarray, L: float) -> np.ndarray:
    return (a - b + L / 2.0) % L - L / 2.0


def wrapped_centroid(r_members: np.ndarray, L: float) -> np.ndarray:
    ref = r_members[0]
    rel = wrap_delta(r_members, ref, L)
    return (ref + rel.mean(axis=0)) % L


def analyze_episode(r_hist: np.ndarray, z_hist: np.ndarray, L: float, R: float,
                     mf: MovingFlock611, burn_in: int = BURN_IN, nt: int = NT,
                     sat_sample_every: int = 10) -> dict:
    uv4 = mf.pm.UV4 if hasattr(mf.pm, "UV4") else None
    from flock_sim.model import UV4 as _UV4
    uv4 = _UV4

    steps = list(range(burn_in, nt))
    pol_series, frac_series, domsize_series = [], [], []
    comp_series = []
    sat_frac = []
    for t in steps:
        r, z = r_hist[t], z_hist[t]
        pol_series.append(pm611.polarization(z, uv4))
        comps = pm611.coherent_components(r, z, L, R, heading_match=True)
        comp_series.append(comps)
        frac_series.append(pm611.largest_component_fraction(comps, len(z)))
        domsize_series.append(pm611.domain_size_fractions(comps, len(z)))
        if (t - burn_in) % sat_sample_every == 0:
            u = mf.policy(r, z)
            sat_frac.append(pm611.policy_saturation_fraction(u))

    collapse = {}
    for label, (pth, fth, mr) in SENSITIVITY.items():
        runs = pm611.global_collapse_runs(pol_series, frac_series, pth, fth, mr)
        collapse[label] = dict(collapsed=len(runs) > 0, n_runs=len(runs),
                                total_steps_in_collapse=sum(e - s for s, e in runs))

    # -- domain lifetime / displacement tracking (world-selection proxy) --
    N = z_hist.shape[1]
    active: dict[int, dict] = {}
    next_id = 0
    finished: list[dict] = []
    for k, comps in enumerate(comp_series):
        comps = [c for c in comps if len(c) >= 3]
        r_t = r_hist[steps[k]]
        used_prev, used_cur = set(), set()
        pairs = []
        for did, rec in active.items():
            for ci, cmem in enumerate(comps):
                j = pm611.jaccard(rec["members"], cmem)
                if j >= 0.3:
                    pairs.append((j, did, ci))
        pairs.sort(reverse=True)
        new_active = {}
        for j, did, ci in pairs:
            if did in used_prev or ci in used_cur:
                continue
            used_prev.add(did); used_cur.add(ci)
            rec = active[did]
            cmem = comps[ci]
            c_new = wrapped_centroid(r_t[cmem], L)
            rec["centroid_unwrapped"] = rec["centroid_unwrapped"] + wrap_delta(c_new, rec["last_centroid"], L)
            rec["last_centroid"] = c_new
            rec["duration"] += 1
            rec["size_fracs"].append(len(cmem) / N)
            rec["members"] = cmem
            new_active[did] = rec
        for did, rec in active.items():
            if did not in used_prev:
                finished.append(rec)
        for ci, cmem in enumerate(comps):
            if ci not in used_cur:
                c0 = wrapped_centroid(r_t[cmem], L)
                new_active[next_id] = dict(members=cmem, duration=1, size_fracs=[len(cmem) / N],
                                            last_centroid=c0, centroid_unwrapped=np.zeros(2))
                next_id += 1
        active = new_active
    finished.extend(active.values())

    qualifying = 0
    domain_records = []
    for rec in finished:
        disp = float(np.hypot(*rec["centroid_unwrapped"]))
        size_ok_frac = float(np.mean([DOM_SIZE_RANGE[0] <= s <= DOM_SIZE_RANGE[1] for s in rec["size_fracs"]]))
        qualifies = (rec["duration"] >= DOM_MIN_DURATION and size_ok_frac >= DOM_SIZE_FRAC_STEPS
                     and disp >= DOM_MIN_DISPLACEMENT_R * R)
        if qualifies:
            qualifying += 1
        domain_records.append(dict(duration=rec["duration"], size_ok_frac=size_ok_frac,
                                    displacement=disp, displacement_in_R=disp / R, qualifies=qualifies))

    return dict(
        n_measured_steps=len(steps),
        mean_polarization=float(np.mean(pol_series)),
        mean_largest_frac=float(np.mean(frac_series)),
        mean_n_domains_size_ge3=float(np.mean([len(d) for d in domsize_series])),
        mean_policy_saturation=float(np.mean(sat_frac)) if sat_frac else None,
        collapse=collapse,
        n_domains_tracked=len(finished),
        n_domains_qualifying=qualifying,
        has_mesoscopic=qualifying > 0,
        domain_records=domain_records,
    )


def run_cell(R: float, v: float, cohesion: float, seeds: list[int], social: str = "raw") -> dict:
    ep_results = []
    t0 = time.time()
    for seed in seeds:
        pm = resolved_params(BETA_610, S_610)
        mf = MovingFlock611(N=N_BIRDS, L=L_BOX, R=R, v=v, params=pm,
                             social=social, cohesion=cohesion)
        res = mf.run(nt=NT, seed=seed)
        ep_results.append(analyze_episode(res.r_hist, res.z_hist, L_BOX, R, mf,
                                           burn_in=BURN_IN, nt=NT))
    wall = time.time() - t0

    meso_frac = float(np.mean([e["has_mesoscopic"] for e in ep_results]))
    collapse_prob = {label: float(np.mean([e["collapse"][label]["collapsed"] for e in ep_results]))
                      for label in SENSITIVITY}
    is_candidate = (meso_frac >= MESO_FRAC_THRESH and collapse_prob["primary"] <= COLLAPSE_PROB_THRESH)
    return dict(
        R=R, v=v, cohesion=cohesion, social=social, seeds=seeds, wall_time_s=wall,
        mesoscopic_episode_fraction=meso_frac,
        collapse_probability=collapse_prob,
        mean_policy_saturation=float(np.mean([e["mean_policy_saturation"] for e in ep_results
                                               if e["mean_policy_saturation"] is not None])),
        is_world_selection_candidate=is_candidate,
        episodes=ep_results,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["a", "b"], default="a")
    ap.add_argument("--R", type=float, default=None)
    ap.add_argument("--v", type=float, default=None)
    ap.add_argument("--cohesion", type=float, default=None)
    ap.add_argument("--out", type=str, default=None)
    args = ap.parse_args()

    if args.stage == "a":
        cells = []
        grid = list(itertools.product(R_GRID, V_GRID, COHESION_GRID))
        print(f"[phase_scan_611] stage a: {len(grid)} cells x {len(DEV_SEEDS)} dev seeds, nt={NT}")
        for i, (R, v, c) in enumerate(grid):
            cell = run_cell(R, v, c, DEV_SEEDS)
            cells.append(cell)
            print(f"  [{i+1}/{len(grid)}] R={R} v={v} coh={c}: "
                  f"meso_frac={cell['mesoscopic_episode_fraction']:.2f} "
                  f"collapse_p={cell['collapse_probability']['primary']:.2f} "
                  f"sat={cell['mean_policy_saturation']:.3f} "
                  f"candidate={cell['is_world_selection_candidate']} "
                  f"({cell['wall_time_s']:.1f}s)")
        out = dict(stage="a", nt=NT, burn_in=BURN_IN, beta=BETA_610, s=S_610,
                   N=N_BIRDS, L=L_BOX, dev_seeds=DEV_SEEDS, cells=cells)
        path = DATA_DIR / "phase_scan_611__stage_a.json"
        dump_json(out, path)
        print(f"[phase_scan_611] wrote {path}")
    else:
        assert args.R is not None and args.v is not None and args.cohesion is not None
        print(f"[phase_scan_611] stage b (held-out confirmation): R={args.R} v={args.v} coh={args.cohesion}, "
              f"{len(HELDOUT_SEEDS)} seeds")
        cell = run_cell(args.R, args.v, args.cohesion, HELDOUT_SEEDS)
        print(f"  meso_frac={cell['mesoscopic_episode_fraction']:.2f} "
              f"collapse_p={cell['collapse_probability']} sat={cell['mean_policy_saturation']:.3f} "
              f"confirmed={cell['is_world_selection_candidate']}")
        out = dict(stage="b", nt=NT, burn_in=BURN_IN, beta=BETA_610, s=S_610,
                   N=N_BIRDS, L=L_BOX, heldout_seeds=HELDOUT_SEEDS, cell=cell)
        name = args.out or f"phase_scan_611__stage_b_R{args.R}_v{args.v}_c{args.cohesion}.json"
        path = DATA_DIR / name
        dump_json(out, path)
        print(f"[phase_scan_611] wrote {path}")


if __name__ == "__main__":
    main()
