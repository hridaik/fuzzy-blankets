"""Observer-facing detection and translation-aware tracking for Stage 6.9
(task brief sections 27-29, 31-32).

INFERENCE-SIDE. Uses observed positions and headings ONLY. No target path, no
oracle interaction graph, no simulator centre trajectory.

The affinity is the Stage 6.8 one, with torus distance substituted for lattice
distance and nothing else changed:

    W_ij(t) = K_sigma(||r_i - r_j||_torus) * recent heading agreement

Communities come from the same deterministic weighted Louvain
(`stage6_8_dynamic_interactions/code/louvain.py`), so the detector really is
"the same observer-facing logic" the brief asks for.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from louvain import louvain
from identity_69 import (centroid, field as make_field, field_distance,
                         estimate_translation, similarity, shape_metrics, torus_delta)

W_AFFINITY = 6
SIGMA = 1.1
KERNEL_CUTOFF = 3.3
MIN_SIZE_FRAC = 0.03
MAX_SIZE_FRAC = 0.55
MIN_SCORE = 0.30           # lineage continuation threshold
UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])


def torus_distance(r, L):
    d = np.abs(r[:, None, :] - r[None, :, :])
    d = np.minimum(d, L - d)
    return np.sqrt((d ** 2).sum(-1))


def affinity(r, z_window, L, sigma=SIGMA, cutoff=KERNEL_CUTOFF):
    D = torus_distance(r, L)
    K = np.exp(-(D ** 2) / (2 * sigma ** 2))
    K[D > cutoff] = 0.0
    np.fill_diagonal(K, 0.0)
    agree = np.zeros_like(K)
    for z in z_window:
        agree += (z[:, None] == z[None, :]).astype(float)
    return K * agree / len(z_window)


def propose(r, z_window, L, sigma=SIGMA):
    N = r.shape[0]
    lab = louvain(affinity(r, z_window, L, sigma))
    out = []
    for c in np.unique(lab):
        m = np.where(lab == c)[0]
        if MIN_SIZE_FRAC * N <= len(m) <= MAX_SIZE_FRAC * N:
            out.append(np.array(sorted(m.tolist())))
    out.sort(key=len, reverse=True)
    return out


@dataclass
class TrackState:
    members: np.ndarray
    t: int
    centre: np.ndarray
    rho: np.ndarray
    m: np.ndarray
    pos: np.ndarray        # observed positions of the members at time t


class TranslatingTracker:
    """Follows one collective and records all three identity notions.

    Continuation is by set overlap plus co-moving field similarity, so a group
    that exchanges members but keeps its moving organization is continued,
    while a group that keeps its members but loses its organization is not
    silently credited (task brief section 37, "material-only persistence")."""

    def __init__(self, L: float, min_score: float = MIN_SCORE):
        self.L = L
        self.min_score = min_score
        self.origin: set | None = None
        self.state: TrackState | None = None
        self.records: list = []
        self.branch_events: list = []
        self.d_norm: float | None = None

    def _state(self, members, r, z, t) -> TrackState:
        pos = r[members]
        c = centroid(pos, self.L)
        rho, m, _ = make_field(pos, UV4[z[members]], self.L, c)
        return TrackState(members=members, t=t, centre=c, rho=rho, m=m, pos=pos)

    def start(self, members, r, z, t):
        self.origin = set(int(x) for x in members)
        self.state = self._state(members, r, z, t)
        # d_norm: the distance between this collective's field and an
        # independently drawn same-size random subset, i.e. "how far apart are
        # two unrelated groups of this size". Observer-computable.
        rng = np.random.default_rng(0)
        other = np.array(sorted(rng.choice(r.shape[0], size=len(members), replace=False)))
        s2 = self._state(other, r, z, t)
        self.d_norm = max(field_distance(self.state.rho, self.state.m, s2.rho, s2.m), 1e-3)
        self._record(self.state, None, None)

    def _record(self, st, prev, tr):
        cur = set(int(x) for x in st.members)
        prevset = set(int(x) for x in prev.members) if prev is not None else cur
        sh = shape_metrics(st.pos, self.L, st.centre) if len(st.members) else {}
        rec = dict(
            t=st.t, size=len(cur),
            R_M=len(cur & self.origin) / max(1, len(self.origin)),
            J_prev=len(cur & prevset) / max(1, len(cur | prevset)),
            turnover=len(cur - prevset) / max(1, len(cur)),
            centroid=st.centre.tolist(),
        )
        rec.update(sh)
        if tr is not None:
            rec.update(
                bulk_delta=list(map(float, tr["total_delta"])),
                bulk_speed=float(np.linalg.norm(torus_delta(np.asarray(tr["total_delta"]), 0.0, self.L))),
                D_deform=float(tr["distance"]),
                D_centroid_aligned_only=float(tr["distance_centroid_only"]),
                D_world_frame=float(tr["distance_world_frame"]),
                R_F=similarity(tr["distance"], self.d_norm),
            )
        self.records.append(rec)

    def update(self, candidates, r, z, t) -> bool:
        if self.state is None or not len(candidates):
            return False
        prev = self.state
        prevset = set(int(x) for x in prev.members)
        scored = []
        for c in candidates:
            cs = set(int(x) for x in c)
            J = len(cs & prevset) / max(1, len(cs | prevset))
            scored.append((J, c))
        scored.sort(key=lambda x: -x[0])
        # lineage branch event: two candidates each carrying a substantial share
        if len(scored) > 1 and scored[0][0] >= 0.25 and scored[1][0] >= 0.25:
            self.branch_events.append(dict(t=t, jaccards=[scored[0][0], scored[1][0]],
                                           sizes=[len(scored[0][1]), len(scored[1][1])]))
        best_J, best = scored[0]
        st = self._state(best, r, z, t)
        tr = estimate_translation(prev.rho, prev.m, st.rho, st.m, prev.centre, st.centre)
        # The same comparison with NO translation removed at all: the current
        # members' field rendered about the PREVIOUS centre, i.e. in world
        # coordinates. d_world >> D_deform is what shows that bulk motion was
        # being mistaken for destruction before alignment (task brief 31).
        rho_w, m_w, _ = make_field(st.pos, UV4[z[best]], self.L, prev.centre)
        tr["distance_world_frame"] = float(field_distance(prev.rho, prev.m, rho_w, m_w))
        score = 0.6 * best_J + 0.4 * similarity(tr["distance"], self.d_norm)
        if score < self.min_score:
            return False
        self.state = st
        self._record(st, prev, tr)
        return True
