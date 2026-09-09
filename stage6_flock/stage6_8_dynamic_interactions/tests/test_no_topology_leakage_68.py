"""Stage 6.8 information firewall (task brief section 6).

Directly modelled on `stage6_7_blind_boundary/tests/test_no_topology_leakage.py`
and `stage6_5/boundary_inference/tests/test_no_lattice_leakage.py`: an
AST-based import / identifier / signature scan of every inference-side module,
plus a runtime seal.

    ALLOWED to inference code : bird ids, positions, headings, past
                                trajectories, its own interventions
    WITHHELD                  : the FOV rule, the effective interaction edges,
                                the latent stochastic edge gates, B_t^D, the
                                simulator's neighbour lists

Positions are newly permitted relative to Stage 6.7 and that weakening is
deliberate and disclosed (PLAN.md, PROTOCOL_6_8.md section 1): an external
observer of a physical flock sees where the birds are. What must stay hidden
is the heading-dependent DIRECTED subset of adjacency that is live at time t.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

CODE = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE))

INFERENCE_SIDE = [
    "observer.py", "louvain.py", "candidate_detection.py", "spectral_proposal.py",
    "tracker.py", "heading_stratified.py", "predictive_boundary_68.py",
    "challenger.py", "probing.py",
]

FORBIDDEN_IMPORT_ROOTS = {
    "flock_sim", "common_68", "fov_dynamics", "oracle_68", "intervention_api_68",
    "phase_metrics", "common_v2", "common_66", "common_67", "dynamical_shell",
    "exact_intervention", "archetypes", "windowed_data", "spectral",
    "run_phase_scan", "run_phase_scan_fov", "run_size_scan", "run_episode_screen",
    "run_oracle_characterization", "adaptive_control",
}

FORBIDDEN_IDENTIFIERS = {
    "Lattice", "FovSimulator", "ExactPropagator", "neighbor_ids", "neighbor_slot",
    "neighbor_slots_1based", "visible_mask", "visibility_table", "SLOT_VEC",
    "SLOT_OVERRIDES", "oracle_B_D", "active_in_edges", "flatten_edges",
    "one_hop_neighbors", "structural_shell", "graph_distance_from_set",
    "compute_G", "compute_G_masked", "next_state_dist", "GateParams",
    "gate_hist", "active_mask_hist", "interface_series", "B_D",
}

FORBIDDEN_PARAM_SUBSTRINGS = (
    "lattice", "neighbor", "neighbour", "adjacency_true", "oracle", "edge_mask",
    "active_mask", "gate", "visib", "shell",
)


def _tree(name: str) -> ast.AST:
    return ast.parse((CODE / name).read_text(), filename=name)


@pytest.mark.parametrize("mod", INFERENCE_SIDE)
def test_no_forbidden_imports(mod):
    for node in ast.walk(_tree(mod)):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                assert root not in FORBIDDEN_IMPORT_ROOTS, f"{mod} imports {a.name}"
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in FORBIDDEN_IMPORT_ROOTS, f"{mod} imports from {node.module}"


@pytest.mark.parametrize("mod", INFERENCE_SIDE)
def test_no_forbidden_identifiers(mod):
    for node in ast.walk(_tree(mod)):
        if isinstance(node, ast.Name):
            assert node.id not in FORBIDDEN_IDENTIFIERS, f"{mod} references {node.id}"
        if isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_IDENTIFIERS, f"{mod} references .{node.attr}"


@pytest.mark.parametrize("mod", INFERENCE_SIDE)
def test_no_topology_shaped_parameters(mod):
    for node in ast.walk(_tree(mod)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            names = [a.arg for a in list(args.args) + list(args.kwonlyargs) + list(args.posonlyargs)]
            for a in (args.vararg, args.kwarg):
                if a is not None:
                    names.append(a.arg)
            for n in names:
                low = n.lower()
                for bad in FORBIDDEN_PARAM_SUBSTRINGS:
                    assert bad not in low, f"{mod}:{node.name} takes a parameter named {n!r}"


def test_runtime_seal_no_simulator_object_reaches_results():
    """Run the whole blind pipeline on SYNTHETIC data and assert no simulator/
    oracle object appears anywhere in its outputs -- catching a reference
    smuggled in via **kwargs, which the AST scan alone cannot see."""
    import observer, candidate_detection, spectral_proposal, tracker

    rng = np.random.default_rng(0)
    L = 12
    nn = L * L
    pos = np.stack([np.repeat(np.arange(L), L), np.tile(np.arange(L), L)], axis=1).astype(float)
    z = np.zeros((30, nn), dtype=int)
    block = (pos[:, 0] < L / 2).astype(int)
    for t in range(30):
        z[t] = np.where(rng.random(nn) < 0.9, block, rng.integers(0, 4, nn))

    obs = observer.Observation(pos, z, 20)
    ok_a, all_a = candidate_detection.propose(obs)
    ok_s, all_s = spectral_proposal.propose(obs)
    tr = tracker.LineageTracker("affinity_louvain")
    for t in range(10, 21):
        tr.update(candidate_detection.propose(obs.advanced_to(t))[0])
    results = [ok_a, all_a, ok_s, all_s, tr.summary()]

    banned = ("Lattice", "FovSimulator", "FovResult", "ExactPropagator", "FiniteProbe",
              "PrecomputedModel", "GateParams")

    def walk(o, depth=0):
        assert type(o).__name__ not in banned, f"{type(o).__name__} leaked into results"
        if depth > 8:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(k, depth + 1); walk(v, depth + 1)
        elif isinstance(o, (list, tuple, set)):
            for v in o:
                walk(v, depth + 1)
        elif hasattr(o, "__dict__"):
            for v in vars(o).values():
                walk(v, depth + 1)

    walk(results)
    assert len(ok_a) >= 1, "the blind detector produced no valid candidate on synthetic data"


def test_observer_cannot_see_the_future():
    import observer
    pos = np.zeros((4, 2))
    z = np.arange(40).reshape(10, 4) % 4
    obs = observer.Observation(pos, z, 5)
    assert obs.window(100).shape[0] == 6            # t=5 inclusive, clipped at 0
    assert np.array_equal(obs.window(3), z[3:6])
    with pytest.raises(ValueError):
        obs.at(6)
