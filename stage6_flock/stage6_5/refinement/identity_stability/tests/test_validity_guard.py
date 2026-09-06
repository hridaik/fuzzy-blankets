"""C3/C4 tests: the validity envelope and guard logic should flag a
synthetic collapse trajectory as invalid/unresolved, and should NOT flag a
genuine large-but-coherent transition as collapse."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from validity_guard import compute_envelope, is_valid  # noqa: E402


def test_envelope_from_stable_baseline_tracks():
    """A baseline where |I_t| stays near |I_0| and membership is stable
    should produce a permissive-but-nontrivial envelope."""
    I0 = np.arange(20)
    track = [I0.copy() for _ in range(10)]  # perfectly stable, material-like
    envelope = compute_envelope([track], [20])
    assert envelope["S_I_min"] == 1.0  # every observation has |I_t|/|I_0| == 1
    assert envelope["J_min"] == 1.0


def test_collapse_candidate_flagged_invalid():
    """A candidate that shrinks to near-one-bird should fail both the size
    and continuity bars set by a stable baseline."""
    I0 = np.arange(20)
    track = [I0.copy() for _ in range(10)]
    envelope = compute_envelope([track], [20])

    last_valid = I0.copy()
    collapse_candidate = np.array([3])  # 1 of 20 members
    check = is_valid(collapse_candidate, last_valid, n_I0=20, envelope=envelope)
    assert not check["valid"]
    assert check["S_I"] == 1 / 20


def test_genuine_but_nontrivial_transition_can_pass_a_loose_envelope():
    """A baseline with realistic (nonzero) variability should tolerate a
    same-order-of-magnitude membership shift, not just an exact match."""
    rng = np.random.default_rng(0)
    I0 = np.arange(20)
    track = [I0.copy()]
    prev = I0.copy()
    for _ in range(30):
        # simulate mild natural churn: swap ~2 members each step
        cur = prev.copy()
        idx_out = rng.choice(len(cur), size=2, replace=False)
        pool = np.array([j for j in range(20, 100) if j not in cur])
        cur[idx_out] = rng.choice(pool, size=2, replace=False)
        track.append(np.array(sorted(cur.tolist())))
        prev = track[-1]
    envelope = compute_envelope([track], [20])

    candidate = track[-1]  # a realistic, mildly-churned continuation
    check = is_valid(candidate, track[-2], n_I0=20, envelope=envelope)
    assert check["valid"]
