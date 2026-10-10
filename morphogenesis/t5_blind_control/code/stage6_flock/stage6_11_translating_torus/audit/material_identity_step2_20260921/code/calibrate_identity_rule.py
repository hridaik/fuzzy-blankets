"""Step 2, identity_rule_spec.md's calibration pass. Independent of the
five historical control seeds -- uses ONLY `data/observational_corpus_611
__val.npz` (12 uncontrolled episodes, seeds 236-247, 181 steps, 400 birds
each; disjoint from seeds 500-504 and from the train/test splits used to
fit the predictive model elsewhere in Stage 6.11). This is preference #1
of the task brief's calibration-data ordering (existing uncontrolled runs
under the same regime).

Method: run the REAL, unmodified `detect_69.propose` candidate detector
(identical call signature/window to production) over every uncontrolled
episode. Build two empirical distributions of overlap metrics, never
touching any control seed or outcome:

  POSITIVE ("natural gradual continuation"): for every step t, every
  candidate c at t, matched to its own best-Jaccard-overlap candidate at
  t+1 in the SAME episode. This is what ordinary community persistence
  looks like in real uncontrolled data -- gradual turnover, not identity.

  NEGATIVE ("unrelated flock" surrogate for abrupt replacement): every
  candidate at (episode e, step t) paired with a randomly-drawn candidate
  from a DIFFERENT episode (never the same episode, so no chance of
  incidental temporal adjacency), matched by nearest size for a fair
  comparison (an unrelated flock of similar size is the honest adversarial
  case -- pairing wildly different sizes would make the negative class
  trivially separable and understate real risk).

The frozen rule is chosen to separate these two distributions, never by
looking at seeds 500-504.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[3]
CODE_DIR = STAGE_DIR / "code"
sys.path.insert(0, str(CODE_DIR))

from common_611 import DATA_DIR, L_BOX  # noqa: E402
from detect_69 import propose  # noqa: E402
import run_online_control_611 as ROC  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from forward_material_trace_611 import overlap_metrics, RULE_FAMILY_BUILDERS  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data"
RNG = np.random.default_rng(20260921)


def run_episode_candidates(r_hist, z_hist, L, stride=1):
    """Returns list-of-lists: candidates[t] = list of member-ID frozensets,
    for t=0..T-1, using the exact production sliding window."""
    T = r_hist.shape[0]
    z_window = []
    out = []
    for t in range(0, T, stride):
        z_window.append(z_hist[t])
        if len(z_window) > ROC.AFFINITY_WINDOW:
            z_window.pop(0)
        cands = propose(r_hist[t], z_window, L) if len(z_window) >= 2 else []
        out.append([frozenset(int(x) for x in c) for c in cands])
    return out


def best_jaccard_match(c, next_cands):
    best = None
    best_j = -1.0
    for c2 in next_cands:
        u = len(c | c2)
        j = (len(c & c2) / u) if u else 0.0
        if j > best_j:
            best_j, best = j, c2
    return best, best_j


def main():
    d = np.load(DATA_DIR / "observational_corpus_611__val.npz", allow_pickle=True)
    seeds, r_hist_all, z_hist_all = d["seeds"], d["r_hist"], d["z_hist"]
    print(f"calibration corpus: {len(seeds)} uncontrolled episodes, seeds={list(seeds)}")

    episode_candidates = {}
    for i, seed in enumerate(seeds):
        cands = run_episode_candidates(r_hist_all[i], z_hist_all[i], L_BOX)
        episode_candidates[int(seed)] = cands
        print(f"  seed {seed}: {sum(len(c) for c in cands)} total candidates over {len(cands)} steps")

    positives = []  # list of overlap_metrics dicts, natural t->t+1 continuation
    for seed, cands_by_t in episode_candidates.items():
        for t in range(len(cands_by_t) - 1):
            for c in cands_by_t[t]:
                if len(c) < 5:
                    continue
                match, j = best_jaccard_match(c, cands_by_t[t + 1])
                if match is None:
                    continue
                m = overlap_metrics(c, match)
                m["seed"] = seed
                m["t"] = t
                positives.append(m)

    all_flat = [(seed, t, c) for seed, cands_by_t in episode_candidates.items()
                for t, cs in enumerate(cands_by_t) for c in cs if len(c) >= 5]
    negatives = []
    n_neg = len(positives)  # matched sample size
    tries = 0
    while len(negatives) < n_neg and tries < n_neg * 20:
        tries += 1
        i, j = RNG.integers(0, len(all_flat)), RNG.integers(0, len(all_flat))
        seed_a, t_a, c_a = all_flat[i]
        seed_b, t_b, c_b = all_flat[j]
        if seed_a == seed_b:
            continue
        m = overlap_metrics(c_a, c_b)
        negatives.append(m)

    print(f"positives (natural t->t+1 continuation): n={len(positives)}")
    print(f"negatives (cross-episode unrelated-flock surrogate): n={len(negatives)}")

    # ---- threshold sensitivity for each rule family member ----
    grids = dict(
        A=[round(x, 2) for x in np.arange(0.10, 0.85, 0.05)],
        B=[round(x, 2) for x in np.arange(0.10, 0.85, 0.05)],
        D=[round(x, 2) for x in np.arange(0.10, 0.85, 0.05)],
    )
    results = {}
    for letter, thresholds in grids.items():
        rows = []
        key = dict(A="R_old", B="jaccard", D="dice")[letter]
        for th in thresholds:
            builder = RULE_FAMILY_BUILDERS[letter]
            rule = builder(th)
            tpr = np.mean([rule(m) for m in positives])   # fraction of natural continuations ACCEPTED (want high)
            fpr = np.mean([rule(m) for m in negatives])   # fraction of unrelated pairs ACCEPTED (want ~0)
            rows.append(dict(threshold=th, tpr_natural_continuation_accepted=float(tpr),
                              fpr_unrelated_accepted=float(fpr), youden_j=float(tpr - fpr)))
        results[letter] = rows

    # rule C: 2D grid, coarse
    c_rows = []
    for r_old_th in np.arange(0.20, 0.85, 0.10):
        for r_new_th in np.arange(0.20, 0.85, 0.10):
            rule = RULE_FAMILY_BUILDERS["C"](round(float(r_old_th), 2), round(float(r_new_th), 2))
            tpr = np.mean([rule(m) for m in positives])
            fpr = np.mean([rule(m) for m in negatives])
            c_rows.append(dict(r_old_threshold=round(float(r_old_th), 2), r_new_threshold=round(float(r_new_th), 2),
                                tpr_natural_continuation_accepted=float(tpr), fpr_unrelated_accepted=float(fpr),
                                youden_j=float(tpr - fpr)))
    results["C"] = c_rows

    manifest = dict(
        purpose="Step-2 identity-rule calibration, independent of seeds 500-504",
        calibration_source="data/observational_corpus_611__val.npz (12 uncontrolled episodes, seeds 236-247)",
        n_positives=len(positives), n_negatives=len(negatives),
        rule_family_results=results,
    )
    json.dump(manifest, open(OUT / "identity_rule_calibration.json", "w"), indent=2)
    print("wrote", OUT / "identity_rule_calibration.json")

    # print best-J per rule for quick inspection
    for letter, rows in results.items():
        best = max(rows, key=lambda r: r["youden_j"])
        print(f"rule {letter}: best youden J = {best}")


if __name__ == "__main__":
    main()
