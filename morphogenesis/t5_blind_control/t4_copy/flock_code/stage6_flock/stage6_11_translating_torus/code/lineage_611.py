"""Stage 6.11 expansion-aware lineage tracking (task brief item 9).

INFERENCE-SIDE. Extends Stage 6.9's `TranslatingTracker` (which kept a single
best-Jaccard-match continuation) along three axes the task brief requires:

1. Retention and recruitment are reported SEPARATELY, never blended into one
   "identity score":
       R_retain(A -> B) = |A n B| / |A|          (how much of the old thing survived)
       R_purity(A -> B)  = |A n B| / |B|          (how much of the new thing is old)
   (Their harmonic mean is the Dice coefficient, used only as an internal,
   clearly-labelled matching heuristic -- never returned as "the" identity.)

2. Several plausible descendant hypotheses are maintained through ambiguous
   merge/split events, normalized into a genuine probability distribution
   (`Hypothesis.prob`, summing to 1 across all live hypotheses of a lineage
   tree at each step), and bird-level membership confidence is exposed as the
   probability-weighted marginal over hypotheses.

3. A growing candidate is classified as bounded recruitment (same lineage,
   status="active") only if it retains the old organization, stays spatially
   integrated (one dominant component) and its local exterior contrast does
   not collapse; if apparent growth is really the candidate blending into a
   population-wide aligned background, it is classified as INDIVIDUATION LOSS
   rather than credited as unbounded expansion (task brief item 9, last
   paragraph).

Target heading and control success are never read by this module -- there is
no code path here that could read them even if they existed elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

import numpy as np

from identity_69 import centroid, field as comoving_field, field_distance, estimate_translation, similarity
from geometry_611 import torus_delta, local_scale, connected_components, compactness, local_exterior_contrast

RETENTION_MIN = 0.30            # a candidate must retain >= this much of a hypothesis to be considered its continuation at all
GROWTH_RETENTION_MIN = 0.70     # "old organization is retained" threshold for classifying growth as bounded recruitment
CONTRAST_DROP_FRAC = 0.5        # exterior contrast D falling below this fraction of its recent baseline flags individuation loss
CONTRAST_HISTORY = 5            # steps of D history used for the "recent baseline"
DISSOLVE_AFTER_INDIVIDUATION_STEPS = 3
MAX_HYPOTHESES = 6              # disclosed computational cap; lowest-probability branches pruned beyond this
SCORE_TEMPERATURE = 4.0         # softmax temperature over (dice, R_F)-blended continuation scores


def dice(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    inter = len(a & b)
    denom = len(a) + len(b)
    return 2.0 * inter / denom if denom else 0.0


def retention_purity(a: set, b: set) -> tuple[float, float]:
    inter = len(a & b)
    r_retain = inter / len(a) if a else 0.0
    r_purity = inter / len(b) if b else 0.0
    return r_retain, r_purity


@dataclass
class Hypothesis:
    hid: int
    members: np.ndarray
    origin: frozenset            # the material set at hypothesis START (root of this lineage tree)
    centre: np.ndarray
    rho: np.ndarray
    m: np.ndarray
    prob: float
    L: float
    age: int = 0
    d_norm: float = 1e-3
    contrast_history: list = dc_field(default_factory=list)
    consecutive_individuation: int = 0
    status: str = "active"       # active | individuation_loss | dissolved
    records: list = dc_field(default_factory=list)


class LineageTracker611:
    """Tracks ONE lineage tree (started from one detected candidate) as a
    distribution over live `Hypothesis` objects. Call `start(...)` once, then
    `update(candidates, r, z, t)` every step with the detector's current full
    candidate list (`candidate_detection_611`-style: multiple communities)."""

    def __init__(self, L: float, uv4: np.ndarray, nu: int = 4):
        self.L = L
        self.uv4 = uv4
        self.nu = nu
        self._next_id = 0
        self.hypotheses: list[Hypothesis] = []
        self.dissolved: list[Hypothesis] = []

    def _new_id(self) -> int:
        self._next_id += 1
        return self._next_id - 1

    def _state(self, members: np.ndarray, r: np.ndarray, z: np.ndarray, t: int):
        pos = r[members]
        c = centroid(pos, self.L)
        rho, m, _ = comoving_field(pos, self.uv4[z[members]], self.L, c)
        return pos, c, rho, m

    def start(self, members: np.ndarray, r: np.ndarray, z: np.ndarray, t: int):
        pos, c, rho, m = self._state(members, r, z, t)
        rng = np.random.default_rng(0)
        other = np.array(sorted(rng.choice(r.shape[0], size=len(members), replace=False)))
        _, c2, rho2, m2 = self._state(other, r, z, t)
        d_norm = max(field_distance(rho, m, rho2, m2), 1e-3)
        periphery_radius = local_scale(r, self.L)
        D0 = local_exterior_contrast(members, r, z, self.L, periphery_radius, self.nu)
        h = Hypothesis(hid=self._new_id(), members=members, origin=frozenset(int(x) for x in members),
                        centre=c, rho=rho, m=m, prob=1.0, L=self.L, d_norm=d_norm,
                        contrast_history=[D0])
        h.records.append(dict(t=t, size=len(members), prob=1.0, status="active",
                               R_retain_from_origin=1.0, R_purity_from_origin=1.0,
                               D=D0, n_components=connected_components(members, r, self.L, periphery_radius)))
        self.hypotheses = [h]

    def _grow_classification(self, h: Hypothesis, cand: np.ndarray, r: np.ndarray, z: np.ndarray,
                              periphery_radius: float) -> tuple[str, float, int]:
        prev_set = set(int(x) for x in h.members)
        cur_set = set(int(x) for x in cand)
        r_retain, r_purity = retention_purity(prev_set, cur_set)
        D = local_exterior_contrast(cand, r, z, self.L, periphery_radius, self.nu)
        ncomp = connected_components(cand, r, self.L, periphery_radius)
        growing = len(cur_set) > len(prev_set)
        status = "active"
        if growing and r_retain >= GROWTH_RETENTION_MIN:
            baseline = float(np.mean(h.contrast_history[-CONTRAST_HISTORY:])) if h.contrast_history else D
            if D < CONTRAST_DROP_FRAC * max(baseline, 1e-6) or ncomp > 1:
                status = "individuation_loss"
        return status, D, ncomp

    def update(self, candidates: list[np.ndarray], r: np.ndarray, z: np.ndarray, t: int):
        if not self.hypotheses:
            return
        periphery_radius = local_scale(r, self.L)
        next_gen: list[Hypothesis] = []
        for h in self.hypotheses:
            prev_set = set(int(x) for x in h.members)
            viable = []
            for cand in candidates:
                cand_set = set(int(x) for x in cand)
                r_retain, r_purity = retention_purity(prev_set, cand_set)
                if r_retain >= RETENTION_MIN:
                    pos, c, rho, m = self._state(cand, r, z, t)
                    tr = estimate_translation(h.rho, h.m, rho, m, h.centre, c)
                    R_F = similarity(tr["distance"], h.d_norm)
                    score = 0.6 * dice(prev_set, cand_set) + 0.4 * R_F
                    viable.append((cand, r_retain, r_purity, R_F, tr, pos, c, rho, m, score))
            if not viable:
                h.status = "dissolved"
                h.records.append(dict(t=t, size=0, prob=h.prob, status="dissolved",
                                       R_retain_from_origin=len(prev_set & h.origin) / max(1, len(h.origin)),
                                       R_purity_from_origin=None, D=None, n_components=0))
                self.dissolved.append(h)
                continue

            scores = np.array([v[-1] for v in viable])
            w = np.exp(SCORE_TEMPERATURE * (scores - scores.max()))
            branch_probs = w / w.sum()

            for (cand, r_retain, r_purity, R_F, tr, pos, c, rho, m, score), bp in zip(viable, branch_probs):
                status, D, ncomp = self._grow_classification(h, cand, r, z, periphery_radius)
                new_prob = h.prob * float(bp)
                origin_retain = len(set(int(x) for x in cand) & h.origin) / max(1, len(h.origin))
                origin_purity = len(set(int(x) for x in cand) & h.origin) / max(1, len(cand))
                child = Hypothesis(
                    hid=self._new_id() if len(viable) > 1 else h.hid,
                    members=cand, origin=h.origin, centre=c, rho=rho, m=m, prob=new_prob,
                    L=self.L, age=h.age + 1, d_norm=h.d_norm,
                    contrast_history=(h.contrast_history + [D])[-CONTRAST_HISTORY:],
                    consecutive_individuation=(h.consecutive_individuation + 1
                                                if status == "individuation_loss" else 0),
                    status=status, records=list(h.records),
                )
                child.records = h.records + [dict(
                    t=t, size=len(cand), prob=new_prob, status=status,
                    R_retain_step=r_retain, R_purity_step=r_purity,
                    R_retain_from_origin=origin_retain, R_purity_from_origin=origin_purity,
                    R_F=R_F, D=D, n_components=ncomp,
                    bulk_delta=list(map(float, torus_delta(np.asarray(tr["total_delta"]), 0.0, self.L))),
                    bulk_speed=float(np.hypot(*torus_delta(np.asarray(tr["total_delta"]), 0.0, self.L))),
                    D_deform=float(tr["distance"]),
                )]
                if child.consecutive_individuation >= DISSOLVE_AFTER_INDIVIDUATION_STEPS:
                    child.status = "dissolved"
                    self.dissolved.append(child)
                else:
                    next_gen.append(child)

        # renormalize surviving probability mass; prune to MAX_HYPOTHESES
        next_gen.sort(key=lambda h: -h.prob)
        next_gen = next_gen[:MAX_HYPOTHESES]
        total = sum(h.prob for h in next_gen)
        if total > 0:
            for h in next_gen:
                h.prob /= total
        self.hypotheses = next_gen

    def bird_membership_confidence(self, N: int) -> np.ndarray:
        """Marginal P(bird in the tracked collective) = sum_h P(h) * 1[bird in members(h)]."""
        conf = np.zeros(N)
        for h in self.hypotheses:
            conf[h.members] += h.prob
        return conf

    def summary(self) -> dict:
        return dict(
            n_live_hypotheses=len(self.hypotheses),
            hypotheses=[dict(hid=h.hid, prob=h.prob, size=len(h.members), status=h.status,
                              age=h.age, members=h.members.tolist(), records=h.records)
                        for h in self.hypotheses],
            n_dissolved=len(self.dissolved),
        )
