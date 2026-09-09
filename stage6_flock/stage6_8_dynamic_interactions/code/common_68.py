"""Shared EVALUATION-SIDE setup for Stage 6.8.

This module imports `flock_sim.lattice` and therefore must NEVER be imported
by an inference-side module (`observer.py`, `candidate_detection.py`,
`louvain.py`, `spectral_proposal.py`, `tracker.py`, `heading_stratified.py`,
`predictive_boundary_68.py`, `challenger.py`, `probing.py`) -- enforced by
`tests/test_no_topology_leakage_68.py`.

Nothing in Stage 6-6.7 is modified by this stage. Everything imported from
`../python`, `../stage6_5`, `../stage6_6_collective_landscape` and
`../stage6_7_blind_boundary` is read-only and used verbatim.
"""
from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]      # stage6_8_dynamic_interactions/
ROOT = STAGE_DIR.parent                               # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "stage6_5" / "boundary_inference" / "code"))
sys.path.insert(0, str(ROOT / "stage6_5" / "refinement" / "causal_redundancy" / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flock_sim.lattice import Lattice                      # noqa: E402
from flock_sim.model import ModelParams, UV4, rotate_cw, rotate_ccw  # noqa: E402
from flock_sim.active_inference import build_model, PrecomputedModel  # noqa: E402
from flock_sim.metrics import polarization, coherence       # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

DATA_DIR = STAGE_DIR / "data"
FIG_DIR = STAGE_DIR / "figures"
LOG_DIR = STAGE_DIR / "logs"
CONFIG_DIR = STAGE_DIR / "configs"

NN = 100
NU = 4
L_SIDE = 10

# ---------------------------------------------------------------- geometry --
# Position convention (derived, not invented; see PROTOCOL_6_8.md section 2):
# `flock_sim.lattice` uses 0-based column-major indices with
#   row = idx % L, col = idx // L
# and slot 0 ("top") = idx-1 = row-1. `flock_sim.model.SLOT_OVERRIDES` sets the
# collision term R[down, up] = -ca for slot 0, i.e. "my TOP neighbour heading
# DOWN while I head UP is a collision" -- which fixes `top` == the +y direction
# of `UV4`'s up = (0, 1). Hence:
#       x = col,      y = (L - 1) - row
# and the eight slot displacement vectors below follow by arithmetic.
SLOT_VEC = np.array([
    [0.0,  1.0],   # 0 top       idx-1     -> row-1 -> y+1
    [0.0, -1.0],   # 1 down      idx+1     -> row+1 -> y-1
    [-1.0, 0.0],   # 2 left      idx-L     -> col-1 -> x-1
    [1.0,  0.0],   # 3 right     idx+L     -> col+1 -> x+1
    [-1.0, 1.0],   # 4 topleft   idx-L-1   -> col-1,row-1
    [1.0, -1.0],   # 5 downright idx+L+1   -> col+1,row+1
    [-1.0,-1.0],   # 6 downleft  idx-L+1   -> col-1,row+1
    [1.0,  1.0],   # 7 topright  idx+L-1   -> col+1,row-1
])


def lattice_positions(nn: int = NN) -> np.ndarray:
    """(nn, 2) float positions in the same plane as UV4 headings."""
    L = int(round(nn ** 0.5))
    idx = np.arange(nn)
    row, col = idx % L, idx // L
    return np.stack([col.astype(float), (L - 1) - row.astype(float)], axis=1)


def lattice_100() -> Lattice:
    return Lattice(nn=NN, nh=8)


# ------------------------------------------------------------------- edges --
def flatten_edges(lattice: Lattice):
    """Flatten the static geometric Moore graph into parallel arrays.

    Returns (recv, slot, src) where `recv[e]` is the bird whose update the edge
    feeds, `src[e]` the observed neighbour, and `slot[e]` the canonical slot id.
    Matches the edge enumeration inside `flock_sim.active_inference.compute_G`
    exactly, so masking edges here is a strict restriction of that function.
    """
    recv = np.concatenate([np.full(len(ids), i) for i, ids in enumerate(lattice.neighbor_ids)])
    slot = np.concatenate(lattice.neighbor_slot)
    src = np.concatenate(lattice.neighbor_ids)
    return recv.astype(int), slot.astype(int), src.astype(int)


def visibility_table() -> np.ndarray:
    """VIS[slot, h] = True iff a neighbour in `slot` satisfies
    (r_j - r_i) . d_i >= 0 for a receiver whose current heading is `h`.
    This is the FOV rule of task brief section 3, precomputed."""
    return (SLOT_VEC @ UV4.T) >= 0.0        # (8, 4)


# --------------------------------------------------------------------- io ---
def dump_json(obj, path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def load_json(path: Path):
    with open(path) as f:
        return json.load(f)


def _json_default(o):
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


def jaccard(a, b) -> float:
    sa, sb = set(int(x) for x in a), set(int(x) for x in b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


# ------------------------------------------------- frozen Stage 6.8 constants
BETA_GRID = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]     # task brief section 2, primary scan
RHO = 15.0
OMEGA = 3.0
S_GRID = [0.5, 0.75, 1.0, 1.5, 2.0]                # secondary (rho, omega) = s*(15, 3) scan
L0_BETA = 1.0                                       # frozen Stage 6-6.7 reference

PHASE_SEEDS = list(range(20))                       # phase scan seeds
PHASE_NT = 120
PHASE_BURN_IN = 40                                  # statistics measured on t >= 40

DEV_SEEDS = [0, 1, 2, 3, 4, 5, 6, 7]                # calibration / development
HELDOUT_SEEDS = [20, 21, 22, 23, 24, 25, 26, 27, 28, 29]  # never used for any threshold
