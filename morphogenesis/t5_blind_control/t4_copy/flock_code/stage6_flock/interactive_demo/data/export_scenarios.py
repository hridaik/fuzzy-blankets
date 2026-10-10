"""Exports real Python-simulator trajectory bundles for the interactive HTML
demo. NO dynamics are reimplemented in JavaScript -- the browser only reads
these JSON files.

v2 of this script (UX refinement pass). What changed from v1, and why:

- Every bundle now also captures `natural_action_hist` / `applied_action_hist`
  / `overridden_hist` from the SAME deterministic simulation run (same seed,
  same lattice, same interventions) that v1 already used for `headings`.
  These arrays were always computed by `flock_sim.active_inference.step`
  internally; v1 simply discarded them. Re-running to capture them changes
  NOTHING about the trajectories themselves (bit-identical `headings` output,
  verified by the smoke test in this directory) -- it only recovers a
  diagnostic the simulator was already producing. This is the "actual
  override count" (Part 1C of the UX refinement brief) and is NOT a new
  scientific experiment.
- Every (method, target) combination scientifically meaningful for the
  primary demo flock is now precomputed (9 methods x 3 nontrivial targets),
  replacing v1's ad hoc "only the default method supports target-switching"
  behavior.
- A `V2_conservative_shell` method (k=ceil(0.75*|B^D_0|), DEG rule -- V2's
  own frozen policy) is added so the V2-vs-V3 budget/reliability trade-off
  requested in the UX brief can be shown directly.
- Every bundle carries a `summary` (trajectory-level: this run's actual
  outcome) and an `ensemble` block (population-level: cross-referenced from
  v3_refinement/data/*.json and v2_interface_control/data/*.json WHERE a
  genuinely matching per-flock condition exists -- never fabricated, and
  left `available: false` otherwise, per the UX brief's Part 12).

Run from stage6_flock/interactive_demo/data/:
    python3 export_scenarios.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

DEMO_DATA_DIR = Path(__file__).resolve().parent
ROOT = DEMO_DATA_DIR.parents[1]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))

from flock_sim.lattice import Lattice, bird_to_rowcol  # noqa: E402
from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from flock_sim.spectral import analyze_window  # noqa: E402
from flock_sim.model import rotate_cw, rotate_ccw  # noqa: E402
from analysis.baseline_characterization import find_qualifying_t0  # noqa: E402
from common_v2 import dynamical_shell  # noqa: E402
from selection_rules import rule_A_degree, rule_C_patch, rule_D_random  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover, q_coverage_fraction  # noqa: E402
from coverage_metrics import core_coverage, multiplicity_summary  # noqa: E402

T_U, T_R, TW = 20, 20, 5
FROZEN_Q, FROZEN_GAMMA = 2, 0.5
V2_FRACTION = 0.75
C_RECOVER, RECOVER_DWELL = 0.8, 3
TARGET_DWELL = 3  # exploratory only -- borrowed from the frozen recovery dwell; NOT a frozen
                   # protocol quantity for H*, see METRIC_DEFINITIONS.md
PROTOCOL_VERSION = "V3 (protocol_v3.yaml, sha256 6907b889c320ccec49b5c5ee0f7bde2ed9cb291c8a8e3d7feadf65a87b4b09ba)"

V3_DATA = ROOT / "v3_refinement" / "data"
V2_DATA = ROOT / "v2_interface_control" / "data"


# ---------------------------------------------------------------- discovery

def discover_flock(seed: int, nt_search: int = 60):
    lattice = Lattice(nn=100, nh=8)
    res = run_simulation(nn=100, nt=nt_search, seed=seed, lattice=lattice)
    q = find_qualifying_t0(res.z_hist)
    if q is None:
        return None
    t0, I0, h0 = q["t0"], np.array(q["I0"]), q["h0"]
    return dict(seed=seed, lattice=lattice, t0=t0, I0=I0, h0=h0, eigengap=q["eigengap"])


def compute_B_F0(fl):
    lattice, seed, t0, I0 = fl["lattice"], fl["seed"], fl["t0"], fl["I0"]
    res = run_simulation(nn=100, nt=t0, seed=seed, lattice=lattice)
    window = res.z_hist[t0 - TW + 1: t0 + 1]
    sr = analyze_window(window, refclust=I0)
    return sr.boundary_nodes


def target_headings(h0: int) -> dict:
    """The 3 nontrivial targets for this h0: the frozen-protocol 90 deg CW
    turn, the 90 deg CCW turn, and the 180 deg opposite."""
    return dict(cw=int(rotate_cw(h0)), ccw=int(rotate_ccw(h0)), opposite=int(rotate_cw(rotate_cw(h0))))


# ------------------------------------------------------------- ensemble refs

_cs_cache, _mi_cache, _v2_cache = None, None, None


def _load_ensembles():
    global _cs_cache, _mi_cache, _v2_cache
    if _cs_cache is None:
        _cs_cache = json.loads((V3_DATA / "coverage_sweep.json").read_text())
        _mi_cache = json.loads((V3_DATA / "minimal_interface.json").read_text())
        _v2_cache = json.loads((V2_DATA / "replication_results.json").read_text())


def ensemble_frozen_v3(seed: int) -> dict:
    """Exact match: the frozen (q=2, gamma=0.5) condition for this seed,
    from v3_refinement/data/minimal_interface.json (Part 1D)."""
    _load_ensembles()
    row = next((r for r in _mi_cache["per_q"]["2"] if r["gamma"] == FROZEN_GAMMA), None)
    if row is None:
        return dict(available=False)
    rec = next((r for r in row["per_flock"] if r["seed"] == seed), None)
    if rec is None:
        return dict(available=False)
    return dict(available=True, source="v3_refinement/data/minimal_interface.json (q=2, gamma=0.5)",
                matched_exactly=True, matched_k=rec["k"], matched_f_A=rec["f_A"],
                success_probability=rec["p_success"], mean_actuators=rec["k"],
                n_replicates=_mi_cache["n_replicates"])


def ensemble_closest_by_rule(seed: int, rule: str, target_k: int) -> dict:
    """Closest-by-k condition for this (seed, rule) in coverage_sweep.json
    (Part 1B). Reports the ACTUAL matched k/fraction -- never claims an
    exact match it doesn't have."""
    _load_ensembles()
    fl = next((f for f in _cs_cache["flocks"] if f["seed"] == seed), None)
    if fl is None:
        return dict(available=False)
    conds = [c for c in fl["conditions"] if c["rule"] == rule]
    if not conds:
        return dict(available=False)
    best = min(conds, key=lambda c: abs(c["n_actuators"] - target_k))
    return dict(available=True,
                source=f"v3_refinement/data/coverage_sweep.json (rule={rule})",
                matched_exactly=(best["n_actuators"] == target_k),
                matched_k=best["n_actuators"], matched_f_A=best["f_A_target"],
                success_probability=best["p_success"], mean_actuators=best["n_actuators"],
                n_replicates=best["n_replicates"])


def ensemble_v2_baseline(seed: int) -> dict:
    _load_ensembles()
    fl = next((f for f in _v2_cache["flocks"] if f.get("seed") == seed), None)
    if fl is None or "rules" not in fl:
        return dict(available=False)
    rec = fl["rules"]["reference_baseline"]
    return dict(available=True, source="v2_interface_control/data/replication_results.json (reference_baseline)",
                matched_exactly=True, matched_k=0, matched_f_A=0.0,
                success_probability=rec["p_success"], mean_actuators=0,
                n_replicates=rec["n_replicates"])


NO_ENSEMBLE = dict(available=False)


# ------------------------------------------------------------- explanations

WHY = {
    "no_control": dict(
        success="Reached the target spontaneously, without intervention -- rare; see ensemble baseline rate.",
        fail="No intervention applied; the flock continued its pre-existing dynamics and did not reach the target."),
    "random_exterior": dict(
        success="Succeeded by chance: this particular random exterior draw happened to overlap the true interaction shell.",
        fail="Failed: actuators drawn from anywhere outside the core, not the true interaction shell -- most have no direct edge into the frozen core."),
    "fiedler_boundary": dict(
        success="Succeeded despite a small, spectral-only boundary -- atypical; V1/V2 found this arm fails completely (p_success=0.00) in general.",
        fail="Failed: only {k} controlled birds, with incomplete overlap with the true one-step interaction shell (B^D)."),
    "connected_patch": dict(
        success="Succeeded, but relied on a spatially concentrated patch -- V3 found this rule the weakest and most variable across flocks.",
        fail="Weak: sufficient actuator count, but support was concentrated on one part of the shell, leaving the rest of the core's boundary unforced."),
    "distributed_shell": dict(
        success="Succeeded: a random sample from the TRUE interaction shell -- being on the correct interface mattered more than exact node ranking.",
        fail="Failed on this particular random draw from the correct shell; see ensemble statistics for the typical outcome at this budget."),
    "v2_conservative_shell": dict(
        success="Succeeded: a large, conservative fraction of the true interaction shell gives high reliability at higher actuator cost.",
        fail="Failed despite a conservative budget on this particular run; see ensemble statistics for this flock's typical reliability."),
    "sparse_interface_multicover": dict(
        success="Succeeded: enough of the core received redundant (>=2 actuator) target-consistent support, using fewer actuators than the conservative V2 policy.",
        fail="Failed at this sparse budget -- V3 found the double-coverage criterion trades some reliability for a smaller footprint; see ensemble statistics."),
    "full_dynamical_shell": dict(
        success="Succeeded: strong redundant support across the entire interaction interface, at the highest actuator cost of any admissible method.",
        fail="Failed even at full-shell forcing -- exceptionally rare; check ensemble statistics."),
    "direct_core_diagnostic": dict(
        success="Succeeded trivially: core birds are forced directly, bypassing the interface entirely -- inadmissible as a control method, shown only for diagnostic contrast.",
        fail="Even direct core forcing failed on this particular run; check ensemble statistics."),
}


def why_text(method_id: str, success: bool, k: int) -> str:
    branch = WHY.get(method_id, {})
    text = branch.get("success" if success else "fail", "")
    return text.format(k=k)


# --------------------------------------------------------------- core build

def dwell_min_crossing(series: list[float], threshold: float, dwell: int, start: int, end: int):
    """First index t (start <= t <= end-dwell) such that series[t:t+dwell] are
    all >= threshold. Returns None if never achieved with the required dwell
    in [start, end]."""
    n = len(series)
    for t in range(start, min(end, n - dwell) + 1):
        if all(series[t + j] >= threshold for j in range(dwell)):
            return t
    return None


def first_crossing(series: list[float], threshold: float, start: int, end: int):
    for t in range(start, min(end, len(series) - 1) + 1):
        if series[t] >= threshold:
            return t
    return None


def build_bundle(fl, B_D0, B_F0, actuators, target_id, h_star, method_id, method_label,
                  method_subtitle, method_short, diagnostic_only, ensemble):
    seed, lattice, t0, I0, h0 = fl["seed"], fl["lattice"], fl["t0"], fl["I0"], fl["h0"]
    nt_total = t0 + T_U + T_R
    interventions = make_pulse(actuators, h_star, t0=t0, t_u=T_U) if len(actuators) else None
    res = run_simulation(nn=100, nt=nt_total, seed=seed, lattice=lattice, interventions=interventions)

    L = lattice.L
    positions = [list(map(int, p)) for p in zip(*bird_to_rowcol(np.arange(100), L))]
    neighbors = {int(i): lattice.neighbor_ids[i].tolist() for i in range(100)}

    A_list = [int(a) for a in actuators]
    Hstar_t, C_t, Gamma_t, Gamma2_t, n_active_t = [], [], [], [], []
    for t in range(nt_total + 1):
        Hstar_t.append(round(target_heading_fraction(res.z_hist[t], I0, h_star), 4))
        C_t.append(round(coherence(res.z_hist[t], I0), 4))
        active = list(interventions.get(t, {}).keys()) if (interventions and t < nt_total) else []
        n_active_t.append(len(active))
        if active:
            Gamma_t.append(round(core_coverage(active, I0, lattice), 4))
            ms = multiplicity_summary(active, I0, lattice)
            Gamma2_t.append(round(ms["frac_m_ge2"], 4))
        else:
            Gamma_t.append(0.0)
            Gamma2_t.append(0.0)

    control_start, control_end, release_end = t0, t0 + T_U, t0 + T_U + T_R

    # --- summary (trajectory-level, this run only) ---
    success = Hstar_t[control_end] >= 0.8            # frozen, unchanged scientific success definition (endpoint)
    persistent = Hstar_t[release_end] >= 0.5          # frozen persistence definition
    peak_actuators = max(n_active_t) if any(n_active_t) else 0
    bird_steps = int(sum(n_active_t))
    override_count = int(res.overridden_hist.sum())
    t_hit_dwell = dwell_min_crossing(Hstar_t, 0.8, TARGET_DWELL, control_start, release_end)
    t_hit_first = first_crossing(Hstar_t, 0.8, control_start, release_end)
    t_recovery = dwell_min_crossing(C_t, C_RECOVER, RECOVER_DWELL, control_start, release_end)

    static_ms = multiplicity_summary(A_list, I0, lattice) if A_list else dict(mean_m=0.0, frac_m_ge2=0.0)
    static_gamma = core_coverage(A_list, I0, lattice) if A_list else 0.0

    summary = dict(
        success=bool(success), persistent=bool(persistent),
        peak_actuators=int(peak_actuators), bird_steps=bird_steps,
        override_count=override_count,
        time_to_target_dwell3=(t_hit_dwell - control_start) if t_hit_dwell is not None else None,
        time_to_target_dwell3_abs=t_hit_dwell,
        time_to_target_first_crossing=(t_hit_first - control_start) if t_hit_first is not None else None,
        recovery_time=(t_recovery - control_start) if t_recovery is not None else None,
        recovery_time_abs=t_recovery,
        final_post_release_Hstar=Hstar_t[release_end],
        Hstar_at_control_end=Hstar_t[control_end],
        min_coherence_during_control=round(min(C_t[control_start:control_end + 1]), 4),
        mean_multiplicity=round(static_ms["mean_m"], 4),
        gamma=round(static_gamma, 4),
        gamma2=round(static_ms["frac_m_ge2"], 4),
        n_actuators=len(A_list), f_A=(len(A_list) / len(B_D0)) if len(B_D0) else 0.0,
        n_shell=len(B_D0),
    )

    scenario_id = f"seed{seed}__{method_id}__{target_id}"

    return dict(
        scenario_id=scenario_id, flock_id=f"seed{seed}",
        method_id=method_id, method_label=method_label, method_subtitle=method_subtitle,
        method_short=method_short, diagnostic_only=diagnostic_only,
        target_id=target_id,
        initial_heading=int(h0), target_heading=int(h_star),
        lattice=dict(L=L, nn=100, positions=positions), neighbors=neighbors,
        roles=dict(core=I0.tolist(), dynamic_shell=B_D0.tolist(), fiedler=B_F0.tolist()),
        actuators=A_list,
        timeline=dict(start=0, identify=int(t0), control_start=int(control_start),
                      control_end=int(control_end), release_end=int(release_end), nt_total=int(nt_total)),
        trajectory=res.z_hist.tolist(),
        control=dict(natural_actions=res.natural_action_hist.tolist(),
                     applied_actions=res.applied_action_hist.tolist(),
                     overridden=res.overridden_hist.astype(int).tolist()),
        metrics=dict(Hstar=Hstar_t, coherence=C_t, coverage=Gamma_t, double_coverage=Gamma2_t,
                     n_actuators_t=n_active_t),
        summary=summary,
        ensemble=ensemble,
        why=why_text(method_id, success, len(A_list)),
        provenance=dict(seed=int(seed), protocol_version=PROTOCOL_VERSION,
                        source_result_json="v3_refinement/data/{coverage_sweep,minimal_interface}.json; "
                                            "v2_interface_control/data/replication_results.json",
                        target_heading=int(h_star), actuator_rule=method_id, success=bool(success)),
        single_run_disclaimer=(
            "This bundle is ONE continuous stochastic realization (the flock's own discovery seed, "
            "continued through control and release). The `summary` block describes THIS run only. "
            "The `ensemble` block (where available) reports replicated statistics from v3_refinement/ "
            "or v2_interface_control/ -- the two are never the same number and must not be conflated."
        ),
    )


def dump(bundle, name):
    path = DEMO_DATA_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(bundle, f)
    s = bundle["summary"]
    print(f"wrote {name}.json  ({path.stat().st_size/1024:.0f} KB)  success={s['success']} "
          f"k={s['n_actuators']} H*(end)={s['Hstar_at_control_end']}")


def main():
    for old in DEMO_DATA_DIR.glob("seed*_*.json"):
        old.unlink()  # clear v1-schema bundles before writing the v2 schema

    # ================= Primary demo flock: seed 16 =================
    fl = discover_flock(16)
    assert fl is not None
    lattice, I0 = fl["lattice"], fl["I0"]
    B_D0 = dynamical_shell(lattice, I0)
    B_F0 = compute_B_F0(fl)
    targets = target_headings(fl["h0"])

    A_cover = min_actuators_for_multicover(B_D0, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
    k = len(A_cover)
    A_patch = rule_C_patch(B_D0, I0, lattice, k)
    A_random_shell = rule_D_random(B_D0, k, np.random.default_rng(42))
    A_random_exterior = np.random.default_rng(43).choice(
        np.setdiff1d(np.arange(100), I0), size=k, replace=False).tolist()
    k_v2 = max(1, math.ceil(V2_FRACTION * len(B_D0)))
    A_v2 = rule_A_degree(B_D0, I0, lattice, k_v2)

    METHODS = [
        dict(id="no_control", label="No Control", subtitle="Natural dynamics, no intervention",
             short="No Control", actuators=[], diagnostic=False,
             ensemble=lambda: ensemble_v2_baseline(16)),
        dict(id="random_exterior", label="Random Exterior", subtitle="Generic external forcing (wrong pool)",
             short="Random Exterior", actuators=A_random_exterior, diagnostic=False,
             ensemble=lambda: NO_ENSEMBLE),
        dict(id="fiedler_boundary", label="Fiedler Boundary", subtitle="Spectral separator, not the true interface",
             short="Fiedler Boundary", actuators=B_F0.tolist(), diagnostic=False,
             ensemble=lambda: NO_ENSEMBLE),
        dict(id="connected_patch", label="Connected Shell Patch", subtitle="Correct interface, concentrated support",
             short="Connected Patch", actuators=A_patch, diagnostic=False,
             ensemble=lambda: ensemble_closest_by_rule(16, "PATCH_patch", k)),
        dict(id="distributed_shell", label="Distributed Shell Sample", subtitle="Correct interface, random distribution",
             short="Distributed Shell", actuators=A_random_shell, diagnostic=False,
             ensemble=lambda: ensemble_closest_by_rule(16, "R_random", k)),
        dict(id="v2_conservative_shell", label="V2 Conservative Shell", subtitle="Large-budget policy (V2, frozen)",
             short="V2 Conservative", actuators=A_v2, diagnostic=False,
             ensemble=lambda: ensemble_closest_by_rule(16, "DEG_degree", k_v2)),
        dict(id="sparse_interface_multicover", label="Sparse Interface Multicover", subtitle="Our refined controller (V3)",
             short="Our Method", actuators=A_cover, diagnostic=False,
             ensemble=lambda: ensemble_frozen_v3(16)),
        dict(id="full_dynamical_shell", label="Full Dynamical Shell", subtitle="Maximal admissible interface control",
             short="Full Shell", actuators=B_D0.tolist(), diagnostic=False,
             ensemble=lambda: ensemble_closest_by_rule(16, "COVER_greedy", len(B_D0))),
        dict(id="direct_core_diagnostic", label="Direct Core Forcing", subtitle="Diagnostic only -- bypasses the interface",
             short="Direct Core", actuators=I0.tolist(), diagnostic=True,
             ensemble=lambda: NO_ENSEMBLE),
    ]

    manifest_primary = []
    for m in METHODS:
        for target_id, h_star in targets.items():
            bundle = build_bundle(fl, B_D0, B_F0, m["actuators"], target_id, h_star,
                                   m["id"], m["label"], m["subtitle"], m["short"], m["diagnostic"],
                                   m["ensemble"]())
            name = bundle["scenario_id"]
            dump(bundle, name)
            manifest_primary.append(dict(scenario_id=name, method_id=m["id"], target_id=target_id,
                                          method_label=m["label"], diagnostic_only=m["diagnostic"]))

    # ================= Canonical flock: seed 2 (V1-vs-V3 comparison) =================
    fl2 = discover_flock(2)
    lattice2, I02 = fl2["lattice"], fl2["I0"]
    B_D0_2 = dynamical_shell(lattice2, I02)
    B_F0_2 = compute_B_F0(fl2)
    targets2 = target_headings(fl2["h0"])
    h_star2 = targets2["cw"]  # the frozen-protocol target for this flock (matches PROTOCOL_V1)
    A_cover2 = min_actuators_for_multicover(B_D0_2, I02, lattice2, q=FROZEN_Q, gamma=FROZEN_GAMMA)
    A_v1_pair = [57, 77]  # best pair, v1_mechanism_audit/data/pair_synergy.json (R_ij=0.16, p_success=0.0)

    CANON_METHODS = [
        dict(id="no_control", label="No Control", subtitle="Natural dynamics, no intervention", short="No Control",
             actuators=[], diagnostic=False, ensemble=lambda: ensemble_v2_baseline(2) if False else NO_ENSEMBLE),
        dict(id="v1_best_pair", label="V1 Best Pair (global search)", subtitle="Sparse global actuator search (V1, frozen)",
             short="V1 Best Pair", actuators=A_v1_pair, diagnostic=False, ensemble=lambda: NO_ENSEMBLE),
        dict(id="sparse_interface_multicover", label="Sparse Interface Multicover", subtitle="Our refined controller (V3)",
             short="Our Method", actuators=A_cover2, diagnostic=False, ensemble=lambda: ensemble_frozen_v3(2)),
    ]
    manifest_canonical = []
    for m in CANON_METHODS:
        bundle = build_bundle(fl2, B_D0_2, B_F0_2, m["actuators"], "cw", h_star2,
                               m["id"], m["label"], m["subtitle"], m["short"], m["diagnostic"], m["ensemble"]())
        name = bundle["scenario_id"]
        dump(bundle, name)
        manifest_canonical.append(dict(scenario_id=name, method_id=m["id"], target_id="cw",
                                        method_label=m["label"], diagnostic_only=m["diagnostic"]))

    manifest = dict(
        protocol_version=PROTOCOL_VERSION,
        primary_flock_id="seed16", canonical_flock_id="seed2",
        primary_methods=[dict(id=m["id"], label=m["label"], subtitle=m["subtitle"], short=m["short"],
                               diagnostic=m["diagnostic"]) for m in METHODS],
        primary_targets={k: v for k, v in targets.items()},
        primary_initial_heading=int(fl["h0"]),
        primary_scenarios=manifest_primary,
        canonical_methods=[dict(id=m["id"], label=m["label"], subtitle=m["subtitle"], short=m["short"],
                                 diagnostic=m["diagnostic"]) for m in CANON_METHODS],
        canonical_target=h_star2,
        canonical_initial_heading=int(fl2["h0"]),
        canonical_scenarios=manifest_canonical,
        default_scenario_id=f"seed16__sparse_interface_multicover__cw",
    )
    with open(DEMO_DATA_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"wrote manifest.json  ({len(manifest_primary)} primary + {len(manifest_canonical)} canonical scenarios)")


if __name__ == "__main__":
    main()
