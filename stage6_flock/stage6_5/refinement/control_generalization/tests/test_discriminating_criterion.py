"""Pure logic tests for the B2 discriminating-flock filter -- no simulator."""
from __future__ import annotations

import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1] / "code"
sys.path.insert(0, str(CODE_DIR))

from seed_scan import is_discriminating  # noqa: E402


def test_qualifies_on_frozen_boundary():
    assert is_discriminating(p_oracle=0.7, p_random=0.3)
    assert is_discriminating(p_oracle=1.0, p_random=0.0)


def test_rejects_easy_flock_where_random_also_succeeds():
    assert not is_discriminating(p_oracle=1.0, p_random=0.95)


def test_rejects_hard_flock_where_oracle_fails():
    assert not is_discriminating(p_oracle=0.17, p_random=0.0)


def test_rejects_just_below_oracle_threshold():
    assert not is_discriminating(p_oracle=0.69, p_random=0.0)


def test_rejects_just_above_random_threshold():
    assert not is_discriminating(p_oracle=1.0, p_random=0.31)
