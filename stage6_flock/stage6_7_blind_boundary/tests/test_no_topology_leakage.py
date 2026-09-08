"""Architectural test for the task brief's central firewall: "Inference code
may see trajectories and interventions, but not topology." Directly modeled
on stage6_5/boundary_inference/tests/test_no_lattice_leakage.py -- AST-based
static analysis (not a string grep, which a comment could defeat, and not
only today's function bodies, which a future edit could quietly break) of
every import, attribute access, identifier, and function signature in the
inference-side module set below.

Run: pytest stage6_flock/stage6_7_blind_boundary/tests/ -q
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

# The modules that make up the blind inference algorithm itself. Anything
# that builds/simulates trajectories or reveals B^D for evaluation
# (common_67.py, candidate_panel.py, intervention_api.py, oracle_validation.py,
# blind_landscape.py, run_*.py drivers) is deliberately NOT in this list --
# those are evaluation-side and are allowed to touch the lattice, exactly
# matching stage6_5's own inference/evaluation split.
INFERENCE_SIDE_MODULES = [
    "blind_cache.py",
    "directed_graph_inference.py",
    "graph_bootstrap.py",
    "predictive_boundary.py",
    "causal_discovery.py",
]

FORBIDDEN_MODULE_SUBSTRINGS = [
    "flock_sim.lattice", "flock_sim.spectral", "lattice", "spectral",
    "common_v2", "common_v3", "common_66", "common_67", "archetypes",
    "dynamical_shell", "windowed_data", "selection_rules", "coverage_metrics",
    "flock_sim.interventions", "intervention_api", "oracle_validation",
    "candidate_panel", "blind_landscape",
]
FORBIDDEN_BARE_MODULES = {"flock_sim"}

FORBIDDEN_IDENTIFIERS = {
    "Lattice", "neighbor_ids", "neighbor_slot", "dynamical_shell",
    "one_hop_neighbors", "k_hop_shell", "analyze_window", "build_adjacency",
    "fiedler_norm", "fiedler_raw", "B_D", "B_D0", "BD", "true_shell",
    "graph_distance", "graph_distance_from_set", "bfs_distances_from",
    "grid_side", "bird_to_rowcol", "rowcol_to_bird", "structural_shell",
    "near_exterior", "distant_exterior", "InterventionOracle",
}

FORBIDDEN_PARAM_NAME_SUBSTRINGS = ["lattice", "neighbor", "moore", "graph_dist"]


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


@pytest.mark.parametrize("fname", INFERENCE_SIDE_MODULES)
def test_no_forbidden_imports(fname):
    tree = _parse(CODE_DIR / fname)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in FORBIDDEN_BARE_MODULES, (
                    f"{fname}: forbidden bare import {alias.name!r}"
                )
                for bad in FORBIDDEN_MODULE_SUBSTRINGS:
                    assert bad not in alias.name, f"{fname}: forbidden import {alias.name!r}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert mod not in FORBIDDEN_BARE_MODULES, f"{fname}: forbidden bare import {mod!r}"
            for bad in FORBIDDEN_MODULE_SUBSTRINGS:
                assert bad not in mod, f"{fname}: forbidden import-from {mod!r}"
            for alias in node.names:
                for bad in FORBIDDEN_MODULE_SUBSTRINGS:
                    assert bad not in alias.name.lower(), (
                        f"{fname}: forbidden imported name {alias.name!r} from {mod!r}"
                    )


@pytest.mark.parametrize("fname", INFERENCE_SIDE_MODULES)
def test_no_forbidden_identifiers(fname):
    tree = _parse(CODE_DIR / fname)
    for node in ast.walk(tree):
        name = None
        if isinstance(node, ast.Name):
            name = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        if name is not None:
            assert name not in FORBIDDEN_IDENTIFIERS, f"{fname}: forbidden identifier {name!r} referenced"


@pytest.mark.parametrize("fname", INFERENCE_SIDE_MODULES)
def test_no_lattice_shaped_function_arguments(fname):
    """No function in the inference side may declare a parameter that looks
    like it is meant to carry a Lattice / neighbour-graph / topology-derived
    object, and no parameter may be type-annotated as Lattice."""
    tree = _parse(CODE_DIR / fname)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            all_args = (
                node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                + ([node.args.vararg] if node.args.vararg else [])
                + ([node.args.kwarg] if node.args.kwarg else [])
            )
            for arg in all_args:
                lname = arg.arg.lower()
                for bad in FORBIDDEN_PARAM_NAME_SUBSTRINGS:
                    assert bad not in lname, f"{fname}:{node.name}: parameter {arg.arg!r} looks graph-shaped"
                if arg.annotation is not None:
                    ann_src = ast.dump(arg.annotation)
                    assert "Lattice" not in ann_src, (
                        f"{fname}:{node.name}: parameter {arg.arg!r} annotated with Lattice"
                    )


def test_running_pipeline_does_not_touch_a_lattice_object():
    """Behavioral seal on the static checks: run the blind pipeline
    end-to-end on synthetic heading data (graph inference -> bootstrap ->
    predictive boundary -> causal discovery with a fake, non-lattice oracle)
    and confirm no Lattice instance exists anywhere in the results -- catches
    a Lattice object smuggled in via **kwargs."""
    stage_dir = Path(__file__).resolve().parents[2]  # stage6_flock/
    sys.path.insert(0, str(stage_dir / "python"))
    sys.path.insert(0, str(stage_dir / "stage6_5" / "boundary_inference" / "code"))
    from flock_sim.lattice import Lattice  # only the TEST is allowed to import this
    import directed_graph_inference
    import graph_bootstrap
    import predictive_boundary
    import causal_discovery

    rng = np.random.default_rng(0)
    n_bird, n_traj, n_time = 20, 8, 6
    I0 = list(range(4))
    z_train = rng.integers(0, 4, size=(n_traj, n_time + 1, n_bird))
    z_val = rng.integers(0, 4, size=(n_traj, n_time + 1, n_bird))
    from nodewise_model import flatten_transitions
    train_prev, train_next = flatten_transitions(z_train)
    val_prev, val_next = flatten_transitions(z_val)

    single = directed_graph_inference.infer_directed_graph(
        train_prev, train_next, val_prev, val_next, n_bird=n_bird, shortlist_k=5)
    boot = graph_bootstrap.bootstrap_graph(z_train, z_val, n_boot=3, shortlist_k=5, n_bird=n_bird,
                                            rng=rng)
    flags = graph_bootstrap.stability_flags(boot["edge_stats"], tau_freq=0.0, tau_sign=0.0)
    pb = predictive_boundary.infer_predictive_boundary(
        I0, single["G"], flags, train_prev, train_next, val_prev, val_next, n_bird=n_bird,
        delta_tol=0.05, min_gain=0.0, max_size=5)

    class FakeOracle:
        """Duck-typed stand-in with no lattice reference at all."""
        def do(self, I, j, z_prime, X_t):
            return dict(D_do_joint=0.0, per_bird_kl={int(i): 0.0 for i in I})

    X_samples = z_train[0, :3]
    eff = causal_discovery.estimate_causal_effects(I0, [j for j in range(n_bird) if j not in I0],
                                                     X_samples, FakeOracle())

    for blob in (single, boot, flags, pb, eff):
        for v in _walk_values(blob):
            assert not isinstance(v, Lattice)


def _walk_values(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_values(v)
    elif isinstance(obj, (list, tuple, set)):
        for v in obj:
            yield from _walk_values(v)
    else:
        yield obj
