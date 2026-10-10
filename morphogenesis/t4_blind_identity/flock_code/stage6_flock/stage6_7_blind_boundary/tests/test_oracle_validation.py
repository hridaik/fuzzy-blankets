"""Unit tests for oracle_validation.py's pure-arithmetic functions
(graph_recovery_metrics, overlap_categories, classify_outcome) -- hand-worked
examples, no simulation needed."""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from oracle_validation import graph_recovery_metrics, overlap_categories, classify_outcome  # noqa: E402


def test_graph_recovery_metrics_perfect_match():
    m = graph_recovery_metrics([1, 2, 3], [1, 2, 3], n_exterior=10)
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["jaccard"] == 1.0
    assert m["exact_match"] is True


def test_graph_recovery_metrics_partial_overlap():
    # B_hat={1,2,4}, B_true={1,2,3}: tp=2, fp=1, fn=1
    m = graph_recovery_metrics([1, 2, 4], [1, 2, 3], n_exterior=10)
    assert m["tp"] == 2 and m["fp"] == 1 and m["fn"] == 1
    assert m["precision"] == 2 / 3
    assert m["recall"] == 2 / 3
    assert m["jaccard"] == 2 / 4
    assert m["exact_match"] is False


def test_graph_recovery_metrics_empty_bhat():
    m = graph_recovery_metrics([], [1, 2, 3], n_exterior=10)
    assert m["tp"] == 0
    assert m["recall"] == 0.0


def test_overlap_categories():
    B_pred = [1, 2, 3]
    B_causal = [2, 3, 4]
    B_true = [1, 2, 3, 4, 5]
    o = overlap_categories(B_pred, B_causal, B_true)
    assert o["predictive_only"] == [1]
    assert o["causal_only"] == [4]
    assert o["both"] == [2, 3]
    assert o["true_missed_by_both"] == [5]


def test_classify_outcome_all_four_quadrants():
    assert classify_outcome(excess_loss=0.005, jaccard=0.8) == "A_identifiable"
    assert classify_outcome(excess_loss=0.005, jaccard=0.1) == "B_reduced_interface"
    assert classify_outcome(excess_loss=0.05, jaccard=0.8) == "C_estimator_inadequate"
    assert classify_outcome(excess_loss=0.05, jaccard=0.1) == "D_failed"
