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

# ---- Stage 6.10's selected "robust-responsive precision" operating point ----
# RESULTS_6_10.md / SUMMARY_6_10.md Part G. `s` is a single scalar multiplier
# applied to BOTH precB (rho) and precC (omega) at simulator construction time
# -- this is stage6_8_dynamic_interactions/code/episode_data.py:make_simulator,
# quoted exactly (not re-derived):
#
#   def make_simulator(nn, beta, s):
#       return FovSimulator(ModelParams(beta=beta, precB=s*RHO, precC=s*OMEGA), ...)
#
# with RHO = 15.0, OMEGA = 3.0 (stage6_8 common_68.py). So (beta=0.4, s=0.75)
# resolves to ModelParams(beta=0.4, precB=11.25, precC=2.25); PROTOCOL/RESULTS
# for 6.10 report only the (beta, s) pair, never the resolved precB/precC --
# `resolved_params()` below makes that mapping explicit for Stage 6.11 so it
# is not re-copied as an ambiguous pair. See PARAMETER_DICTIONARY.md.
BETA_610 = 0.4
S_610 = 0.75
RHO_BASE = 15.0    # precB at s=1 (stage6_8 common_68.RHO)
OMEGA_BASE = 3.0   # precC at s=1 (stage6_8 common_68.OMEGA)


def resolved_params(beta: float = BETA_610, s: float = S_610) -> "ModelParams":
    """ModelParams for a given (beta, s) pair, using Stage 6.10's exact
    precB/precC scaling convention. `s` is NOT itself a ModelParams field."""
    return ModelParams(beta=beta, precB=s * RHO_BASE, precC=s * OMEGA_BASE)


# ---- Section O/P world-selection result --------------------------------
# See logs/regime_selection_predeclared_611.txt (ADDENDUM). Selected by the
# predeclared rule (rank by mesoscopic episode fraction on held-out seeds);
# this is the exact Stage 6.9 spec (R, v) pair with the Section M/N
# positional-cohesion term switched on, which converts Stage 6.9's 0/40
# translation-gate failure into a 20/20 held-out mesoscopic confirmation.
R_PRIMARY, V_PRIMARY, COHESION_PRIMARY = 0.9, 0.28, 1.0
SOCIAL_PRIMARY = "raw"

# Validated secondary/robustness regime (lower policy saturation: 4.7% vs
# 53.8%). Not the primary; kept as a disclosed comparator and a fallback if
# causal-interface identifiability (item 11) fails at the primary regime --
# never swapped in on the basis of control success (PLAN.md Section V rule 5).
R_SECONDARY, V_SECONDARY, COHESION_SECONDARY = 1.1, 0.14, 0.0


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
