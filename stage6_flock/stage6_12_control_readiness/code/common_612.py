"""Stage 6.12 shared setup. Path bootstrap + re-exports only.

Reuses, unmodified:
  - MovingFlock611 (stage6_11 simulator; identical physics to Stage 6.9's
    frozen model when social="raw", cohesion=1.0 -- the Section O/P primary
    operating point, quoted from common_611.py, not re-derived).
  - detect_69.propose (raw detector).
  - ForwardMaterialTrace611 (frozen material-association identity layer,
    Jaccard >= 0.30, from the material_identity_step2_20260921 audit).
  - blind_pool_611.nearest_M_pool (PRIMARY position-only nearest-20 exterior
    pool) and intervention_api_611.near_exterior (SECONDARY true-R oracle
    pool, sensitivity only).
  - UV4 / ROT_CCW (cardinal-direction bookkeeping) and
    run_online_control_611.bearing_to_cardinal (historical deterministic
    h_star convention: one 90-degree CCW cardinal turn from the observed
    bulk-translation direction).

Nothing here redesigns identity, RNG, or pool semantics -- see
NEXT_CONTROLLER_SPEC_INPUTS.md and RNG_PROTOCOL.md for why.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

STAGE12_DIR = Path(__file__).resolve().parents[1]           # stage6_12_control_readiness/
FLOCK_ROOT = STAGE12_DIR.parent                              # stage6_flock/
S611_CODE = FLOCK_ROOT / "stage6_11_translating_torus" / "code"
S611_AUDIT = FLOCK_ROOT / "stage6_11_translating_torus" / "audit"
S609_CODE = FLOCK_ROOT / "stage6_9_translating_collective" / "code"
S608_CODE = FLOCK_ROOT / "stage6_8_dynamic_interactions" / "code"
MATERIAL_TRACE_CODE = S611_AUDIT / "material_identity_step2_20260921" / "code"

for _p in (FLOCK_ROOT / "python", S608_CODE, S609_CODE, S611_CODE,
           S611_AUDIT, MATERIAL_TRACE_CODE, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DATA_DIR = STAGE12_DIR / "data"
FIG_DIR = STAGE12_DIR / "figures"
LOG_DIR = STAGE12_DIR / "logs"

from flock_sim.model import UV4, ROT_CCW, ROT_CW                       # noqa: E402,F401
from common_611 import (                                                # noqa: E402,F401
    N_BIRDS, L_BOX, BETA_610, S_610, resolved_params,
    R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY,
)
from moving_flock_611 import MovingFlock611                             # noqa: E402,F401
from detect_69 import propose as detect_propose                          # noqa: E402,F401
from geometry_611 import torus_delta                                     # noqa: E402,F401
from blind_pool_611 import nearest_M_pool                                # noqa: E402,F401
from intervention_api_611 import near_exterior                           # noqa: E402,F401 (ORACLE, sensitivity only)
from forward_material_trace_611 import ForwardMaterialTrace611, RULE_FAMILY_BUILDERS  # noqa: E402,F401
import json

FROZEN_RULE_JSON = MATERIAL_TRACE_CODE.parent / "data" / "identity_rule_calibration.json"

AFFINITY_WINDOW = 6   # detect_69.W_AFFINITY, quoted from run_online_control_611.py


def make_flock() -> MovingFlock611:
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                           social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def load_frozen_rule():
    calib = json.load(open(FROZEN_RULE_JSON))
    frozen = calib["frozen_rule"]
    return RULE_FAMILY_BUILDERS[frozen["letter"]](**frozen["params"]), frozen


def bearing_to_cardinal(delta: np.ndarray) -> int:
    """Quoted verbatim from run_online_control_611.py."""
    return int(np.argmax(UV4 @ delta))


def bulk_centroid(r: np.ndarray, members, L: float) -> np.ndarray:
    """Torus-aware centroid of a member set: unwrap relative to the first
    member using torus_delta, then average -- avoids the wraparound-average
    artefact of a naive mean on a periodic domain."""
    ids = np.array(sorted(int(m) for m in members))
    anchor = r[ids[0]]
    rel = torus_delta(r[ids], anchor[None, :], L)
    return anchor + rel.mean(axis=0)


def frac_at_heading(members, z: np.ndarray, heading: int):
    if not members:
        return None
    ids = np.array(sorted(int(m) for m in members), dtype=int)
    return float((z[ids] == heading).mean())
