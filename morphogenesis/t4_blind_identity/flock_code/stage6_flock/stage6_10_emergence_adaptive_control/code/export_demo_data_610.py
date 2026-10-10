"""Stage 6.10 -> interactive_demo/data/stage6_10_bundle.json.

VISUALIZATION EXPORT ONLY. This script produces no new scientific statistic,
runs no new experiment, and writes nothing back into `data/`. Its only output
is the demo bundle.

It does three things, in the same shape as
`stage6_8_dynamic_interactions/code/export_demo_data_68.py`:

  (a) READS the frozen Stage 6.10 result files, read-only:
          data/release__fixedk.json            (Parts K + L)
          data/closed_loop__fixedk.json        (Part I, fixed-K convention)
          data/controllability__main.json      (Part H, the frozen task + stratum)
          data/uncontrolled_reference__main.json (Part J, the validity envelope)

  (b) TAKES the episode named by Part L's `clarity_trajectory` -- seed, arm,
      and the declared selection rule as recorded by `run_release_clarity.py`.
      The episode is never re-chosen here and no nicer-looking one is
      substituted; `rule` and `caveat` are carried into the bundle verbatim so
      the page can display them.

  (c) REPLAYS the frozen simulator deterministically to recover the
      per-timestep headings the science runs did not persist
      (`run_closed_loop.py` drops `z_hist` explicitly: "the full trajectory does
      not fit in the result file"). Every replayed quantity is asserted against
      the frozen file it must match:

        - the qualifying start I0 at t0 must equal the episode's stored `I0`,
          and h0 / h* must equal the stored ones;
        - the replayed control trajectory's H*(I_t, t+1) must equal each
          record's `H_current` exactly (1e-12), at all `horizon` steps;
        - the replayed final state and final lineage must equal `final_z` /
          `final_I`;
        - the recomputed structural interface's size must equal the recorded
          `B_struct_size` at every step;
        - the replayed release must reproduce `release__fixedk.json`'s records
          (H, |I|, Q_clump, components) and `H_trace` exactly, all 16 steps.

      A replay that drifted fails the export loudly rather than silently
      feeding the demo a different trajectory.

The exporter is re-runnable and idempotent: it re-reads whatever is currently
on disk and rewrites the bundle. Every required key is asserted with a message
naming the file and the key, so a mid-write or regenerated result file produces
a clear failure instead of a partial bundle.

Usage:  python export_demo_data_610.py [tag]        (tag defaults to "fixedk")
"""
from __future__ import annotations

import sys
import time

import numpy as np

from common_610 import (DATA_DIR, load_json, dump_json, target_alignment,
                        rotate_cw)
from common_68 import lattice_positions
from episode_data import make_simulator, run_episode, observation_record
from morphology import morphology
import candidate_detection as cd
import reference_truth as rt
from closed_loop import qualifying_start, detect

DEMO_DATA = DATA_DIR.parents[1] / "interactive_demo" / "data"
OUT_NAME = "stage6_10_bundle.json"

# The 7-phase walkthrough this view exists to show. Phase boundaries are
# derived from the frozen protocol constants below, never hand-placed.
#   1 unstructured  2 emergence  3 detected thing  4 dynamic interface
#   5 target introduced  6 adaptive steering  7 release
W_DET = cd.W_AFFINITY          # the detector's affinity window: before t = W_DET
                               # it has no window to propose from at all.


# --------------------------------------------------------------- helpers ----
def need(d, key, where):
    """Fetch a required key, or fail with a message naming the file."""
    assert isinstance(d, dict) and key in d, \
        f"{where}: required key '{key}' is missing -- the result file is absent, " \
        f"mid-write, or was regenerated with a different schema. Re-run the " \
        f"Stage 6.10 driver that writes it, then re-run this exporter."
    return d[key]


def enc_z(z):
    """400 headings -> a 400-char string of '0'..'3' (compact, exact)."""
    return "".join(chr(48 + int(v)) for v in z)


def close(a, b, tol=1e-12):
    return abs(float(a) - float(b)) <= tol


# ----------------------------------------------------------------- main -----
def main(tag="fixedk"):
    t_start = time.time()
    cl_path = DATA_DIR / f"closed_loop__{tag}.json"
    rl_path = DATA_DIR / f"release__{tag}.json"
    ct_path = DATA_DIR / "controllability__main.json"
    ur_path = DATA_DIR / "uncontrolled_reference__main.json"
    for p in (cl_path, rl_path, ct_path, ur_path):
        assert p.exists(), f"missing frozen result file: {p}"

    cl = load_json(cl_path)
    rl = load_json(rl_path)
    ctl = load_json(ct_path)
    ref = load_json(ur_path)

    # ---- Part L: the declared clarity trajectory, taken as given -----------
    clarity = need(rl, "clarity_trajectory", rl_path.name)
    seed = need(clarity, "seed", "release__*.json:clarity_trajectory")
    assert seed is not None, (
        "release__%s.json: clarity_trajectory.seed is null -- no episode "
        "qualified under the declared rule, so there is nothing to visualize. "
        "An unsuccessful episode is not substituted." % tag)
    arm = need(clarity, "arm", "clarity_trajectory")
    rule = need(clarity, "rule", "clarity_trajectory")
    caveat = need(clarity, "caveat", "clarity_trajectory")
    n_eligible = clarity.get("n_eligible")
    final_H_declared = need(clarity, "final_H", "clarity_trajectory")

    # ---- the frozen task and the stratum it is scoped to -------------------
    assert need(cl, "budget_convention", cl_path.name) == "fixed_k", (
        f"{cl_path.name}: budget_convention is "
        f"{cl['budget_convention']!r}, expected 'fixed_k'. The clarity "
        f"trajectory is a fixed-K episode; export the fixed-K file.")
    reg = need(cl, "regime", cl_path.name)
    T0 = int(need(cl, "t0", cl_path.name))
    horizon = int(need(cl, "horizon", cl_path.name))
    frac = float(need(cl, "actuator_fraction", cl_path.name))
    h_thresh = float(need(cl, "h_threshold", cl_path.name))

    ft = need(ctl, "frozen_task", ct_path.name)
    cell = need(ft, "frozen_cell", "controllability__main.json:frozen_task")
    prim = need(ft, "primary_episodes", "frozen_task")
    excl = need(ft, "excluded_episodes", "frozen_task")
    assert close(cell["frac"], frac) and int(cell["horizon"]) == horizon, (
        f"frozen cell {cell} disagrees with the closed-loop run "
        f"(frac={frac}, horizon={horizon}); the two files are out of step.")
    assert seed in prim, (
        f"clarity trajectory seed {seed} is not in the frozen primary stratum "
        f"{prim}; the release file and the controllability file disagree.")
    n_prim, n_excl = int(ft["n_primary"]), int(ft["n_excluded"])
    assert n_prim == len(prim) and n_excl == len(excl), \
        "frozen_task episode counts disagree with its own lists"

    # ---- the validity envelope actually used to score this episode ---------
    env_by_h = need(ref, "validity_envelope_by_horizon", ur_path.name)
    assert str(horizon) in env_by_h, (
        f"{ur_path.name}: no validity envelope at horizon {horizon}; the "
        f"uncontrolled reference was built at horizons {sorted(env_by_h)}.")
    env_ref = env_by_h[str(horizon)]
    env_used = need(cl, "validity_envelope", cl_path.name)
    for side in ("lower", "upper"):
        for k, v in env_ref[side].items():
            assert close(env_used[side][k], v, 1e-9), (
                f"validity envelope mismatch on {side}.{k}: closed loop scored "
                f"against {env_used[side][k]}, uncontrolled reference now says "
                f"{v}. Re-run the closed loop against the current envelope.")

    # ---- the episode / arm named by Part L ---------------------------------
    eps = need(cl, "episodes", cl_path.name)
    match = [e for e in eps if int(e["seed"]) == int(seed)]
    assert len(match) == 1, (
        f"{cl_path.name}: expected exactly one episode with seed {seed}, "
        f"found {len(match)} (seeds present: {[e['seed'] for e in eps]}).")
    ep = match[0]
    assert arm in ep["arms"], \
        f"{cl_path.name}: episode {seed} has no arm {arm!r}"
    r = ep["arms"][arm]
    score = need(r, "score", f"episode {seed} arm {arm}")
    assert score["success"], (
        f"the declared clarity trajectory (seed {seed}, {arm}) is not a "
        f"conjunctive success in {cl_path.name}; the two files are out of step.")
    assert close(r["final_H_current"], final_H_declared, 1e-9), (
        f"clarity_trajectory.final_H ({final_H_declared}) != the closed loop's "
        f"final_H_current ({r['final_H_current']}) for seed {seed} / {arm}.")

    recs = need(r, "records", f"episode {seed} arm {arm}")
    assert len(recs) == horizon, (
        f"episode {seed} / {arm}: {len(recs)} control records against a "
        f"recorded horizon of {horizon}.")
    for k, rec in enumerate(recs):
        assert int(rec["step"]) == k, f"control records are not in step order at k={k}"

    rel_eps = need(rl, "episodes", rl_path.name)
    rel_match = [e for e in rel_eps if int(e["seed"]) == int(seed)]
    assert len(rel_match) == 1, \
        f"{rl_path.name}: expected one release episode for seed {seed}"
    assert arm in rel_match[0]["arms"], (
        f"{rl_path.name}: episode {seed} has no released arm {arm!r} -- release "
        f"is only recorded for conjunctive successes.")
    rel_arm = rel_match[0]["arms"][arm]
    n_rel = int(need(rl, "release_steps", rl_path.name))
    rel_recs = need(rel_arm, "records", f"release episode {seed} arm {arm}")
    assert len(rel_recs) == n_rel, (
        f"release episode {seed} / {arm}: {len(rel_recs)} records against a "
        f"recorded release_steps of {n_rel}.")

    # ---------------------------------------------------------- replay ------
    sim = make_simulator(reg["nn"], reg["beta"], reg["s"])
    L = int(round(reg["nn"] ** 0.5))
    nn = int(reg["nn"])

    # 1-3. Emergence, from the episode's own seed. `run_closed_loop` builds the
    #      identical prefix with the identical call, so this IS the prefix the
    #      controlled episode ran on -- anchored by the t0 assertions below.
    res = run_episode(sim, seed, nt=T0 + 2, record_oracle=False)
    zh = res.z_hist

    h_star = int(ep["h_star"])
    h0 = int(ep["h0"])
    ok0, _ = cd.propose(observation_record(sim, zh, T0))
    I0_replay = qualifying_start(ok0, L)
    assert I0_replay is not None, \
        f"replay: no qualifying collective at t0={T0} for seed {seed}"
    assert sorted(int(x) for x in I0_replay) == sorted(int(x) for x in ep["I0"]), \
        f"replay diverged: qualifying start at t0 != {cl_path.name}'s I0 for seed {seed}"
    h0_replay = int(np.bincount(zh[T0][I0_replay], minlength=4).argmax())
    assert h0_replay == h0, f"replay: h0 {h0_replay} != recorded {h0}"
    assert int(rotate_cw(h0_replay)) == h_star, \
        f"replay: rotate_cw(h0) {rotate_cw(h0_replay)} != recorded h* {h_star}"

    # The blind detector's own output over the emergence window, re-derived with
    # the frozen detector on the frozen trajectory. The science only ran it at
    # t0; these earlier steps are shown as detector output, not as a Stage 6.10
    # result, and the t0 entry is the one asserted equal to the frozen I0.
    emergence = []
    for t in range(T0 + 1):
        e = dict(t=t)
        if t >= W_DET:
            cands, _ = cd.propose(observation_record(sim, zh[:t + 1], t))
            q = qualifying_start(cands, L)
            e["n_cand"] = len(cands)
            if q is not None:
                m = morphology(q, L)
                e["I"] = [int(x) for x in q]
                e["coh"] = float(cd.internal_coherence(
                    observation_record(sim, zh[:t + 1], t), q))
                e["q_clump"] = float(m["q_clump"])
        emergence.append(e)
    assert emergence[T0].get("I") == sorted(int(x) for x in ep["I0"]), \
        "the emergence pass's t0 collective is not the episode's I0"

    # 4-6. The control window. The action sequence is read from the frozen
    #      records; only the physics is replayed.
    rng = np.random.default_rng(70_000 + seed)
    hist = np.zeros((T0 + 1 + horizon, nn), dtype=int)
    hist[:T0 + 1] = zh[:T0 + 1]
    control = []
    for k, rec in enumerate(recs):
        cur = T0 + k
        z_now = hist[cur]
        I_now = np.array(sorted(int(x) for x in rec["I"]))
        B_struct = sorted(int(x) for x in rt.structural_interface(sim, z_now, I_now))
        assert len(B_struct) == int(rec["B_struct_size"]), (
            f"replay diverged: |B_struct| {len(B_struct)} != recorded "
            f"{rec['B_struct_size']} at control step {k}")
        A = [int(j) for j in rec["actuators"]]
        out = sim.step(z_now, rng, forced_actions={j: h_star for j in A})
        hist[cur + 1] = out["z_new"]
        H = target_alignment(hist[cur + 1], I_now, h_star)
        assert close(H, rec["H_current"]), (
            f"replay diverged from {cl_path.name} at control step {k}: "
            f"H*={H} vs recorded {rec['H_current']}")
        B_do = sorted(int(x) for x in rec["B_do"])
        control.append(dict(
            step=k, t=cur, I=[int(x) for x in I_now], I_size=int(rec["I_size"]),
            actuators=A, n_act=int(rec["n_act"]),
            B_struct=B_struct, B_do=B_do,
            B_symdiff=len(set(B_struct) ^ set(B_do)),
            H=float(rec["H_current"]), H_I0=float(rec["H_I0"]),
            q_clump=float(rec["q_clump"]), n_components=int(rec["n_components"]),
            jaccard_prev=float(rec["jaccard_prev"]), turnover=float(rec["turnover"]),
            n_cands=int(rec["n_cands"]),
            support_coverage=(float(rec["support_coverage"])
                              if "support_coverage" in rec else None)))
    assert [int(x) for x in hist[-1]] == [int(x) for x in r["final_z"]], \
        f"replay diverged: final state != {cl_path.name}'s final_z for seed {seed}"
    assert control[-1]["I"] == sorted(int(x) for x in r["final_I"]), \
        f"replay diverged: final lineage != {cl_path.name}'s final_I for seed {seed}"

    # 7. Release: control off. Mirrors `closed_loop.release` exactly and is
    #    asserted equal to the frozen release record, field by field.
    rng_r = np.random.default_rng(80_000 + seed)
    z_rel = [np.array(r["final_z"], dtype=int)]
    warm = np.tile(z_rel[0], (cd.W_AFFINITY, 1))
    I_rel = np.array(sorted(int(x) for x in r["final_I"]))
    release = []
    for k in range(n_rel):
        full = (np.concatenate([warm, np.array(z_rel[1:])], axis=0)
                if len(z_rel) > 1 else warm)
        I_rel, _ = detect(sim, full, full.shape[0] - 1, I_rel)
        m = morphology(I_rel, L)
        H = target_alignment(z_rel[-1], I_rel, h_star)
        frozen = rel_recs[k]
        assert int(frozen["step"]) == k, "release records are not in step order"
        assert close(H, frozen["H_current"]) and len(I_rel) == int(frozen["I_size"]) \
            and close(m["q_clump"], frozen["q_clump"]) \
            and int(m["n_components"]) == int(frozen["n_components"]), (
            f"release replay diverged from {rl_path.name} at step {k}: "
            f"H={H}/{frozen['H_current']} |I|={len(I_rel)}/{frozen['I_size']} "
            f"Q={m['q_clump']}/{frozen['q_clump']} "
            f"comp={m['n_components']}/{frozen['n_components']}")
        release.append(dict(
            step=k, t=T0 + horizon + k, I=[int(x) for x in I_rel],
            I_size=len(I_rel), H=float(H), q_clump=float(m["q_clump"]),
            n_components=int(m["n_components"]),
            z_index=T0 + horizon + k))
        out = sim.step(z_rel[-1], rng_r)
        z_rel.append(out["z_new"])
        warm = np.concatenate([warm[1:], out["z_new"][None, :]], axis=0)
    assert [round(x["H"], 12) for x in release] == \
        [round(float(v), 12) for v in rel_arm["H_trace"]], \
        f"release replay's H trace != {rl_path.name}'s H_trace"

    # ---- one continuous timeline of headings -------------------------------
    # t = 0..T0            emergence (and t0 itself)
    # t = T0..T0+horizon-1 control, pre-action state at each step
    # t = T0+horizon..+n_rel-1  release, free running
    frames = []
    for t in range(T0 + horizon):
        frames.append(enc_z(hist[t]))
    for k in range(n_rel):
        frames.append(enc_z(z_rel[k]))
    n_frames = T0 + horizon + n_rel
    assert len(frames) == n_frames, "frame count does not match the timeline"
    assert frames[T0] == enc_z(zh[T0]), "control frame at t0 != the emergence frame"
    assert frames[T0 + horizon] == enc_z(np.array(r["final_z"])), \
        "the first release frame is not the control window's final state"

    # ---- the same-episode no-control floor, verbatim (no replay needed) -----
    nc = ep["arms"].get("no_control")
    no_control = (dict(H=[float(x["H_current"]) for x in nc["records"]],
                       final_H=float(nc["final_H_current"]),
                       identity_valid=bool(nc["score"]["identity_valid"]))
                  if nc else None)

    # ------------------------------------------------------------- payload --
    P = lattice_positions(nn)
    nbr = {str(i): [int(x) for x in ids] for i, ids in enumerate(sim.lattice.neighbor_ids)}

    out = dict(
        provenance=dict(
            stage="6.10",
            regime=dict(nn=nn, beta=reg["beta"], s=reg["s"]),
            sources=[cl_path.name, rl_path.name, ct_path.name, ur_path.name],
            selection_rule=rule,
            selection_note=(
                f"Part L's declared rule, applied in run_release_clarity.py and "
                f"copied here verbatim. {n_eligible} episode(s) were eligible. "
                f"The episode is not re-chosen by this exporter."),
            caveat=caveat,
            replay_note=(
                "Per-timestep headings were not persisted by the science runs "
                "(run_closed_loop.py drops z_hist explicitly). They are "
                "regenerated here by a deterministic replay of the frozen "
                "simulator at the same seed, the same regime and the recorded "
                "action sequence, and every replayed quantity is asserted equal "
                "to the frozen file: the qualifying start I0, H*(I_t) at all "
                f"{horizon} control steps, the final state and lineage, the "
                f"structural interface size at every step, and all {n_rel} "
                "release records including the H trace. No new statistic is "
                "computed and no result file is modified."),
            detector_note=(
                "The emergence pass runs the frozen blind detector at each "
                f"timestep from t = {W_DET} (its affinity window) to t = {T0}. "
                "The science only ran it at t0; the earlier steps are shown as "
                "detector output, not as a Stage 6.10 result. The t0 entry is "
                "asserted equal to the episode's frozen I0."),
        ),
        lattice=dict(nn=nn, L=L,
                     positions=[[int(L - 1 - int(p[1])), int(p[0])] for p in P],
                     neighbors=nbr),
        episode=dict(
            seed=int(seed), arm=arm, h0=h0, h_star=h_star,
            turn="90 degrees clockwise (h0 -> rotate_cw(h0))",
            t0=T0, horizon=horizon, release_steps=n_rel, n_frames=n_frames,
            k_act=int(ep["k_act"]), I0=[int(x) for x in ep["I0"]],
            I0_size=int(ep["I0_size"]),
            final_H=float(r["final_H_current"]),
            final_H_I0=float(r["final_H_I0"]),
            mean_actuators=float(r["mean_actuators"]),
            identity=r["identity"], score=score,
            predictive_boundary=ep.get("predictive_boundary"),
            release=dict(H_at_release=float(rel_arm["H_at_release"]),
                         H_final=float(rel_arm["H_final"]),
                         retention=float(rel_arm["retention"]),
                         q_final=float(rel_arm["q_final"]),
                         comp_final=int(rel_arm["comp_final"]),
                         size_final=int(rel_arm["size_final"])),
        ),
        frames=frames,
        emergence=emergence,
        control=control,
        release=release,
        no_control=no_control,
        phases=[
            dict(key="unstructured", label="Unstructured", t_start=0, t_end=W_DET - 1,
                 note="Before the detector's affinity window is filled, nothing "
                      "is proposed."),
            dict(key="emergence", label="Emergence", t_start=W_DET, t_end=T0 - 1,
                 note="Coherent domains form; the blind detector proposes "
                      "candidates each step."),
            dict(key="detected", label="Detected thing", t_start=T0, t_end=T0,
                 note="The qualifying start I0 -- moderate size, single "
                      "component, most clump-like. Morphology only: no target "
                      "heading and no control outcome enter this choice."),
            dict(key="steering", label="Adaptive steering", t_start=T0,
                 t_end=T0 + horizon - 1,
                 note="Control on. The interior and the interface are both "
                      "re-inferred online."),
            dict(key="release", label="Release", t_start=T0 + horizon,
                 t_end=T0 + horizon + n_rel - 1,
                 note="Control off for the remaining steps."),
        ],
        task=dict(
            frac=frac, horizon=horizon, h_threshold=h_thresh,
            cell_key=cell.get("key"),
            n_primary=n_prim, n_excluded=n_excl,
            primary_episodes=[int(x) for x in prim],
            excluded_episodes=[int(x) for x in excl],
            selected_by=ft.get("selected_by"),
            claim_scope=ft.get("claim_scope"),
            scope_line=(
                f"Results are scoped to the stratum where full-model control "
                f"itself steers the collective ({n_prim} of {n_prim + n_excl} "
                f"episodes); this is one illustrative episode and supports no "
                f"aggregate claim."),
            reliability_threshold=ft.get("reliability_threshold"),
        ),
        envelope=dict(
            horizon=horizon, lower=env_ref["lower"], upper=env_ref["upper"],
            quantile=env_ref.get("quantile"),
            achieved_joint_pass=env_ref.get("calibration", {}).get("achieved_joint_pass"),
            target_joint_pass=env_ref.get("calibration", {}).get("target_joint_pass"),
            n_calibration=env_ref.get("calibration", {}).get("n_calibration"),
            n_validation=env_ref.get("calibration", {}).get("n_validation"),
            source=ur_path.name,
        ),
        arm_summary={a: dict(final_H=float(v["final_H_current"]),
                             mean_actuators=float(v["mean_actuators"]),
                             success=bool(v["score"]["success"]),
                             task_met=bool(v["score"]["task_met"]),
                             identity_valid=bool(v["score"]["identity_valid"]))
                     for a, v in ep["arms"].items()},
    )

    DEMO_DATA.mkdir(parents=True, exist_ok=True)
    dump_json(out, DEMO_DATA / OUT_NAME)
    kb = (DEMO_DATA / OUT_NAME).stat().st_size / 1024
    print(f"wrote {DEMO_DATA / OUT_NAME} ({kb:.0f} KB) in {time.time()-t_start:.1f}s")
    print(f"  clarity trajectory: seed {seed}, arm {arm}, final H "
          f"{r['final_H_current']:.3f}  ({rule}; {n_eligible} eligible)")
    print(f"  frames {n_frames}  (emergence 0..{T0}, control {T0}..{T0+horizon-1}, "
          f"release {T0+horizon}..{T0+horizon+n_rel-1})")
    print(f"  turn h0={h0} -> h*={h_star} (90 deg cw); k_act={ep['k_act']}; "
          f"stratum {n_prim} of {n_prim + n_excl}")
    print("  all replay assertions passed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fixedk")
