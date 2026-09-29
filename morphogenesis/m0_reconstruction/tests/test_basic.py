"""Minimal sanity tests for the M0 Python reconstruction.

Run with: python -m pytest tests/ -q   (from morphogenesis/m0_reconstruction/)
or:       python tests/test_basic.py

These test the PYTHON PORT's internal consistency only -- they cannot and do
not test fidelity to spm_ADEM, since no reference run exists (README.md).
"""
import os
import sys
import shutil
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from template import decode_template, T_L2, T_L4  # noqa: E402
from generative import spm_softmax_cols, sensitivity  # noqa: E402
from field import field_concentration  # noqa: E402
from solver import run as solver_run  # noqa: E402
from generative import Mg  # noqa: E402
import storage  # noqa: E402


def test_template_n_cells():
    P_x, P_s, n, m = decode_template(T_L2)
    assert n == 8, f"expected 8 cells for L=2 template, got {n}"
    assert m == 4
    assert P_x.shape == (2, 8)
    assert P_s.shape == (4, 8)
    # spm_detrend removes column mean -> P.x rows should sum ~0
    assert np.allclose(P_x.sum(axis=1), 0, atol=1e-9)


def test_template_l4_n_cells():
    P_x, P_s, n, m = decode_template(T_L4)
    assert n == 16


def test_softmax_columns_sum_to_one():
    rng = np.random.default_rng(0)
    v = rng.standard_normal((8, 8))
    p = spm_softmax_cols(v)
    assert np.allclose(p.sum(axis=0), 1.0)
    assert (p >= 0).all()


def test_sensitivity_bounds():
    assert sensitivity(0) == 0.0
    assert 0 < sensitivity(0.5) < 1
    assert np.isclose(sensitivity(1.0), 1 - np.exp(-2), atol=1e-12)


def test_field_law_self_and_decay():
    x = np.array([[0.0, 1.0], [0.0, 0.0]])  # 2 cells at (0,0),(1,0)
    s = np.array([[1.0, 0.0]])  # only cell 0 secretes signal 0
    c = field_concentration(x, s)
    # concentration at cell 0's own location: exp(0)*1 + exp(-1)*0 = 1
    assert np.isclose(c[0, 0], 1.0)
    # at cell 1's location: exp(-1)*1 (distance 1) + 0
    assert np.isclose(c[0, 1], np.exp(-1.0))


def test_solver_no_nan_short_run():
    P_x, P_s, n, m = decode_template()
    P_c = field_concentration(P_x, P_s)
    rng = np.random.default_rng(0)
    v0 = rng.standard_normal((n, n)) / 8.0
    gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / 8)
    tr = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=8)
    assert not np.isnan(tr["a_x"]).any()
    assert not np.isinf(tr["a_x"]).any()


def test_determinism_no_noise():
    P_x, P_s, n, m = decode_template()
    P_c = field_concentration(P_x, P_s)
    rng = np.random.default_rng(0)
    v0 = rng.standard_normal((n, n)) / 8.0
    gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / 8)
    tr1 = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=8)
    tr2 = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=8)
    assert np.array_equal(tr1["a_x"], tr2["a_x"])


def test_hidden_tier_blocked_without_audit(tmp_path=None):
    root = os.path.join(os.path.dirname(__file__), "_tmp_storage_test")
    if os.path.exists(root):
        shutil.rmtree(root)
    P_x, P_s, n, m = decode_template()
    P_c = field_concentration(P_x, P_s)
    rng = np.random.default_rng(0)
    v0 = rng.standard_normal((n, n)) / 8.0
    gx, gs, _, _ = Mg(v0, P_x, P_s, P_c, t=1 / 8)
    tr = solver_run(v0, gx, gs, P_x, P_s, P_c, n_bins=8)
    storage.save_run(root, "unit_test_run", tr, config={"note": "test"},
                      intervention_log=[])
    try:
        storage.load_hidden(root, "unit_test_run")
        assert False, "should have raised PermissionError"
    except PermissionError:
        pass
    h = storage.load_hidden(root, "unit_test_run", audit=True)
    assert "v_expectations" in h
    shutil.rmtree(root)


if __name__ == "__main__":
    fns = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"OK: {fn.__name__}")
    print(f"{len(fns)} tests passed")
