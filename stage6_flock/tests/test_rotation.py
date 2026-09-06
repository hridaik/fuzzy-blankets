import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from flock_sim.model import UV4, ROT_CW, ROT_CCW


def test_rot_cw_matches_geometric_90_degree_clockwise_rotation():
    # clockwise rotation in standard (x,y) axes: (x,y) -> (y,-x)
    for h in range(4):
        x, y = UV4[h]
        rotated = np.array([y, -x])
        target_state = ROT_CW[h]
        assert np.allclose(UV4[target_state], rotated), (h, rotated, UV4[target_state])


def test_rot_ccw_is_inverse_of_rot_cw():
    for h in range(4):
        assert ROT_CCW[ROT_CW[h]] == h


def test_naive_mod_increment_is_NOT_a_rotation():
    # documents the bug that was caught: (h+1)%4 is not equal to either rotation
    # for at least one starting heading.
    naive = np.array([(h + 1) % 4 for h in range(4)])
    assert not np.array_equal(naive, ROT_CW)
    assert not np.array_equal(naive, ROT_CCW)
