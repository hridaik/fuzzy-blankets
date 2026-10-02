"""Regression tests pinning the Part 0 audit findings to the saved data (fast; no simulation)."""
import os, sys, unittest
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from m2a_common import *

W = f"{M1}/data/withdrawal"
class F(unittest.TestCase):
    def test_AN_is_bitwise_DH(self):          # M1 harness defect: cells=[] for AN
        for i in (0, 3, 11):
            for t in ("DEV-SHORT", "DEV-LONG", "ADULT"):
                a = sio.loadmat(f"{W}/primary_{i:04d}_AN_{t}_N1024.mat")["positions"]
                b = sio.loadmat(f"{W}/primary_{i:04d}_DH_{t}_N1024.mat")["positions"]
                self.assertEqual(np.abs(a - b).max(), 0.0)
    def test_direct_octave_matches_m1(self):
        for nm, (k, i) in {"direct_primary_0000": ("primary", 0), "direct_secondary_0000": ("secondary", 0)}.items():
            a = sio.loadmat(f"{DATA}/part0/{nm}.mat")["positions"]
            b = sio.loadmat(f"{M1}/data/census/{k}_{i:04d}_N512.mat")["positions"]
            self.assertEqual(np.abs(a - b).max(), 0.0)
    def test_noise_seed_has_no_effect(self):
        a = sio.loadmat(f"{DATA}/part0/noiseseed_primary0000_s1001.mat")["positions"]
        b = sio.loadmat(f"{M1}/data/census/primary_0000_N512.mat")["positions"]
        self.assertEqual(np.abs(a - b).max(), 0.0)
    def test_secondary_bin0_equals_injected_draw(self):
        from analysis import P_X
        m = sio.loadmat(f"{M1}/data/census/secondary_0000_N512.mat")
        v0 = secondary_v0(0); p = softmax_cols(v0)
        self.assertLess(np.abs(m["positions"][:, 0].reshape(8, 2).T - P_X @ p).max(), 1e-12)
    def test_designed_role_maps(self):
        import json
        from analysis import d_target
        perms = json.load(open(f"{DATA}/part0/perms.json"))["perms"]
        for nm, p in perms.items():
            m = sio.loadmat(f"{DATA}/part0/perm_{nm}.mat")
            d, rm, _, _ = d_target(m["positions"][:, -1].reshape(8, 2).T, m["secretion"][:, -1].reshape(4, 8, order="F"))
            self.assertEqual([int(x) for x in rm], p)
if __name__ == "__main__":
    unittest.main()
