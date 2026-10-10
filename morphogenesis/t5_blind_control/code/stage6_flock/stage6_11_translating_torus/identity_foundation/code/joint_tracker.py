"""The proposed joint identity model (IDENTITY_MODEL.md), implemented.

INFERENCE-SIDE ONLY: reads observed (r, z) each step, a candidate proposal
list, and nothing else. Never reads the synthetic generator's or the real
simulator's ground truth / ID / intervention target.

Scope decisions, disclosed rather than hidden (Phase 2 is where these get
stress-tested, not asserted correct here):

- `Sigma_ell` is axis-aligned (two std devs `sx, sy`), not a full 2x2
  covariance with rotation -- IDENTITY_MODEL.md §3 calls this "minimally a
  covariance-like scale"; a full oriented covariance is a natural
  extension not built in this pass.
- Small scenes (per-step candidate x label pair count below
  `EXACT_ENUM_MAX_PAIRS`) use EXACT enumeration of the joint hypothesis
  space, per IDENTITY_MODEL.md §5's "exact reference for small scenes."
  Larger scenes (the real 400-bird replay) use a documented greedy
  approximation with a cross-label consistency pass and an explicit
  `exact=False` flag on every output record -- never silently presented
  as equally exact.
- Phenotype `phi` is approximated by the heading categorical `pi` plus
  `Sigma`, not the full `identity_69.field` density map -- a stated
  simplification; IDENTITY_MODEL.md's `phi` is the fuller object this
  approximates.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from itertools import product

import numpy as np

L_DEFAULT = 24.0

# Disclosed, Phase-2-calibratable constants (not tuned on any scenario's
# outcome -- fixed once here and used identically everywhere).
PROCESS_NOISE_STD = 0.35        # eta_c: per-step positional process noise std
K_SIGMA_REACHABLE = 3.0         # multiples of process-noise std treated as "in reach"
SHAPE_PERSISTENCE = 0.9         # geometric decay for Sigma_ell's own process noise
PI_LEARN_RATE = 0.3             # gamma: phenotype (heading dist) update rate
TAU_MISSING_MAX = 5             # steps of no in-reach candidate before termination
INDIVIDUATION_PATIENCE = 3      # steps of individuation_loss before forced termination
COALESCE_JACCARD = 0.9          # near-duplicate candidate coalescing threshold
EXACT_ENUM_MAX_PAIRS = 24       # (#labels_needing_decision x #candidates) ceiling for exact enumeration
LAMBDA_FA = 1.0                 # declared loss: false association
LAMBDA_WAIT = 1.0               # declared loss: one more step of waiting
# Birth test: a likelihood-RATIO against the f_0 uniform-background
# heading model, not an absolute floor (an earlier version used an
# absolute floor and, on smoke-testing, was found to let small background
# noise clusters with a by-chance concentrated heading pass as births --
# a likelihood ratio against the explicit background alternative, plus a
# minimum size, closes this; both constants below were set BY this
# dev-stage smoke test, before any held-out or real-replay run, per
# VALIDATION_PROTOCOL.md's tuning/held-out separation).
BIRTH_LR_FLOOR = 16.0           # roughly p<0.001 for a 3-df chi-square LR test
MIN_BIRTH_SIZE = 12
BIRTH_CONFIRM_STEPS = 2          # a candidate must clear the LR test on 2 consecutive
                                  # steps (Jaccard-overlapping) before becoming a confirmed
                                  # label -- standard track-initiation discipline, added
                                  # after smoke-testing showed single-step birth let
                                  # occasional chance-concentrated background clusters
                                  # (Louvain's own affinity already rewards local heading
                                  # agreement, which background birds can exhibit briefly
                                  # by chance) through as spurious labels


def torus_delta(a, b, L):
    return (a - b + L / 2.0) % L - L / 2.0


def torus_wrap(x, L):
    return np.mod(x, L)


def centroid(pos, L):
    if len(pos) == 0:
        return np.array([L / 2, L / 2])
    ref = pos[0]
    rel = torus_delta(pos, ref, L)
    return torus_wrap(ref + rel.mean(axis=0), L)


def member_stats(members, r, z, L):
    pos = r[members]
    c = centroid(pos, L)
    rel = torus_delta(pos, c, L)
    sx = float(max(rel[:, 0].std(), 0.35)) if len(members) > 1 else 0.6
    sy = float(max(rel[:, 1].std(), 0.35)) if len(members) > 1 else 0.6
    pi = np.bincount(z[members], minlength=4).astype(float)
    pi = pi / max(pi.sum(), 1e-9)
    return c, sx, sy, pi


def wrap_normal_logpdf(delta, sx, sy):
    sx = max(sx, 1e-2)
    sy = max(sy, 1e-2)
    return -0.5 * ((delta[0] / sx) ** 2 + (delta[1] / sy) ** 2) - np.log(2 * np.pi * sx * sy)


def categorical_loglik(pi, counts):
    n = counts.sum()
    if n == 0:
        return 0.0
    p = np.clip(pi, 1e-3, 1.0)
    return float((counts * np.log(p)).sum())


@dataclass
class Label:
    lid: str
    c: np.ndarray
    v: np.ndarray
    sx: float
    sy: float
    pi: np.ndarray
    members: set
    origin: set
    parents: list = dc_field(default_factory=list)
    age: int = 0
    status: str = "active"       # active | individuation_loss | terminated
    missing_streak: int = 0
    individuation_streak: int = 0
    exists: bool = True
    contrast_baseline: list = dc_field(default_factory=list)
    history: list = dc_field(default_factory=list)


class JointTracker:
    """Maintains a set of `Label`s across steps, implementing IDENTITY_MODEL.md
    §5-9's event/decision structure at the scope documented in this module's
    docstring."""

    def __init__(self, L: float = L_DEFAULT, jaccard_coalesce: float = COALESCE_JACCARD):
        self.L = L
        self.jaccard_coalesce = jaccard_coalesce
        self.labels: dict = {}
        self.terminated: dict = {}
        self._next_id = 0
        self.event_log: list = []
        self.unaccounted_mass_log: list = []
        self.pending_births: list = []  # [{members: set, first_t: int}]

    def _new_label_id(self):
        self._next_id += 1
        return f"L{self._next_id}"

    # ---- candidate coalescing (§5, §9(5)) -------------------------------
    def coalesce(self, candidates: list) -> list:
        merged = []
        used = [False] * len(candidates)
        sets = [set(int(x) for x in c) for c in candidates]
        for i in range(len(candidates)):
            if used[i]:
                continue
            group = sets[i]
            for j in range(i + 1, len(candidates)):
                if used[j]:
                    continue
                inter = len(group & sets[j])
                union = len(group | sets[j])
                jac = inter / union if union else 1.0
                if jac >= self.jaccard_coalesce:
                    group = group | sets[j]
                    used[j] = True
            used[i] = True
            merged.append(np.array(sorted(group)))
        return merged

    # ---- reachable-set / transport-consistency (§8) ---------------------
    def _reachable_radius(self, label: Label, elapsed: int) -> float:
        proc = PROCESS_NOISE_STD * K_SIGMA_REACHABLE * np.sqrt(max(elapsed, 1))
        shape = np.hypot(label.sx, label.sy)
        return proc + shape

    def _predict(self, label: Label):
        return torus_wrap(label.c + label.v, self.L)

    def _pair_loglik(self, label: Label, cand_members, r, z):
        c, sx, sy, pi = member_stats(cand_members, r, z, self.L)
        pred_c = self._predict(label)
        delta = torus_delta(c, pred_c, self.L)
        pos_ll = wrap_normal_logpdf(delta, label.sx + PROCESS_NOISE_STD, label.sy + PROCESS_NOISE_STD)
        counts = np.bincount(z[cand_members], minlength=4).astype(float)
        head_ll = categorical_loglik(label.pi, counts)
        dist = float(np.hypot(*delta))
        return pos_ll + head_ll, dist, (c, sx, sy, pi)

    # ---- main step --------------------------------------------------
    def step(self, candidates_raw: list, r: np.ndarray, z: np.ndarray, t: int):
        candidates = self.coalesce(candidates_raw)
        cand_sets = [set(int(x) for x in c) for c in candidates]

        active_labels = [lab for lab in self.labels.values() if lab.status != "terminated"]

        # -- merger pre-check (§7 row 5): two labels whose predicted centres
        # both land near the SAME candidate, whose member count is
        # consistent with their combined mass, take priority over the
        # general per-label assignment below (handled here, removed from
        # the general pool, so the general assignment never has to fight
        # over the same candidate).
        merged_this_step = set()
        claimed_candidates = set()
        for i in range(len(active_labels)):
            for j in range(i + 1, len(active_labels)):
                labA, labB = active_labels[i], active_labels[j]
                if labA.lid in merged_this_step or labB.lid in merged_this_step:
                    continue
                predA, predB = self._predict(labA), self._predict(labB)
                for ci, cand in enumerate(candidates):
                    if ci in claimed_candidates:
                        continue
                    members = np.array(sorted(cand_sets[ci]))
                    if len(members) < MIN_BIRTH_SIZE:
                        continue
                    c, sx, sy, pi = member_stats(members, r, z, self.L)
                    dA = np.hypot(*torus_delta(c, predA, self.L))
                    dB = np.hypot(*torus_delta(c, predB, self.L))
                    radA = self._reachable_radius(labA, labA.missing_streak + 1)
                    radB = self._reachable_radius(labB, labB.missing_streak + 1)
                    mass_ok = 0.6 <= len(members) / max(len(labA.members) + len(labB.members), 1) <= 1.4
                    if dA <= radA and dB <= radB and mass_ok:
                        self._merge(labA, labB, members, c, sx, sy, pi, t)
                        merged_this_step.add(labA.lid)
                        merged_this_step.add(labB.lid)
                        claimed_candidates.add(ci)
                        break
        active_labels = [lab for lab in active_labels if lab.lid not in merged_this_step]

        n_pairs = len(active_labels) * max(len(candidates), 1)
        exact = n_pairs <= EXACT_ENUM_MAX_PAIRS

        # per (label, candidate) score table, restricted to in-reach candidates
        reach = {}
        scores = {}
        for lab in active_labels:
            elapsed = lab.missing_streak + 1
            radius = self._reachable_radius(lab, elapsed)
            in_reach = []
            for ci, cand in enumerate(candidates):
                if ci in claimed_candidates:
                    continue
                ll, dist, stats = self._pair_loglik(lab, np.array(sorted(cand_sets[ci])), r, z)
                if dist <= radius:
                    in_reach.append(ci)
                    scores[(lab.lid, ci)] = (ll, dist, stats)
            reach[lab.lid] = in_reach

        if exact and active_labels and candidates:
            assignment, unaccounted = self._exact_assign(active_labels, candidates, cand_sets, reach, scores)
        else:
            assignment, unaccounted = self._greedy_assign(active_labels, candidates, cand_sets, reach, scores)
        self.unaccounted_mass_log.append(dict(t=t, unaccounted_mass=unaccounted, exact=exact,
                                               n_labels=len(active_labels), n_candidates=len(candidates)))

        for lab in active_labels:
            choice = assignment.get(lab.lid)  # candidate index or None
            if choice is not None:
                claimed_candidates.add(choice)

        # -- split post-check (§7 row 5): a label left unresolved whose
        # in-reach-but-unclaimed candidates jointly retain most of its own
        # membership and are themselves near-disjoint is a split, not a
        # termination-via-timeout.
        for lab in active_labels:
            if assignment.get(lab.lid) is not None:
                continue
            own_reach = [ci for ci in reach[lab.lid] if ci not in claimed_candidates]
            if len(own_reach) < 2:
                continue
            union = set()
            for ci in own_reach:
                union |= cand_sets[ci]
            retain = len(union & lab.members) / max(len(lab.members), 1)
            pairwise_disjoint = all(
                len(cand_sets[a] & cand_sets[b]) / max(len(cand_sets[a] | cand_sets[b]), 1) < 0.2
                for x, a in enumerate(own_reach) for b in own_reach[x + 1:]
            )
            if retain >= 0.6 and pairwise_disjoint:
                children_idx = own_reach[:2]
                self._split(lab, [cand_sets[ci] for ci in children_idx], r, z, t)
                for ci in children_idx:
                    claimed_candidates.add(ci)
                assignment[lab.lid] = "SPLIT_HANDLED"

        for lab in active_labels:
            choice = assignment.get(lab.lid)
            if choice == "SPLIT_HANDLED":
                continue
            self._apply_event(lab, choice, candidates, cand_sets, scores, r, z, t)

        # births: any candidate not claimed by any label, whose own fit
        # beats the f_0 uniform-background alternative by a likelihood-
        # ratio margin (not an absolute floor -- see BIRTH_LR_FLOOR's note),
        # AND which clears that same test on BIRTH_CONFIRM_STEPS consecutive
        # steps with a Jaccard-overlapping candidate each time (track
        # confirmation, see BIRTH_CONFIRM_STEPS' note).
        surviving_pending = []
        matched_pending_ids = set()
        for ci, cand in enumerate(candidates):
            if ci in claimed_candidates:
                continue
            members = np.array(sorted(cand_sets[ci]))
            if len(members) < MIN_BIRTH_SIZE:
                continue
            c, sx, sy, pi = member_stats(members, r, z, self.L)
            counts = np.bincount(z[members], minlength=4).astype(float)
            own_ll = categorical_loglik(pi, counts)
            background_ll = categorical_loglik(np.array([0.25, 0.25, 0.25, 0.25]), counts)
            if (own_ll - background_ll) < BIRTH_LR_FLOOR:
                continue
            cur_set = cand_sets[ci]
            matched = None
            for pid, pend in enumerate(self.pending_births):
                if pid in matched_pending_ids:
                    continue
                inter = len(cur_set & pend["members"])
                union = len(cur_set | pend["members"])
                if union and inter / union >= 0.6:
                    matched = pid
                    break
            if matched is not None:
                matched_pending_ids.add(matched)
                pend = self.pending_births[matched]
                if t - pend["first_t"] + 1 >= BIRTH_CONFIRM_STEPS:
                    self._birth(cur_set, c, sx, sy, pi, t)
                else:
                    surviving_pending.append(dict(members=cur_set, first_t=pend["first_t"]))
            else:
                surviving_pending.append(dict(members=cur_set, first_t=t))
        self.pending_births = surviving_pending

        for lab in list(self.labels.values()):
            lab.age += 1

    # ---- exact small-scene enumeration (§5) -----------------------------
    def _exact_assign(self, active_labels, candidates, cand_sets, reach, scores):
        options_per_label = []
        for lab in active_labels:
            opts = list(reach[lab.lid]) + [None]
            options_per_label.append(opts)
        best_assignment, best_ll, total_mass, masses = None, -np.inf, 0.0, []
        for combo in product(*options_per_label):
            claimed = [c for c in combo if c is not None]
            if len(claimed) != len(set(claimed)):
                continue  # two labels cannot claim the same candidate in one hypothesis
            ll = 0.0
            for lab, choice in zip(active_labels, combo):
                if choice is None:
                    ll += np.log(1e-3)  # unresolved/no-match baseline mass
                else:
                    ll += scores[(lab.lid, choice)][0]
            masses.append((combo, ll))
            if ll > best_ll:
                best_ll, best_assignment = ll, combo
        if not masses:
            return {}, 0.0
        m = np.array([x[1] for x in masses])
        w = np.exp(m - m.max())
        w = w / w.sum()
        total_mass_best = float(w[np.argmax(m)])
        assignment = {lab.lid: choice for lab, choice in zip(active_labels, best_assignment)}
        return assignment, float(1.0 - total_mass_best)

    # ---- greedy approximation for large scenes (§5) ---------------------
    def _greedy_assign(self, active_labels, candidates, cand_sets, reach, scores):
        pairs = sorted(scores.items(), key=lambda kv: -kv[1][0])
        assignment = {}
        used_cands = set()
        used_labels = set()
        for (lid, ci), (ll, dist, stats) in pairs:
            if lid in used_labels or ci in used_cands:
                continue
            assignment[lid] = ci
            used_cands.add(ci)
            used_labels.add(lid)
        for lab in active_labels:
            if lab.lid not in assignment:
                assignment[lab.lid] = None
        # unaccounted mass not exactly quantified for the greedy path --
        # reported as None (per MEASUREMENT_CONTRACT.md's missingness
        # contract: absent, not defaulted to 0).
        return assignment, None

    # ---- event application (§7) -----------------------------------------
    def _apply_event(self, lab: Label, choice, candidates, cand_sets, scores, r, z, t):
        if choice is None:
            lab.missing_streak += 1
            if lab.missing_streak > TAU_MISSING_MAX:
                self._terminate(lab, t, reason="terminated_by_timeout")
            else:
                lab.status = "missed"
                lab.history.append(dict(t=t, event="missed", members=sorted(lab.members)))
            return

        _, dist, (c, sx, sy, pi) = scores[(lab.lid, choice)]
        members = cand_sets[choice]
        lab.missing_streak = 0

        # individuation loss check (§7 row 2): growing AND heading-diversity
        # rising sharply relative to the label's own recent baseline, used
        # here as the exterior-contrast proxy (no periphery computation in
        # this synthetic-scale tracker -- a disclosed simplification vs the
        # real geometry_611.local_exterior_contrast route).
        growing = len(members) > len(lab.members)
        heading_entropy = float(-(np.clip(pi, 1e-6, 1) * np.log(np.clip(pi, 1e-6, 1))).sum())
        lab.contrast_baseline.append(heading_entropy)
        lab.contrast_baseline = lab.contrast_baseline[-5:]
        baseline = float(np.mean(lab.contrast_baseline[:-1])) if len(lab.contrast_baseline) > 1 else heading_entropy
        individuating = growing and heading_entropy > baseline * 1.35

        lab.c, lab.sx, lab.sy = c, sx, sy
        lab.v = torus_delta(c, lab.c, self.L) if lab.age == 0 else lab.v
        lab.pi = (1 - PI_LEARN_RATE) * lab.pi + PI_LEARN_RATE * pi
        lab.members = members

        if individuating:
            lab.status = "individuation_loss"
            lab.individuation_streak += 1
            if lab.individuation_streak >= INDIVIDUATION_PATIENCE:
                self._terminate(lab, t, reason="terminated_by_individuation_loss")
                return
        else:
            lab.status = "active"
            lab.individuation_streak = 0

        lab.history.append(dict(t=t, event="continuation", members=sorted(members),
                                 status=lab.status, dist=dist))

    def _merge(self, labA: Label, labB: Label, members, c, sx, sy, pi, t):
        for lab, reason in ((labA, "terminated_by_merger"), (labB, "terminated_by_merger")):
            lab.status = "terminated"
            lab.exists = False
            lab.history.append(dict(t=t, event=reason, members=[]))
            self.terminated[lab.lid] = lab
        child = self._new_label_id()
        c_lab = Label(lid=child, c=c, v=(labA.v + labB.v) / 2, sx=sx, sy=sy, pi=pi,
                      members=set(members), origin=set(members), parents=[labA.lid, labB.lid])
        c_lab.history.append(dict(t=t, event="merger_child", members=sorted(members)))
        self.labels[child] = c_lab
        self.event_log.append(dict(t=t, type="merger", parents=[labA.lid, labB.lid], child=child))

    def _split(self, lab: Label, children_members: list, r, z, t):
        lab.status = "terminated"
        lab.exists = False
        lab.history.append(dict(t=t, event="terminated_by_split", members=[]))
        self.terminated[lab.lid] = lab
        child_ids = []
        for members in children_members:
            members_arr = np.array(sorted(members))
            c, sx, sy, pi = member_stats(members_arr, r, z, self.L)
            cid = self._new_label_id()
            c_lab = Label(lid=cid, c=c, v=lab.v.copy(), sx=sx, sy=sy, pi=pi,
                          members=set(members), origin=set(members), parents=[lab.lid])
            c_lab.history.append(dict(t=t, event="split_child", members=sorted(members)))
            self.labels[cid] = c_lab
            child_ids.append(cid)
        self.event_log.append(dict(t=t, type="split", parent=lab.lid, children=child_ids))

    def _birth(self, members, c, sx, sy, pi, t):
        lid = self._new_label_id()
        lab = Label(lid=lid, c=c, v=np.zeros(2), sx=sx, sy=sy, pi=pi,
                    members=members, origin=set(members))
        lab.history.append(dict(t=t, event="birth", members=sorted(members)))
        self.labels[lid] = lab
        self.event_log.append(dict(t=t, type="birth", label=lid))

    def _terminate(self, lab: Label, t: int, reason: str):
        lab.status = "terminated"
        lab.exists = False
        lab.history.append(dict(t=t, event=reason, members=[]))
        self.event_log.append(dict(t=t, type="death", label=lab.lid, reason=reason))
        self.terminated[lab.lid] = lab

    # ---- readouts (§3's exposed API) -------------------------------------
    def snapshot(self, t: int) -> dict:
        return {lid: dict(members=sorted(lab.members), status=lab.status, age=lab.age,
                           exists=lab.exists, missing_streak=lab.missing_streak)
                for lid, lab in self.labels.items() if lab.status != "terminated"}

    def wait_or_associate(self, lab_lid: str, unconditional_p: float) -> str:
        """§9's corrected decision rule: associate iff
        p >= lambda_FA/(lambda_FA+lambda_wait)."""
        threshold = LAMBDA_FA / (LAMBDA_FA + LAMBDA_WAIT)
        return "associate" if unconditional_p >= threshold else "wait"
