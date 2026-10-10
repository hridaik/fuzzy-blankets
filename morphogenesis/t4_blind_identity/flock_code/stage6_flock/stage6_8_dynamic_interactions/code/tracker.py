"""Task-neutral candidate lineage tracking for Stage 6.8 (task brief section 9).

INFERENCE-SIDE MODULE. Fixed-lattice only; Stage 6.9's translation-aware
tracker is a separate object and does not live here.

Continuation score between a tracked collective at t-1 and a proposal at t:

    score = w_J * J(I_t, I_{t-1}) + w_F * functional_similarity

with functional similarity = agreement of the two sets' modal headings times
the similarity of their internal coherence. Material identity is NOT imposed
as exact equality: a lineage survives arbitrary membership change as long as
the overlap-plus-function score clears `MIN_SCORE`.

Recorded per step: size, Jaccard retention, membership turnover, coherence,
centroid, compactness/aspect ratio.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from candidate_detection import Candidate


W_JACCARD = 0.7
W_FUNCTIONAL = 0.3
MIN_SCORE = 0.35          # frozen continuation threshold (PROTOCOL_6_8.md section 6)


def functional_similarity(a: Candidate, b: Candidate) -> float:
    head = 1.0 if a.modal_heading == b.modal_heading else 0.0
    coh = 1.0 - min(1.0, abs(a.coherence - b.coherence))
    return 0.5 * head + 0.5 * coh


def continuation_score(prev: Candidate, cur: Candidate) -> float:
    sa, sb = prev.key(), cur.key()
    J = len(sa & sb) / max(1, len(sa | sb))
    return W_JACCARD * J + W_FUNCTIONAL * functional_similarity(prev, cur)


@dataclass
class Lineage:
    lineage_id: int
    method: str
    t_start: int
    frames: list = field(default_factory=list)      # list of Candidate
    records: list = field(default_factory=list)     # list of dict
    alive: bool = True

    @property
    def t_end(self) -> int:
        return self.frames[-1].t if self.frames else self.t_start

    @property
    def duration(self) -> int:
        return len(self.frames)

    def origin(self) -> Candidate:
        return self.frames[0]


class LineageTracker:
    """Greedy mutual-best-match continuation, one pass per timestep."""

    def __init__(self, method: str, min_score: float = MIN_SCORE):
        self.method = method
        self.min_score = min_score
        self.lineages: list[Lineage] = []
        self._alive: list[int] = []
        self._next_id = 0

    def _record(self, lin: Lineage, cur: Candidate):
        prev = lin.frames[-1] if lin.frames else None
        if prev is None:
            J, turn = 1.0, 0.0
        else:
            sa, sb = prev.key(), cur.key()
            J = len(sa & sb) / max(1, len(sa | sb))
            turn = len(sb - sa) / max(1, len(sb))
        s0 = lin.origin().key() if lin.frames else cur.key()
        lin.frames.append(cur)
        lin.records.append(dict(
            t=cur.t, size=cur.size, jaccard_prev=float(J), turnover=float(turn),
            material_retention=len(s0 & cur.key()) / max(1, len(s0)),
            coherence=cur.coherence, compactness=cur.compactness,
            aspect_ratio=cur.aspect_ratio, centroid=list(cur.centroid),
            modal_heading=cur.modal_heading,
        ))

    def update(self, candidates: list[Candidate]) -> dict:
        """Advance the tracker one frame with this timestep's proposals."""
        alive = [self.lineages[i] for i in self._alive]
        if not alive:
            for c in candidates:
                lin = Lineage(self._next_id, self.method, c.t)
                self._next_id += 1
                self._record(lin, c)
                self.lineages.append(lin)
            self._alive = [l.lineage_id for l in self.lineages if l.alive]
            return dict(continued=0, born=len(candidates), died=0)

        S = np.zeros((len(alive), len(candidates)))
        for a, lin in enumerate(alive):
            for b, c in enumerate(candidates):
                S[a, b] = continuation_score(lin.frames[-1], c)

        used_a, used_b, continued = set(), set(), 0
        if S.size:
            order = np.dstack(np.unravel_index(np.argsort(-S, axis=None), S.shape))[0]
            for a, b in order:
                a, b = int(a), int(b)
                if a in used_a or b in used_b or S[a, b] < self.min_score:
                    continue
                used_a.add(a); used_b.add(b)
                self._record(alive[a], candidates[b])
                continued += 1

        died = 0
        for a, lin in enumerate(alive):
            if a not in used_a:
                lin.alive = False
                died += 1
        born = 0
        for b, c in enumerate(candidates):
            if b not in used_b:
                lin = Lineage(self._next_id, self.method, c.t)
                self._next_id += 1
                self._record(lin, c)
                self.lineages.append(lin)
                born += 1
        self._alive = [l.lineage_id for l in self.lineages if l.alive]
        return dict(continued=continued, born=born, died=died)

    def summary(self) -> list[dict]:
        out = []
        for lin in self.lineages:
            recs = lin.records
            out.append(dict(
                lineage_id=lin.lineage_id, method=lin.method, t_start=lin.t_start,
                t_end=lin.t_end, duration=lin.duration, alive=lin.alive,
                mean_size=float(np.mean([r["size"] for r in recs])),
                mean_jaccard=float(np.mean([r["jaccard_prev"] for r in recs[1:]])) if len(recs) > 1 else 1.0,
                mean_turnover=float(np.mean([r["turnover"] for r in recs[1:]])) if len(recs) > 1 else 0.0,
                final_material_retention=float(recs[-1]["material_retention"]),
                mean_coherence=float(np.nanmean([r["coherence"] for r in recs])),
                records=recs,
            ))
        return out
