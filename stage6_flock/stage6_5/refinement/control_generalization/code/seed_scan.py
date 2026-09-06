"""B1/B2: scan NEW seeds (never touched by Stage 6.5's own development or
held-out evaluation) for a discriminating-flock benchmark set, using only
frozen oracle/random baselines -- never the inferred controller. The
criterion and scan range are frozen in ../../PROTOCOL_6_5R.md /
../../configs/protocol_6_5r.yaml BEFORE this script ran.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]  # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "v3_refinement" / "code"))

from common_v2 import find_flock, dynamical_shell, evaluate_arm  # noqa: E402
from selection_rules_v3 import min_actuators_for_multicover  # noqa: E402

SCAN_START = 41
SCAN_END_INCLUSIVE = 140
TARGET_MIN, TARGET_MAX = 8, 12
P_ORACLE_MIN = 0.7
P_RANDOM_MAX = 0.3
SCREENING_N_REP = 20
SCREENING_SEED_OFFSET = 8_100_000
FROZEN_Q, FROZEN_GAMMA = 2, 0.5


def is_discriminating(p_oracle: float, p_random: float, p_oracle_min: float = P_ORACLE_MIN,
                       p_random_max: float = P_RANDOM_MAX) -> bool:
    return (p_oracle >= p_oracle_min) and (p_random <= p_random_max)


def screen_one_seed(seed: int, rng: np.random.Generator) -> dict | None:
    fl = find_flock(seed)
    if fl is None:
        return None
    I0, lattice, z_t0, h_star = fl["I0"], fl["lattice"], fl["z_t0"], fl["h_star"]
    nn = lattice.nn
    B_D = dynamical_shell(lattice, I0)
    if len(B_D) == 0:
        return dict(seed=seed, qualifies_find_flock=True, has_shell=False)

    A_oracle = min_actuators_for_multicover(B_D, I0, lattice, q=FROZEN_Q, gamma=FROZEN_GAMMA)
    m_oracle = evaluate_arm(A_oracle, z_t0, I0, h_star, lattice, n_replicates=SCREENING_N_REP,
                             seed_offset=SCREENING_SEED_OFFSET + 1000 * seed)

    budget = max(len(A_oracle), 1)
    exterior = [j for j in range(nn) if j not in set(I0.tolist())]
    A_random = sorted(rng.choice(exterior, size=min(budget, len(exterior)), replace=False).tolist())
    m_random = evaluate_arm(A_random, z_t0, I0, h_star, lattice, n_replicates=SCREENING_N_REP,
                             seed_offset=SCREENING_SEED_OFFSET + 1000 * seed + 500)

    discriminating = is_discriminating(m_oracle["p_success"], m_random["p_success"])
    return dict(
        seed=seed, qualifies_find_flock=True, has_shell=True,
        n_I0=len(I0), n_B_D=len(B_D), n_actuators_oracle=len(A_oracle),
        p_success_oracle=m_oracle["p_success"], p_success_random=m_random["p_success"],
        discriminating=bool(discriminating),
    )


def scan() -> dict:
    all_candidates = []
    discriminating = []
    seed = SCAN_START
    while seed <= SCAN_END_INCLUSIVE and len(discriminating) < TARGET_MAX:
        rng = np.random.default_rng(SCREENING_SEED_OFFSET + seed)
        row = screen_one_seed(seed, rng)
        if row is not None:
            all_candidates.append(row)
            tag = ("DISCRIMINATING" if row.get("discriminating") else
                   "no-shell" if not row.get("has_shell", True) else "not discriminating")
            extra = (f"p_oracle={row.get('p_success_oracle', float('nan')):.2f} "
                     f"p_random={row.get('p_success_random', float('nan')):.2f}" if row.get("has_shell") else "")
            print(f"seed={seed}: {tag} {extra}")
            if row.get("discriminating"):
                discriminating.append(row["seed"])
        seed += 1

    return dict(
        scan_start=SCAN_START, scan_end_inclusive=seed - 1, scan_end_configured=SCAN_END_INCLUSIVE,
        target_min=TARGET_MIN, target_max=TARGET_MAX,
        p_oracle_success_min=P_ORACLE_MIN, p_random_success_max=P_RANDOM_MAX,
        screening_n_replicates=SCREENING_N_REP,
        all_candidates=all_candidates, discriminating_seeds=discriminating,
        n_discriminating=len(discriminating),
        n_qualifying_flocks_scanned=sum(1 for r in all_candidates if r.get("has_shell")),
        n_seeds_scanned=len(all_candidates),
    )
