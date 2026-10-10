"""Shared V3 utilities. Self-contained relative to v1_mechanism_audit (does not
import its code), builds directly on v2_interface_control's frozen policy and
utilities (imported unmodified), exactly as v2's common_v2 relates to v1.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]           # stage6_flock/
V3_DIR = Path(__file__).resolve().parents[1]           # v3_refinement/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))

from flock_sim.lattice import Lattice  # noqa: E402
from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from flock_sim.spectral import analyze_window  # noqa: E402
from flock_sim.model import rotate_cw  # noqa: E402

from common_v2 import (  # noqa: E402
    find_flock, dynamical_shell, evaluate_arm as evaluate_arm_v2,
    T_U, T_R, TW, N_REP,
)
from selection_rules import (  # noqa: E402
    rule_A_degree, rule_B_leverage, rule_C_patch, rule_D_random,
)

DEV_SEEDS = [2, 3, 4, 8, 9, 10, 11, 13, 14, 16]  # V2's frozen 10, reused as V3 dev set
HELD_OUT_SCAN_START = 17
HELD_OUT_TARGET = 6
HELD_OUT_MAX_SEED = 40

V3_SEED_OFFSET = 900_000  # distinct range from v1 (100k), phase6 (200k), v2 (300k/400k)


def dump_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)


def load_dev_flocks():
    """Recompute the 10 dev flocks (seeds 2,3,4,8,9,10,11,13,14,16) fresh from
    structure -- identical procedure to v2_interface_control/code/replicate.py,
    just addressed directly by seed rather than by scanning, since the seed
    list is already frozen, published evidence (RESULTS_V2.md)."""
    flocks = []
    for seed in DEV_SEEDS:
        fl = find_flock(seed)
        assert fl is not None, f"dev seed {seed} unexpectedly failed to qualify -- V2 freeze violated"
        flocks.append(fl)
    return flocks


def find_held_out_flocks(cache_path: Path | None = None):
    """First HELD_OUT_TARGET qualifying flocks found scanning seeds
    HELD_OUT_SCAN_START..HELD_OUT_MAX_SEED, numeric order, first-found -- a
    range never touched by V1 or V2. Cached to data/held_out_flocks.json on
    first run so the exact seed list is fixed thereafter."""
    cache_path = cache_path or (V3_DIR / "data" / "held_out_flocks.json")
    if cache_path.exists():
        seeds = json.load(open(cache_path))["seeds"]
        return [find_flock(s) for s in seeds]

    flocks = []
    seed = HELD_OUT_SCAN_START
    while len(flocks) < HELD_OUT_TARGET and seed <= HELD_OUT_MAX_SEED:
        fl = find_flock(seed)
        if fl is not None:
            flocks.append(fl)
        seed += 1
    seeds = [fl["seed"] for fl in flocks]
    dump_json(dict(scan_start=HELD_OUT_SCAN_START, scan_end_inclusive=seed - 1,
                    target=HELD_OUT_TARGET, seeds=seeds), cache_path)
    return flocks
