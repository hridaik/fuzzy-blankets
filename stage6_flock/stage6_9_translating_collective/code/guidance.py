"""Guidance / control of a translating collective (task brief §§35-37).

EVALUATION-SIDE driver composing blind modules with the simulator.

The collective travels at speed `v` in its members' modal heading, so steering
it along a path means turning it. At each step the controller:

    1. re-detects / continues the current collective (blind);
    2. estimates its moving frame (blind);
    3. re-infers the causal interface and influence matrix (black-box probing);
    4. picks boundary actuators by causal weighted multicover;
    5. forces those birds toward the cardinal heading that best reduces the
       distance to the target path; observes; repeats.

**The target path never enters the detector or the identity tracker** -- it is
used only in step 5, to choose which heading to command.

Success is CONJUNCTIVE (§36):
    S_full = S_path AND S_functional_identity AND S_nondegenerate AND S_boundary
Material retention is reported but is NOT required to stay high.

The four failure modes of §37 are detected explicitly rather than left to be
noticed: destruction+replacement, splitting (lineage branch events),
shrink-to-win, and material-only persistence.
"""
from __future__ import annotations

import numpy as np

from common_69 import UV4
from intervention_api_69 import FiniteProbeMoving, ExactPropagatorMoving, near_exterior
import detect_69 as det

K_ACT = 24
REINFER_EVERY = 3
PROBE_ROLLOUTS = 25
PROBE_REPEATS = 2
THETA = 0.02
Q_SUPPORT = 0.9
LOOKAHEAD = 6            # steps ahead on the path the controller aims at

# conjunctive success thresholds, frozen before the experiment ran
S_PATH_MAX_MEAN_ERR_RADII = 3.0
S_FUNC_MIN_MEAN_RF = 0.70
S_NONDEG_SIZE_FRAC = (0.03, 0.55)
S_BOUNDARY_MIN_FRAC_STEPS = 0.80


def l_shaped_path(c0, L, leg1=(1.0, 0.0), leg2=(0.0, 1.0), n1=30, n2=30, speed=0.5):
    """An L-shaped route in world coordinates, starting at the collective's own
    initial centroid. Never shown to the detector or the identity tracker."""
    pts = [np.asarray(c0, dtype=float)]
    for d, n in ((np.asarray(leg1, float), n1), (np.asarray(leg2, float), n2)):
        d = d / np.linalg.norm(d)
        for _ in range(n):
            pts.append((pts[-1] + speed * d) % L)
    return np.array(pts)


def _multicover(influence, I, k_act, theta=THETA, q_support=Q_SUPPORT):
    I = [int(i) for i in I if any(influence[j].get(int(i), 0.0) > 0 for j in influence)]
    if not I:
        return []
    s = {i: 0.0 for i in I}
    A, avail = [], sorted(influence)
    need = int(np.ceil(q_support * len(I)))
    while avail and len(A) < k_act:
        if sum(1 for i in I if s[i] >= theta) >= need:
            break
        best, gain = None, 0.0
        for j in avail:
            g = sum(min(theta, s[i] + influence[j].get(i, 0.0)) - s[i] for i in I if s[i] < theta)
            if g > gain:
                best, gain = j, g
        if best is None:
            break
        A.append(int(best)); avail.remove(best)
        for i in I:
            s[i] += influence[best].get(i, 0.0)
    return sorted(A)


def desired_heading(centre, target, L):
    d = (np.asarray(target) - np.asarray(centre) + L / 2) % L - L / 2
    return int(np.argmax(UV4 @ d))


def run_arm(mf, r0, z0, arm: str, seed: int, path: np.ndarray, t_control: int,
            k_act: int = K_ACT, budget_schedule=None) -> dict:
    rng = np.random.default_rng(50_000 + seed)
    r, z = r0.copy(), z0.copy()
    hist_z, hist_r = [z.copy()], [r.copy()]
    # warm the detector on the pre-control window
    warm_z = [z.copy() for _ in range(det.W_AFFINITY)]

    tracker, recs, acts = None, [], []
    lineage_breaks, influence = 0, {}
    probe_budget = dict(n_probe_calls=0, n_rollouts=0)
    last_A = []
    for step in range(t_control):
        zw = np.array((warm_z + hist_z)[-det.W_AFFINITY:])
        cands = det.propose(r, zw, mf.L)
        if not cands:
            break
        if tracker is None:
            tracker = det.TranslatingTracker(mf.L)
            tracker.start(cands[0], r, z, step)
        elif not tracker.update(cands, r, z, step):
            lineage_breaks += 1
            tracker = det.TranslatingTracker(mf.L)
            tracker.start(max(cands, key=len), r, z, step)
        I = tracker.state.members
        centre = tracker.state.centre
        tgt = path[min(step + LOOKAHEAD, len(path) - 1)]
        h_cmd = desired_heading(centre, tgt, mf.L)
        cands_ext = near_exterior(mf, r, I)
        budget = k_act if budget_schedule is None else int(
            budget_schedule[min(step, len(budget_schedule) - 1)])

        if arm == "no_control":
            A = []
        elif arm == "random_matched":
            A = sorted(rng.choice(cands_ext, size=min(budget, len(cands_ext)),
                                  replace=False).tolist()) if cands_ext else []
        elif arm == "interior_forcing":
            # deliberately identity-DESTROYING comparator: force interior members
            # directly instead of the boundary
            A = sorted(rng.choice(I, size=min(budget, len(I)), replace=False).tolist())
        elif arm in ("adaptive_causal", "adaptive_oracle"):
            if step % REINFER_EVERY == 0 and cands_ext:
                if arm == "adaptive_oracle":
                    ep = ExactPropagatorMoving(mf, r)
                    influence = {}
                    for j in cands_ext:
                        acc = {int(i): 0.0 for i in I}
                        others = [h for h in range(4) if h != int(z[int(j)])]
                        for zp in others:
                            for i, v in ep.exact(I, int(j), zp, z)["per_bird_kl"].items():
                                acc[int(i)] += v / len(others)
                        influence[int(j)] = acc
                else:
                    import probing
                    probe = FiniteProbeMoving(mf, r, n_rollouts=PROBE_ROLLOUTS, seed=seed + step)
                    res = probing.probe_sources(probe, I, cands_ext, [z] * PROBE_REPEATS,
                                                rng=np.random.default_rng(seed + step))
                    influence = probing.influence_matrix(res, I)
                    b = probe.budget()
                    probe_budget["n_probe_calls"] += b["n_probe_calls"]
                    probe_budget["n_rollouts"] += b["n_rollouts"]
                last_A = _multicover(influence, I, budget)
            A = last_A
        else:
            raise ValueError(arm)

        r, z, _ = mf.step(r, z, rng, forced_actions={int(j): h_cmd for j in A})
        hist_r.append(r.copy()); hist_z.append(z.copy())
        acts.append(len(A))
        rec = dict(tracker.records[-1])
        err = np.linalg.norm((centre - path[min(step, len(path) - 1)] + mf.L / 2)
                             % mf.L - mf.L / 2)
        rec.update(step=step, n_actuators=len(A), path_error=float(err),
                   path_error_radii=float(err / mf.R), h_cmd=h_cmd,
                   n_boundary=len(A))
        recs.append(rec)

    return summarize(mf, arm, seed, recs, acts, tracker, lineage_breaks, probe_budget,
                     np.array(hist_r), np.array(hist_z), path)


def summarize(mf, arm, seed, recs, acts, tracker, lineage_breaks, probe_budget,
              hist_r, hist_z, path) -> dict:
    if not recs:
        return dict(arm=arm, seed=seed, ok=False)
    rf = [r["R_F"] for r in recs if "R_F" in r]
    sizes = [r["size"] for r in recs]
    lo, hi = S_NONDEG_SIZE_FRAC[0] * mf.N, S_NONDEG_SIZE_FRAC[1] * mf.N
    S_path = float(np.mean([r["path_error_radii"] for r in recs])) <= S_PATH_MAX_MEAN_ERR_RADII
    S_func = (float(np.mean(rf)) if rf else 0.0) >= S_FUNC_MIN_MEAN_RF
    S_nondeg = float(np.mean([lo <= s <= hi for s in sizes])) >= 0.9
    S_bound = float(np.mean([r["n_boundary"] > 0 for r in recs])) >= S_BOUNDARY_MIN_FRAC_STEPS \
        if arm not in ("no_control",) else False
    return dict(
        arm=arm, seed=seed, ok=True, n_steps=len(recs),
        mean_path_error_radii=float(np.mean([r["path_error_radii"] for r in recs])),
        final_path_error_radii=float(recs[-1]["path_error_radii"]),
        mean_R_F=float(np.mean(rf)) if rf else float("nan"),
        min_R_F=float(np.min(rf)) if rf else float("nan"),
        final_R_M=float(recs[-1]["R_M"]), min_R_M=float(min(r["R_M"] for r in recs)),
        mean_D_deform=float(np.mean([r["D_deform"] for r in recs if "D_deform" in r])),
        mean_size=float(np.mean(sizes)), min_size=int(min(sizes)), max_size=int(max(sizes)),
        mean_actuators=float(np.mean(acts)) if acts else 0.0,
        actuator_schedule=acts,
        S_path=bool(S_path), S_functional_identity=bool(S_func),
        S_nondegenerate=bool(S_nondeg), S_boundary=bool(S_bound),
        S_full=bool(S_path and S_func and S_nondeg and S_bound),
        # explicit failure-mode detection (task brief 37)
        failure_destruction_and_replacement=bool(lineage_breaks > 0),
        n_lineage_breaks=int(lineage_breaks),
        failure_splitting=bool(tracker is not None and len(tracker.branch_events) > 0),
        n_branch_events=int(len(tracker.branch_events)) if tracker is not None else 0,
        failure_shrink_to_win=bool(min(sizes) < lo),
        failure_material_only_persistence=bool(
            recs[-1]["R_M"] > 0.9 and (np.mean(rf) if rf else 1.0) < S_FUNC_MIN_MEAN_RF),
        probe_budget=probe_budget,
        records=recs,
    )
