"""Tests for code/analysis.py, including a regression test for the
cell_type_from_expression bug (matched against all 8 per-slot codes,
which have duplicates, instead of the unique type codes) caught during
this stage's own development."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from analysis import (cell_type_from_expression, _UNIQ_TYPES, _SLOT_TYPE,
                       d_target, d_pair, TARGET_TYPE_CODES, P_X, P_S)


def test_unique_types_count():
    # This template has 4 distinct expression codes (T in {1,2,3,4})
    assert _UNIQ_TYPES.shape[0] == 4


def test_cell_type_from_expression_on_exact_targets():
    # Feeding the TARGET's own expression codes back in must recover the
    # correct TYPE for every cell (regression test for the duplicate-slot bug)
    types = cell_type_from_expression(P_S)
    assert np.array_equal(types, _SLOT_TYPE), (types, _SLOT_TYPE)


def test_d_target_on_exact_target_is_zero():
    dist, role_map, ftype, n_mismatch = d_target(P_X, P_S)
    assert dist < 1e-9, dist
    assert np.array_equal(role_map, np.arange(8)) or dist < 1e-9


def test_d_pair_role_swap_invariance():
    # Swap two cells of the SAME type between two copies of the target --
    # d_pair must be ~0 (role-swap must never count as a difference)
    x1, s1 = P_X.copy(), P_S.copy()
    x2, s2 = P_X.copy(), P_S.copy()
    # cells 0,1,2 are all the same type (see analysis.py's _SLOT_TYPE)
    x2[:, [0, 1]] = x2[:, [1, 0]]
    s2[:, [0, 1]] = s2[:, [1, 0]]
    d = d_pair(x1, s1, x2, s2)
    assert d < 1e-9, d


def test_d_pair_zero_for_identical():
    d = d_pair(P_X, P_S, P_X, P_S)
    assert d < 1e-12


if __name__ == "__main__":
    test_unique_types_count()
    print("OK: test_unique_types_count")
    test_cell_type_from_expression_on_exact_targets()
    print("OK: test_cell_type_from_expression_on_exact_targets")
    test_d_target_on_exact_target_is_zero()
    print("OK: test_d_target_on_exact_target_is_zero")
    test_d_pair_role_swap_invariance()
    print("OK: test_d_pair_role_swap_invariance")
    test_d_pair_zero_for_identical()
    print("OK: test_d_pair_zero_for_identical")
