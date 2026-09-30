"""Tests for code/storage.py's tiered blinding and engine-tagging."""
import os
import sys
import shutil
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))
import storage  # noqa: E402


def test_hidden_tier_blocked_and_engine_recorded():
    root = os.path.join(os.path.dirname(__file__), "_tmp_storage_test")
    if os.path.exists(root):
        shutil.rmtree(root)
    rollout = {
        "positions": np.random.randn(16, 8),
        "secretion": np.random.randn(32, 8),
        "v_expect": np.random.randn(64, 8),
        "free_energy": np.random.randn(1, 8),
    }
    manifest = storage.save_rollout(
        root, "test_run", rollout, config={"note": "test"},
        intervention_log=[], engine="fallback_octave_subprocess",
        validation_status="validated")
    assert manifest["engine"] == "fallback_octave_subprocess"

    try:
        storage.load_hidden(root, "test_run")
        assert False, "should have raised"
    except PermissionError:
        pass

    obs = storage.load_observable(root, "test_run")
    assert obs["engine"] == "fallback_octave_subprocess"
    assert "v_expect" not in obs

    hid = storage.load_hidden(root, "test_run", audit=True)
    assert "v_expect" in hid

    shutil.rmtree(root)


if __name__ == "__main__":
    test_hidden_tier_blocked_and_engine_recorded()
    print("OK: test_hidden_tier_blocked_and_engine_recorded")
