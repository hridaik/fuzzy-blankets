"""Shared EVALUATION-SIDE setup for Stage 6.10.

Imports the simulator and Stage 6.8's modules read-only. Nothing in Stages
6-6.9 is modified by this stage; every path below is opened for reading.
"""
from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]
ROOT = STAGE_DIR.parent                       # stage6_flock/
S68 = ROOT / "stage6_8_dynamic_interactions" / "code"
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(S68))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flock_sim.model import ModelParams, UV4, rotate_cw, rotate_ccw   # noqa: E402
from flock_sim.lattice import Lattice                                  # noqa: E402
from flock_sim.active_inference import policy_posterior                # noqa: E402

DATA_DIR = STAGE_DIR / "data"
FIG_DIR = STAGE_DIR / "figures"
LOG_DIR = STAGE_DIR / "logs"
CONFIG_DIR = STAGE_DIR / "configs"
S68_DATA = ROOT / "stage6_8_dynamic_interactions" / "data"

NU = 4


def dump_json(obj, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_default)


def load_json(path):
    with open(path) as f:
        return json.load(f)


def _default(o):
    if isinstance(o, np.ndarray): return o.tolist()
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, (np.floating,)): return float(o)
    if isinstance(o, (np.bool_,)): return bool(o)
    if isinstance(o, (set, frozenset)): return sorted(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


def sha256_of_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def target_alignment(z, I, h_star) -> float:
    """H*(I, t) -- fraction of the CURRENT tracked lineage on the target heading."""
    I = np.asarray(sorted(int(x) for x in I))
    if len(I) == 0:
        return float("nan")
    return float(np.mean(np.asarray(z)[I] == int(h_star)))
