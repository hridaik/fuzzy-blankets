"""A5: compare Python model.Mg/model.Gg against live Octave output on 20
identical random inputs. Imports m0b's validated model.py (not modified).
"""
import sys
import os
import numpy as np
import scipy.io as sio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                 "m0b_reference_port", "code"))
from model import Mg, Gg  # noqa: E402

TOL_REL = 1e-9


def run():
    d = sio.loadmat(
        os.path.join(os.path.dirname(__file__), "..", "data", "oracle_traces",
                      "a5_function_check.mat"),
        struct_as_record=False, squeeze_me=True)
    P = d["P"]
    P_x, P_s, P_c = np.atleast_2d(P.x), np.atleast_2d(P.s), np.atleast_2d(P.c)
    n = int(d["n"])
    m = int(d["m"])

    v_tests = d["v_tests"]
    a_tests = d["a_tests"]
    t_tests = np.atleast_1d(d["t_tests"])
    Mg_out = d["Mg_out"]
    Gg_out = d["Gg_out"]

    max_rel_mg = 0.0
    max_rel_gg = 0.0
    n_tests = len(v_tests)
    for k in range(n_tests):
        v = np.atleast_2d(v_tests[k])
        t = float(t_tests[k])
        v_flat = v.ravel(order="F")
        g_flat = Mg(v_flat, n, P_x, P_s, P_c, t)
        g_x_py = g_flat[:2 * n].reshape(2, n, order="F")
        g_s_py = g_flat[2 * n:2 * n + m * n].reshape(m, n, order="F")
        g_c_py = g_flat[2 * n + m * n:].reshape(m, n, order="F")

        oct_g = Mg_out[k]
        rel_x = np.abs(g_x_py - oct_g.x).max() / (np.abs(oct_g.x).max() + 1e-12)
        rel_s = np.abs(g_s_py - oct_g.s).max() / (np.abs(oct_g.s).max() + 1e-12)
        rel_c = np.abs(g_c_py - oct_g.c).max() / (np.abs(oct_g.c).max() + 1e-12)
        max_rel_mg = max(max_rel_mg, rel_x, rel_s, rel_c)

        a = a_tests[k]
        a_flat = np.concatenate([np.atleast_2d(a.x).ravel(order="F"),
                                  np.atleast_2d(a.s).ravel(order="F")])
        gg_flat = Gg(a_flat, n, m, t)
        gg_x_py = gg_flat[:2 * n].reshape(2, n, order="F")
        gg_s_py = gg_flat[2 * n:2 * n + m * n].reshape(m, n, order="F")
        gg_c_py = gg_flat[2 * n + m * n:].reshape(m, n, order="F")

        oct_gg = Gg_out[k]
        rel_x2 = np.abs(gg_x_py - oct_gg.x).max() / (np.abs(oct_gg.x).max() + 1e-12)
        rel_s2 = np.abs(gg_s_py - oct_gg.s).max() / (np.abs(oct_gg.s).max() + 1e-12)
        rel_c2 = np.abs(gg_c_py - oct_gg.c).max() / (np.abs(oct_gg.c).max() + 1e-12)
        max_rel_gg = max(max_rel_gg, rel_x2, rel_s2, rel_c2)

    print(f"A5: {n_tests} test cases")
    print(f"Mg max relative deviation: {max_rel_mg:.3e}")
    print(f"Gg max relative deviation: {max_rel_gg:.3e}")
    print(f"tolerance declared: {TOL_REL:.0e}")
    passed = max_rel_mg < TOL_REL and max_rel_gg < TOL_REL
    print("PASS" if passed else "FAIL")
    return passed, max_rel_mg, max_rel_gg


if __name__ == "__main__":
    run()
