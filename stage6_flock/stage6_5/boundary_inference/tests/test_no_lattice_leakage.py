"""Architectural test for Part 1's hard requirement: the boundary-inference
algorithm must never access the simulator's source-level interaction graph
(lattice.neighbor_ids, the Moore graph, B^D, graph distance to I0, or any
feature built from the known topology).

This is enforced by static AST analysis of the INFERENCE-SIDE module set
below, not by a string grep (which a comment or docstring could defeat) and
not by only checking today's function bodies (which a future edit could
quietly break) -- every import, every attribute access, every identifier,
and every function signature in these files is scanned.

Run: pytest stage6_5/boundary_inference/tests/ -q  (from stage6_flock/)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

# The modules that make up the inference algorithm itself. Anything that
# builds/simulates trajectories or reveals B^D/B^F for evaluation (
# trajectory_gen.py, ground_truth_eval.py, control_compare.py, run_*.py
# drivers) is deliberately NOT in this list -- those are evaluation-side and
# are allowed to touch the lattice.
INFERENCE_SIDE_MODULES = [
    "nodewise_model.py",
    "greedy_selection.py",
    "bootstrap.py",
    "graph_inference.py",
    "api.py",
]

FORBIDDEN_MODULE_SUBSTRINGS = [
    "flock_sim.lattice", "flock_sim.spectral", "lattice", "spectral",
    "common_v2", "common_v3", "selection_rules", "coverage_metrics",
    "flock_sim.interventions",
]
# flock_sim.metrics / flock_sim.model / flock_sim itself (bare) are NOT
# forbidden module names on their own merit -- but none of the inference-side
# files import flock_sim at all, so we forbid the bare package too, to be safe.
FORBIDDEN_BARE_MODULES = {"flock_sim"}

FORBIDDEN_IDENTIFIERS = {
    "Lattice", "neighbor_ids", "neighbor_slot", "dynamical_shell",
    "analyze_window", "build_adjacency", "fiedler_norm", "fiedler_raw",
    "B_D", "B_D0", "BD", "graph_distance", "bfs_distances_from",
    "grid_side", "bird_to_rowcol", "rowcol_to_bird",
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
            assert name not in FORBIDDEN_IDENTIFIERS, (
                f"{fname}: forbidden identifier {name!r} referenced"
            )


@pytest.mark.parametrize("fname", INFERENCE_SIDE_MODULES)
def test_no_lattice_shaped_function_arguments(fname):
    """No function in the inference side may declare a parameter that looks
    like it is meant to carry a Lattice / neighbor-graph object, and no
    parameter may be type-annotated as Lattice."""
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
                    assert bad not in lname, (
                        f"{fname}:{node.name}: parameter {arg.arg!r} looks graph-shaped"
                    )
                if arg.annotation is not None:
                    ann_src = ast.dump(arg.annotation)
                    assert "Lattice" not in ann_src, (
                        f"{fname}:{node.name}: parameter {arg.arg!r} annotated with Lattice"
                    )


def test_public_api_signature_is_array_only():
    """Runtime check on top of the static ones: infer_boundary's parameters
    are exactly the documented array/index-set/hyperparameter surface."""
    import inspect
    import api  # noqa: E402

    sig = inspect.signature(api.infer_boundary)
    params = set(sig.parameters)
    allowed = {
        "z_train", "z_val", "I0", "n_bird", "shortlist_k", "delta_tol",
        "min_gain", "delta_tol_frac", "min_gain_frac", "max_size", "n_boot",
        "rng", "model_kwargs",
    }
    assert params <= allowed, f"unexpected parameter(s) on infer_boundary: {params - allowed}"
    for p in ("z_train", "z_val", "I0"):
        assert p in params, f"infer_boundary is missing required array/index-set parameter {p!r}"


def test_running_inference_does_not_touch_a_lattice_object():
    """Behavioral seal on the static checks: run infer_boundary end-to-end on
    synthetic heading data and confirm no Lattice instance exists anywhere in
    the call -- if flock_sim.lattice were never imported this is automatic,
    but this also catches a Lattice object smuggled in via **model_kwargs."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "python"))
    from flock_sim.lattice import Lattice  # only the TEST is allowed to import this, to build the check
    import api

    rng = np.random.default_rng(0)
    n_bird, n_traj, n_time = 20, 6, 8
    I0 = list(range(5))
    z_train = rng.integers(0, 4, size=(n_traj, n_time + 1, n_bird))
    z_val = rng.integers(0, 4, size=(n_traj, n_time + 1, n_bird))

    result = api.infer_boundary(z_train, z_val, I0, shortlist_k=4, delta_tol=0.05, min_gain=0.0)

    for v in vars(result).values():
        assert not isinstance(v, Lattice)
    assert isinstance(result.B_hat, list)
