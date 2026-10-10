"""C3: identity-validity envelope, estimated ONLY from uncontrolled baseline
continuations (never controlled-episode outcomes). Distinguishes a
"candidate collective" (whatever an adaptive definition proposes at t) from
a "valid continuation" of the original lineage: a lower-tail bound on
relative size S_I(t) = |I_t|/|I_0|, and a minimum local continuity J_min on
J(I_t, I_{t-1}).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

COLLECTIVE_IDENTITY_CODE = Path(__file__).resolve().parents[4] / "stage6_5" / "collective_identity" / "code"
sys.path.insert(0, str(COLLECTIVE_IDENTITY_CODE))
from definitions import jaccard  # noqa: E402

PERCENTILE = 5.0


def compute_envelope(tracks: list[list[np.ndarray]], n_I0_per_track: list[int]) -> dict:
    """tracks: list of I_t sequences (one per baseline flock/replicate),
    each a causal, uncontrolled-continuation track under one identity
    definition. Returns the 5th-percentile lower bounds on S_I and J,
    pooling all (flock, t) observations."""
    S_I_vals, J_vals = [], []
    for track, n_I0 in zip(tracks, n_I0_per_track):
        for t, I_t in enumerate(track):
            S_I_vals.append(len(I_t) / n_I0 if n_I0 else float("nan"))
            if t > 0:
                J_vals.append(jaccard(track[t - 1], I_t))
    S_I_vals = np.array(S_I_vals)
    J_vals = np.array(J_vals) if J_vals else np.array([1.0])
    return dict(
        S_I_min=float(np.percentile(S_I_vals, PERCENTILE)),
        J_min=float(np.percentile(J_vals, PERCENTILE)),
        n_observations_S_I=len(S_I_vals), n_observations_J=len(J_vals),
        percentile=PERCENTILE,
    )


def is_valid(I_t: np.ndarray, last_valid: np.ndarray, n_I0: int, envelope: dict) -> dict:
    S_I = len(I_t) / n_I0 if n_I0 else float("nan")
    J = jaccard(I_t, last_valid)
    valid = (S_I >= envelope["S_I_min"]) and (J >= envelope["J_min"])
    return dict(valid=bool(valid), S_I=float(S_I), J=float(J))


def retrospective_guard(raw_track: list[np.ndarray], n_I0: int, envelope: dict,
                         grace_period: int = 3) -> dict:
    """C4's guard applied post-hoc to an already-generated raw candidate
    track (used for C5's evaluation-only pass, where there is no live
    control loop to intervene in -- only re-labeling of an existing
    trajectory's already-realized candidate sequence). Returns the guarded
    track plus per-step validity/collapse flags, using the SAME
    hold-last-valid-then-declare-unresolved rule as the closed-loop guard."""
    guarded = [raw_track[0]]
    valid_track = [True]
    collapsed_track = [False]
    last_valid = raw_track[0]
    grace_counter = 0
    collapsed = False
    for t in range(1, len(raw_track)):
        raw = raw_track[t]
        check = is_valid(raw, last_valid, n_I0, envelope)
        if check["valid"]:
            last_valid = raw
            grace_counter = 0
            guarded.append(raw)
            valid_track.append(True)
            collapsed_track.append(collapsed)
        else:
            grace_counter += 1
            if grace_counter > grace_period:
                collapsed = True
            guarded.append(last_valid)
            valid_track.append(False)
            collapsed_track.append(collapsed)
    return dict(guarded_track=guarded, valid_track=valid_track, collapsed_track=collapsed_track,
                identity_collapse_unresolved=collapsed)
