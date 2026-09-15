"""Transparent motion+shape association baseline, WITH an explicit no-match
alternative (VALIDATION_PROTOCOL.md §4 item 3). Deliberately simple: no
event taxonomy beyond continuation/unresolved-death/birth, no duplicate
coalescing beyond exact-set dedup, no likelihood model -- included so the
proposed joint model is checked against an honest simple alternative, not
only against the two already-diagnosed-flawed priors (v1, v2).

Rule: for each existing track, pick the nearest (by centroid displacement)
candidate within a fixed reachable radius; if none is within radius,
declare unresolved for `PATIENCE` steps, then terminate. Every candidate
not claimed by any track becomes a new track (birth). **No candidate
deduplication of any kind** (confirmed by this pass's own duplicate-
invariance check, `metrics.duplicate_invariance_check`: feeding the same
candidate list 3x over produces 3x as many spurious tracks) -- this is a
deliberate property of the "transparent simple baseline," not a bug to
fix: it is the honest point of comparison the mandate asks for, showing
what happens WITHOUT the proposed model's §5/§9(5) coalescing step. No
split/merge handling at all -- a split shows up as a death (nothing claims the track)
plus two births; a merger shows up as two tracks converging on the same
candidate, with only the nearer one keeping it and the other timing out
and then reappearing as a birth once its own members regroup -- exactly
the kind of behaviour the proposed model's dedicated split/merger events
are meant to improve on, given as an honest point of comparison.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dc_field

import numpy as np

L_DEFAULT = 24.0
REACHABLE_RADIUS = 3.5
PATIENCE = 5


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


@dataclass
class Track:
    tid: str
    c: np.ndarray
    members: set
    origin: set
    missing_streak: int = 0
    status: str = "active"
    history: list = dc_field(default_factory=list)


class BaselineTracker:
    def __init__(self, L: float = L_DEFAULT):
        self.L = L
        self.tracks: dict = {}
        self.terminated: dict = {}
        self._next_id = 0
        self.event_log: list = []

    def _new_id(self):
        self._next_id += 1
        return f"B{self._next_id}"

    def step(self, candidates: list, r: np.ndarray, z: np.ndarray, t: int):
        cand_sets = [set(int(x) for x in c) for c in candidates]
        cand_c = [centroid(r[np.array(sorted(cs))], self.L) if cs else np.array([self.L / 2] * 2)
                  for cs in cand_sets]
        active = [tr for tr in self.tracks.values() if tr.status != "terminated"]
        claimed = set()
        for tr in active:
            best_ci, best_d = None, np.inf
            for ci, c in enumerate(cand_c):
                if ci in claimed:
                    continue
                d = float(np.hypot(*torus_delta(c, tr.c, self.L)))
                if d < best_d:
                    best_d, best_ci = d, ci
            if best_ci is not None and best_d <= REACHABLE_RADIUS:
                tr.c = cand_c[best_ci]
                tr.members = cand_sets[best_ci]
                tr.missing_streak = 0
                tr.status = "active"
                tr.history.append(dict(t=t, event="continuation", members=sorted(tr.members)))
                claimed.add(best_ci)
            else:
                tr.missing_streak += 1
                if tr.missing_streak > PATIENCE:
                    tr.status = "terminated"
                    tr.history.append(dict(t=t, event="terminated_by_timeout", members=[]))
                    self.terminated[tr.tid] = tr
                    self.event_log.append(dict(t=t, type="death", label=tr.tid))
                else:
                    tr.status = "unresolved"
                    tr.history.append(dict(t=t, event="unresolved", members=sorted(tr.members)))

        for ci, cs in enumerate(cand_sets):
            if ci in claimed or not cs:
                continue
            tid = self._new_id()
            tr = Track(tid=tid, c=cand_c[ci], members=cs, origin=set(cs))
            tr.history.append(dict(t=t, event="birth", members=sorted(cs)))
            self.tracks[tid] = tr
            self.event_log.append(dict(t=t, type="birth", label=tid))

    def snapshot(self, t: int) -> dict:
        return {tid: dict(members=sorted(tr.members), status=tr.status)
                for tid, tr in self.tracks.items() if tr.status != "terminated"}
