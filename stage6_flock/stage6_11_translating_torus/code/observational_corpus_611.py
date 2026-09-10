"""Stage 6.11 observational corpus builder (task brief item 5).

EVALUATION-SIDE (runs the real simulator to generate whole uncontrolled
episodes at the SELECTED primary regime). This is NOT simulator branching --
each episode is an independent run from its own random start, never a clone
of a live episode's mid-trajectory state (that pattern is reserved for the
labelled oracle/causal-probing diagnostic in probing_611.py). Episodes are
reduced to plain (r_hist, z_hist) numpy arrays before being handed to any
inference-side code, so no simulator object ever crosses the firewall.

Split by EPISODE (never by row) into train/validation/test, before any
predictive model exists. `report()` prints the machine-readable corpus
statistics task brief item 5 requires.
"""
from __future__ import annotations

import time

import numpy as np

from common_611 import (
    N_BIRDS, L_BOX, BETA_610, S_610, resolved_params,
    R_PRIMARY, V_PRIMARY, COHESION_PRIMARY, SOCIAL_PRIMARY,
    dump_json, DATA_DIR,
)
from moving_flock_611 import MovingFlock611

NT = 240
BURN_IN = 60
CORPUS_SEEDS = list(range(200, 260))          # disjoint from world-selection seeds (0-3, 100-119)
TRAIN_SEEDS = CORPUS_SEEDS[:36]
VAL_SEEDS = CORPUS_SEEDS[36:48]
TEST_SEEDS = CORPUS_SEEDS[48:60]


def make_primary_flock() -> MovingFlock611:
    pm = resolved_params(BETA_610, S_610)
    return MovingFlock611(N=N_BIRDS, L=L_BOX, R=R_PRIMARY, v=V_PRIMARY, params=pm,
                           social=SOCIAL_PRIMARY, cohesion=COHESION_PRIMARY)


def generate_episode(seed: int) -> dict:
    mf = make_primary_flock()
    res = mf.run(nt=NT, seed=seed)
    return dict(seed=seed, r_hist=res.r_hist[BURN_IN:], z_hist=res.z_hist[BURN_IN:])


def build_split(seeds: list[int]) -> list[dict]:
    return [generate_episode(s) for s in seeds]


def corpus_stats(split: list[dict], N: int) -> dict:
    n_episodes = len(split)
    steps_per_ep = split[0]["z_hist"].shape[0] - 1 if split else 0     # transitions, not states
    n_examples = n_episodes * steps_per_ep * N
    class_counts = np.zeros(4, dtype=int)
    for ep in split:
        z = ep["z_hist"]
        for c in range(4):
            class_counts[c] += int((z[1:] == c).sum())
    return dict(n_episodes=n_episodes, steps_per_episode=steps_per_ep,
                n_bird_level_one_step_examples=int(n_examples),
                class_counts=class_counts.tolist())


def main():
    t0 = time.time()
    print(f"[observational_corpus_611] generating train={len(TRAIN_SEEDS)} "
          f"val={len(VAL_SEEDS)} test={len(TEST_SEEDS)} episodes at PRIMARY regime "
          f"R={R_PRIMARY} v={V_PRIMARY} cohesion={COHESION_PRIMARY}, nt={NT}, burn_in={BURN_IN}")
    train = build_split(TRAIN_SEEDS)
    val = build_split(VAL_SEEDS)
    test = build_split(TEST_SEEDS)
    wall = time.time() - t0

    report = dict(
        regime=dict(R=R_PRIMARY, v=V_PRIMARY, cohesion=COHESION_PRIMARY, social=SOCIAL_PRIMARY,
                    N=N_BIRDS, L=L_BOX, beta=BETA_610, s=S_610),
        nt=NT, burn_in=BURN_IN, wall_time_s=wall,
        train=corpus_stats(train, N_BIRDS), val=corpus_stats(val, N_BIRDS), test=corpus_stats(test, N_BIRDS),
        train_seeds=TRAIN_SEEDS, val_seeds=VAL_SEEDS, test_seeds=TEST_SEEDS,
    )
    print("[observational_corpus_611] report:")
    for split_name in ("train", "val", "test"):
        s = report[split_name]
        print(f"  {split_name}: episodes={s['n_episodes']} steps/ep={s['steps_per_episode']} "
              f"bird_level_examples={s['n_bird_level_one_step_examples']} class_counts={s['class_counts']}")
    dump_json(report, DATA_DIR / "observational_corpus_611__report.json")

    # Save raw arrays split-by-split (npz, compact) -- consumed only by
    # predictive_boundary_611.py as plain (r_hist, z_hist) arrays, never as a
    # simulator object.
    for name, split in (("train", train), ("val", val), ("test", test)):
        np.savez(DATA_DIR / f"observational_corpus_611__{name}.npz",
                  seeds=np.array([e["seed"] for e in split]),
                  r_hist=np.stack([e["r_hist"] for e in split]),
                  z_hist=np.stack([e["z_hist"] for e in split]))
    print(f"[observational_corpus_611] wrote npz splits to {DATA_DIR}")


if __name__ == "__main__":
    main()
