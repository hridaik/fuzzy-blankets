"""Stage 6.11B item 1: lineage_v2 -- a present-state-coalesced lineage tracker,
as a COMPARATOR to lineage_611.LineageTracker611 (which is never modified).

Design, addressing LINEAGE_FORENSICS_6_11.md's two confirmed defects:

1. "Duplicate hypotheses" (same current member set, different branch-history
   id) are coalesced BEFORE normalization every step, so probability mass is
   never split across identical present states. Genealogy (which branch(es)
   fed into this present state) is kept as metadata on the Lineage object,
   never as a distinct competing hypothesis.
2. "No death alternative": every lineage's transition always competes an
   explicit `dead` outcome against its viable candidates. The prior mass NOT
   absorbed by a live continuation is prior*(1 - p_continue), tracked as a
   genuine `dead` bucket per lineage (reported, not silently discarded),
   rather than being forced entirely onto whichever candidate happened to
   clear a material-retention floor.

p_continue is a single scalar-in/scalar-out calibration,
`p_continue = sigmoid(a * score + b)`, fit ONCE from uncontrolled development
data (calibrate_lineage_v2_611.py) against a labelled good/bad-continuation
set, and used unchanged everywhere -- never tuned on control outcome. It is
reported as a "calibrated continuation confidence," and its reliability
(Brier score, binned calibration curve on a held-out slice) is checked in
`LINEAGE_V2_METHOD_AND_VALIDATION.md`; it is NOT called a Bayesian posterior.

Continuation evidence per candidate transition A -> B:
    R_retain, R_purity   (material overlap, existing lineage_611 formulas)
    dice                 (existing lineage_611 formula, used only as an
                           internal matching heuristic, per lineage_611's own
                           discipline)
    d_transport          (raw post-alignment field distance, identity_69)
    R_F                  (= 1 - d_transport/d_norm, identity_69.similarity)
    size_ratio           |B|/|A|
    Q                     compactness (geometry_611.compactness)
    f_main                largest-connected-component fraction of |B|
                          (torus-aware; NEW -- lineage_611/geometry_611 expose
                          component COUNT but not component SIZES, so this
                          module adds `component_sizes`, reusing the same
                          torus-distance/union-find primitives)

VIABILITY (replaces lineage_611's single R_retain>=0.30 gate): a candidate is
eligible to compete for a lineage's mass iff EITHER material retention is
non-trivial (R_retain >= RETENTION_MIN_SOFT) OR transport consistency is
good (R_F >= R_F_MIN_TRANSPORT, i.e. the field, after best-fit bulk
alignment, is closer to the parent than two unrelated same-size groups would
be) -- so a zero-material-overlap candidate remains eligible if the
co-moving organization propagates continuously (transport-consistent), while
a materially-disjoint AND transport-inconsistent candidate (an unrelated
spatial jump) is never eligible at all, regardless of size or any other
coincidence.

Unmatched candidates (viable for no live lineage) may start new lineages,
exactly as detect_69/lineage_611 already do for a from-scratch start, but
here for EVERY step, not only after total tracker death.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field as dc_field
from pathlib import Path

import numpy as np

from identity_69 import centroid, field as comoving_field, field_distance, estimate_translation, similarity
from geometry_611 import torus_delta, local_scale, compactness

RETENTION_MIN_SOFT = 0.10     # material-overlap eligibility floor (soft; well below v1's 0.30)
R_F_MIN_TRANSPORT = 0.50      # SHAPE-similarity eligibility floor (identity_69's R_F -- centroid-relative
                               # field comparison; NOT by itself a displacement/transport-magnitude check,
                               # see TRANSPORT_NO_HISTORY_MULTIPLIER below)
SCORE_TEMPERATURE = 4.0       # unchanged from lineage_611, for comparability
MAX_LIVE_LINEAGES = 6         # same computational cap as lineage_611.MAX_HYPOTHESES
DICE_WEIGHT, RF_WEIGHT = 0.6, 0.4   # unchanged weights, for comparability with v1's score
VELOCITY_HISTORY_LEN = 5
TRANSPORT_NO_HISTORY_MULTIPLIER = 5.0   # first transition after birth: accept a displacement up to this
                                          # many multiples of local_scale (no velocity estimate exists yet
                                          # to check consistency against, so fall back to a physically-
                                          # motivated "not an absurd jump" bound instead)
TRANSPORT_HISTORY_MULTIPLIER = 2.0       # subsequent transitions: accept a residual (actual - predicted
                                          # displacement, from the lineage's OWN recent velocity history) up
                                          # to this many multiples of local_scale
DWELL_CONTINUITY_MIN = 0.5     # item 2: a transition only extends dwell if ITS OWN p_continue clears this;
                                # otherwise dwell resets to 1 even if the candidate ends up as the sole
                                # (and therefore, after renormalization, high-probability) survivor -- this
                                # is what stops qualification age from surviving a disjoint-thread switch

# Fitted by calibrate_lineage_v2_611.py on 10 uncontrolled train-split episodes
# (1768 "good"/1736 "bad" labelled continuation pairs; held-out Brier=0.0123).
# See lineage_v2_calibration_611.json for the full reliability curve. Fixed
# here rather than re-fit at import time so every script in this pass uses
# the SAME calibration, frozen before any adjudication run.
DEFAULT_CALIBRATION = dict(a=11.870393215092983, b=-7.548703380210431)


def component_sizes(members: np.ndarray, r: np.ndarray, L: float, radius: float) -> list[int]:
    """Sizes of every spatially-connected component within `members`, at
    `radius` (torus-aware minimum-image distance -- same primitive
    geometry_611.connected_components uses, extended to return sizes rather
    than only a count)."""
    if len(members) <= 1:
        return [len(members)] if len(members) else []
    sub = r[members]
    d = torus_delta(sub[None, :, :], sub[:, None, :], L)
    D = np.sqrt((d ** 2).sum(-1))
    adj = D <= radius
    n = len(members)
    seen = np.zeros(n, dtype=bool)
    sizes = []
    for s in range(n):
        if seen[s]:
            continue
        stack, count = [s], 0
        seen[s] = True
        while stack:
            a = stack.pop()
            count += 1
            for b in np.where(adj[a] & ~seen)[0]:
                seen[b] = True
                stack.append(int(b))
        sizes.append(count)
    return sizes


def retention_purity(a: set, b: set) -> tuple[float, float]:
    inter = len(a & b)
    return (inter / len(a) if a else 0.0, inter / len(b) if b else 0.0)


def dice(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    denom = len(a) + len(b)
    return 2.0 * inter / denom if denom else 0.0


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class LineageV2:
    lid: int
    members: np.ndarray
    origin: frozenset
    centre: np.ndarray
    rho: np.ndarray
    m: np.ndarray
    prob: float
    d_norm: float
    dwell: int = 1                       # item 2: consecutive steps THIS present-state identity has existed
    genealogy: list = dc_field(default_factory=list)   # metadata only: [(parent_lid, contributed_prob), ...]
    status: str = "active"               # active | dead
    records: list = dc_field(default_factory=list)
    velocity_history: list = dc_field(default_factory=list)   # recent (torus-wrapped) total_delta vectors


class LineageTrackerV2:
    """Present-state-coalesced lineage tracker. Never imports or mutates
    lineage_611.LineageTracker611 -- a fully independent comparator."""

    def __init__(self, L: float, uv4: np.ndarray, nu: int = 4,
                 calibration: dict | None = None):
        self.L = L
        self.uv4 = uv4
        self.nu = nu
        self._next_id = 0
        self.lineages: list[LineageV2] = []
        self.dead: list[LineageV2] = []
        self.calibration = calibration or DEFAULT_CALIBRATION

    def _new_id(self) -> int:
        self._next_id += 1
        return self._next_id - 1

    def _state(self, members: np.ndarray, r: np.ndarray, z: np.ndarray):
        pos = r[members]
        c = centroid(pos, self.L)
        rho, m, _ = comoving_field(pos, self.uv4[z[members]], self.L, c)
        return c, rho, m

    def p_continue(self, score: float) -> float:
        a, b = self.calibration["a"], self.calibration["b"]
        return float(sigmoid(a * score + b))

    def _spawn(self, members: np.ndarray, r: np.ndarray, z: np.ndarray, t: int,
               prob: float, genealogy: list) -> LineageV2:
        c, rho, m = self._state(members, r, z)
        rng = np.random.default_rng(0)
        other = np.array(sorted(rng.choice(r.shape[0], size=len(members), replace=False)))
        c2, rho2, m2 = self._state(other, r, z)
        d_norm = max(field_distance(rho, m, rho2, m2), 1e-3)
        periphery_radius = local_scale(r, self.L)
        sizes = component_sizes(members, r, self.L, periphery_radius)
        f_main = max(sizes) / max(1, sum(sizes)) if sizes else 1.0
        Q = compactness(members, r, self.L, c)
        lin = LineageV2(lid=self._new_id(), members=members, origin=frozenset(int(x) for x in members),
                          centre=c, rho=rho, m=m, prob=prob, d_norm=d_norm, dwell=1,
                          genealogy=genealogy)
        lin.records.append(dict(t=t, size=len(members), prob=prob, dwell=1, status="active",
                                  R_retain_from_origin=1.0, R_purity_from_origin=1.0,
                                  Q=Q, f_main=f_main, n_components=len(sizes),
                                  d_transport=0.0, R_F=1.0, size_ratio=1.0))
        return lin

    def start(self, members: np.ndarray, r: np.ndarray, z: np.ndarray, t: int):
        self.lineages = [self._spawn(members, r, z, t, 1.0, genealogy=[("root", 1.0)])]

    def _evaluate(self, lin: LineageV2, cand: np.ndarray, r: np.ndarray, z: np.ndarray, t: int):
        prev_set = set(int(x) for x in lin.members)
        cand_set = set(int(x) for x in cand)
        r_retain, r_purity = retention_purity(prev_set, cand_set)
        dc = dice(prev_set, cand_set)
        c, rho, m = self._state(cand, r, z)
        tr = estimate_translation(lin.rho, lin.m, rho, m, lin.centre, c)
        R_F = similarity(tr["distance"], lin.d_norm)     # SHAPE similarity only (identity_69's own
                                                           # centroid-relative comparison) -- does not by
                                                           # itself check displacement magnitude/direction
        actual_delta = torus_delta(np.asarray(tr["total_delta"]), 0.0, self.L)
        disp_mag = float(np.hypot(*actual_delta))
        local_sc = local_scale(r, self.L)
        if lin.velocity_history:
            predicted = np.mean(np.asarray(lin.velocity_history), axis=0)
            residual = float(np.hypot(*torus_delta(actual_delta - predicted, 0.0, self.L)))
            transport_scale = max(2.0 * float(np.hypot(*predicted)), TRANSPORT_HISTORY_MULTIPLIER * local_sc)
        else:
            residual = disp_mag
            transport_scale = TRANSPORT_NO_HISTORY_MULTIPLIER * local_sc
        transport_ok = residual <= transport_scale
        eligible = (r_retain >= RETENTION_MIN_SOFT) or (R_F >= R_F_MIN_TRANSPORT and transport_ok)
        score = DICE_WEIGHT * dc + RF_WEIGHT * R_F
        sizes = component_sizes(cand, r, self.L, local_sc)
        f_main = max(sizes) / max(1, sum(sizes)) if sizes else 1.0
        Q = compactness(cand, r, self.L, c)
        return dict(eligible=eligible, r_retain=r_retain, r_purity=r_purity, dice=dc,
                     d_transport=tr["distance"], R_F=R_F, score=score,
                     transport_residual=residual, transport_scale=transport_scale, transport_ok=transport_ok,
                     size_ratio=len(cand_set) / max(1, len(prev_set)),
                     Q=Q, f_main=f_main, n_components=len(sizes),
                     bulk_delta=list(map(float, actual_delta)), c=c, rho=rho, m=m)

    def update(self, candidates: list[np.ndarray], r: np.ndarray, z: np.ndarray, t: int):
        if not self.lineages:
            return
        if not candidates:
            # Temporary missed detection: the detector found NOTHING at all
            # this step (a detector hiccup), which is a different situation
            # from "the detector found things but none of them matched this
            # lineage" (handled below, and correctly treated as evidence of
            # death). With zero candidates there is no evidence either way,
            # so carry every lineage forward unchanged rather than killing
            # it -- disclosed grace behaviour, not present in lineage_611.
            for lin in self.lineages:
                lin.records = lin.records + [dict(t=t, size=len(lin.members), prob=lin.prob,
                                                     dwell=lin.dwell, status="active",
                                                     note="no_candidates_this_step_carried_forward")]
            return
        # ---- 1. evaluate every (lineage, candidate) pair -------------------
        eval_table = {}   # (lin_idx, cand_idx) -> eval dict
        for li, lin in enumerate(self.lineages):
            for ci, cand in enumerate(candidates):
                eval_table[(li, ci)] = self._evaluate(lin, cand, r, z, t)

        # ---- 2. per-lineage: split prior mass into (candidate shares, dead) ---
        contributions = {}   # cand_idx (as frozenset key) -> [(prob_share, parent_lid, cand_members), ...]
        dead_mass = {}
        for li, lin in enumerate(self.lineages):
            elig = [(ci, eval_table[(li, ci)]) for ci in range(len(candidates)) if eval_table[(li, ci)]["eligible"]]
            if not elig:
                dead_mass[li] = lin.prob
                continue
            best_score = max(ev["score"] for _, ev in elig)
            p_cont = self.p_continue(best_score)
            live_mass = lin.prob * p_cont
            dead_mass[li] = lin.prob * (1.0 - p_cont)
            scores = np.array([ev["score"] for _, ev in elig])
            w = np.exp(SCORE_TEMPERATURE * (scores - scores.max()))
            branch_probs = w / w.sum()
            for (ci, ev), bp in zip(elig, branch_probs):
                key = frozenset(int(x) for x in candidates[ci])
                contributions.setdefault(key, []).append(dict(
                    prob=live_mass * float(bp), parent_lin=lin, ev=ev, cand_idx=ci))

        # ---- 3. coalesce: identical present member sets merge BEFORE any -----
        #         renormalization, regardless of which lineage(s) fed them
        new_lineages = []
        for key, contribs in contributions.items():
            total_prob = sum(c["prob"] for c in contribs)
            cand_members = np.array(sorted(key))
            best = max(contribs, key=lambda c: c["prob"])
            ev = best["ev"]
            parent = best["parent_lin"]
            genealogy = [(c["parent_lin"].lid, c["prob"]) for c in contribs]
            # item 2: dwell only extends if THIS transition's own p_continue
            # (the parent's calibrated confidence that its best-viable
            # candidate is a genuine continuation, not merely the least-bad
            # of a poor field) cleared DWELL_CONTINUITY_MIN -- a candidate
            # that squeaks past eligibility on a weak match resets dwell to 1
            # even if it ends up the sole (and therefore, post-renormalization,
            # high-probability) survivor.
            p_cont_this_parent = self.p_continue(ev["score"])
            new_dwell = parent.dwell + 1 if p_cont_this_parent >= DWELL_CONTINUITY_MIN else 1
            vhist = (parent.velocity_history + [ev["bulk_delta"]])[-VELOCITY_HISTORY_LEN:]
            lin = LineageV2(lid=parent.lid if len(contribs) == 1 else self._new_id(),
                              members=cand_members, origin=parent.origin,
                              centre=ev["c"], rho=ev["rho"], m=ev["m"], prob=total_prob,
                              d_norm=parent.d_norm, dwell=new_dwell,
                              genealogy=genealogy, records=list(parent.records),
                              velocity_history=vhist)
            origin_retain = len(set(int(x) for x in cand_members) & lin.origin) / max(1, len(lin.origin))
            origin_purity = len(set(int(x) for x in cand_members) & lin.origin) / max(1, len(cand_members))
            lin.records = lin.records + [dict(
                t=t, size=len(cand_members), prob=total_prob, dwell=lin.dwell, status="active",
                R_retain_step=ev["r_retain"], R_purity_step=ev["r_purity"], dice=ev["dice"],
                d_transport=ev["d_transport"], R_F=ev["R_F"], size_ratio=ev["size_ratio"],
                Q=ev["Q"], f_main=ev["f_main"], n_components=ev["n_components"],
                transport_residual=ev["transport_residual"], transport_ok=ev["transport_ok"],
                p_continue_this_transition=p_cont_this_parent, dwell_reset=(new_dwell == 1 and parent.dwell > 1),
                R_retain_from_origin=origin_retain, R_purity_from_origin=origin_purity,
                n_contributing_parents=len(contribs),
            )]
            new_lineages.append(lin)

        # ---- 4. dead lineages: report, do not silently drop ------------------
        for li, dm in dead_mass.items():
            if dm <= 1e-9:
                continue
            lin = self.lineages[li]
            dlin = LineageV2(lid=lin.lid, members=lin.members, origin=lin.origin, centre=lin.centre,
                               rho=lin.rho, m=lin.m, prob=dm, d_norm=lin.d_norm, dwell=lin.dwell,
                               genealogy=lin.genealogy, status="dead", records=list(lin.records))
            dlin.records = dlin.records + [dict(t=t, size=0, prob=dm, dwell=lin.dwell, status="dead",
                                                    note="no_valid_continuation")]
            self.dead.append(dlin)

        # ---- 5. unmatched candidates may start NEW lineages -------------------
        claimed = set()
        for lin in new_lineages:
            claimed.add(frozenset(int(x) for x in lin.members))
        for ci, cand in enumerate(candidates):
            key = frozenset(int(x) for x in cand)
            if key in claimed:
                continue
            # a candidate is "unmatched" if it was not eligible for ANY live lineage
            if any(eval_table[(li, ci)]["eligible"] for li in range(len(self.lineages))):
                continue
            new_lineages.append(self._spawn(cand, r, z, t, prob=0.0, genealogy=[("new_birth", 0.0)]))
            claimed.add(key)

        # ---- 6. prune and renormalize -----------------------------------------
        new_lineages.sort(key=lambda h: -h.prob)
        new_lineages = new_lineages[:MAX_LIVE_LINEAGES]
        total = sum(h.prob for h in new_lineages)
        if total > 0:
            for h in new_lineages:
                h.prob /= total
        else:
            # every live lineage died and no unmatched candidate existed this
            # step -- surface as a genuinely empty belief, not a crash
            for h in new_lineages:
                h.prob = 1.0 / max(1, len(new_lineages))
        self.lineages = new_lineages

    def dominant(self) -> LineageV2 | None:
        if not self.lineages:
            return None
        return max(self.lineages, key=lambda h: h.prob)

    def entropy(self) -> float:
        probs = np.array([h.prob for h in self.lineages if h.prob > 0])
        return float(-(probs * np.log(probs)).sum()) if len(probs) else 0.0

    def margin(self) -> float:
        probs = sorted((h.prob for h in self.lineages), reverse=True)
        return probs[0] - probs[1] if len(probs) > 1 else (probs[0] if probs else 0.0)

    def summary(self) -> dict:
        return dict(
            n_live=len(self.lineages),
            lineages=[dict(lid=h.lid, prob=h.prob, size=len(h.members), dwell=h.dwell,
                             status=h.status, genealogy=h.genealogy, members=h.members.tolist())
                       for h in self.lineages],
            n_dead=len(self.dead),
        )
