import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from flock_sim.model import ModelParams, base_R, neighbor_R, neighbor_likelihood, transition_matrix, softmax_cols


def test_base_R_diagonal_is_vm_offdiag_matches_dot_products():
    R = base_R(vm=4.0, fc=1.0)
    assert np.allclose(np.diag(R), 4.0)
    # up(0) vs down(1): opposite -> dot=-1 -> fc*-1=-1
    assert np.isclose(R[0, 1], -1.0)
    # up(0) vs left(2): orthogonal -> dot=0
    assert np.isclose(R[0, 2], 0.0)
    # left(2) vs right(3): opposite -> -1
    assert np.isclose(R[2, 3], -1.0)


def test_neighbor_R_top_slot_override():
    R = neighbor_R(slot=0, vm=4.0, ca=2.0, fc=1.0)  # slot 0 = "top"
    assert R[1, 0] == -2.0  # override (o=2,s=1) 1-based -> (1,0) 0-based
    # everything else should match base_R except that one entry
    base = base_R(4.0, 1.0)
    base[1, 0] = -2.0
    assert np.allclose(R, base)


def test_softmax_cols_sums_to_one():
    x = np.random.default_rng(0).normal(size=(4, 4))
    y = softmax_cols(x, precision=3.0)
    assert np.allclose(y.sum(axis=0), 1.0)
    assert np.all(y >= 0)


def test_transition_matrix_columns_identical_across_prev_state():
    p = ModelParams()
    B = transition_matrix(p)
    for u in range(p.nu):
        col0 = B[:, 0, u]
        for c in range(1, p.nu):
            assert np.allclose(B[:, c, u], col0), "every column of B(:,:,u) must be identical (Eq. 5)"


def test_transition_matrix_peaked_at_commanded_action():
    p = ModelParams(precB=15.0)
    B = transition_matrix(p)
    for u in range(p.nu):
        dist = B[:, 0, u]
        assert np.argmax(dist) == u
        assert dist[u] > 0.9  # high precision -> concentrated


def test_neighbor_likelihood_is_column_stochastic():
    p = ModelParams()
    for slot in range(8):
        A = neighbor_likelihood(slot, p)
        assert np.allclose(A.sum(axis=0), 1.0)
