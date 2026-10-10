"""Stage 6.9 information firewall.

Same rule as Stage 6.8, plus one addition specific to this stage: inference
code may not see the simulator's TRUE CENTRE TRAJECTORY. The translating frame
must be estimated from observed positions and headings alone (task brief §29).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import numpy as np
import pytest

CODE = Path(__file__).resolve().parents[1] / "code"
S68 = Path(__file__).resolve().parents[2] / "stage6_8_dynamic_interactions" / "code"
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(S68))

INFERENCE_SIDE = ["identity_69.py", "detect_69.py"]

FORBIDDEN_IMPORT_ROOTS = {
    "flock_sim", "common_69", "common_68", "moving_flock", "fov_dynamics",
    "oracle_68", "intervention_api_68", "run_translation_gate", "run_guidance",
}

FORBIDDEN_IDENTIFIERS = {
    "MovingFlock", "Lattice", "FovSimulator", "live_edges", "oracle_B_D",
    "compute_G", "visible_mask", "SLOT_VEC", "OCTANT_TO_SLOT", "MovingResult",
    "true_centre", "r_hist", "z_hist", "live_hist",
}

FORBIDDEN_PARAM_SUBSTRINGS = (
    "lattice", "neighbor", "neighbour", "oracle", "true_centre", "true_center",
    "edge", "visib", "sim", "target_path",
)


def _tree(name):
    return ast.parse((CODE / name).read_text(), filename=name)


@pytest.mark.parametrize("mod", INFERENCE_SIDE)
def test_no_forbidden_imports(mod):
    for node in ast.walk(_tree(mod)):
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] not in FORBIDDEN_IMPORT_ROOTS, f"{mod}: {a.name}"
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in FORBIDDEN_IMPORT_ROOTS, \
                f"{mod}: {node.module}"


@pytest.mark.parametrize("mod", INFERENCE_SIDE)
def test_no_forbidden_identifiers(mod):
    for node in ast.walk(_tree(mod)):
        if isinstance(node, ast.Name):
            assert node.id not in FORBIDDEN_IDENTIFIERS, f"{mod}: {node.id}"
        if isinstance(node, ast.Attribute):
            assert node.attr not in FORBIDDEN_IDENTIFIERS, f"{mod}: .{node.attr}"


@pytest.mark.parametrize("mod", INFERENCE_SIDE)
def test_no_simulator_shaped_parameters(mod):
    for node in ast.walk(_tree(mod)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = node.args
            names = [x.arg for x in list(a.args) + list(a.kwonlyargs) + list(a.posonlyargs)]
            for x in (a.vararg, a.kwarg):
                if x is not None:
                    names.append(x.arg)
            for n in names:
                for bad in FORBIDDEN_PARAM_SUBSTRINGS:
                    assert bad not in n.lower(), f"{mod}:{node.name} takes {n!r}"


def test_runtime_seal_tracker_never_holds_a_simulator():
    """Drive the tracker on synthetic data and assert nothing simulator-shaped
    reaches its records."""
    import detect_69 as det

    L, N, T = 20.0, 120, 30
    rng = np.random.default_rng(0)
    pos = rng.random((N, 2)) * L
    blob = np.arange(60)
    pos[blob] = 5.0 + rng.random((60, 2)) * 3.0
    r = np.zeros((T, N, 2)); z = np.zeros((T, N), dtype=int)
    for t in range(T):
        r[t] = (pos + np.array([0.4 * t, 0.0])) % L
        z[t] = np.where(np.isin(np.arange(N), blob), 3, rng.integers(0, 4, N))

    tr = det.TranslatingTracker(L)
    cands = det.propose(r[6], z[:7], L)
    assert cands, "detector found nothing on a planted moving blob"
    tr.start(cands[0], r[6], z[6], 6)
    for t in range(7, T):
        tr.update(det.propose(r[t], z[max(0, t - 6):t + 1], L), r[t], z[t], t)
    assert len(tr.records) > 5

    banned = ("MovingFlock", "MovingResult", "Lattice", "FovSimulator")

    def walk(o, d=0):
        assert type(o).__name__ not in banned
        if d > 6:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(k, d + 1); walk(v, d + 1)
        elif isinstance(o, (list, tuple, set)):
            for v in o:
                walk(v, d + 1)
    walk(tr.records)


def test_translation_is_estimated_not_supplied():
    """A pure translation of a fixed configuration must be recovered, and the
    residual deformation must be far smaller than the unaligned distance."""
    import detect_69 as det
    import identity_69 as idy

    L, N, T = 20.0, 80, 20
    rng = np.random.default_rng(1)
    pos = 6.0 + rng.random((N, 2)) * 3.0
    r = np.array([(pos + np.array([0.5 * t, 0.0])) % L for t in range(T)])
    z = np.full((T, N), 3, dtype=int)

    tr = det.TranslatingTracker(L)
    tr.start(np.arange(N), r[6], z[6], 6)
    for t in range(7, T):
        tr.update([np.arange(N)], r[t], z[t], t)
    recs = [x for x in tr.records if "D_deform" in x]
    assert len(recs) > 5
    assert np.mean([x["D_deform"] for x in recs]) < 0.05, "rigid translation left deformation"
    assert np.mean([x["D_world_frame"] for x in recs]) > \
           5 * np.mean([x["D_deform"] for x in recs]), \
        "removing translation must matter -- otherwise bulk motion is being read as destruction"
    assert np.mean([x["R_F"] for x in recs]) > 0.9


def test_material_and_functional_identity_are_separate_numbers():
    import detect_69 as det
    src = (Path(CODE) / "detect_69.py").read_text()
    assert "R_M" in src and "R_F" in src
    assert "identity_score" not in src, "the three notions must never be summed into one"
