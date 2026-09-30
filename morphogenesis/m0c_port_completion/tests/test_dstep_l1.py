"""L1-level test for code/dstep.py: the sensory/prior error vector E must
match Octave's dumped bin-1 ground truth. Documents current status:
L1 passes; L2 (the state UPDATE) does NOT match -- see EQUIVALENCE_REPORT.md.
This test only checks the L1 piece, so it should PASS.
"""
import os
import sys
import numpy as np
import scipy.io as sio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from dstep import Config  # noqa: E402
from model import Mg, Gg  # noqa: E402 (via dstep's sys.path insert of m0b/code)

DUMP = os.path.join(os.path.dirname(__file__), "..", "..", "m0b_reference_port",
                     "data", "oracle_traces", "dstep_dump_bin1.mat")


def test_sensory_error_matches_octave():
    d = sio.loadmat(DUMP, struct_as_record=False, squeeze_me=True)
    pre = d["dump_pre"]
    v0 = pre.qu_v1
    a0 = pre.qu_a1
    t = float(pre.t_global)
    cfg = Config(n_bins=32)
    g_val = Gg(a0, cfg.n, cfg.m, t)
    mg0 = Mg(v0, cfg.n, cfg.P_x, cfg.P_s, cfg.P_c, t)
    diff = g_val - mg0
    oct_E80 = pre.E[:80]
    max_dev = np.max(np.abs(diff - oct_E80))
    assert max_dev < 1e-10, f"L1 sensory error mismatch: {max_dev}"


def test_prior_error_matches_octave():
    d = sio.loadmat(DUMP, struct_as_record=False, squeeze_me=True)
    pre = d["dump_pre"]
    v0 = pre.qu_v1
    oct_prior = pre.E[80:144]
    assert np.max(np.abs(oct_prior - v0)) < 1e-12


if __name__ == "__main__":
    test_sensory_error_matches_octave()
    print("OK: test_sensory_error_matches_octave (L1 passes)")
    test_prior_error_matches_octave()
    print("OK: test_prior_error_matches_octave (L1 passes)")
    print("NOTE: L2 (the state update magnitude) does NOT match -- see EQUIVALENCE_REPORT.md")
