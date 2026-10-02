"""Fast unit tests for the M2A Octave toolkit (no long simulations)."""
import os, re, sys, unittest
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from m2a_common import *

def parse_T(src, L):
    txt = open(src).read()
    blocks = re.findall(r"T\s*=\s*\[(.*?)\];", txt, re.S)
    mats = [np.array([[float(x) for x in row.split()] for row in b.replace("\n", ";").split(";") if row.strip()]) for b in blocks]
    return mats[0] if L == 2 else mats[1]

class T(unittest.TestCase):
    def test_templates_match_spm_source(self):
        src = os.path.join(SPM12, "toolbox", "DEM", "DEM_morphogenesis.m")
        for L in (2, 4):
            out = os.path.join(DATA, f"tmpl{L}.mat")
            octave(f"T=m2a_templates({L}); save('-v7','{out}','T');")
            np.testing.assert_array_equal(sio.loadmat(out)["T"], parse_T(src, L))
            os.remove(out)

    def test_pulse_and_ramp(self):
        out = os.path.join(DATA, "tmp_pulse.mat")
        octave(f"p=arrayfun(@(b) m2a_pulse(b,10,4),0:20); global M2A; M2A=struct('ramp_mode','const','ramp_const',0.3,'N',64); s=m2a_ramp(0.5); save('-v7','{out}','p','s');")
        d = sio.loadmat(out); os.remove(out)
        p = d["p"].ravel()
        self.assertAlmostEqual(p[12], 1.0); self.assertEqual(p[10], 0.0); self.assertEqual(p[14], 0.0)
        self.assertAlmostEqual(p.sum(), 2.0)       # discrete sum of raised cosine of width 4
        self.assertAlmostEqual(d["s"].item(), 0.3)

    def test_default_ramp_is_spm(self):
        out = os.path.join(DATA, "tmp_ramp.mat")
        octave(f"global M2A; M2A=struct('ramp_mode','N','N',512); tt=(1:512)/512; s=arrayfun(@(x) m2a_ramp(x),tt); save('-v7','{out}','s');")
        s = sio.loadmat(out)["s"].ravel(); os.remove(out)
        np.testing.assert_allclose(s, 1 - np.exp(-(np.arange(1, 513) / 512) * 2), rtol=1e-14)

    def test_integer_cast_guard(self):
        # regression: Python ints saved via savemat become int64 in Octave; run() must cast (caught in Part 0)
        src = open(os.path.join(M2A_ORACLE, "m2a_run.m")).read()
        self.assertIn("double(cfg.(f{1}))", src)

class TestEvents(unittest.TestCase):
    def _gg(self, evs, bin_abs=10):
        """Call the process mapping m2a_Gg with/without events on a fixed action; return (g_ref, g_ev) arrays."""
        import m2a_sim
        out = os.path.join(DATA, "tmp_gg.mat"); cf = os.path.join(DATA, "tmp_gg_cfg.mat")
        sio.savemat(cf, {"ev": m2a_sim.make_events(evs)})
        octave(f"S=load('{cf}'); global M2A t; M2A=struct('ramp_mode','abs','ramp_ref',32,'t_off',0,'N',64,'events',S.ev); "
               f"T=m2a_templates(2); P.x=rand(2,8)*2-1; P.s=double(rand(4,8)>0.5); P.c=m2a_field(P.x,P.s); a.x=P.x; a.s=P.s; av=spm_vec(a); "
               f"t={bin_abs}/64; g1=m2a_Gg([],[],av,a); M2A.events=[]; g0=m2a_Gg([],[],av,a); "
               f"save('-v7','{out}','g0','g1');")
        d = sio.loadmat(out); os.remove(out); os.remove(cf)
        return d["g0"], d["g1"]

    def test_AN_only_target_cell_sensation_changes(self):
        ev = [dict(type="kuch", cells=[3], sign=1, onset=0, off=None, w=4)]
        g0, g1 = self._gg(ev, bin_abs=10)
        for field in ("x", "s", "c"):
            diff = np.abs(g1[field][0, 0] - g0[field][0, 0])
            changed_cols = np.nonzero(diff.reshape(diff.shape[0], -1).max(axis=0) > 0)[0] if diff.ndim > 1 else None
            if field == "x":
                self.assertEqual(list(changed_cols), [3])             # only cell 3 (0-based)
                self.assertEqual(np.abs(diff[1]).max(), 0.0)          # only the long-axis row
            else:
                self.assertEqual(diff.max(), 0.0)                     # secretion, field sensation untouched
    def test_DH_changes_all_cells(self):
        ev = [dict(type="kuch", cells=list(range(8)), sign=1, onset=0, off=None, w=4)]
        g0, g1 = self._gg(ev)
        self.assertEqual(len(np.nonzero(np.abs(g1["x"][0, 0] - g0["x"][0, 0])[0] > 0)[0]), 8)
    def test_switch_off_restores(self):
        ev = [dict(type="kuch", cells=[3], sign=1, onset=0, off=20, w=4)]
        g0, g1 = self._gg(ev, bin_abs=30)
        self.assertEqual(np.abs(g1["x"][0, 0] - g0["x"][0, 0]).max(), 0.0)

if __name__ == "__main__":
    unittest.main()
