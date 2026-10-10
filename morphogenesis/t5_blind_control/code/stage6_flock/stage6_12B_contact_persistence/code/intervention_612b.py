"""Stage 6.12B intervention primitives. Reuses `intervention_612.py`'s
`simulate_branch`, `trace_target`, `outcome_metrics`, `mechanism_diagnostics`
UNMODIFIED (imported as `I611`) -- never re-implemented. Adds:

  - conservative identity scoring (V_conservative / J_conservative), applied
    at COMPUTE TIME here (unlike Stage 6.12, which had to reconstruct it
    post hoc in Part I's correction pass -- see STAGE612_CORRECTION_MEMO.md's
    disclosed Phase-B/C data gap; this stage does not repeat that gap).
  - `simulate_scheduled`: a general per-step forced-action rollout (a
    {step_offset: {bird: heading}} schedule, or an ONLINE callback that
    picks the forced set at each refresh boundary from the CURRENT
    simulated state) -- generalizes `intervention_612.simulate_branch`'s
    single-fixed-K-birds-for-d-steps case to Stage 6.12B-B's refreshing
    actuator sets.
  - kinematic (deployable, no future truth) and oracle (audit-only, uses a
    paired no-control future trajectory) contact-persistence predictors.

RNG separation (unchanged from Stage 6.12): physics streams
(`np.random.default_rng(physics_seed)`) are consumed ONLY inside
`mf.step`; actuator-set sampling/search/strategy-selection RNG is always a
SEPARATE generator, passed explicitly, never sharing a seed value with a
physics stream.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_612b as C           # noqa: E402
import intervention_612 as I611   # noqa: E402

R_RELEASE = I611.R_RELEASE   # 24, unchanged


def add_conservative(entry: dict) -> dict:
    V = entry["V"]
    vc = 1 if (V == 1 and entry["n_split_flags"] == 0 and entry["n_merge_flags"] == 0
               and entry["n_unresolved_steps"] == 0) else 0
    a = entry.get("A_release_late")
    entry["V_conservative"] = vc
    entry["J_conservative"] = float(vc * a) if a is not None else 0.0
    entry["J_assoc"] = entry["J"]   # explicit alias, original semantics
    entry["event_corrected"] = entry["event"].replace("confirmed_split", "material_split_flag").replace(
        "confirmed_merge", "material_merge_flag")
    return entry


def run_one_b(mf, r0, z0, z_context, seed_members, rule, h_star, S, d, physics_seed):
    """Fixed-set rollout (Stage 6.12B-A), identical semantics to
    Stage 6.12's `run_one`, with conservative fields added at compute
    time and mechanism diagnostics always attached (they're a cheap
    post-hoc analysis of an already-simulated trajectory, not an extra
    simulation cost)."""
    out = I611.run_one(mf, r0, z0, z_context, seed_members, rule, h_star, S, d, physics_seed, with_mechanism=True)
    return add_conservative(out)


def run_no_control_full_b(mf, r0, z0, z_context, seed_members, rule, h_star, physics_seed, d_grid):
    n_steps = max(d_grid) + R_RELEASE
    r_hist, z_hist = I611.simulate_branch(mf, r0, z0, physics_seed, None, h_star, 0, n_steps)
    tr = I611.trace_target(r_hist, z_hist, z_context, seed_members, rule)
    out = {d: add_conservative(I611.outcome_metrics(tr, z_hist, h_star, d)) for d in d_grid}
    return out, r_hist, z_hist, tr


# ---------------------------------------------------------------------
# Kinematic (deployable) predicted-contact scoring -- uses ONLY current
# observable positions/headings + known constant speed + torus geometry.
# Never touches future simulator truth.
# ---------------------------------------------------------------------

def kinematic_contact_scores(r_t, z_t, candidates, target_members, L, v, window, R=None):
    """Returns {candidate_id: score}. If R is given, score = count of
    predicted future steps (tau=1..window) where the predicted candidate-
    target distance is <= R, summed over all target members (labelled
    'physics-assisted predicted contact' by the caller). If R is None,
    score = -mean predicted distance over tau and target members (a
    radius-free relative-persistence variant; higher score = closer
    predicted proximity)."""
    cand_arr = np.array(sorted(int(c) for c in candidates))
    tgt_arr = np.array(sorted(int(m) for m in target_members))
    if len(cand_arr) == 0 or len(tgt_arr) == 0:
        return {int(c): 0.0 for c in cand_arr}
    uv = C.UV4
    taus = np.arange(1, window + 1)[:, None, None]           # (window,1,1)
    r_cand_future = r_t[cand_arr][None, :, :] + taus * v * uv[z_t[cand_arr]][None, :, :]   # (window,Ncand,2)
    r_tgt_future = r_t[tgt_arr][None, :, :] + taus * v * uv[z_t[tgt_arr]][None, :, :]       # (window,Ntgt,2)
    delta = C.torus_delta(r_cand_future[:, :, None, :], r_tgt_future[:, None, :, :], L)     # (window,Ncand,Ntgt,2)
    dist = np.sqrt((delta ** 2).sum(-1))                                                     # (window,Ncand,Ntgt)
    if R is not None:
        score = (dist <= R).sum(axis=(0, 2)).astype(float)
    else:
        score = -dist.mean(axis=(0, 2))
    return {int(cand_arr[i]): float(score[i]) for i in range(len(cand_arr))}


def top_k_by_score(scores: dict, K: int) -> list[int]:
    return [int(k) for k, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:K]]


# ---------------------------------------------------------------------
# Oracle no-intervention future contact (audit-only, S18.3 / S22.D) --
# uses a PAIRED no-control trajectory (same physics_seed) as the source of
# "future truth". Never uses the intervention's OWN (forced) trajectory.
# ---------------------------------------------------------------------

def oracle_future_contact_scores(nc_r_hist, nc_z_hist, nc_trace, t_offset, window, candidates, L, R,
                                   fallback_members=None):
    """Score = count of steps tau in [t_offset+1, t_offset+window] (clipped
    to the no-control trajectory's length) where a candidate is within true
    R of ANY no-control-traced target member at that step. `fallback_members`
    is used if the no-control trace has no accepted membership at a given
    step (e.g. temporarily unresolved) -- holds the last known membership,
    matching ForwardMaterialTrace611's own 'pin, don't switch' convention."""
    cand_arr = np.array(sorted(int(c) for c in candidates))
    n = nc_r_hist.shape[0]
    end = min(t_offset + window, n - 1)
    scores = np.zeros(len(cand_arr))
    last_members = fallback_members
    for t in range(t_offset + 1, end + 1):
        dec = nc_trace.history[t] if t < len(nc_trace.history) else None
        members = (dec.accepted_members if dec and dec.accepted_members else last_members) or frozenset()
        if members:
            last_members = members
        if not members:
            continue
        mem_arr = np.array(sorted(int(m) for m in members))
        delta = C.torus_delta(nc_r_hist[t][cand_arr][:, None, :], nc_r_hist[t][mem_arr][None, :, :], L)
        dist = np.sqrt((delta ** 2).sum(-1))
        scores += (dist <= R).any(axis=1).astype(float)
    return {int(cand_arr[i]): float(scores[i]) for i in range(len(cand_arr))}
