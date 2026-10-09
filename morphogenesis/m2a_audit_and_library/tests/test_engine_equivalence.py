"""Engine tests (run ~3 min): (1) the state-exporting engine copy is bit-identical to unmodified SPM12 spm_ADEM on a fresh run;
(2) a split run (A then continuation B) equals the single run; (3) dt = 1 given explicitly equals the default (sub-stepping code path is inert at m = 1)."""
import os, sys, unittest, tempfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from m2a_sim import simulate, load
class E(unittest.TestCase):
    def test_equivalence(self):
        d = tempfile.mkdtemp(); kw = dict(seed=0, ramp_mode="abs", ramp_ref=32.0)
        simulate(f"{d}/spm.mat", 24, engine="spm", **kw); simulate(f"{d}/m2a.mat", 24, engine="m2a", **kw)
        simulate(f"{d}/a.mat", 12, engine="m2a", **kw); simulate(f"{d}/b.mat", 12, engine="m2a", cont_file=f"{d}/a.mat", **kw)
        simulate(f"{d}/dt1.mat", 24, engine="m2a", dt=1.0, **kw)
        S, M, A, B, D = (load(f"{d}/{n}.mat") for n in ("spm", "m2a", "a", "b", "dt1"))
        np.testing.assert_array_equal(S["positions"], M["positions"])
        np.testing.assert_array_equal(S["v_expect"], M["v_expect"])
        np.testing.assert_array_equal(np.hstack([A["positions"], B["positions"]]), M["positions"])
        np.testing.assert_array_equal(D["positions"], M["positions"])
if __name__ == "__main__": unittest.main()
