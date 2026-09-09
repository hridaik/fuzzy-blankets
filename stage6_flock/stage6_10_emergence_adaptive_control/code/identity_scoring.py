"""Stage 6.10 Part J -- identity-valid scoring.

A controller only gets credit for steering *the same collective*. This module
separates the three things that a naive "final target fraction" collapses:

  1. TASK        H*(I_t, t) on the CURRENT TRACKED LINEAGE, not on the frozen
                 initial member set. Material membership is allowed to turn
                 over; that is the phenomenon, not a failure.
  2. VALIDITY    whether the tracked lineage at the end is still a legitimate
                 continuation of the one that was detected at the start.
  3. ENVELOPE    what "legitimate" means, calibrated from UNCONTROLLED
                 lineages of the same regime and horizon -- never from any
                 controlled episode and never from control success.

The four failure modes the envelope has to catch:

  destruction+replacement   the tracked label survives but the thing does not
  splitting                 the lineage fragments and one piece is scored
  shrink-to-win             the lineage contracts onto an easy core
  material-only persistence membership is preserved but coherence is gone

Bounds are one-sided lower bounds (or upper, for component count). A controlled
lineage that is MORE coherent than uncontrolled ones is not penalised; the
envelope exists to stop credit being claimed for a degraded object.
"""
from __future__ import annotations

import numpy as np

from morphology import morphology

# Per-axis envelope quantile. A naive 5% per axis is WRONG here: with six axes
# tested conjunctively, a genuinely valid uncontrolled lineage fails the joint
# test far more than 5% of the time, and `no_control` gets scored
# identity-invalid. The quantile is therefore CALIBRATED so that the JOINT pass
# rate on held-out uncontrolled lineages hits `TARGET_JOINT_PASS`
# (`calibrate_envelope`), which is the only rate that matters for scoring.
ENVELOPE_Q = 5.0
Q_GRID = (5.0, 2.5, 1.0, 0.5, 0.1, 0.0)
TARGET_JOINT_PASS = 0.90

AXES = ("min_step_jaccard", "final_jaccard_to_I0", "final_size_ratio",
        "final_q_clump", "mean_coherence")
UPPER_AXES = ("max_n_components",)


def jaccard(a, b) -> float:
    a, b = set(int(x) for x in a), set(int(x) for x in b)
    return len(a & b) / len(a | b) if (a or b) else 1.0


def lineage_statistics(I_seq, z_seq, L) -> dict:
    """Identity statistics of one lineage trajectory. Control-agnostic:
    it never sees the arm, the actuators, or the target heading."""
    I0 = I_seq[0]
    steps = [jaccard(I_seq[t], I_seq[t - 1]) for t in range(1, len(I_seq))]
    morphs = [morphology(I, L) for I in I_seq]
    coh = []
    for I, z in zip(I_seq, z_seq):
        I = np.asarray(sorted(int(x) for x in I))
        coh.append(float(np.bincount(z[I], minlength=4).max() / len(I)) if len(I) else 0.0)
    return dict(
        min_step_jaccard=float(min(steps)) if steps else 1.0,
        mean_step_jaccard=float(np.mean(steps)) if steps else 1.0,
        final_jaccard_to_I0=jaccard(I_seq[-1], I0),
        final_size_ratio=float(len(I_seq[-1]) / max(1, len(I0))),
        min_size_ratio=float(min(len(I) for I in I_seq) / max(1, len(I0))),
        final_q_clump=float(morphs[-1]["q_clump"]),
        max_n_components=int(max(m["n_components"] for m in morphs)),
        mean_coherence=float(np.mean(coh)),
        final_size=int(len(I_seq[-1])),
        initial_size=int(len(I0)),
    )


def build_envelope(uncontrolled_stats, q=ENVELOPE_Q) -> dict:
    """Lower/upper validity bounds from UNCONTROLLED lineages only.

    `uncontrolled_stats` is a list of dicts from `lineage_statistics` computed
    on episodes in which no actuator was ever forced.
    """
    env = dict(quantile=q, n_reference=len(uncontrolled_stats), lower={}, upper={})
    for ax in AXES:
        v = [s[ax] for s in uncontrolled_stats]
        env["lower"][ax] = float(np.percentile(v, q))
    for ax in UPPER_AXES:
        v = [s[ax] for s in uncontrolled_stats]
        env["upper"][ax] = float(np.percentile(v, 100.0 - q))
    return env


def calibrate_envelope(calib_stats, valid_stats, target=TARGET_JOINT_PASS,
                       grid=Q_GRID) -> dict:
    """Pick the LARGEST (tightest) per-axis quantile whose JOINT pass rate on
    held-out uncontrolled lineages is at least `target`.

    Built on `calib_stats`, scored on the disjoint `valid_stats`. Tightening the
    bound is what costs pass rate, so the grid is walked from tight to loose and
    the first setting that clears the target is taken. If nothing clears it, the
    loosest setting is returned and `achieved` records the shortfall honestly
    rather than the result being presented as calibrated.
    """
    trace = []
    chosen = None
    for q in grid:
        env = build_envelope(calib_stats, q=q)
        rate = float(np.mean([identity_valid(s, env)["valid"] for s in valid_stats]))
        trace.append(dict(q=q, joint_pass_rate=rate))
        if rate >= target and chosen is None:
            chosen = (q, env, rate)
    if chosen is None:
        q = grid[-1]
        env = build_envelope(calib_stats, q=q)
        rate = float(np.mean([identity_valid(s, env)["valid"] for s in valid_stats]))
        chosen = (q, env, rate)
    q, env, rate = chosen
    env["calibration"] = dict(target_joint_pass=target, achieved_joint_pass=rate,
                              chosen_q=q, grid_trace=trace,
                              n_calibration=len(calib_stats),
                              n_validation=len(valid_stats),
                              met_target=bool(rate >= target))
    return env


def identity_valid(stats, env) -> dict:
    """Is this lineage still the same valid lineage? Per-axis, never collapsed
    into a single number before the per-axis verdicts are recorded."""
    checks = {ax: bool(stats[ax] >= env["lower"][ax]) for ax in AXES}
    checks.update({ax: bool(stats[ax] <= env["upper"][ax]) for ax in UPPER_AXES})
    return dict(valid=bool(all(checks.values())), checks=checks,
                failed=[k for k, v in checks.items() if not v])


def diagnose_failure(stats, env, checks) -> list:
    """Name the failure mode(s) rather than reporting a bare invalid flag."""
    out = []
    if not checks["final_jaccard_to_I0"] and checks["final_size_ratio"]:
        out.append("destruction+replacement")
    if not checks.get("max_n_components", True):
        out.append("splitting")
    if not checks["final_size_ratio"] or stats["min_size_ratio"] < env["lower"]["final_size_ratio"]:
        out.append("shrink-to-win")
    if not checks["mean_coherence"] and checks["final_jaccard_to_I0"]:
        out.append("material-only persistence")
    if not checks["min_step_jaccard"]:
        out.append("lineage discontinuity")
    return out


def conjunctive_success(final_H, stats, env, h_threshold) -> dict:
    """Success requires BOTH the task and identity validity. The two are
    reported separately as well; a run that hits the heading target on a
    degraded object is a failure, and is labelled with which mode."""
    idv = identity_valid(stats, env)
    task = bool(final_H >= h_threshold)
    return dict(success=bool(task and idv["valid"]),
                task_met=task, identity_valid=idv["valid"],
                final_H=float(final_H), checks=idv["checks"],
                failure_modes=diagnose_failure(stats, env, idv["checks"]) if not idv["valid"] else [])
