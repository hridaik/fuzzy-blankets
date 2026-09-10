"""Shared EVALUATION-SIDE setup for Stage 6.11.

Path bootstrap only. Stages 6-6.10 are imported read-only and are never
modified by this stage; `moving_flock_611` subclasses Stage 6.9's simulator
rather than editing it, so the frozen 6.9 model stays byte-identical and stays
available as the comparator every Stage 6.11 claim is measured against.

Importing this module puts `../python` (the frozen `flock_sim` package),
Stage 6.8's `code/` and Stage 6.9's `code/` on `sys.path`, in that order.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]      # stage6_11_translating_torus/
ROOT = STAGE_DIR.parent                              # stage6_flock/
S68 = ROOT / "stage6_8_dynamic_interactions" / "code"
S69 = ROOT / "stage6_9_translating_collective" / "code"
for _p in (ROOT / "python", S68, S69, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from flock_sim.model import ModelParams, UV4            # noqa: E402,F401

DATA_DIR = STAGE_DIR / "data"
FIG_DIR = STAGE_DIR / "figures"
LOG_DIR = STAGE_DIR / "logs"
CONFIG_DIR = STAGE_DIR / "configs"

NU = 4

# ---- Stage 6.9's spec-compliant operating point, quoted not re-derived ------
# From stage6_9_translating_collective/code/common_69.py. R = 0.9 / v = 0.28 is
# the pair whose mean realized live in-degree (8.9) is closest to the Moore
# model's 8; R = 1.6 / v = 0.5 is the superseded 3x-over-connected pair whose
# consequences (77% policy saturation, 1-of-47 causal interface) motivated
# Section N. Both are reference points for validation, not new choices.
N_BIRDS = 400
L_BOX = 24.0
R_SPEC, V_SPEC = 0.9, 0.28
R_SUPERSEDED, V_SUPERSEDED = 1.6, 0.5


def dump_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_default)


def _default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(f"not JSON serializable: {type(o)}")
