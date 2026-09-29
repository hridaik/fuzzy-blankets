"""Final translating-flock closure (A: organizational role, B: directed
causal interface, C: timing susceptibility). Shared setup.

Reuses, unmodified: the whole Stage 6.12/6.12B/6.12C infrastructure --
simulator (MovingFlock611), detector, ForwardMaterialTrace611, nearest-20
exterior pool, frozen identity rule, RNG/CRN architecture,
simulate_branch/trace_target/outcome_metrics, J_assoc/J_conservative.

NEW in this stage (own modules, not reused): live_edges-based organizational
class assignment, live-edge diagnostic persistence, minimal temporal
reachability, and the A_minus_j/J_minus_j interior-actuation correction
(implementing INTERIOR_ACTUATION_METHOD_NOTE.md).
"""
from __future__ import annotations

import sys
from pathlib import Path

CLOSURE_DIR = Path(__file__).resolve().parents[1]      # final_translating_flock_closure/
FLOCK_ROOT = CLOSURE_DIR.parent                          # stage6_flock/
S612_CODE = FLOCK_ROOT / "stage6_12_control_readiness" / "code"
S612B_CODE = FLOCK_ROOT / "stage6_12B_contact_persistence" / "code"
S612C_CODE = FLOCK_ROOT / "stage6_12C_kinematic_contact_confirmation" / "code"

for _p in (S612_CODE, S612B_CODE, S612C_CODE, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DATA_DIR = CLOSURE_DIR / "data"
FIG_DIR = CLOSURE_DIR / "figures"
LOG_DIR = CLOSURE_DIR / "logs"

from common_612c import (                                     # noqa: E402,F401
    N_BIRDS, L_BOX, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY,
    UV4, ROT_CCW, ROT_CW, AFFINITY_WINDOW,
    make_flock, load_frozen_rule, bearing_to_cardinal, bulk_centroid,
    frac_at_heading, torus_delta, nearest_M_pool, near_exterior,
    detect_propose, ForwardMaterialTrace611, MovingFlock611,
)
import intervention_612 as I611                               # noqa: E402,F401
import intervention_612b as IB                                 # noqa: E402,F401
