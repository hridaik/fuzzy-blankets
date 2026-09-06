"""Shared utilities for the V1 mechanism audit. Imports flock_sim/analysis from
the existing, frozen `python/` tree (../../python) WITHOUT modifying anything
there. All new code and data for the audit live under v1_mechanism_audit/.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]           # stage6_flock/
AUDIT_DIR = Path(__file__).resolve().parents[1]        # v1_mechanism_audit/
sys.path.insert(0, str(ROOT / "python"))

from flock_sim.lattice import Lattice, bird_to_rowcol  # noqa: E402
from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from flock_sim.metrics import target_heading_fraction, coherence  # noqa: E402
from flock_sim.spectral import analyze_window, jaccard  # noqa: E402
from flock_sim.model import rotate_cw, ModelParams  # noqa: E402
from analysis.baseline_characterization import find_qualifying_t0  # noqa: E402

T_U = 20
T_R = 20
TW = 5
BASE_SEED_OFFSET = 100_000   # identical to protocol_v1 phase3/4/5 -> common random numbers
N_DEV = 50                   # development-scale replicate count, matching protocol_v1


def load_canonical():
    d = ROOT / "data" / "protocol_v1"
    data = np.load(d / "canonical_snapshot.npz")
    meta = json.load(open(d / "canonical_snapshot_meta.json"))
    I0 = np.array(meta["I0"])
    t0 = meta["t0"]
    h_star = meta["h_star"]
    h0 = meta["h0"]
    z_t0 = data["z_hist_full"][t0]
    z_hist_full = data["z_hist_full"]
    lattice = Lattice(nn=100, nh=8)
    return dict(I0=I0, t0=t0, h0=h0, h_star=h_star, z_t0=z_t0,
                z_hist_full=z_hist_full, lattice=lattice, meta=meta)


def load_phase4_response_map():
    d = ROOT / "data" / "protocol_v1"
    return json.load(open(d / "phase4_5_response_map.json"))


def load_baseline_rows():
    d = ROOT / "data" / "baseline_v1"
    return json.load(open(d / "baseline_rows.json"))


def dump_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else o)


def percentile_rank(value: float, population: np.ndarray) -> float:
    """Fraction of the population <= value (0-100 scale)."""
    population = np.asarray(population)
    return float(100.0 * np.mean(population <= value))
