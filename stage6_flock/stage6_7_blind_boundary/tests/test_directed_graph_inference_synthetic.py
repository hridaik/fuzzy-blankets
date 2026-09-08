"""Sanity check for directed_graph_inference.py on synthetic data with a
KNOWN injected dependency: bird 0's next heading is a deterministic copy of
bird 1's current heading, and independent of everyone else. The inferred
graph should recover a large positive Delta_{0<-1} and (near-)zero for every
other source, with bird 1 appearing in bird 0's coefficient shortlist."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[2]  # stage6_flock/
CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(STAGE_DIR / "stage6_5" / "boundary_inference" / "code"))
sys.path.insert(0, str(CODE_DIR))

from directed_graph_inference import infer_directed_graph, coefficient_shortlist  # noqa: E402
from blind_cache import BlindCache  # noqa: E402


def _make_synthetic(n_bird=6, n_train=1200, n_val=400, seed=0):
    rng = np.random.default_rng(seed)

    def _gen(n):
        prev = rng.integers(0, 4, size=(n, n_bird))
        nxt = rng.integers(0, 4, size=(n, n_bird))
        nxt[:, 0] = prev[:, 1]  # bird 0's next heading == bird 1's current heading, exactly
        return prev, nxt

    return _gen(n_train), _gen(n_val)


def test_injected_dependency_recovered_with_large_positive_delta():
    (train_prev, train_next), (val_prev, val_next) = _make_synthetic()
    result = infer_directed_graph(train_prev, train_next, val_prev, val_next,
                                   n_bird=6, shortlist_k=5)
    row0 = result["G"][0]
    assert row0[1] > 0.1, f"expected a large positive Delta_0<-1, got {row0[1]}"
    for j in (2, 3, 4, 5):
        assert row0[j] <= row0[1], f"unrelated source {j} should not out-rank the injected dependency"


def test_shortlist_includes_injected_source():
    (train_prev, train_next), (val_prev, val_next) = _make_synthetic()
    cache = BlindCache(train_prev, train_next, val_prev, val_next)
    shortlist = coefficient_shortlist(cache, i=0, n_bird=6, shortlist_k=3)
    assert 1 in shortlist


def test_no_dependency_case_gives_near_zero_or_unshortlisted_deltas():
    """A target bird with NO real dependency on anyone should not show a
    strong stable positive edge to any single source (only sampling noise)."""
    (train_prev, train_next), (val_prev, val_next) = _make_synthetic()
    result = infer_directed_graph(train_prev, train_next, val_prev, val_next,
                                   n_bird=6, shortlist_k=5)
    row2 = result["G"][2]  # bird 2's next heading is pure noise, independent of everyone
    assert max(row2.values()) < 0.1, f"expected small deltas for a target with no real dependency, got {row2}"
