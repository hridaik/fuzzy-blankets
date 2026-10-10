"""Derives lattice/graph-ready visualization data for the "Inference &
Identity" mode. Every number here is either read verbatim from an already-
frozen stage6_5/refinement result file, or DETERMINISTICALLY REPRODUCED from
one (same seeds, same frozen protocol, same frozen code) purely to expose a
finer-grained view (a full trajectory, a full probability vector) that the
frozen driver scripts summarized before discarding. This script:

  - never re-runs boundary inference, never re-selects actuators with new
    thresholds, never re-tunes any controller or identity mechanism;
  - only calls already-frozen functions (find_flock, dynamical_shell,
    min_actuators_for_multicover, the identity `definitions.py` tracks, the
    exact_intervention closed-form propagator, the retrospective validity
    guard) with the exact same seeds/arguments the frozen drivers used;
  - is documented field-by-field in ../STAGE6_5_VISUALIZATION_NOTES.md.

Writes interactive_demo/data/refinement_viz_data.json.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[2]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))
BI_CODE = ROOT / "stage6_5" / "boundary_inference" / "code"
CI_CODE = ROOT / "stage6_5" / "collective_identity" / "code"
CR_CODE = ROOT / "stage6_5" / "refinement" / "causal_redundancy" / "code"
CG_CODE = ROOT / "stage6_5" / "refinement" / "control_generalization" / "code"
IS_CODE = ROOT / "stage6_5" / "refinement" / "identity_stability" / "code"
for p in (BI_CODE, CI_CODE, CR_CODE, CG_CODE, IS_CODE):
    sys.path.insert(0, str(p))

BI_DATA = ROOT / "stage6_5" / "boundary_inference" / "data"
CR_DATA = ROOT / "stage6_5" / "refinement" / "causal_redundancy" / "data"
CG_DATA = ROOT / "stage6_5" / "refinement" / "control_generalization" / "data"
IS_DATA = ROOT / "stage6_5" / "refinement" / "identity_stability" / "data"
OUT_PATH = Path(__file__).resolve().parent / "refinement_viz_data.json"

from flock_sim.lattice import Lattice, bird_to_rowcol  # noqa: E402
from flock_sim.model import ModelParams  # noqa: E402
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from common_v2 import find_flock, dynamical_shell  # noqa: E402
from definitions import material_track, lineage_track, functional_track, jaccard  # noqa: E402
from identity_metrics import turnover, retention_fraction  # noqa: E402
from validity_guard import retrospective_guard  # noqa: E402
from exact_intervention import default_precomputed_model, next_heading_dist_all, do_next_heading_dist_all  # noqa: E402
from load_frozen_inputs import load_flock_with_frozen_boundary, generate_perturbation_checkpoints, exterior_classes  # noqa: E402
from run_identity_stability import run_controlled_episode, CONTROLLED_SEED_OFFSET  # noqa: E402


def load(path):
    return json.loads(Path(path).read_text())


def jarr(x):
    """JSON-safe: numpy array/scalar -> plain python."""
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    return x


# --------------------------------------------------------------- shared lattice
def build_shared_lattice():
    """Positions + Moore-neighbour adjacency are IDENTICAL for every flock in
    this port (the physical lattice never moves) -- computed once, reused by
    every tab/flock."""
    lat = Lattice(nn=100, nh=8)
    rows, cols = bird_to_rowcol(np.arange(100), lat.L)
    positions = [[int(r), int(c)] for r, c in zip(rows, cols)]
    neighbors = {str(i): lat.neighbor_ids[i].tolist() for i in range(100)}
    return dict(L=lat.L, nn=100, positions=positions, neighbors=neighbors), lat


# --------------------------------------------------------------------- Tab 1
def build_tab1():
    boot = load(BI_DATA / "bootstrap_membership.json")
    held_out = load(BI_DATA / "held_out_evaluation.json")
    sample_eff = load(BI_DATA / "sample_efficiency.json")
    dev_sweep = load(BI_DATA / "dev_sweep.json")
    frozen_row = next(r for r in dev_sweep["rows"]
                       if r["seed"] == boot["seed"] and r["delta_tol_frac"] == 0.05)

    membership = {int(k): v for k, v in boot["membership"].items()}
    return dict(
        canonical=dict(
            # Authoritative point estimate + precision/recall/excess-loss: the
            # frozen dev_sweep.json row at delta_tol_frac=0.05 (PROTOCOL_6_5.md's
            # own table). Bootstrap membership frequency (a separate, complementary
            # diagnostic over 15 resamples) is layered on top for the halo overlay
            # -- its own point estimate (B_hat_point_estimate) can differ by a
            # member or two from this single frozen run; both are real, neither
            # is hidden (see STAGE6_5_VISUALIZATION_NOTES.md).
            seed=boot["seed"], I0=boot["I0"], B_D=boot["B_D"], B_hat=frozen_row["B_hat"],
            z_t0=find_flock(boot["seed"])["z_t0"].tolist(),
            precision=(frozen_row["tp"] / frozen_row["size_hat"]) if frozen_row["size_hat"] else None,
            recall=frozen_row["tp"] / frozen_row["size_true"],
            excess_loss=frozen_row["excess_loss_B_hat"],
            bootstrap_B_hat_point_estimate=boot["B_hat_point_estimate"],
            membership=membership, n_boot=boot["n_boot"],
        ),
        held_out=[dict(
            seed=r["seed"], B_D=r["B_D"], B_hat=r["B_hat"],
            precision=r["recovery_vs_BD"]["precision"], recall=r["recovery_vs_BD"]["recall"],
            excess_loss=r["excess_loss"],
        ) for r in held_out["results"]],
        sample_efficiency=dict(
            seed=sample_eff["seed"], I0=sample_eff["I0"], B_D=sample_eff["B_D"],
            rows=[dict(n_traj=row["n_traj"], jaccard=row["jaccard"], size_hat=row["size_hat"],
                       excess_loss=row["excess_loss_B_hat"], B_hat=row["B_hat"])
                  for row in sample_eff["rows"]],
        ),
    )


# --------------------------------------------------------------------- Tab 2
STRESS_TEST_SEED = 20  # the "clean" discriminating case, per CAUSAL_REDUNDANCY_RESULTS.md


def _core_effect_snapshot(pm, lattice, X_t, I0, j, z_prime):
    natural = next_heading_dist_all(pm, lattice, X_t)[I0]
    perturbed = do_next_heading_dist_all(pm, lattice, X_t, j, z_prime)[I0]
    kl = (perturbed * (np.log(np.clip(perturbed, 1e-16, 1)) - np.log(np.clip(natural, 1e-16, 1)))).sum(axis=1)
    return natural, perturbed, kl


def _find_representative(pm, lattice, checkpoints, I0, bird_ids, pick="max"):
    """Re-derives, exactly as perturbation_experiment.py did, the
    (state, heading) achieving the requested (max or a fixed representative)
    joint KL for a given bird pool -- so the example shown is picked by a
    documented, pre-specifiable rule (the single largest effect in the
    omitted-shell class), not hand-selected."""
    best = None
    for j in bird_ids:
        for X_t in checkpoints:
            z_j = int(X_t[j])
            for z_prime in range(4):
                if z_prime == z_j:
                    continue
                natural, perturbed, kl = _core_effect_snapshot(pm, lattice, X_t, I0, j, z_prime)
                joint = float(kl.sum())
                if best is None or (pick == "max" and joint > best["joint"]):
                    best = dict(joint=joint, j=j, X_t=X_t, z_prime=z_prime, z_j=z_j,
                                natural=natural, perturbed=perturbed, kl=kl)
    return best


def build_tab2():
    fl = load_flock_with_frozen_boundary(STRESS_TEST_SEED)
    classes = exterior_classes(fl)
    checkpoints = generate_perturbation_checkpoints(fl)
    pm = default_precomputed_model()
    lattice, I0 = fl["lattice"], fl["I0"]

    examples = {}
    for cls_name, bird_ids, pick in (
        ("omitted_shell", classes["omitted_shell"], "max"),
        ("included_shell", classes["included_shell"], "max"),
        ("non_shell", classes["non_shell_sample"], "max"),  # will be exactly 0 by construction
    ):
        best = _find_representative(pm, lattice, checkpoints, I0, bird_ids, pick=pick)
        affected = [int(I0[k]) for k in range(len(I0)) if best["kl"][k] > 1e-9]
        examples[cls_name] = dict(
            bird=int(best["j"]), natural_heading=int(best["z_j"]), perturb_heading=int(best["z_prime"]),
            D_do_joint=best["joint"], z_t=best["X_t"].tolist(),
            per_core=[dict(core_id=int(i), natural=best["natural"][k].tolist(), perturbed=best["perturbed"][k].tolist(),
                            kl=float(best["kl"][k])) for k, i in enumerate(I0.tolist())],
            affected_core_ids=affected,
            is_neighbor_of_core=[int(i) for i in affected],
        )

    cr = load(CR_DATA / "causal_redundancy.json")
    res = cr["results"][str(STRESS_TEST_SEED)]
    return dict(
        seed=STRESS_TEST_SEED, I0=I0.tolist(), B_D=fl["B_D"], B_hat=fl["B_hat"], classes=classes,
        examples=examples,
        excess_loss_natural=res["natural_exact"]["excess"],
        delta_shift_by_class={cls: {k2: float(np.mean([v["B_hat"] for v in vals.values()])) if vals else 0.0
                                     for k2, vals in [("B_hat", shift)]}
                               for cls, shift in res["delta_shift_by_class"].items()},
    )


# --------------------------------------------------------------------- Tab 3
def build_tab3():
    disc = load(CG_DATA / "discriminating_flocks.json")
    fcc = load(CG_DATA / "four_controller_comparison.json")
    agg = load(CG_DATA / "aggregate_summary.json")

    rows = []
    for r in fcc["rows"]:
        fl = find_flock(r["seed"])
        rows.append(dict(
            seed=r["seed"], I0=sorted(int(i) for i in fl["I0"].tolist()), z_t0=fl["z_t0"].tolist(),
            B_D=r["B_D"], B_hat=r["B_hat"], recall=r["recall_B_hat"], precision=r["precision_B_hat"],
            excess_loss_B_hat=r["excess_loss_B_hat"],
            arms={name: dict(actuators=r["arms"][name], p_success=r[name]["p_success"],
                              n_actuators=r[name]["n_actuators"])
                  for name in ("oracle", "inferred", "fiedler", "random_matched")},
        ))

    return dict(
        scan_range=[disc["scan_start"], disc["scan_end_inclusive"]],
        n_scanned=disc["n_seeds_scanned"], n_qualifying=disc["n_qualifying_flocks_scanned"],
        n_discriminating=disc["n_discriminating"],
        rows=rows, summary=agg["summary"],
    )


# --------------------------------------------------------------------- Tab 4
IDENTITY_FLOCK_SEED = 2
IDENTITY_REPLICATE = 0  # first replicate -- a pre-specifiable choice, not cherry-picked


def _track_series(z_hist, I0, track, h_star, lattice):
    n = len(track)
    sizes, R0, J, T_I, Hstar, coh = [], [], [], [], [], []
    for t in range(n):
        I_t = track[t]
        sizes.append(len(I_t))
        R0.append(retention_fraction(I0, I_t))
        Hstar.append(target_heading_fraction(z_hist[t], I_t, h_star) if len(I_t) else float("nan"))
        coh.append(coherence(z_hist[t], I_t) if len(I_t) else float("nan"))
        if t == 0:
            J.append(1.0)
            T_I.append(0)
        else:
            J.append(jaccard(track[t - 1], I_t))
            T_I.append(turnover(track[t - 1], I_t))
    return dict(size=sizes, R0=R0, jaccard=J, turnover=T_I, Hstar=Hstar, coherence=coh,
                members=[sorted(int(b) for b in I_t.tolist()) for I_t in track])


def build_tab4():
    fl = find_flock(IDENTITY_FLOCK_SEED)
    I0, lattice, h_star = fl["I0"], fl["lattice"], fl["h_star"]
    seed = CONTROLLED_SEED_OFFSET + 1000 * IDENTITY_FLOCK_SEED + IDENTITY_REPLICATE
    z_hist = run_controlled_episode(fl, seed)
    n = z_hist.shape[0]

    envelope = load(IS_DATA / "validity_envelope.json")["F"]

    track_M = material_track(I0, n)
    track_L = lineage_track(z_hist, I0, t_start=0, t_end=n - 1)
    track_F = functional_track(z_hist, I0, t_start=0, t_end=n - 1, lattice=lattice)
    guard = retrospective_guard(track_F, len(I0), envelope)
    track_Fguard = guard["guarded_track"]

    tracks = {}
    for name, track in (("M", track_M), ("L", track_L), ("F", track_F), ("F_guard", track_Fguard)):
        s = _track_series(z_hist, I0, track, h_star, lattice)
        tracks[name] = s
    tracks["F_guard"]["valid"] = guard["valid_track"]
    tracks["F_guard"]["collapsed"] = guard["collapsed_track"]
    tracks["F"]["valid"] = [True] * n
    tracks["F"]["collapsed"] = [False] * n
    tracks["M"]["valid"] = [True] * n
    tracks["M"]["collapsed"] = [False] * n
    tracks["L"]["valid"] = [True] * n
    tracks["L"]["collapsed"] = [False] * n

    T_u, T_r = 20, 20
    end_idx = min(T_u, n - 1)
    nominal_success = {name: bool(tracks[name]["Hstar"][end_idx] >= 0.8) for name in tracks}
    identity_valid_success = {name: bool(nominal_success[name] and not tracks[name]["collapsed"][end_idx])
                               for name in tracks}

    return dict(
        seed=IDENTITY_FLOCK_SEED, replicate=IDENTITY_REPLICATE, I0=sorted(int(i) for i in I0.tolist()),
        h_star=int(h_star), T_u=T_u, T_r=T_r, n_steps=n,
        z_hist=z_hist.tolist(), tracks=tracks,
        nominal_success=nominal_success, identity_valid_success=identity_valid_success,
        validity_envelope_F=envelope,
        jitter_note="lambda_T regularization could not be cleanly tuned on baseline data; see identity_stability results",
    )


def main():
    print("shared lattice...")
    lattice_json, _ = build_shared_lattice()
    print("tab 1 (predictive boundary)...")
    tab1 = build_tab1()
    print("tab 2 (causal stress test)...")
    tab2 = build_tab2()
    print("tab 3 (prediction vs control)...")
    tab3 = build_tab3()
    print("tab 4 (collective identity)...")
    tab4 = build_tab4()

    out = dict(lattice=lattice_json, predictive_boundary=tab1, causal_stress_test=tab2,
               prediction_vs_control=tab3, collective_identity=tab4)
    OUT_PATH.write_text(json.dumps(out, separators=(",", ":"), default=jarr))
    print(f"wrote {OUT_PATH} ({OUT_PATH.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
