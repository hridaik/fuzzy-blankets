"""Unit tests for regularized_lineage.py's scoring rule: raising lambda_T
should strengthen the previous collective's advantage over a marginally
better-coherence, low-overlap candidate (suppressing jitter), while a small
lambda_T still lets a genuinely large coherence gain win (permitting real
transitions). Parameters below are verified numerically, not just derived by
hand -- see the module docstring's own note on why lambda_J=1.0 was
rejected during protocol prep (it made ANY transition mathematically
unbeatable, since F in [0,1] can never exceed the guaranteed +lambda_J
continuity bonus for keeping the previous collective).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from regularized_lineage import score, LAMBDA_J_FIXED  # noqa: E402


def test_high_overlap_marginal_gain_loses_more_as_lambda_T_rises():
    """prev={0,1,2,3,4}, candidate={1,2,3,4,5} (4/5 shared): candidate's
    coherence edge (1.0 vs 0.8) is small relative to the turnover cost of
    dropping bird 0 and recruiting bird 5. Raising lambda_T should widen
    prev's margin over this marginal alternative -- exactly the "suppress
    jitter" behavior."""
    prev = np.array([0, 1, 2, 3, 4])
    cand = np.array([1, 2, 3, 4, 5])
    z = np.array([2, 1, 1, 1, 1, 1, 0, 0, 0, 0])  # prev: F=4/5=0.8; cand: F=5/5=1.0

    margins = []
    for lt in (0.0, 0.5, 1.0, 2.0):
        s_prev = score(prev, prev, z, lambda_J=LAMBDA_J_FIXED, lambda_T=lt)
        s_cand = score(cand, prev, z, lambda_J=LAMBDA_J_FIXED, lambda_T=lt)
        margins.append(s_prev - s_cand)

    assert margins == sorted(margins), "prev's margin over a marginal candidate should grow monotonically with lambda_T"
    assert margins[0] < 0, "at lambda_T=0 the marginally more coherent candidate should still win"
    assert margins[-1] > 0, "at large lambda_T, prev should win despite the small coherence edge"


def test_low_overlap_large_coherence_gain_wins_at_small_lambda_T_only():
    """prev={0,1,2,3,4} (F=0.4, scattered headings), candidate={4,5,6,7,8}
    (F=1.0, one shared bird): a genuinely large reorganization with a big
    coherence gain should still be selected at a small lambda_T, but lose
    once lambda_T is large enough -- regularization has a real dial, not an
    all-or-nothing lock."""
    prev = np.array([0, 1, 2, 3, 4])
    cand = np.array([4, 5, 6, 7, 8])
    z = np.array([0, 0, 1, 2, 3, 3, 3, 3, 3])  # prev: F=2/5=0.4; cand: F=5/5=1.0

    s_prev_small = score(prev, prev, z, lambda_J=LAMBDA_J_FIXED, lambda_T=0.1)
    s_cand_small = score(cand, prev, z, lambda_J=LAMBDA_J_FIXED, lambda_T=0.1)
    assert s_cand_small > s_prev_small, "a large coherence gain should win under a small lambda_T"

    s_prev_large = score(prev, prev, z, lambda_J=LAMBDA_J_FIXED, lambda_T=1.0)
    s_cand_large = score(cand, prev, z, lambda_J=LAMBDA_J_FIXED, lambda_T=1.0)
    assert s_prev_large > s_cand_large, "the same transition should be suppressed once lambda_T is large enough"


def test_keeping_previous_always_gets_maximum_jaccard():
    COLLECTIVE_IDENTITY_CODE = Path(__file__).resolve().parents[4] / "stage6_5" / "collective_identity" / "code"
    sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))
    from definitions import jaccard
    prev = np.array([0, 1, 2])
    assert jaccard(prev, prev) == 1.0
