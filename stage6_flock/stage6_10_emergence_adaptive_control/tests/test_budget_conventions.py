"""The fixed-K budget convention must not change what an arm chose.

These are regression tests for a real failure: `_rank_by_influence` was written
against a matrix while `adaptive_control._exact_influence` returns a nested
dict, so every arm after the benchmark crashed with
`TypeError: bad operand type for unary -: 'dict'` -- five hours into a run.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

CODE = Path(__file__).resolve().parents[1] / "code"
S68 = Path(__file__).resolve().parents[2] / "stage6_8_dynamic_interactions" / "code"
sys.path.insert(0, str(CODE)); sys.path.insert(0, str(S68))

import closed_loop as cl


INFLUENCE = {5: {1: 0.1, 2: 0.2}, 7: {1: 0.9}, 9: {1: 0.0, 2: 0.0}}
CANDS = [5, 7, 9, 11]


def test_rank_accepts_the_nested_dict_the_controller_actually_produces():
    order = cl._rank_by_influence(INFLUENCE, CANDS)
    assert order[0] == 7                      # 0.9 total
    assert order[1] == 5                      # 0.3 total
    assert set(order) == set(CANDS)           # unscored candidates still ranked
    assert order.index(11) > order.index(5)   # absent from influence -> last


def test_pad_preserves_the_arms_own_choices():
    rng = np.random.default_rng(0)
    chosen = [9]
    out = cl._pad_to_k(chosen, cl._rank_by_influence(INFLUENCE, CANDS), CANDS, 3, rng)
    assert 9 in out                           # never drops what the arm picked
    assert len(out) == 3
    assert out == sorted(out)


def test_pad_is_a_noop_when_already_at_budget():
    rng = np.random.default_rng(0)
    out = cl._pad_to_k([5, 7], cl._rank_by_influence(INFLUENCE, CANDS), CANDS, 2, rng)
    assert out == [5, 7]


def test_pad_falls_back_to_candidates_without_a_ranking():
    rng = np.random.default_rng(0)
    out = cl._pad_to_k([], None, CANDS, 2, rng)
    assert len(out) == 2 and set(out) <= set(CANDS)


def test_private_keys_never_reach_the_record():
    src = (CODE / "closed_loop.py").read_text()
    assert 'if not k.startswith("_")' in src
