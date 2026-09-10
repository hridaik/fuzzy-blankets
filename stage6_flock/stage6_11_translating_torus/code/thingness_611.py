"""Stage 6.11 thingness gate (task brief item 10).

INFERENCE-SIDE. A gate on the SCIENTIFIC OBJECT (is this candidate a "thing"
worth calling a translating collective), never on the mechanism preventing
global order -- that stays in the simulator, behind the physics/observer
firewall (item 1). All geometric quantities (C, D, Q, n_components,
size_frac) are computed here from observed positions/headings alone; G
(positive/internal predictive integration) and L (certified residual
leakage) are produced by the predictive-boundary module (item 7,
`predictive_boundary_611.py`) and are only CONSUMED here, never computed.

Thresholds are calibrated on UNCONTROLLED DEVELOPMENT DATA ONLY (percentiles
over development-set candidate records), predeclared before being applied to
any detection or control run -- PLAN.md Section V rule 6 ("do not tune
thingness thresholds on control success").
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from identity_69 import centroid
from geometry_611 import local_scale, local_exterior_contrast, compactness, connected_components


def internal_coherence(members: np.ndarray, z: np.ndarray, uv4: np.ndarray) -> float:
    """C: |mean heading vector| among members -- how aligned the candidate's
    own membership currently is, independent of anything exterior."""
    m = uv4[z[members]].mean(axis=0)
    return float(np.hypot(m[0], m[1]))


def geometry_features(members: np.ndarray, r: np.ndarray, z: np.ndarray, L: float,
                       uv4: np.ndarray, nu: int = 4) -> dict:
    """The observable half of a thingness record (C, D, Q, n_components,
    size_frac). G and L are added by the caller once the predictive-boundary
    module has scored this candidate."""
    periphery_radius = local_scale(r, L)
    D = local_exterior_contrast(members, r, z, L, periphery_radius, nu)
    ncomp = connected_components(members, r, L, periphery_radius)
    c = centroid(r[members], L)
    Q = compactness(members, r, L, c)
    C = internal_coherence(members, z, uv4)
    return dict(C=C, D=D, Q=Q, n_components=ncomp, size_frac=len(members) / len(z),
                periphery_radius=periphery_radius)


@dataclass
class ThingnessThresholds:
    C_min: float
    G_min: float
    L_max: float
    D_min: float
    Q_min: float
    size_frac_range: tuple
    dwell_min: int
    percentile: float


def calibrate_thresholds(dev_records: list[dict], size_frac_range=(0.03, 0.55),
                          dwell_min: int = 15, percentile: float = 25.0) -> ThingnessThresholds:
    """Percentile thresholds from UNCONTROLLED DEVELOPMENT candidates only.
    `percentile` is the lower-tail cut for C/G/D/Q (candidate must clear the
    bottom `percentile`% of the development distribution) and the matching
    upper-tail cut for L (leakage must be below the top `percentile`%)."""
    def pct(key, p):
        vals = [r[key] for r in dev_records if r.get(key) is not None]
        return float(np.percentile(vals, p)) if vals else 0.0

    return ThingnessThresholds(
        C_min=pct("C", percentile),
        G_min=pct("G", percentile),
        L_max=pct("L", 100 - percentile) if any(r.get("L") is not None for r in dev_records) else float("inf"),
        D_min=pct("D", percentile),
        Q_min=pct("Q", percentile),
        size_frac_range=size_frac_range,
        dwell_min=dwell_min,
        percentile=percentile,
    )


def passes_gate(record: dict, thr: ThingnessThresholds, dwell: int) -> dict:
    """record: a geometry_features()-style dict, optionally extended with
    'G' and 'L' keys from the predictive-boundary module. Missing G/L (not
    yet computed for this candidate/step) does not fail the gate on that
    criterion alone -- it is reported as `None` in checks rather than True or
    False, so callers can distinguish "not yet evaluated" from "failed"."""
    checks = dict(
        C=record.get("C", 0.0) >= thr.C_min,
        G=None if record.get("G") is None else (record["G"] >= thr.G_min),
        L=None if record.get("L") is None else (record["L"] <= thr.L_max),
        D=record.get("D", 0.0) >= thr.D_min,
        Q=record.get("Q", 0.0) >= thr.Q_min,
        one_dominant_component=record.get("n_components", 99) == 1,
        moderate_population_fraction=(thr.size_frac_range[0] <= record.get("size_frac", 0.0)
                                       <= thr.size_frac_range[1]),
        dwell=dwell >= thr.dwell_min,
    )
    hard_checks = [v for v in checks.values() if v is not None]
    return dict(passes=all(hard_checks), all_evaluated=all(v is not None for v in checks.values()),
                checks=checks)
