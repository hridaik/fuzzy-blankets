"""Shared EVALUATION-SIDE setup for Stage 6.9.

Imports the simulator and Stage 6.8's evaluation-side helpers, so it must never
be imported by an inference-side module (`identity_69.py`, `detect_69.py`) --
enforced by `tests/test_no_topology_leakage_69.py`.

Stage 6.8's inference modules (`louvain.py` in particular) are imported
read-only; nothing in Stages 6-6.8 is modified by this stage.
"""
from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]      # stage6_9_translating_collective/
ROOT = STAGE_DIR.parent                               # stage6_flock/
S68 = ROOT / "stage6_8_dynamic_interactions" / "code"
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(S68))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flock_sim.model import ModelParams, UV4, rotate_cw, rotate_ccw   # noqa: E402
from flock_sim.active_inference import build_model                     # noqa: E402

DATA_DIR = STAGE_DIR / "data"
FIG_DIR = STAGE_DIR / "figures"
LOG_DIR = STAGE_DIR / "logs"
CONFIG_DIR = STAGE_DIR / "configs"

NU = 4

# ---- frozen Stage 6.9 constants (PROTOCOL_6_9.md) --------------------------
N_BIRDS = 400
L_BOX = 24.0
# R and v re-specified after the degree mis-specification recorded in
# logs/translation_gate_criteria_predeclared.txt, ADDENDUM 4. R = 0.9 gives a
# mean realized live in-degree of 8.9 in the clustered steady state -- the Moore
# model's scale, as the task brief requires -- against 21.2 at the original
# R = 1.6. v is scaled with R to preserve the neighbour-crossing time v/R = 0.31.
V_SPEED = 0.28
R_RADIUS = 0.9
V_SPEED_SUPERSEDED = 0.5        # the mis-specified pair; its results are not
R_RADIUS_SUPERSEDED = 1.6       # reported, only cited as superseded
BETA, RHO, OMEGA = 1.0, 15.0, 3.0     # the frozen Stage 6-6.8 values

GATE_NT = 200
GATE_T_START = 40
GATE_SEEDS = list(range(40))
DEV_SEEDS = list(range(0, 20))
HELDOUT_SEEDS = list(range(20, 40))


def dump_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_default)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def _default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


def sha256_of_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
