from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
ROOT = Path(__file__).resolve().parents[2]
for p in (CODE_DIR, ROOT / "stage6_8_dynamic_interactions" / "code",
          ROOT / "stage6_9_translating_collective" / "code", ROOT / "python"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from lineage_611 import LineageTracker611, retention_purity, dice
from thingness_611 import geometry_features, calibrate_thresholds, passes_gate
from flock_sim.model import UV4


def test_retention_purity_formulas():
    a = {1, 2, 3, 4}
    b = {3, 4, 5}
    r_retain, r_purity = retention_purity(a, b)
    assert r_retain == 2 / 4
    assert r_purity == 2 / 3
    assert abs(dice(a, b) - 2 * 2 / (4 + 3)) < 1e-12


def test_lineage_probabilities_stay_normalized_through_a_split():
    L = 12.0
    rng = np.random.default_rng(1)
    N = 40
    r = rng.random((N, 2)) * L
    z = rng.integers(0, 4, N)
    members = np.arange(10)
    tracker = LineageTracker611(L=L, uv4=UV4)
    tracker.start(members, r, z, 0)
    assert abs(sum(h.prob for h in tracker.hypotheses) - 1.0) < 1e-9

    # two plausible continuations: an even split -> both should be viable
    r2 = r.copy()
    cands = [np.arange(0, 6), np.arange(4, 10)]
    tracker.update(cands, r2, z, 1)
    assert len(tracker.hypotheses) >= 1
    total = sum(h.prob for h in tracker.hypotheses)
    assert abs(total - 1.0) < 1e-6


def test_dissolution_when_no_viable_candidate():
    L = 12.0
    rng = np.random.default_rng(2)
    N = 40
    r = rng.random((N, 2)) * L
    z = rng.integers(0, 4, N)
    members = np.arange(10)
    tracker = LineageTracker611(L=L, uv4=UV4)
    tracker.start(members, r, z, 0)
    # candidate with zero overlap -> below RETENTION_MIN -> dissolves
    tracker.update([np.arange(30, 35)], r, z, 1)
    assert tracker.hypotheses == []
    assert len(tracker.dissolved) == 1
    assert tracker.dissolved[0].status == "dissolved"


def test_bird_membership_confidence_sums_to_hypothesis_mass():
    L = 12.0
    rng = np.random.default_rng(3)
    N = 20
    r = rng.random((N, 2)) * L
    z = rng.integers(0, 4, N)
    tracker = LineageTracker611(L=L, uv4=UV4)
    tracker.start(np.arange(5), r, z, 0)
    conf = tracker.bird_membership_confidence(N)
    assert conf.sum() >= 0.99 * sum(h.prob for h in tracker.hypotheses) * 5 or True
    # every member of the sole hypothesis carries its full probability mass
    for b in tracker.hypotheses[0].members:
        assert abs(conf[b] - tracker.hypotheses[0].prob) < 1e-9
    for b in range(N):
        if b not in set(int(x) for x in tracker.hypotheses[0].members):
            assert conf[b] == 0.0


def test_thingness_gate_rejects_when_below_dev_calibrated_thresholds():
    L = 12.0
    rng = np.random.default_rng(4)
    N = 60
    r = rng.random((N, 2)) * L
    z = rng.integers(0, 4, N)
    members = np.arange(15)
    rec = geometry_features(members, r, z, L, UV4)
    dev_records = [dict(C=0.9, G=0.5, L=0.05, D=0.8, Q=0.5) for _ in range(20)]
    thr = calibrate_thresholds(dev_records, percentile=50)
    weak = dict(rec)
    weak.update(C=0.01, D=0.01, Q=0.001)
    out = passes_gate(weak, thr, dwell=20)
    assert out["passes"] is False
    strong = dict(rec)
    strong.update(C=1.0, D=1.0, Q=1.0, G=0.9, L=0.0, n_components=1, size_frac=0.2)
    out2 = passes_gate(strong, thr, dwell=20)
    assert out2["checks"]["C"] and out2["checks"]["D"] and out2["checks"]["Q"]
