"""Stage 6.11 observer/simulator firewall test (task brief item 1).

Mirrors stage6_8_dynamic_interactions/tests/test_no_topology_leakage_68.py and
stage6_9_translating_collective/tests/test_no_topology_leakage_69.py exactly:
AST-scan every INFERENCE-SIDE module for forbidden imports, forbidden
identifiers, and topology-shaped parameter names, then run the blind
pipeline on synthetic data and recursively check no simulator object reached
the results.

INFERENCE_SIDE lists Stage 6.11's own observer modules plus the Stage 6.8/6.9
modules they reuse read-only (those already carry their own firewall tests
in their home stage; re-scanning them here means a Stage 6.11 addition can
never quietly loosen what is imported downstream of them). Extend this list
as later phases (predictive-boundary, causal-probe estimation, control
decision logic) add new observer-side modules.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

THIS_DIR = Path(__file__).resolve().parent
CODE_DIR = THIS_DIR.parent / "code"
ROOT = THIS_DIR.parent.parent
S68 = ROOT / "stage6_8_dynamic_interactions" / "code"
S69 = ROOT / "stage6_9_translating_collective" / "code"
for _p in (CODE_DIR, S68, S69, ROOT / "python"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

INFERENCE_SIDE = {
    "geometry_611.py": CODE_DIR / "geometry_611.py",
    "lineage_611.py": CODE_DIR / "lineage_611.py",
    "thingness_611.py": CODE_DIR / "thingness_611.py",
    "predictive_boundary_611.py": CODE_DIR / "predictive_boundary_611.py",
    "probing_611.py": CODE_DIR / "probing_611.py",
    "control_authority_611.py": CODE_DIR / "control_authority_611.py",
    "detect_69.py": S69 / "detect_69.py",
    "identity_69.py": S69 / "identity_69.py",
    "louvain.py": S68 / "louvain.py",
    "observer.py": S68 / "observer.py",
}

FORBIDDEN_IMPORT_ROOTS = {
    "flock_sim", "common_611", "common_68", "common_69",
    "moving_flock_611", "moving_flock", "fov_dynamics",
    "oracle_68", "oracle_611", "intervention_api_68", "intervention_api_69", "intervention_api_611",
    "phase_metrics_611", "run_phase_scan_611", "run_model_validation",
    "adaptive_control", "closed_loop", "episode_data",
    "observational_corpus_611", "run_predictive_boundary_611", "run_online_control_611",
}

FORBIDDEN_IDENTIFIERS = {
    "MovingFlock", "MovingFlock611", "Lattice", "FovSimulator",
    "live_edges", "oracle_B_D", "compute_G", "compute_G_masked",
    "visible_mask", "visibility_table", "SLOT_VEC", "SLOT_OVERRIDES",
    "OCTANT_TO_SLOT", "MovingResult", "FovResult", "GateParams",
    "ExactPropagator", "ExactPropagatorMoving", "FiniteProbe", "FiniteProbeMoving",
    "ModelParams", "build_model", "G_table", "Risk_table", "policy_posterior",
    "true_centre", "live_hist", "gate_hist", "active_mask_hist",
    "R_PRIMARY", "V_PRIMARY", "COHESION_PRIMARY", "R_SECONDARY", "V_SECONDARY",
    "R_SPEC", "V_SPEC", "R_SUPERSEDED", "V_SUPERSEDED", "resolved_params",
}
# NOTE: "z_hist"/"r_hist" are deliberately NOT banned as bare identifiers here
# (unlike Stage 6.9's list) because `observer.Observation` -- itself part of
# INFERENCE_SIDE, the sanctioned channel -- legitimately carries a bounded,
# time-gated `z_hist` field (see observer.py's own docstring/test above:
# `.at(t)` refuses t > current t). What must stay banned is any INFERENCE_SIDE
# module ever holding a raw simulator result (`MovingResult`/`FovResult`,
# whose own `.z_hist`/`.r_hist` carry the FULL, un-gated trajectory including
# the future) -- that is enforced by FORBIDDEN_IMPORT_ROOTS (no inference-side
# module can import the modules that construct one) and the runtime-seal
# type check below, not by banning the shared attribute name.

FORBIDDEN_PARAM_SUBSTRINGS = (
    "lattice", "neighbor", "neighbour", "oracle", "true_centre", "true_center",
    "edge", "visib", "sim", "gate", "shell",
)


def _cases():
    out = []
    for name, path in INFERENCE_SIDE.items():
        assert path.exists(), f"missing inference-side file: {path}"
        out.append((name, path))
    return out


@pytest.mark.parametrize("name,path", _cases())
def test_no_forbidden_imports(name, path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in FORBIDDEN_IMPORT_ROOTS, f"{name}: forbidden import {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                assert root not in FORBIDDEN_IMPORT_ROOTS, f"{name}: forbidden import from {node.module}"


@pytest.mark.parametrize("name,path", _cases())
def test_no_forbidden_identifiers(name, path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in FORBIDDEN_IDENTIFIERS, f"{name}: forbidden identifier {node.id}"
        elif isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_IDENTIFIERS, f"{name}: forbidden attribute {node.attr}"


@pytest.mark.parametrize("name,path", _cases())
def test_no_topology_shaped_parameters(name, path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            all_args = (list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs)
                        + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else []))
            for arg in all_args:
                lname = arg.arg.lower()
                for bad in FORBIDDEN_PARAM_SUBSTRINGS:
                    assert bad not in lname, f"{name}.{node.name}: forbidden param name '{arg.arg}'"


def test_runtime_seal_no_simulator_object_reaches_results():
    """Run the blind pipeline (detect -> lineage -> thingness geometry) on
    SYNTHETIC data (no real simulator ever touched) and recursively check
    that no simulator-side object type leaked into the results."""
    from detect_69 import propose
    from lineage_611 import LineageTracker611
    from thingness_611 import geometry_features
    from flock_sim.model import UV4

    rng = np.random.default_rng(0)
    N, L = 60, 12.0
    r = rng.random((N, 2)) * L
    z = rng.integers(0, 4, N)
    z[:20] = 0  # a synthetic aligned cluster
    r[:20] = rng.normal(loc=[3.0, 3.0], scale=0.5, size=(20, 2)) % L
    z_window = [z.copy() for _ in range(4)]

    cands = propose(r, z_window, L)
    assert len(cands) >= 1

    tracker = LineageTracker611(L=L, uv4=UV4)
    tracker.start(cands[0], r, z, 0)
    z2 = z.copy()
    r2 = (r + rng.normal(scale=0.05, size=r.shape)) % L
    tracker.update(cands, r2, z2, 1)
    summary = tracker.summary()

    geo = geometry_features(cands[0], r, z, L, UV4)

    BANNED_TYPES = ("MovingFlock", "MovingFlock611", "MovingResult", "Lattice",
                     "FovSimulator", "FovResult", "ExactPropagator", "ExactPropagatorMoving",
                     "FiniteProbe", "FiniteProbeMoving", "GateParams", "ModelParams")

    def walk(o, seen=None):
        seen = seen if seen is not None else set()
        if id(o) in seen or isinstance(o, (str, bytes, int, float, bool, type(None), np.ndarray, np.generic)):
            return
        seen.add(id(o))
        assert type(o).__name__ not in BANNED_TYPES, f"leaked simulator object: {type(o).__name__}"
        if isinstance(o, dict):
            for k, v in o.items():
                walk(k, seen)
                walk(v, seen)
        elif isinstance(o, (list, tuple, set)):
            for v in o:
                walk(v, seen)
        elif hasattr(o, "__dict__"):
            for v in vars(o).values():
                walk(v, seen)

    walk(summary)
    walk(geo)


def test_observer_cannot_see_the_future():
    from observer import Observation

    N = 5
    positions = np.zeros((N, 2))
    z_hist = np.zeros((3, N), dtype=int)
    obs = Observation(positions=positions, z_hist=z_hist, t=1, interventions={})
    with pytest.raises(ValueError):
        obs.at(2)
