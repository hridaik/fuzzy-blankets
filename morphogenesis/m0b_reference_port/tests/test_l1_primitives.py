"""L1 (function-level) equivalence tests: each asserts a Python primitive
matches a value obtained by actually running the corresponding Octave
function (not re-derived) -- see EQUIVALENCE_REPORT.md for the live Octave
session transcripts these expected values come from.

Run: python tests/test_l1_primitives.py   (from m0b_reference_port/)
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
from spm_port import spm_DEM_R, spm_dx, spm_DEM_embed, spm_diff_jacobian  # noqa: E402


def test_spm_DEM_R():
    R = spm_DEM_R(3, 1)
    expected = np.array([[1.5, 0, 1.0], [0, 2.0, 0], [1.0, 0, 2.0]])
    assert np.allclose(R, expected), R


def test_spm_dx():
    A = np.array([[-0.5, 0.2], [0.1, -0.3]])
    f = np.array([1.0, -0.5])
    dx = spm_dx(A, f, 1.0)
    expected = np.array([0.75079871, -0.39467986])
    assert np.allclose(dx, expected, atol=1e-6), dx


def test_spm_DEM_embed_interior():
    Y = np.array([[1, 2, 4, 7, 11, 16, 22, 30]], dtype=float)
    y = spm_DEM_embed(Y, 3, 4, 1.0, (0,))
    vals = [v[0] for v in y]
    assert np.allclose(vals, [7.0, 3.5, 1.0]), vals


def test_spm_DEM_embed_boundary():
    Y = np.array([[1, 2, 4, 7, 11, 16, 22, 30]], dtype=float)
    y = spm_DEM_embed(Y, 3, 1, 1.0, (0,))
    vals = [v[0] for v in y]
    assert np.allclose(vals, [1.0, 0.5, 1.0]), vals


def test_spm_diff_jacobian():
    def f(x):
        return np.array([x[0] ** 2 + x[1], np.sin(x[1]) - x[0]])
    x0 = np.array([0.5, 1.2])
    J = spm_diff_jacobian(f, x0)
    expected = np.array([[1.00033546, 1.0], [-1.0, 0.36220142]])
    assert np.allclose(J, expected, atol=1e-6), J


if __name__ == "__main__":
    fns = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK: {fn.__name__}")
    print(f"{len(fns)}/{len(fns)} L1 tests passed")
