"""Stage 6.9 minimal moving-agent extension of the Stage 6.8 flock
(task brief sections 24-26).

EVALUATION-SIDE / SIMULATOR module.

What is kept, unchanged
-----------------------
* discrete four-state cardinal headings (`flock_sim.model.UV4`);
* the existing active-inference heading update -- the SAME precomputed
  `G_table` / `Risk_table` from `flock_sim.active_inference.build_model`, the
  same `policy_posterior`, the same two categorical draws per bird per step;
* the Stage 6.8 FOV rule, `(r_j - r_i) . d_i >= 0`.

What is added, and only this
----------------------------
* continuous positions on a periodic torus `r_i(t) in [0, L)^2`;
* candidate interaction partners are birds within a local radius `R`
  (replacing the lattice's Moore neighbourhood);
* after each heading update, `r_i(t+1) = r_i(t) + v d_i(t+1)  (mod L)`.

No attraction, repulsion, centering or collision term is invented. The
model's existing centering/collision-avoidance physics lives entirely in
`flock_sim.model.SLOT_OVERRIDES` -- the `compAexceps` switch-case that sets
`R[o, s] = -ca` for particular (neighbour-direction, own-heading) pairs -- and
it is reused faithfully by assigning each continuous neighbour to the Moore
SLOT whose direction it falls in:

    slot(i, j) = the octant of (r_j - r_i)

`SLOT_VEC`'s eight directions are exactly the eight octant bisectors, so this
is the natural continuous generalization of "which of my eight neighbours is
this", and it means a bird approaching head-on from the left still incurs the
same `-ca` collision penalty it would have on the lattice. This is the only
new modelling decision in Stage 6.9, and it adds no free parameter.

`R` is chosen so the expected number of candidate partners is on the scale of
the Moore neighbourhood's 8 (see `expected_degree`).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common_69 import ModelParams, UV4
from common_68 import SLOT_VEC
from flock_sim.active_inference import build_model, policy_posterior, sample_categorical_rows

# octant index -> Moore slot id, derived from SLOT_VEC's own directions
_ANG = np.arctan2(SLOT_VEC[:, 1], SLOT_VEC[:, 0]) % (2 * np.pi)
OCTANT_TO_SLOT = np.zeros(8, dtype=int)
for _s in range(8):
    OCTANT_TO_SLOT[int(np.round(_ANG[_s] / (np.pi / 4))) % 8] = _s


@dataclass
class MovingResult:
    r_hist: np.ndarray            # (nt+1, N, 2)
    z_hist: np.ndarray            # (nt+1, N)
    live_hist: list | None        # per-step (recv, src) arrays -- ORACLE, validation only
    params: ModelParams
    seed: int


class MovingFlock:
    def __init__(self, N: int = 400, L: float = 24.0, R: float = 1.6, v: float = 0.5,
                 params: ModelParams | None = None):
        self.N, self.L, self.R, self.v = int(N), float(L), float(R), float(v)
        self.params = params or ModelParams()
        self.pm = build_model(self.params)

    # ------------------------------------------------------------- geometry
    def wrap(self, d: np.ndarray) -> np.ndarray:
        """Minimum-image displacement on the torus."""
        return (d + self.L / 2) % self.L - self.L / 2

    def displacements(self, r: np.ndarray) -> np.ndarray:
        """d[i, j] = r_j - r_i, minimum image."""
        return self.wrap(r[None, :, :] - r[:, None, :])

    def distances(self, r: np.ndarray) -> np.ndarray:
        d = self.displacements(r)
        D = np.sqrt((d ** 2).sum(-1))
        np.fill_diagonal(D, np.inf)
        return D

    def expected_degree(self) -> float:
        """Mean number of candidate partners at uniform density, for comparison
        with the Moore neighbourhood's 8."""
        return (self.N / self.L ** 2) * np.pi * self.R ** 2 - 1.0

    def live_edges(self, r: np.ndarray, z: np.ndarray):
        """Directed live interaction edges (src -> recv): within R AND in the
        receiver's field of view. ORACLE; inference code never calls this."""
        d = self.displacements(r)
        D = np.sqrt((d ** 2).sum(-1))
        np.fill_diagonal(D, np.inf)
        near = D <= self.R
        vis = (d * UV4[z][:, None, :]).sum(-1) >= 0.0
        recv, src = np.nonzero(near & vis)
        return recv, src, d[recv, src]

    # --------------------------------------------------------------- update
    def compute_G(self, r: np.ndarray, z: np.ndarray, live=None) -> np.ndarray:
        recv, src, dvec = self.live_edges(r, z) if live is None else live
        G = np.zeros((self.N, 4))
        if len(recv) == 0:
            return G
        ang = np.arctan2(dvec[:, 1], dvec[:, 0]) % (2 * np.pi)
        slot = OCTANT_TO_SLOT[np.round(ang / (np.pi / 4)).astype(int) % 8]
        contrib = self.pm.G_table[slot, :] + self.pm.Risk_table[slot, :, z[src]]
        np.add.at(G, recv, contrib)
        return G

    # ------------------------------------------------- fixed-position cache
    def position_cache(self, r: np.ndarray) -> dict:
        """Everything about a one-step update that depends on POSITIONS ONLY.

        A one-step probe holds `r` fixed and varies only `z`, so the pairwise
        displacement matrix, the within-radius mask and the octant->slot
        assignment can all be computed once instead of once per rollout. This is
        a pure speedup: `step_cached` is asserted to reproduce `step` exactly in
        tests/test_moving_flock.py.
        """
        d = self.displacements(r)
        D = np.sqrt((d ** 2).sum(-1))
        np.fill_diagonal(D, np.inf)
        ang = np.arctan2(d[..., 1], d[..., 0]) % (2 * np.pi)
        slot = OCTANT_TO_SLOT[np.round(ang / (np.pi / 4)).astype(int) % 8]
        return dict(r=r, d=d, near=(D <= self.R), slot=slot)

    def step_cached(self, cache: dict, z: np.ndarray, rng,
                    forced_actions: dict | None = None):
        """One step from the cached positions. Identical to `step`."""
        from flock_sim.active_inference import policy_posterior, sample_categorical_rows as _s
        d, near, slot = cache["d"], cache["near"], cache["slot"]
        vis = (d * UV4[z][:, None, :]).sum(-1) >= 0.0
        live = near & vis
        recv, src = np.nonzero(live)
        G = np.zeros((self.N, 4))
        if len(recv):
            sl = slot[recv, src]
            np.add.at(G, recv, self.pm.G_table[sl, :] + self.pm.Risk_table[sl, :, z[src]])
        ut = policy_posterior(self.pm, G)
        applied = _s(ut, rng)
        if forced_actions:
            for b, a in forced_actions.items():
                applied[int(b)] = int(a)
        z_new = _s(self.pm.Bu[:, applied].T, rng)
        r_new = (cache["r"] + self.v * UV4[z_new]) % self.L
        return r_new, z_new, (recv, src)

    def step(self, r, z, rng, forced_actions: dict | None = None):
        recv, src, dvec = self.live_edges(r, z)
        G = self.compute_G(r, z, (recv, src, dvec))
        ut = policy_posterior(self.pm, G)
        action = sample_categorical_rows(ut, rng)
        applied = action.copy()
        if forced_actions:
            for b, a in forced_actions.items():
                applied[int(b)] = int(a)
        z_new = sample_categorical_rows(self.pm.Bu[:, applied].T, rng)
        r_new = (r + self.v * UV4[z_new]) % self.L
        return r_new, z_new, (recv, src)

    def run(self, nt: int = 160, seed: int = 0, interventions: dict | None = None,
            record_oracle: bool = False) -> MovingResult:
        rng = np.random.default_rng(seed)
        r = rng.random((self.N, 2)) * self.L
        z = rng.integers(0, 4, self.N)
        R_ = np.zeros((nt + 1, self.N, 2)); R_[0] = r
        Z_ = np.zeros((nt + 1, self.N), dtype=int); Z_[0] = z
        live = [] if record_oracle else None
        interventions = interventions or {}
        for t in range(nt):
            r, z, ed = self.step(r, z, rng, interventions.get(t))
            R_[t + 1], Z_[t + 1] = r, z
            if live is not None:
                live.append(ed)
        return MovingResult(r_hist=R_, z_hist=Z_, live_hist=live, params=self.params, seed=seed)

    # ------------------------------------------- oracle interface accessors
    def oracle_B_D(self, r, z, I) -> np.ndarray:
        """B_t^D = {j not in I : j -> i for some i in I}. ORACLE only."""
        recv, src, _ = self.live_edges(r, z)
        Iset = set(int(x) for x in I)
        sel = np.isin(recv, list(Iset))
        return np.array(sorted({int(j) for j in src[sel] if int(j) not in Iset}), dtype=int)
