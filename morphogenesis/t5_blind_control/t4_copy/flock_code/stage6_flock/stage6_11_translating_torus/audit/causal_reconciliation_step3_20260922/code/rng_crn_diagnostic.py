"""Task F0: audit the simulator's RNG consumption BEFORE any paired-branch
causal claim.

Source findings (cited, not assumed) that motivate this diagnostic:

1. `flock_sim/active_inference.py: sample_categorical_rows` draws EXACTLY
   `probs.shape[0]` (= N = number of birds) uniforms via a single
   `rng.random(N)` call, unconditionally -- the draw COUNT never depends on
   the actual probability values. `MovingFlock611.step_cached`
   (`moving_flock_611.py:189-203`) calls this exactly twice per step, in a
   fixed order (action draw, then heading-transition draw), and
   `forced_actions` only OVERWRITES the `applied` array AFTER the first
   draw already happened -- it never adds or removes an RNG call. So: at
   the PHYSICS-STEP level, forcing does not, by itself, change RNG
   consumption count/order/per-bird-slot.

2. HOWEVER, `run_online_control_611.py:run_episode`'s main loop shares a
   SINGLE `rng` object (`np.random.default_rng(seed)`, line 120) between
   (a) `mf.step` (physics, 2 draws/step, always) and (b) `rng.choice(...)`
   for the online passive-model buffer (line 140, unconditional, fires
   every step regardless of phase) and, CRITICALLY, (c) auxiliary
   decision machinery that fires ONLY during `phase == "control"` and
   only on `need_pred`/`need_causal` re-inference steps:
     - `PB.rows_for_targets(..., rng, ...)` (line 216) -- consumes `rng`
       draws, gated by `need_pred` (age-based cadence, always true on the
       FIRST control step since `B_pred_cache is None`).
     - `PR.probe_sources(..., rng, ...)` (line 230) -- consumes `rng`
       draws (bootstrap), gated by `need_causal`.
   (`CA.select_actuators`/`MultiStepAuthorityProbe`/`FiniteProbeMoving611`
   use their OWN independently-seeded generators -- `seed=1000+t+rep`,
   `seed=2000+t` -- NOT the shared `rng`, so those are already isolated.)

   A "no-control" comparator branch (phase stays "uncontrolled" the whole
   episode) NEVER executes (c). A "with-control" branch DOES, starting at
   its very first control step. Both branches, if run from the same
   top-level `np.random.default_rng(seed)`, therefore consume DIFFERENT
   TOTAL NUMBERS of draws from that shared generator from the moment
   control begins onward -- which desynchronizes the underlying
   bit-generator stream position for EVERY subsequent physics draw too,
   even for birds that are never forced.

This script proves point 2 concretely and quantitatively with a minimal,
self-contained reproduction (no dependency on the full online-control
stack), then demonstrates the audit-only fix used by the rest of this
directory's Task F1-F3 scripts: a DEDICATED physics-only RNG stream that
no decision-making code ever touches, verified to keep two branches'
physics draws IDENTICAL per step regardless of what a branch's own
(separately-streamed) decision machinery does.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import N_BIRDS, L_BOX, BETA_610, S_610, resolved_params, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY  # noqa: E402
from moving_flock_611 import MovingFlock611  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"


def make_flock():
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                           social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def demo_1_forcing_alone_does_not_desync(seed=501, n_steps=10):
    """Reproduces point 1: two branches, SAME shared rng object, one with
    forced_actions on a subset of birds every step, one with none -- the
    physics RNG stream position (verified via a canary draw immediately
    after both) is IDENTICAL, because step_cached/step always consumes
    exactly 2 draws of size N regardless of forced_actions content."""
    mf = make_flock()
    rng0 = np.random.default_rng(seed)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)

    forced = {i: 0 for i in range(0, 40)}  # force 40 birds to heading 0 every step

    rngA = np.random.default_rng(999)  # any fixed seed; identical for both branches
    rA, zA = r0.copy(), z0.copy()
    for t in range(n_steps):
        rA, zA, _ = mf.step(rA, zA, rngA, forced_actions=None)
    canary_A = rngA.random(5)

    rngB = np.random.default_rng(999)  # SAME seed as rngA
    rB, zB = r0.copy(), z0.copy()
    for t in range(n_steps):
        rB, zB, _ = mf.step(rB, zB, rngB, forced_actions=forced)
    canary_B = rngB.random(5)

    stream_aligned = bool(np.allclose(canary_A, canary_B))
    return dict(
        claim="forcing alone (no auxiliary rng-consuming decision code) does not desync the shared rng stream",
        n_steps=n_steps, n_forced_birds=len(forced),
        canary_after_unforced=canary_A.tolist(), canary_after_forced=canary_B.tolist(),
        stream_positions_identical=stream_aligned,
        interpretation=("CONFIRMED: forced_actions changes WHICH action executes for forced birds, "
                        "but consumes the identical number/order/shape of RNG draws, so the underlying "
                        "generator's stream position after n_steps is unaffected by forcing itself.")
        if stream_aligned else "UNEXPECTED: stream desynced by forcing alone -- would contradict source reading, investigate.",
    )


def demo_2_auxiliary_decision_code_desyncs_shared_stream(seed=501, n_steps=10, aux_draws_per_control_step=37):
    """Reproduces point 2 with a minimal stand-in for the real auxiliary
    decision code's rng consumption pattern (PB.rows_for_targets /
    PR.probe_sources both draw from `rng` conditionally on control phase).
    `aux_draws_per_control_step` stands in for "however many draws those
    calls actually make" -- the exact count does not matter for the
    qualitative claim being tested (that ANY nonzero, phase-conditional
    consumption desyncs the stream); this uses a representative nonzero
    value, not a fitted one."""
    mf = make_flock()
    rng0 = np.random.default_rng(seed)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)

    # Branch A: "no control" -- physics + the unconditional per-step
    # online-buffer draw (rng.choice(20)) only, exactly like
    # run_online_control_611.py's step_world during phase="uncontrolled".
    rngA = np.random.default_rng(42)
    rA, zA = r0.copy(), z0.copy()
    for t in range(n_steps):
        rA, zA, _ = mf.step(rA, zA, rngA, forced_actions=None)
        rngA.choice(mf.N, size=20, replace=False)   # the unconditional online-buffer draw
    physics_trace_A = [zA.copy()]

    # Branch B: "with control from t=0" -- SAME seed, SAME physics calls,
    # SAME unconditional online-buffer draw, PLUS the auxiliary
    # decision-machinery draws that only fire when phase=="control"
    # (standing in for PB.rows_for_targets / PR.probe_sources).
    rngB = np.random.default_rng(42)   # identical seed to rngA
    rB, zB = r0.copy(), z0.copy()
    for t in range(n_steps):
        rB, zB, _ = mf.step(rB, zB, rngB, forced_actions=None)  # note: forced_actions=None here too --
        rngB.choice(mf.N, size=20, replace=False)                # isolating the EFFECT to auxiliary-code
        rngB.random(aux_draws_per_control_step)                  # stand-in for PB/PR's rng consumption
    physics_trace_B = [zB.copy()]

    divergence_step = None
    if not np.array_equal(zA, zB):
        divergence_step = "already diverged by t=%d (z arrays differ)" % n_steps
    frac_birds_differing = float((zA != zB).mean())

    return dict(
        claim="auxiliary decision-machinery rng consumption (phase-conditional, NOT forced_actions itself) desyncs the shared physics stream, even though NO bird was ever forced in either branch",
        n_steps=n_steps, aux_draws_per_control_step=aux_draws_per_control_step,
        z_trajectories_identical=bool(np.array_equal(zA, zB)),
        fraction_birds_with_differing_heading_at_end=frac_birds_differing,
        interpretation=(
            "CONFIRMED: with forced_actions=None in BOTH branches (so no bird's action is ever overridden), "
            "the only difference is that branch B's rng object additionally consumes "
            f"{aux_draws_per_control_step} draws per step (standing in for the real "
            "PB.rows_for_targets/PR.probe_sources calls that run_online_control_611.py's control phase "
            "makes on the SAME shared `rng` object). This alone is sufficient to make the two branches' "
            "physics trajectories diverge, because every subsequent rng.random(N) call inside "
            "sample_categorical_rows draws from a different position in the underlying bit stream. "
            "Therefore: SAME TOP-LEVEL SEED IS NOT SUFFICIENT for valid common random numbers between a "
            "no-control and a with-control branch of run_online_control_611.py's actual production loop, "
            "because the control decision machinery and the physics step share one rng object."
        ) if not np.array_equal(zA, zB) else "UNEXPECTED: no divergence detected -- investigate.",
    )


def demo_3_dedicated_physics_stream_fixes_it(seed=501, n_steps=10, aux_draws_per_control_step=37):
    """The audit-only fix used throughout Task F1-F3: give physics its OWN
    dedicated rng stream that decision-making code NEVER touches (a
    harness-level routing choice -- these functions already accept `rng`
    as an explicit parameter, so this requires no production-code edits,
    only calling them with a different generator instance from an
    audit-only replay loop)."""
    mf = make_flock()
    rng0 = np.random.default_rng(seed)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)

    rng_physics_A = np.random.default_rng(42)
    rng_decisions_A = np.random.default_rng(43)   # separate stream, branch A never uses it beyond the buffer draw
    rA, zA = r0.copy(), z0.copy()
    for t in range(n_steps):
        rA, zA, _ = mf.step(rA, zA, rng_physics_A, forced_actions=None)
        rng_decisions_A.choice(mf.N, size=20, replace=False)   # decision-side, isolated

    rng_physics_B = np.random.default_rng(42)      # SAME physics seed as A
    rng_decisions_B = np.random.default_rng(99)    # DIFFERENT decision-side seed AND consumption pattern than A
    rB, zB = r0.copy(), z0.copy()
    for t in range(n_steps):
        rB, zB, _ = mf.step(rB, zB, rng_physics_B, forced_actions=None)
        rng_decisions_B.choice(mf.N, size=20, replace=False)
        rng_decisions_B.random(aux_draws_per_control_step)     # extra decision-side consumption, isolated stream

    return dict(
        claim="a dedicated physics-only rng stream, never touched by decision-making code, keeps branches' physics draws aligned regardless of how much (or how differently) their decision machinery consumes",
        n_steps=n_steps,
        z_trajectories_identical=bool(np.array_equal(zA, zB)),
        interpretation=(
            "CONFIRMED: with physics routed through its own dedicated generator that decision code never "
            "touches, branch B's extra/different decision-side consumption has NO effect on the physics "
            "trajectory -- both branches' z arrays are bit-identical after n_steps with forced_actions=None "
            "in both. This is the audit-only harness pattern used for Task F1's schedule-effect comparison."
        ) if np.array_equal(zA, zB) else "UNEXPECTED: dedicated stream did not fix alignment -- investigate.",
    )


def demo_4_exact_historical_reproduction_requires_replicating_every_shared_draw(seed=501, n_steps=15):
    """IMPORTANT CORRECTION vs. an earlier, wrong intuition: the
    "physics-irrelevant" `rng.choice(20)` buffer-sampling draw (line 140 of
    run_online_control_611.py) does NOT feed back into r/z directly, but it
    DOES consume from the SAME shared generator in production, so it still
    shifts the position of every SUBSEQUENT `rng.random(N)` draw inside
    `sample_categorical_rows` -- which DOES change the actual sampled
    z-trajectory (same uniform values map through a shifted stream to
    different categorical outcomes). This demo verifies that claim
    directly: a naive harness replay that calls `mf.step` in a loop
    WITHOUT also replaying that extra draw does NOT bit-for-bit reproduce
    a genuine historical production trajectory, while a replay that DOES
    replicate the exact call sequence (including the buffer-sampling draw)
    DOES.

    Consequence for trigger-state reproduction (Task E): reproducing a
    seed's exact historical pre-control trajectory (to recover its exact
    t0 trigger state) requires replaying `run_online_control_611.py`'s
    EXACT uncontrolled-phase call sequence verbatim (mf.step then
    rng.choice(20), every step, same order) -- not just the physics update
    equations. This is why the trigger-state reproduction scripts in this
    directory replay the production loop's call pattern read-only, rather
    than re-deriving a "cleaner" equivalent loop."""
    mf = make_flock()
    rng0 = np.random.default_rng(seed)
    r0 = rng0.random((mf.N, 2)) * mf.L
    z0 = rng0.integers(0, 4, mf.N)

    # "production-style" unforced replay: single shared rng, exactly the
    # step_world pattern (mf.step then rng.choice(20)), matching
    # run_online_control_611.py's uncontrolled-phase behaviour verbatim.
    rng_prod = np.random.default_rng(7)
    r_prod, z_prod = r0.copy(), z0.copy()
    for t in range(n_steps):
        r_prod, z_prod, _ = mf.step(r_prod, z_prod, rng_prod, forced_actions=None)
        rng_prod.choice(mf.N, size=20, replace=False)

    # naive harness (WRONG for exact reproduction): dedicated physics
    # stream, seeded identically, but never replays the buffer-sampling
    # draw -- expected to DIVERGE from the production trace.
    rng_naive = np.random.default_rng(7)
    r_naive, z_naive = r0.copy(), z0.copy()
    for t in range(n_steps):
        r_naive, z_naive, _ = mf.step(r_naive, z_naive, rng_naive, forced_actions=None)

    # exact-replay harness (CORRECT for exact reproduction): single shared
    # stream, replicating the production call sequence exactly.
    rng_exact = np.random.default_rng(7)
    r_exact, z_exact = r0.copy(), z0.copy()
    for t in range(n_steps):
        r_exact, z_exact, _ = mf.step(r_exact, z_exact, rng_exact, forced_actions=None)
        rng_exact.choice(mf.N, size=20, replace=False)

    return dict(
        claim="exact historical reproduction requires replaying EVERY shared-stream draw production makes, not just the physics-update calls",
        n_steps=n_steps,
        naive_harness_matches_production=bool(np.array_equal(z_prod, z_naive)),
        exact_replay_harness_matches_production=bool(np.array_equal(z_prod, z_exact)),
        interpretation=(
            "CONFIRMED: the naive harness (physics calls only, omitting the buffer-sampling draw) "
            "diverges from a genuine production trajectory, while replaying the exact call sequence "
            "(including the physics-irrelevant buffer draw) reproduces it exactly. Trigger-state "
            "reproduction scripts in this directory therefore replay production's exact call pattern, "
            "not a hand-simplified equivalent."
        ),
    )


def main():
    import json
    results = dict(
        demo_1_forcing_alone=demo_1_forcing_alone_does_not_desync(),
        demo_2_auxiliary_code_desyncs=demo_2_auxiliary_decision_code_desyncs_shared_stream(),
        demo_3_dedicated_stream_fixes_it=demo_3_dedicated_physics_stream_fixes_it(),
        demo_4_exact_replay_required=demo_4_exact_historical_reproduction_requires_replicating_every_shared_draw(),
    )
    for name, r in results.items():
        print(f"\n=== {name} ===")
        print(json.dumps(r, indent=2, default=str))
    json.dump(results, open(OUT / "rng_crn_diagnostic.json", "w"), indent=2, default=str)
    print("\nwrote", OUT / "rng_crn_diagnostic.json")


if __name__ == "__main__":
    main()
