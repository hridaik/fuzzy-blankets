"""Shared setup for Stage 6.7, self-contained. Imports flock_sim and a
handful of Stage 6/6.5/6.6 helpers, all unmodified (see PLAN.md "Reused,
unmodified"). This module itself is EVALUATION-SIDE (it imports
`flock_sim.lattice`) and must never be imported by an inference-side module
(`blind_cache.py`, `directed_graph_inference.py`, `graph_bootstrap.py`,
`predictive_boundary.py`, `causal_discovery.py`) -- see
tests/test_no_topology_leakage.py.
"""
from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]      # stage6_7_blind_boundary/
ROOT = STAGE_DIR.parent                                # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v1_mechanism_audit" / "code"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "stage6_5" / "boundary_inference" / "code"))
sys.path.insert(0, str(ROOT / "stage6_5" / "refinement" / "causal_redundancy" / "code"))
sys.path.insert(0, str(ROOT / "stage6_6_collective_landscape" / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flock_sim.lattice import Lattice  # noqa: E402
from flock_sim.model import ModelParams, rotate_cw, rotate_ccw  # noqa: E402
from flock_sim.metrics import coherence, target_heading_fraction  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402

from dynamical_shell import one_hop_neighbors, graph_distance_from_set  # noqa: E402
from common_v2 import find_flock, evaluate_arm, T_U, T_R  # noqa: E402
from common_66 import (  # noqa: E402
    resize_to_k, structural_shell, near_exterior, K_INTERIOR, K_BOUNDARY_BUDGET,
    R_REPLICATES, W_WINDOW, PRIMARY_SEEDS, avg_internal_degree, is_connected,
)
from archetypes import build_condition, CONDITIONS  # noqa: E402
from windowed_data import run_condition_replicates  # noqa: E402
from nodewise_model import NodewiseModel, flatten_transitions, design_matrix  # noqa: E402
from greedy_selection import fit_eval, greedy_forward_select  # noqa: E402

# common_66/common_v2's own headers re-insert several sys.path entries
# (including stage6_5/boundary_inference/code) at position 0 as a SIDE EFFECT
# of the imports above, which would otherwise shadow same-named Stage 6.7
# modules. Re-assert this directory's priority last, so a bare `import X`
# from any Stage 6.7 script always resolves to this directory first.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ---- Stage 6.7 frozen constants (task brief sections 2-8) ----
W_WINDOW_67 = 10
R_REPLICATES_67 = 100
PRIMARY_SEEDS_67 = [2, 3, 4]
NU = 4
K_MAX = 12                      # boundary size cap (section 6)
DELTA_PRED = 0.01               # nats/bird-step, primary predictive criterion (section 7)
SHORTLIST_K_DEFAULT = 25        # coefficient-based shortlist size (section 4), matches api.py default
B_BOOT_SPEC = 30                # frozen "spec" bootstrap count (section 5)
TRAIN_FRAC, VAL_FRAC, TEST_FRAC = 0.6, 0.2, 0.2  # section 2
SNAPSHOT_TIMEPOINT = T_U         # control-end, matching Stage 6.6's convention

assert W_WINDOW_67 == W_WINDOW and R_REPLICATES_67 == R_REPLICATES, (
    "Stage 6.7's W/R must match Stage 6.6's frozen observation protocol (task brief section 2)."
)

DATA_DIR = STAGE_DIR / "data"
FIG_DIR = STAGE_DIR / "figures"
LOG_DIR = STAGE_DIR / "logs"
CONFIG_DIR = STAGE_DIR / "configs"
STAGE66_DATA_DIR = ROOT / "stage6_6_collective_landscape" / "data"


def dump_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lattice_100() -> Lattice:
    return Lattice(nn=100, nh=8)


def snapshot_key(seed: int, condition: str) -> str:
    return f"seed{seed}_{condition}"


SEED_OFFSETS_67 = {  # distinct RNG range, disjoint from V1-V3/6.5/6.6's own offset ranges
    "no_control": 760_000,
    "shell_only": 761_000,
    "same_direction": 762_000,
    "opposite": 763_000,
    "disordered": 764_000,
}


def reference_I0(lattice: Lattice, seed: int, rng: np.random.Generator) -> dict:
    fl = find_flock(seed, lattice=lattice)
    if fl is None:
        raise RuntimeError(f"seed {seed} does not qualify (find_flock returned None)")
    I0_raw = fl["I0"]
    I0 = resize_to_k(lattice, I0_raw, K_INTERIOR, rng=rng)
    return dict(seed=seed, t0=fl["t0"], h0=fl["h0"], h_star=fl["h_star"],
                I0_raw=I0_raw.tolist(), I0=I0, size_raw=len(I0_raw), z_t0=fl["z_t0"])


def build_snapshot_replicates(lattice: Lattice, seed: int, condition: str, rng: np.random.Generator,
                               n_rep: int = R_REPLICATES_67):
    """Reuses Stage 6.6's exact archetype-condition + replicate machinery
    (task brief section 2: 'existing Stage 6.6 observation protocol'). Returns
    (ref, cond, z_reps, t_snapshot)."""
    ref = reference_I0(lattice, seed, rng)
    cond = build_condition(lattice, ref["I0"], ref["h_star"], condition, f_E=1.0, t0=0, t_u=T_U)
    nt = T_U + T_R
    z_reps = run_condition_replicates(ref["z_t0"], lattice, cond["interventions"], nt=nt,
                                       n_rep=n_rep, seed_offset=SEED_OFFSETS_67[condition])
    return ref, cond, z_reps, T_U


class WindowDataset3:
    """60/20/20 trajectory(=replicate)-level split of the trailing W-step
    window ending at `t` (task brief section 2). Never reads index > t.
    Splitting at the replicate level (not the timestep level) means every
    timestep from one replicate's rollout stays in the same split -- no
    future leakage, matching Stage 6.5's `trajectory_gen.make_splits`
    convention extended from a 2-way to a 3-way split."""

    def __init__(self, train_prev, train_next, val_prev, val_next, test_prev, test_next,
                 n_replicates, n_rep_train, n_rep_val, n_rep_test, effective_window, t,
                 representative_z, train_ids, val_ids, test_ids):
        self.train_prev, self.train_next = train_prev, train_next
        self.val_prev, self.val_next = val_prev, val_next
        self.test_prev, self.test_next = test_prev, test_next
        self.n_replicates = n_replicates
        self.n_rep_train, self.n_rep_val, self.n_rep_test = n_rep_train, n_rep_val, n_rep_test
        self.effective_window = effective_window
        self.t = t
        self.representative_z = representative_z
        self.train_ids, self.val_ids, self.test_ids = train_ids, val_ids, test_ids


def build_window_dataset3(z_hist_reps: np.ndarray, t: int, W: int = W_WINDOW_67,
                           fractions: tuple = (TRAIN_FRAC, VAL_FRAC, TEST_FRAC),
                           split_seed: int = 0) -> WindowDataset3:
    n_rep, nt_plus1, n_bird = z_hist_reps.shape
    start = max(0, t - W + 1)
    effective_window = t - start + 1
    if effective_window < 2:
        raise ValueError(f"t={t} leaves fewer than 2 states of history (effective_window={effective_window})")

    rng = np.random.default_rng(split_seed)
    order = rng.permutation(n_rep)
    f_train, f_val, _f_test = fractions
    n_train = max(1, int(round(f_train * n_rep)))
    n_val = max(1, int(round(f_val * n_rep)))
    n_train = min(n_train, n_rep - 2) if n_rep > 2 else n_train
    n_val = min(n_val, max(0, n_rep - n_train - 1))
    train_ids = order[:n_train]
    val_ids = order[n_train:n_train + n_val]
    test_ids = order[n_train + n_val:]
    if len(test_ids) == 0:
        test_ids = val_ids
    if len(val_ids) == 0:
        val_ids = train_ids

    def _flatten(ids):
        prev_list, next_list = [], []
        for r in ids:
            traj = z_hist_reps[r, start:t + 1]
            prev_list.append(traj[:-1])
            next_list.append(traj[1:])
        if not prev_list:
            return np.zeros((0, n_bird), dtype=int), np.zeros((0, n_bird), dtype=int)
        return np.concatenate(prev_list, axis=0), np.concatenate(next_list, axis=0)

    train_prev, train_next = _flatten(train_ids)
    val_prev, val_next = _flatten(val_ids)
    test_prev, test_next = _flatten(test_ids)

    return WindowDataset3(
        train_prev, train_next, val_prev, val_next, test_prev, test_next,
        n_replicates=n_rep, n_rep_train=len(train_ids), n_rep_val=len(val_ids), n_rep_test=len(test_ids),
        effective_window=effective_window, t=t, representative_z=z_hist_reps[0, t],
        train_ids=train_ids.tolist(), val_ids=val_ids.tolist(), test_ids=test_ids.tolist(),
    )
