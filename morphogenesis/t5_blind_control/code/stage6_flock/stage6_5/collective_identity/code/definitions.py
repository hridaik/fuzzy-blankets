"""Three definitions of 'the same collective' over a trajectory (Part 3).

Material (I^M): frozen I0 forever -- Stage 6's own definition, reproduced
here unmodified only so it can sit in the same comparison table as the two
adaptive ones.

Lineage-tracked (I^L, Part 3.2): at each t, the existing Stage-6 spectral
bipartition (core1/core2 of flock_sim.spectral.analyze_window, computed on a
trailing, PAST-ONLY window) offers two candidate groups; pick whichever is
closer (Jaccard) to the previous collective. If neither candidate clears
MIN_CONTINUITY, keep the previous collective unchanged. Part 3.2 requires "a
minimum continuity criterion" but does not specify the fallback when no
candidate meets it; keeping the previous set (rather than, say, forcing the
better-of-two anyway, or collapsing to the empty set) is the choice made
here, stated plainly so it can be challenged. Fiedler sign/degeneracy is
handled by analyze_window's own refclust-alignment logic (align_to_reference
in flock_sim/spectral.py), using the previous collective as the reference.

Functional/coherence (I^F, Part 3.3): the connected component, on the TRUE
physical lattice, of birds that (a) share the same trailing-window MODAL
heading and (b) have held that heading for at least MIN_SELF_COHERENCE of
the window -- i.e. "connectedness on the physical lattice" plus "recent
heading coherence" plus "persistence over a short trailing window", exactly
the three ingredients Part 3.3 suggests, combined in the simplest way that
uses all three. Using the true lattice here is explicitly permitted (Part
3.3 says so) and is NOT the same as boundary_inference's Part 1, which is
barred from it -- this module never claims to infer the interaction graph,
it only asks "which currently-connected, currently-coherent birds are these".
Again picks the Jaccard-nearest candidate component to the previous
collective, with the same keep-previous fallback as I^L.

Both adaptive definitions use ONLY trailing/past information at each t
(causal): I_t is a function of z_hist[max(0,t-TW+1) .. t], never of
z_hist[t' > t] -- Part 3.2's "trailing/past-only window" requirement.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "python"))
from flock_sim.spectral import analyze_window  # noqa: E402

TW = 5                     # trailing window length, matches Stage-6 convention (common_v2.TW)
MIN_CONTINUITY = 0.3       # minimum Jaccard with I_{t-1} to accept a candidate group
MIN_SELF_COHERENCE = 0.6   # F-definition: fraction of window a bird must hold its modal heading
NU = 4


def jaccard(a, b) -> float:
    sa, sb = set(int(x) for x in a), set(int(x) for x in b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def material_track(I0: np.ndarray, n_steps: int) -> list[np.ndarray]:
    fixed = np.array(sorted(int(i) for i in I0.tolist()))
    return [fixed.copy() for _ in range(n_steps)]


def _window(z_hist: np.ndarray, t: int, tw: int = TW) -> np.ndarray:
    lo = max(0, t - tw + 1)
    return z_hist[lo:t + 1]


def lineage_track(z_hist: np.ndarray, I0: np.ndarray, t_start: int, t_end: int) -> list[np.ndarray]:
    """I_t^L for t in [t_start, t_end] inclusive; I_{t_start}^L = I0."""
    out = [np.array(sorted(int(i) for i in I0.tolist()))]
    prev = out[0]
    for t in range(t_start + 1, t_end + 1):
        window = _window(z_hist, t)
        if window.shape[0] < 2:
            out.append(prev)
            continue
        sr = analyze_window(window, refclust=prev)
        candidates = [sr.core1_nodes, sr.core2_nodes]
        best = max(candidates, key=lambda c: jaccard(c, prev))
        if len(best) > 0 and jaccard(best, prev) >= MIN_CONTINUITY:
            cur = np.array(sorted(int(b) for b in best.tolist()))
        else:
            cur = prev
        out.append(cur)
        prev = cur
    return out


def _connected_components(nodes: list[int], lattice) -> list[list[int]]:
    node_set = set(nodes)
    visited = set()
    comps = []
    for start in nodes:
        if start in visited:
            continue
        comp = [start]
        visited.add(start)
        frontier = [start]
        while frontier:
            nxt = []
            for b in frontier:
                for j in lattice.neighbor_ids[b].tolist():
                    if j in node_set and j not in visited:
                        visited.add(j)
                        comp.append(j)
                        nxt.append(j)
            frontier = nxt
        comps.append(comp)
    return comps


def functional_track(z_hist: np.ndarray, I0: np.ndarray, t_start: int, t_end: int, lattice) -> list[np.ndarray]:
    """I_t^F for t in [t_start, t_end] inclusive; I_{t_start}^F = I0. Uses the
    TRUE lattice for spatial connectivity -- permitted for this identity
    definition (Part 3.3), unlike boundary_inference's Part 1."""
    out = [np.array(sorted(int(i) for i in I0.tolist()))]
    prev = out[0]
    n_bird = z_hist.shape[1]
    for t in range(t_start + 1, t_end + 1):
        window = _window(z_hist, t)
        W = window.shape[0]
        modal = np.zeros(n_bird, dtype=int)
        self_coh = np.zeros(n_bird)
        for b in range(n_bird):
            counts = np.bincount(window[:, b], minlength=NU)
            modal[b] = int(np.argmax(counts))
            self_coh[b] = counts.max() / W
        persistent = np.where(self_coh >= MIN_SELF_COHERENCE)[0]
        comps: list[list[int]] = []
        for h in range(NU):
            members = [int(b) for b in persistent if modal[b] == h]
            if members:
                comps.extend(_connected_components(members, lattice))
        if not comps:
            out.append(prev)
            continue
        best = max(comps, key=lambda c: jaccard(c, prev))
        if jaccard(best, prev) >= MIN_CONTINUITY:
            cur = np.array(sorted(best))
        else:
            cur = prev
        out.append(cur)
        prev = cur
    return out
