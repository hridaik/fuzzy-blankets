"""Stage 6.8 -> interactive_demo/data/stage6_8_bundle.json.

VISUALIZATION EXPORT ONLY. This script produces no new scientific statistic.
It (a) SELECTS representative episodes from the frozen result files by an
objective rule, (b) REPLAYS the frozen simulator deterministically to recover
the per-timestep headings and oracle graphs that the science runs never
persisted, and (c) copies the already-frozen inference results verbatim.

Every replayed quantity is asserted against the corresponding frozen file, so
a replay that drifted from the recorded run fails loudly instead of silently
feeding the demo a different trajectory. Nothing here is written back into
`data/`; the only output is the demo bundle.

Selection rule (R1), applied identically everywhere and recorded in
`interactive_demo/STAGE6_8_9_VISUALIZATION_NOTES.md`:

    Given candidate episodes and a metric list, take the median of each metric
    across candidates, score each episode by
        sum_m |x_m - median_m| / MAD_m        (MAD = median absolute deviation;
                                               a metric with MAD = 0 scores 0)
    and choose the minimum. Ties break to the lowest seed id.

This picks the episode closest to the middle of the reported distribution, not
the most photogenic one.
"""
from __future__ import annotations

import base64
import json
import sys

import numpy as np

from common_68 import (ModelParams, Lattice, load_json, dump_json, DATA_DIR, RHO, OMEGA,
                       lattice_positions, flatten_edges, visibility_table)
from fov_dynamics import FovSimulator, GateParams
from episode_data import make_simulator, run_episode
import adaptive_control as ac
import candidate_detection as cd
from episode_data import observation_record

DEMO_DATA = DATA_DIR.parents[1] / "interactive_demo" / "data"
T_START, T_END = 40, 100          # run_oracle_characterization's window
SERIES_T = list(range(55, 67))    # run_boundary_pipeline's series window
T0_CONTROL = 60


# ------------------------------------------------------------------ rule R1 --
def pick_representative(cands, metrics, key_seed="seed"):
    """R1. `cands` is a list of dicts, `metrics` a list of (name, fn)."""
    if not cands:
        return None, []
    X = np.array([[fn(c) for _, fn in metrics] for c in cands], dtype=float)
    med = np.median(X, axis=0)
    mad = np.median(np.abs(X - med), axis=0)
    scale = np.where(mad > 0, mad, np.inf)          # zero-spread metric contributes 0
    score = (np.abs(X - med) / scale).sum(axis=1)
    order = sorted(range(len(cands)), key=lambda i: (score[i], cands[i][key_seed]))
    table = [dict(seed=cands[i][key_seed], score=float(score[i]),
                  metrics={metrics[m][0]: float(X[i, m]) for m in range(len(metrics))})
             for i in order]
    return cands[order[0]], dict(metric_names=[m for m, _ in metrics],
                                 median=[float(v) for v in med],
                                 mad=[float(v) for v in mad], ranked=table)


# ------------------------------------------------------------- encoders ------
def enc_z(z):
    """400 headings -> a 400-char string of '0'..'3' (compact, exact)."""
    return "".join(chr(48 + int(v)) for v in z)


def enc_mask(mask):
    """Boolean edge mask -> base64 of a packed bit array."""
    return base64.b64encode(np.packbits(np.asarray(mask, dtype=bool)).tobytes()).decode("ascii")


# ---------------------------------------------------------------- replays ----
class AlwaysLive(FovSimulator):
    """L0 reference: every geometric Moore edge always live (the subclass
    `run_oracle_characterization._AlwaysLive` used to produce the frozen L0 row)."""
    def visible_mask(self, z):
        return np.ones(self.n_edges, dtype=bool)


def build_lattice_payload(sim):
    P = lattice_positions(sim.nn)
    L = int(round(sim.nn ** 0.5))
    recv, slot, src = flatten_edges(sim.lattice)
    nbr, slt = {}, {}
    for i in range(sim.nn):
        sel = recv == i
        nbr[str(i)] = [int(x) for x in src[sel]]
        slt[str(i)] = [int(x) for x in slot[sel]]
    return dict(nn=sim.nn, L=L,
                positions=[[int(L - 1 - int(p[1])), int(p[0])] for p in P],  # [row, col] for iiXY
                neighbors=nbr, slots=slt,
                vis_table=[[bool(v) for v in row] for row in visibility_table()])


def frames_for(sim, seed, gate_params, I_ref, t_start, t_end):
    """Deterministic replay: headings, oracle B^D for the fixed reference
    interior, and (L3 only) the latent gate state, per timestep."""
    res = sim.run(nt=t_end + 1, seed=seed, gate_params=gate_params, record_oracle=True)
    frames = []
    for t in range(t_start, t_end + 1):
        m = res.active_mask_hist[t]
        f = dict(t=t, z=enc_z(res.z_hist[t]),
                 BD=[int(x) for x in sim.oracle_B_D(m, I_ref)])
        if res.gate_hist is not None:
            f["gate"] = enc_mask(res.gate_hist[t])
        frames.append(f)
    return res, frames


def main():
    op = load_json(DATA_DIR / "episode_screen.json")["ops"]["OP1"]
    nn, beta, s = op["nn"], op["beta"], op["s"]
    lattice = Lattice(nn=nn, nh=8)
    params = ModelParams(beta=beta, precB=s * RHO, precC=s * OMEGA)
    sim = FovSimulator(params, lattice)
    sim0 = AlwaysLive(params, lattice)

    oracle = load_json(DATA_DIR / "oracle_interface.json")
    rev_series = load_json(DATA_DIR / "oracle_reveal__series.json")
    inf_series = load_json(DATA_DIR / "boundary_inference__series.json")
    rev_gated = load_json(DATA_DIR / "oracle_reveal__gated.json")
    gate_choice = load_json(DATA_DIR / "gate_choice.json")
    control = load_json(DATA_DIR / "control.json")

    out = dict(
        provenance=dict(
            stage="6.8",
            operating_point=dict(nn=nn, beta=beta, s=s, rho=s * RHO, omega=s * OMEGA),
            sources=["oracle_interface.json",
                     "boundary_inference__series.json", "oracle_reveal__series.json",
                     "boundary_inference__gated.json", "oracle_reveal__gated.json",
                     "control.json", "gate_choice.json"],
            replay_note=("Per-timestep headings and live-edge state were not persisted by the "
                         "science runs. They are regenerated here by a deterministic replay of "
                         "the frozen simulator at the same seed and configuration, and every "
                         "replayed oracle interface is asserted equal to the frozen file's "
                         "recorded value. No new statistic is computed."),
            selection_rule=("R1: minimise sum_m |x_m - median_m| / MAD_m over the reported "
                            "metrics; ties to the lowest seed id."),
        ),
        lattice=build_lattice_payload(sim),
        conditions={}, selection={},
    )

    # ---------------------------------------------------------------- L0 -----
    l0 = [r for r in oracle["runs"] if r["label"] == "L0_fixed_graph"]
    pick, sel = pick_representative(l0, [
        ("mean_B_size", lambda r: r["mean_B_size"]),
        ("mean_symdiff", lambda r: r["mean_symdiff"]),
        ("mean_B_turnover", lambda r: r["mean_B_turnover"]),
        ("n_distinct_interfaces", lambda r: r["n_distinct_interfaces"]),
    ])
    out["selection"]["L0"] = dict(chosen_seed=pick["seed"], candidates=len(l0), **sel)
    I_ref = np.array(pick["interior"])
    _, frames = frames_for(sim0, pick["seed"], None, I_ref, T_START, T_END)
    for f in frames:                                   # integrity: replay == frozen
        assert f["BD"] == sorted(pick["B_series"][str(f["t"])]), \
            f"L0 replay diverged from oracle_interface.json at t={f['t']}"
    out["conditions"]["L0"] = dict(
        label="L0 — fixed interaction graph", seed=pick["seed"], t_start=T_START, t_end=T_END,
        I_ref=[int(x) for x in I_ref], frames=frames,
        has_tracked=False, has_inference=False, has_gate=False,
        note="Every Moore edge is always live. The interface never changes.",
        stats=dict(mean_B_size=pick["mean_B_size"], n_distinct=pick["n_distinct_interfaces"],
                   mean_symdiff=pick["mean_symdiff"]))

    # ---------------------------------------------------------------- L2 -----
    # Restricted to seeds that ALSO have stored inference overlays, so the
    # overlay controls are backed by real data at every timestep they offer.
    seeds_with_inf = sorted({r["seed"] for r in rev_series["runs"]})
    l2 = [r for r in oracle["runs"] if r["label"] == "L2_fov" and r["seed"] in seeds_with_inf]
    pick, sel = pick_representative(l2, [
        ("mean_B_size", lambda r: r["mean_B_size"]),
        ("mean_symdiff", lambda r: r["mean_symdiff"]),
        ("mean_B_turnover", lambda r: r["mean_B_turnover"]),
        ("mean_node_lifetime", lambda r: r["mean_node_lifetime"]),
        ("n_distinct_interfaces", lambda r: r["n_distinct_interfaces"]),
    ])
    out["selection"]["L2"] = dict(chosen_seed=pick["seed"], candidates=len(l2),
                                  restricted_to_seeds_with_inference=seeds_with_inf, **sel)
    seed2 = pick["seed"]
    I_ref = np.array(pick["interior"])
    res2, frames = frames_for(sim, seed2, None, I_ref, T_START, T_END)
    for f in frames:
        assert f["BD"] == sorted(pick["B_series"][str(f["t"])]), \
            f"L2 replay diverged from oracle_interface.json at t={f['t']}"

    # The tracked collective shown in the demo is the one the stored inference
    # results were actually computed for -- the series pipeline's own tracked
    # lineage. Using detection.json's largest candidate instead would pair the
    # boundaries with a DIFFERENT collective: at every timestep in this window
    # the two sets are disjoint (Jaccard 0.00), so the overlays would be drawn
    # around a group they do not belong to.
    tracked = {}
    for r in inf_series["runs"]:
        if r["seed"] == seed2:
            tracked[r["t"]] = sorted(r["I"])
    inference = {}
    for r in rev_series["runs"]:
        if r["seed"] != seed2:
            continue
        m = sim.visible_mask(res2.z_hist[r["t"]])
        bd_now = [int(x) for x in sim.oracle_B_D(m, np.array(sorted(r["I"] if "I" in r else [])))] \
            if "I" in r else None
        inference[r["t"]] = dict(B_D=r["B_D"], B_pred=r["B_pred"],
                                 B_causal=r["B_causal_sampled"],
                                 B_causal_exact=r["B_causal_exact"],
                                 J_causal=r["structural_agreement"]["jaccard"],
                                 J_pred=r["predictive_vs_BD"]["jaccard"])
    for r in inf_series["runs"]:
        if r["seed"] == seed2 and r["t"] in inference:
            inference[r["t"]]["I"] = r["I"]
    # integrity: the frozen reveal's B^D must equal the replay's B^D for its own I
    for t, d in inference.items():
        assert sorted(d["I"]) == tracked[t], f"tracked/inference interior mismatch at t={t}"
        m = sim.visible_mask(res2.z_hist[t])
        assert sorted(d["B_D"]) == [int(x) for x in sim.oracle_B_D(m, np.array(sorted(d["I"])))], \
            f"L2 inference-window replay diverged at t={t}"
    out["conditions"]["L2"] = dict(
        label="L2 — heading-dependent FOV", seed=seed2, t_start=T_START, t_end=T_END,
        I_ref=[int(x) for x in I_ref], frames=frames,
        tracked={str(k): v for k, v in tracked.items()},
        tracked_t_start=min(tracked), tracked_t_end=max(tracked),
        inference={str(k): v for k, v in inference.items()},
        has_tracked=True, has_inference=True, has_gate=False,
        note="A bird sees only the neighbours in front of it, so the interface moves with headings.",
        stats=dict(mean_B_size=pick["mean_B_size"], n_distinct=pick["n_distinct_interfaces"],
                   mean_symdiff=pick["mean_symdiff"],
                   mean_node_lifetime=pick["mean_node_lifetime"]))

    # ---------------------------------------------------------------- L3 -----
    gp_d = gate_choice["chosen"]
    gp = GateParams(**gp_d)
    g3 = [r for r in rev_gated["runs"]]
    pick3, sel3 = pick_representative(g3, [
        ("BD_size", lambda r: len(r["B_D"])),
        ("J_causal", lambda r: r["structural_agreement"]["jaccard"]),
        ("B_pred_size", lambda r: len(r["B_pred"])),
        ("B_causal_size", lambda r: len(r["B_causal_sampled"])),
    ])
    out["selection"]["L3"] = dict(chosen_seed=pick3["seed"], candidates=len(g3), **sel3)
    seed3, t3 = pick3["seed"], pick3["t"]
    inf_gated = load_json(DATA_DIR / "boundary_inference__gated.json")
    I3 = next(r["I"] for r in inf_gated["runs"] if r["seed"] == seed3 and r["t"] == t3)
    res3, frames3 = frames_for(sim, seed3, gp, np.array(sorted(I3)), T_START, T_END)
    m3 = res3.active_mask_hist[t3]
    assert sorted(pick3["B_D"]) == [int(x) for x in sim.oracle_B_D(m3, np.array(sorted(I3)))], \
        "L3 replay diverged from oracle_reveal__gated.json"
    out["conditions"]["L3"] = dict(
        label="L3 — FOV + hidden gates", seed=seed3, t_start=T_START, t_end=T_END,
        I_ref=sorted(I3), frames=frames3,
        tracked={}, inference={str(t3): dict(
            I=sorted(I3), B_D=pick3["B_D"], B_pred=pick3["B_pred"],
            B_causal=pick3["B_causal_sampled"], B_causal_exact=pick3["B_causal_exact"],
            J_causal=pick3["structural_agreement"]["jaccard"],
            J_pred=pick3["predictive_vs_BD"]["jaccard"])},
        has_tracked=False, has_inference=True, has_gate=True,
        inference_single_t=t3,
        gate_params=dict(p01=gp.p01, p10=gp.p10),
        note="Visible edges are additionally gated by a hidden two-state Markov process.",
        stats=dict(BD_size=len(pick3["B_D"]), J_causal=pick3["structural_agreement"]["jaccard"]))

    # ------------------------------------------------------------ control ----
    seeds_ctl = sorted({r["seed"] for r in control["runs"]})
    arms = control["arms"]
    by_seed = []
    for sd in seeds_ctl:
        rows = {r["arm"]: r for r in control["runs"] if r["seed"] == sd}
        if set(rows) != set(arms):
            continue
        by_seed.append(dict(seed=sd, rows=rows,
                            split=next(iter(rows.values()))["split"]))
    pickc, selc = pick_representative(
        by_seed, [(a, (lambda a: (lambda c: c["rows"][a]["final_target_fraction"]))(a)) for a in arms])
    out["selection"]["control"] = dict(chosen_seed=pickc["seed"], candidates=len(by_seed), **selc)

    seedc = pickc["seed"]
    cal, feas = control["calibration"], control["feasibility"]
    chosen = control["setting"]
    k_act, horizon = chosen["k_act"], control["T_CONTROL"]
    snap = load_json(DATA_DIR / "boundary_inference__snapshot.json")
    Bpred = next((r["predictive"]["B_pred"] for r in snap["runs"]
                  if r["seed"] == seedc and r["method"] == "affinity_louvain"
                  and r["t"] == T0_CONTROL), None)
    resc = run_episode(sim, seedc, nt=T0_CONTROL + 2, record_oracle=False)
    z_prefix = resc.z_hist[:T0_CONTROL + 1]
    obs = observation_record(sim, resc.z_hist, T0_CONTROL)
    ok, _ = cd.propose(obs)
    I0 = np.array(sorted(max(ok, key=lambda c: c.size).members))
    h_star = ac.target_heading(resc.z_hist[T0_CONTROL], I0)

    arm_payload, schedule = {}, None
    for arm in arms:                                    # same order as run_control.ARMS
        r = ac.run_arm(sim, z_prefix, arm, seedc, h_star, B_pred=Bpred,
                       theta=cal["theta"], q_support=cal["q_support"],
                       t_control=horizon, k_act=k_act, I0=I0,
                       budget_schedule=(None if arm == "adaptive_causal" else schedule))
        if arm == "adaptive_causal":
            schedule = r["actuator_schedule"]
        stored = pickc["rows"][arm]
        assert abs(r["final_target_fraction"] - stored["final_target_fraction"]) < 1e-12, \
            f"control replay diverged for arm {arm}"
        zh = r.pop("z_hist")
        arm_payload[arm] = dict(
            frames=[dict(step=i, z=enc_z(zh[i])) for i in range(len(zh))],
            records=[dict(step=x["step"], actuators=x["actuators"],
                          target_fraction=x["target_fraction"], I_size=x["I_size"])
                     for x in r["records"]],
            final_target_fraction=r["final_target_fraction"],
            mean_actuators=r["mean_actuators"])
    out["control"] = dict(
        seed=seedc, split=pickc["split"], t0=T0_CONTROL, horizon=horizon, k_act=k_act,
        h_star=int(h_star), I0=[int(x) for x in I0], arms=arms, by_arm=arm_payload,
        below_feasibility_threshold=control["below_feasibility_threshold"],
        caveat="The oracle task was not reliably feasible at this collective size.")

    DEMO_DATA.mkdir(parents=True, exist_ok=True)
    dump_json(out, DEMO_DATA / "stage6_8_bundle.json")
    size = (DEMO_DATA / "stage6_8_bundle.json").stat().st_size / 1024
    print(f"wrote {DEMO_DATA/'stage6_8_bundle.json'} ({size:.0f} KB)")
    print(f"  L0 seed {out['conditions']['L0']['seed']}, L2 seed {out['conditions']['L2']['seed']}, "
          f"L3 seed {out['conditions']['L3']['seed']}, control seed {seedc}")
    print(f"  L2 tracked timesteps {len(out['conditions']['L2']['tracked'])}, "
          f"inference timesteps {len(out['conditions']['L2']['inference'])}")


if __name__ == "__main__":
    main()
