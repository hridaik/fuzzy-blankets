"""Online organism detection + identity tracking with event flags.
Works on (point positions, member ids) per frame; member ids are O1 cell ids or tracker ids (O2/O3).
Forward identity rule (flock principle): an organism keeps its identity with the current group that
holds the largest share of its previous members; claims are made greedily by overlap size and are never
revised by later frames. Ambiguity (top-two pieces within `margin` of the organism's size) -> UNRESOLVED."""
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
from .geom import body_frame


class OrganismTracker:
    def __init__(self, ch, r_link, m_min, margin, r_hold=None):
        self.ch, self.r, self.m, self.margin = ch, r_link, m_min, margin
        self.r_hold = r_hold if r_hold is not None else r_link   # hysteresis: pairs already co-members stay linked up to r_hold
        self.prev = {}          # org_id -> set(ids) of members at previous frame
        self.prev_e1 = {}       # org_id -> last e1
        self.seen = set()       # every id ever observed inside an organism
        self.next_org = 0
        self.alive_ever = {}    # org_id -> dict(birth frame, parent)
        self.k = -1

    def _link(self, xy, ids):
        if len(xy) == 0:
            return np.zeros(0, int)
        D = cdist(xy, xy)
        A = D < self.r
        if self.r_hold > self.r and self.prev:
            own = {}
            for k, S in self.prev.items():
                for c in S:
                    own[c] = k
            o = np.array([own.get(int(c), -1) for c in ids])
            A |= (D < self.r_hold) & (o[:, None] == o[None, :]) & (o[:, None] >= 0)
        return connected_components(A, directed=False)[1]

    def step(self, t, xy, lev, ids, lab=None, compute_frame=True):
        self.k += 1
        if lab is None:
            lab = self._link(xy, ids)
        ncomp = lab.max() + 1 if len(lab) else 0
        comps = []
        for j in range(ncomp):
            idx = np.where(lab == j)[0]
            if len(idx) >= self.m:
                comps.append(idx)
        cur_sets = [set(ids[i].tolist()) for i in comps]
        events = []
        ok_ids = set(ids.tolist())
        claim = {}      # cur j -> org id
        org_ids = list(self.prev.keys())
        pairs = []
        for k in org_ids:
            for j, S in enumerate(cur_sets):
                n = len(self.prev[k] & S)
                if n >= self.m:
                    pairs.append((n, k, j))
        pairs.sort(key=lambda p: (-p[0], p[1], p[2]))
        claimed_org = {}
        for n, k, j in pairs:
            if k in claimed_org or j in claim:
                continue
            claim[j] = k; claimed_org[k] = j
        # per-org piece analysis
        unresolved = set()
        pieces = {k: sorted([(len(self.prev[k] & cur_sets[j]), j) for j in range(len(comps))
                             if len(self.prev[k] & cur_sets[j]) >= self.m], reverse=True) for k in org_ids}
        for k in org_ids:
            pc = pieces[k]
            if len(pc) >= 2:
                events.append(dict(type='SPLIT', org=k, t=t, k=self.k, sizes=[p[0] for p in pc]))
                if pc[0][0] - pc[1][0] < self.margin * len(self.prev[k]):
                    unresolved.add(k)
        # merges: cur group with >=2 source organisms
        sources = {j: sorted([(len(self.prev[k] & cur_sets[j]), k) for k in org_ids
                              if len(self.prev[k] & cur_sets[j]) >= self.m], reverse=True) for j in range(len(comps))}
        merged_into = {}
        for j, sc in sources.items():
            if len(sc) >= 2:
                win = claim.get(j)
                events.append(dict(type='MERGE', org=win if win is not None else sc[0][1], t=t, k=self.k,
                                   sources=[s[1] for s in sc], sizes=[s[0] for s in sc]))
                if sc[0][0] - sc[1][0] < self.margin * max(len(self.prev[sc[0][1]]), 1):
                    unresolved.add(win if win is not None else sc[0][1])
                for n_, k in sc:
                    if claim.get(j) != k:
                        merged_into[k] = claim.get(j)
        # assign organism ids to current groups
        orgs = []
        new_prev, new_e1 = {}, {}
        all_cur_member_ids = set()
        for j, idx in enumerate(comps):
            if j in claim:
                oid = claim[j]; parent = None
            else:
                oid = self.next_org; self.next_org += 1
                src = sources[j][0][1] if sources[j] else None
                parent = src
                self.alive_ever[oid] = dict(birth_k=self.k, parent=parent)
                if src is not None:
                    events.append(dict(type='SPLIT_CHILD', org=oid, parent=src, t=t, k=self.k))
                elif self.k > 0:
                    events.append(dict(type='BIRTH', org=oid, t=t, k=self.k))
                else:
                    self.alive_ever[oid]['parent'] = None
            S = cur_sets[j]
            all_cur_member_ids |= S
            if j in claim:
                P = self.prev[oid]
                gone = P - S
                other_pieces = set()
                for n_, j2 in pieces[oid]:
                    if j2 != j:
                        other_pieces |= cur_sets[j2]
                for cid in sorted(gone - other_pieces):
                    if cid in ok_ids:
                        events.append(dict(type='EXTRUSION', org=oid, t=t, k=self.k, cell=int(cid)))
                    else:
                        events.append(dict(type='LOSS', org=oid, t=t, k=self.k, cell=int(cid)))
                for cid in sorted(S - P):
                    if any(cid in self.prev[k2] for k2 in merged_into):   # absorbed by a merge
                        continue
                    events.append(dict(type='ARRIVAL', org=oid, t=t, k=self.k, cell=int(cid),
                                       new=bool(cid not in self.seen)))
            bf = body_frame(xy[idx], lev[idx], self.ch, self.prev_e1.get(oid)) if compute_frame else dict(e1=self.prev_e1.get(oid, np.array([1., 0.])))
            orgs.append(dict(org=oid, members=sorted(int(c) for c in S), idx=idx, frame=bf,
                             unresolved=(oid in unresolved), parent=parent))
            new_prev[oid] = S; new_e1[oid] = bf['e1']
        # organisms that vanish
        for k in org_ids:
            if k not in claimed_org:
                if k in merged_into:
                    events.append(dict(type='END_MERGED', org=k, into=merged_into[k], t=t, k=self.k))
                else:
                    events.append(dict(type='END', org=k, t=t, k=self.k))
                    for cid in sorted(self.prev[k]):
                        events.append(dict(type='LOSS' if cid not in ok_ids else 'EXTRUSION', org=k, t=t,
                                           k=self.k, cell=int(cid)))
        self.seen |= all_cur_member_ids
        self.prev, self.prev_e1 = new_prev, new_e1
        return orgs, events
