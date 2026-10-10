"""Stage 6.12B shared setup. Reuses Stage 6.12's frozen infrastructure
(simulator, detector, identity tracker, primary pool, RNG architecture)
unmodified -- imports common_612 and intervention_612 from
stage6_12_control_readiness/code, never re-implements them.
"""
from __future__ import annotations

import sys
from pathlib import Path

STAGE12B_DIR = Path(__file__).resolve().parents[1]         # stage6_12B_contact_persistence/
FLOCK_ROOT = STAGE12B_DIR.parent                             # stage6_flock/
S612_CODE = FLOCK_ROOT / "stage6_12_control_readiness" / "code"

for _p in (S612_CODE, Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DATA_DIR = STAGE12B_DIR / "data"
FIG_DIR = STAGE12B_DIR / "figures"
LOG_DIR = STAGE12B_DIR / "logs"

from common_612 import (                                     # noqa: E402,F401
    N_BIRDS, L_BOX, R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY,
    UV4, ROT_CCW, ROT_CW, AFFINITY_WINDOW,
    make_flock, load_frozen_rule, bearing_to_cardinal, bulk_centroid,
    frac_at_heading, torus_delta, nearest_M_pool, near_exterior,
    detect_propose, ForwardMaterialTrace611, MovingFlock611,
)
import intervention_612 as I611                               # noqa: E402,F401
