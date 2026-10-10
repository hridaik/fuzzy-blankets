"""Stage 6.11 online loop, translation task, adaptive control, and release
(task brief items 14-17).

EVALUATION-SIDE ORCHESTRATION SCRIPT. Drives the real simulator step by step
and therefore legitimately touches MovingFlock611 directly -- but every
DECISION (candidate detection, lineage/interior selection, B^pred, B^causal,
B^C, actuator ranking) is delegated to the inference-side modules
(detect_69.propose, lineage_611.LineageTracker611, predictive_boundary_611,
probing_611, control_authority_611), each of which receives only observed
positions/headings (or, for probing/authority, a duck-typed probe object)
-- never the simulator itself.

Loop, per step (task brief item 14):

    Y_{0:t} -> candidates -> hat I_t -> Bhat^pred_t -> Bhat^causal_t
             -> Ahat_t -> S_t -> u_t -> Y_{t+1}

Phase 1 (uncontrolled): run from a random start; re-detect and update the
lineage tracker every step; do NOT introduce a target until a qualifying
collective has spontaneously emerged, persisted, and translated several
interaction-length scales (item 15) -- the SAME "qualifying domain" logic as
Section O/P's world-selection screen, but now applied ONLINE to the
observer's own OWN blind lineage tracker (never to the privileged
phase_metrics_611 oracle).

Phase 2 (control): target = the adjacent 90-degree cardinal direction of the
lineage's own OBSERVED bulk-translation direction (never the simulator's
true velocity). Actuators are chosen from B^C (control_authority_611,
tau-horizon signed authority) among birds OUTSIDE the current interior.

Phase 3 (release, item 17): remove all intervention, continue observing, and
check whether the lineage persists in the new direction on its own.
"""
from __future__ import annotations

import gc
import pickle

import numpy as np

from common_611 import (
    N_BIRDS, L_BOX, BETA_610, S_610, resolved_params,
    R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY,
    DATA_DIR, dump_json,
)
from moving_flock_611 import MovingFlock611
from flock_sim.model import UV4, ROT_CW, ROT_CCW
from detect_69 import propose
from lineage_611 import LineageTracker611
from geometry_611 import local_scale
import predictive_boundary_611 as PB
import probing_611 as PR
from intervention_api_611 import FiniteProbeMoving611, MultiStepAuthorityProbe, near_exterior
import control_authority_611 as CA

# ---- predeclared online-loop constants -------------------------------
NT_MAX_UNCONTROLLED = 260          # give up searching for emergence after this many steps
QUALIFY_MIN_DURATION = 30          # same rule as Section O's world-selection screen
QUALIFY_SIZE_RANGE = (0.05, 0.50)
QUALIFY_MIN_DISPLACEMENT_R = 3.0
AFFINITY_WINDOW = 6                # detect_69.W_AFFINITY

T_CONTROL = 24
T_RELEASE = 24
REINFER_PRED_EVERY = 12
REINFER_CAUSAL_EVERY = 8
REINFER_AUTHORITY_EVERY = 8
K_ACT = 8
TAU_CONTROL = 4
PROBE_ROLLOUTS_ONLINE = 20     # reduced from the Stage 6.10 reference (40) for this
PROBE_REPEATS_ONLINE = 2       # session's memory-constrained environment; see
AUTHORITY_ROLLOUTS_ONLINE = 10 # run_causal_budget_sensitivity_611.py for the full-budget check


def make_flock(seed_unused=None) -> MovingFlock611:
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                           social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def load_pretrained_model(M_obs: int = 12):
    """Loads the model `run_predictive_boundary_611.py` already fit and
    persisted -- avoids rebuilding the whole corpus and refitting inside a
    live episode (a real memory/time blowup the first version of this script
    hit). Falls back to rebuilding from the raw corpus only if the pickle
    isn't present yet."""
    pkl_path = DATA_DIR / "pretrained_relational_model_611.pkl"
    if pkl_path.exists():
        with open(pkl_path, "rb") as f:
            d = pickle.load(f)
        assert d["M_obs"] == M_obs
        return d["model"], d["train_rows_sample"], d["dist_cuts"]

    d = np.load(DATA_DIR / "observational_corpus_611__train.npz")
    train = [dict(r_hist=d["r_hist"][k], z_hist=d["z_hist"][k]) for k in range(len(d["seeds"]))]
    rng = np.random.default_rng(7)
    dist_cuts = PB.estimate_distance_cuts(train[0]["r_hist"], train[0]["z_hist"], L_BOX, M_obs, rng)
    base_rows = PB.build_rows_multi(train, L_BOX, M_obs, dist_cuts, rng, max_rows_per_episode=400)
    model = PB.RelationalHeadingModel(M_obs=M_obs, dist_cuts=dist_cuts, L=L_BOX)
    model.fit(base_rows)
    return model, base_rows, dist_cuts


def dominant_interior(tracker: LineageTracker611) -> np.ndarray | None:
    if not tracker.hypotheses:
        return None
    return max(tracker.hypotheses, key=lambda h: h.prob).members


def bearing_to_cardinal(delta: np.ndarray) -> int:
    """Nearest of the 4 cardinal UV4 directions to an observed bulk-delta
    vector -- purely a function of the lineage's OWN estimated translation,
    never the simulator's true velocity."""
    return int(np.argmax(UV4 @ delta))


def run_episode(seed: int, model, base_rows, dist_cuts, M_obs: int = 12,
                 record_trajectory: bool = False) -> dict:
    mf = make_flock()
    rng = np.random.default_rng(seed)
    r = rng.random((mf.N, 2)) * mf.L
    z = rng.integers(0, 4, mf.N)

    tracker: LineageTracker611 | None = None
    z_window: list[np.ndarray] = []
    online_buffer: list[PB.Row] = []
    ONLINE_BUFFER_CAP = 3000
    r_snap_window: list[np.ndarray] = []          # rolling raw (r, z) trajectory window,
    z_snap_window: list[np.ndarray] = []          # used to build genuine labelled transitions
    SNAP_WINDOW = 20                              # for periphery boundary construction (item 14)
    log = []
    trajectory = [] if record_trajectory else None

    def step_world(forced=None):
        nonlocal r, z
        r_prev, z_prev = r.copy(), z.copy()
        r, z, _ = mf.step(r, z, rng, forced_actions=forced)
        # append the newly observed transition to the online passive-model buffer
        # (a modest per-step subsample to bound growth, item 5/14), capped in size
        idx = rng.choice(mf.N, size=min(20, mf.N), replace=False)
        for i in idx:
            hist, pool_idx, cats = PB.pool_and_histogram(r_prev, z_prev, int(i), L_BOX, dist_cuts, M_obs)
            online_buffer.append(PB.Row(t=-1, i=int(i), z_i=int(z_prev[i]), hist=hist,
                                          label=int(z[i]), pool_idx=pool_idx, pool_cat=cats))
        if len(online_buffer) > ONLINE_BUFFER_CAP:
            del online_buffer[: len(online_buffer) - ONLINE_BUFFER_CAP]
        r_snap_window.append(r_prev)
        z_snap_window.append(z_prev)
        if len(r_snap_window) > SNAP_WINDOW + 1:
            r_snap_window.pop(0)
            z_snap_window.pop(0)
        return r_prev, z_prev

    phase = "uncontrolled"
    interior = None
    target_heading = None
    B_pred_cache, B_causal_cache, B_C_cache = None, None, None
    age_pred = age_causal = age_authority = 0
    control_step = 0
    release_step = 0
    t = 0

    while t < NT_MAX_UNCONTROLLED + T_CONTROL + T_RELEASE:
        z_window.append(z.copy())
        if len(z_window) > AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r, z_window, L_BOX) if len(z_window) >= 2 else []

        if tracker is None and cands:
            tracker = LineageTracker611(L=L_BOX, uv4=UV4)
            tracker.start(cands[0], r, z, t)
        elif tracker is not None:
            tracker.update(cands, r, z, t)
            if not tracker.hypotheses and cands:
                tracker = LineageTracker611(L=L_BOX, uv4=UV4)
                tracker.start(cands[0], r, z, t)

        interior = dominant_interior(tracker) if tracker is not None else None

        if phase == "uncontrolled":
            if interior is not None and t >= NT_MAX_UNCONTROLLED:
                log.append(dict(t=t, event="stop_condition_no_emergence"))
                break
            if tracker is not None and tracker.hypotheses:
                h = max(tracker.hypotheses, key=lambda h: h.prob)
                recs = h.records
                if len(recs) >= QUALIFY_MIN_DURATION:
                    recent = recs[-QUALIFY_MIN_DURATION:]
                    size_ok = np.mean([QUALIFY_SIZE_RANGE[0] <= r_["size"] / mf.N <= QUALIFY_SIZE_RANGE[1]
                                        for r_ in recent]) >= 0.8
                    disp = float(np.hypot(*np.sum([r_.get("bulk_delta", [0, 0]) for r_ in recent], axis=0)))
                    if size_ok and disp >= QUALIFY_MIN_DISPLACEMENT_R * R_PRIMARY:
                        bulk_delta = np.sum([r_.get("bulk_delta", [0, 0]) for r_ in recent], axis=0)
                        cur_dir = bearing_to_cardinal(bulk_delta)
                        target_heading = int(ROT_CCW[cur_dir])
                        phase = "control"
                        control_step = 0
                        log.append(dict(t=t, event="qualified_and_target_set", cur_dir=cur_dir,
                                         target_heading=target_heading, displacement=disp))

        forced = None
        if phase == "control" and interior is not None:
            need_pred = (B_pred_cache is None) or (age_pred >= REINFER_PRED_EVERY)
            need_causal = (B_causal_cache is None) or (age_causal >= REINFER_CAUSAL_EVERY)
            need_auth = (B_C_cache is None) or (age_authority >= REINFER_AUTHORITY_EVERY)

            if need_pred:
                periphery_radius = local_scale(r, L_BOX)
                # genuine labelled transitions from the ACTUAL observed trajectory
                # so far (rolling window + current state) -- rows_for_targets needs
                # real (t -> t+1) pairs, not a single snapshot with no known label.
                if len(r_snap_window) >= 1:
                    ep_recent = dict(r_hist=np.stack(r_snap_window + [r]),
                                      z_hist=np.stack(z_snap_window + [z]))
                    construct_rows = PB.rows_for_targets([ep_recent], interior, L_BOX, M_obs, dist_cuts,
                                                           periphery_radius, rng, max_rows_total=600)
                else:
                    construct_rows = []
                if len(base_rows) + len(online_buffer) and control_step % (REINFER_PRED_EVERY * 3) == 0:
                    model.refit_with_buffer(base_rows, online_buffer[-4000:])
                B_pred_cache = PB.construct_boundary(model, interior, construct_rows) if construct_rows else B_pred_cache
                age_pred = 0
            else:
                age_pred += 1

            exterior_pool = near_exterior(mf, r, interior, radius_factor=3.0)
            if need_causal:
                probes = [FiniteProbeMoving611(mf, r, n_rollouts=PROBE_ROLLOUTS_ONLINE, seed=1000 + t + rep)
                          for rep in range(PROBE_REPEATS_ONLINE)]
                B_causal_cache = PR.probe_sources(probes, interior, exterior_pool, z, rng, n_boot=100)
                age_causal = 0
            else:
                age_causal += 1

            if need_auth:
                auth_probe = MultiStepAuthorityProbe(mf, r, z, tau=TAU_CONTROL,
                                                       n_rollouts=AUTHORITY_ROLLOUTS_ONLINE, seed=2000 + t)
                B_C_cache = CA.select_actuators(auth_probe, interior, exterior_pool, target_heading, k_act=K_ACT)
                age_authority = 0
            else:
                age_authority += 1

            forced = {j: target_heading for j in B_C_cache["B_C"]} if B_C_cache else None
            control_step += 1
            log.append(dict(t=t, event="control_step", control_step=control_step,
                             B_pred=B_pred_cache["B"] if B_pred_cache else None,
                             B_causal=B_causal_cache["B_causal"] if B_causal_cache else None,
                             B_C=B_C_cache["B_C"] if B_C_cache else None,
                             age_pred=age_pred, age_causal=age_causal, age_authority=age_authority,
                             interior_size=len(interior),
                             frac_interior_at_target=float((z[interior] == target_heading).mean())))
            if control_step >= T_CONTROL:
                phase = "release"
                release_step = 0
                log.append(dict(t=t, event="release_begin"))

        elif phase == "release":
            release_step += 1
            log.append(dict(t=t, event="release_step", release_step=release_step,
                             interior_size=(len(interior) if interior is not None else 0),
                             frac_interior_at_target=(float((z[interior] == target_heading).mean())
                                                       if interior is not None and target_heading is not None
                                                       else None)))
            if release_step >= T_RELEASE:
                log.append(dict(t=t, event="episode_end"))
                break

        if trajectory is not None:
            trajectory.append(dict(
                t=t, r=r.tolist(), z=z.tolist(), phase=phase,
                interior=(interior.tolist() if interior is not None else []),
                actuators=(B_C_cache["B_C"] if phase == "control" and B_C_cache else []),
                target_heading=target_heading,
            ))

        step_world(forced)
        t += 1
        if t % 20 == 0:
            gc.collect()
            print(f"  [t={t}] phase={phase} interior={len(interior) if interior is not None else None}",
                  flush=True)

    result = dict(seed=seed, log=log, ended_phase=phase, final_t=t)
    if trajectory is not None:
        result["trajectory"] = trajectory
        result["L"] = L_BOX
    return result


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=500)
    args = ap.parse_args()

    print("[run_online_control_611] loading pretrained relational model...", flush=True)
    model, base_rows, dist_cuts = load_pretrained_model(M_obs=12)
    print(f"[run_online_control_611] pretrained on {len(base_rows)} rows", flush=True)
    result = run_episode(seed=args.seed, model=model, base_rows=base_rows, dist_cuts=dist_cuts, M_obs=12)
    print(f"[run_online_control_611] episode ended: phase={result['ended_phase']} t={result['final_t']}")
    events = [e["event"] for e in result["log"]]
    for name in ("qualified_and_target_set", "release_begin", "episode_end", "stop_condition_no_emergence"):
        if name in events:
            print(f"  {name} at t={[e['t'] for e in result['log'] if e['event']==name]}")
    out_path = DATA_DIR / f"online_control_611__seed{args.seed}.json"
    dump_json(result, out_path)
    print(f"[run_online_control_611] wrote {out_path}")


if __name__ == "__main__":
    main()
