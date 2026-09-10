"""Stage 6.11 moving flock: Stage 6.9's simulator plus two independently
switchable MODELLING ASSUMPTIONS (PLAN.md sections M and N).

EVALUATION-SIDE / SIMULATOR module.

`MovingFlock611` subclasses Stage 6.9's `MovingFlock`. Stage 6.9's file is not
touched. With both new flags at their defaults

    MovingFlock611(social="raw", cohesion=0.0)

every arithmetic operation performed is the one Stage 6.9 performs, in the same
order, consuming the RNG in the same order, so the default path reproduces
Stage 6.9 bit-for-bit. That equivalence is asserted in
`tests/test_moving_flock_611.py` and measured in `run_model_validation.py`;
it is the reason both additions are opt-in rather than folded in.

Neither addition is a bug fix and neither is presented as one. Both are
declared here, in advance of any Stage 6.11 experiment, and both keep the
Stage 6.9 behaviour alive as the comparator.

--------------------------------------------------------------------------
ADDITION 1 -- degree-normalized social evidence   (PLAN.md section N)
--------------------------------------------------------------------------
Stage 6.9 forms a bird's expected free energy as a RAW SUM over live partners,

    G_i(a) = sum_{j in N_i} g_ij(a),          g_ij = G_table + Risk_table

so the spread of G across the four actions -- and therefore the sharpness of
`policy_posterior` -- grows roughly linearly in |N_i|. That conflates two
things a flock model normally separates: how far a bird interacts (a spatial
scale) and how certain its decisions are (a gain). Stage 6.9's record is the
concrete cost: the only radius at which a translating collective cohered gave
in-degree 21.2, and at that degree 77% of interior birds had max(u_t) == 1.0
to double precision and the causal interface collapsed to 1 live channel of 47.

`social="normalized"` replaces the raw sum with the DEGREE MEAN, restored to a
reference scale:

    G_i(a) = (k_ref / |N_i|) * sum_{j in N_i} g_ij(a)

`k_ref` is the constant left free by section N's "proportional to". It is set
to 8.0 -- the size of the Moore neighbourhood that the frozen `base_R` /
`neighbor_R` / `SLOT_OVERRIDES` matrices were written against -- so that a bird
carrying the model's own design degree sees the model's own design gain. It is
fixed a priori by that argument and is NOT tuned on any outcome; `k_ref = 1`
(the bare mean) is available via `social_ref_degree` for anyone who wants the
unscaled form, and both are measured in `logs/model_validation_611.txt`.

Birds with no live partner keep G = 0 under both variants, exactly as before.

--------------------------------------------------------------------------
ADDITION 2 -- positional cohesion                 (PLAN.md section M)
--------------------------------------------------------------------------
The Section M audit (`logs/moving_model_audit.txt`) found alignment (`vm` on
the diagonal of `base_R`) and separation (`-ca` via `SLOT_OVERRIDES`) present,
and found NO term depending on a neighbour's POSITION: `base_R` is built from
`UV4 @ UV4.T`, an inner product of HEADING vectors, and the only positional
information Stage 6.9 uses is which octant a partner occupies, consumed by the
separation term. A bird whose partners are all to its north therefore has no
preference to move north. On the fixed lattice that gap is unobservable
because positions never change; it becomes load-bearing the moment birds
translate.

`cohesion=fc_pos > 0.0` adds the missing term, and adds it ONCE, as a
per-partner preference contribution over the same four headings, entering the
same accumulation as `G_table`/`Risk_table` -- not as a position nudge applied
after the heading is drawn:

    g^pos_ij(a) = 2 * fc_pos * < UV4[a], (r_j - r_i)/||r_j - r_i|| >

Three deliberate choices, each of which avoids a new free parameter:

* the direction is UNIT-normalized, so the term carries no distance scale of
  its own and cannot be dominated by the farthest partner; the interaction
  range stays entirely in `R`;
* summed over partners this is fc_pos * <UV4[a], sum of unit bearings>, which
  is maximal for the heading pointing at the local centre of mass -- the
  centering force the audit found missing, and nothing else;
* the factor 2 matches the two-lookahead-step doubling that
  `build_model` applies to every other per-edge contribution
  (`G_table = 2*amb`, `Risk_table = 2*risk`), so `fc_pos` is expressed in the
  same expected-free-energy units as the terms it sits beside.

Its functional form deliberately mirrors the existing off-diagonal alignment
term `fc * <UV4[a], UV4[z_j]>`, with the bearing to the partner in place of the
partner's heading. `fc_pos` is the ONLY new number, and it is swept and
reported rather than chosen.

Under `social="normalized"` the cohesion term is normalized with the rest: it
is per-partner social evidence like any other, and exempting it would put the
degree dependence straight back into G.

--------------------------------------------------------------------------
WHAT IS NOT ADDED
--------------------------------------------------------------------------
Neither term references a global direction, an absolute position, a bird index,
a group label, or a target. Both are functions of relative displacements and
neighbours' headings only, so both are isotropic (equivariant under the 90-
degree rotations that map the four-heading lattice onto itself) and agent-local
(equivariant under relabelling of birds). Both properties are asserted as
tests rather than claimed here.
"""
from __future__ import annotations

import numpy as np

from common_611 import UV4                     # noqa: F401  (path bootstrap)
from moving_flock import MovingFlock, OCTANT_TO_SLOT, MovingResult  # noqa: F401
from flock_sim.active_inference import policy_posterior, sample_categorical_rows

SOCIAL_MODES = ("raw", "normalized")

# Size of the Moore neighbourhood the frozen R matrices were designed against.
# See ADDITION 1: this is section N's proportionality constant, fixed a priori.
MOORE_DEGREE = 8.0


class MovingFlock611(MovingFlock):
    """Stage 6.9's moving flock with section M/N terms available but off.

    Parameters
    ----------
    social : {"raw", "normalized"}
        "raw" (default) is Stage 6.9's sum over live partners. "normalized"
        divides by the live in-degree and rescales by `social_ref_degree`.
    social_ref_degree : float
        `k_ref` in ADDITION 1. Only consulted when `social="normalized"`.
    cohesion : float
        `fc_pos` in ADDITION 2. 0.0 (default) disables the term entirely --
        no branch of the arithmetic runs, which is what makes the default path
        bit-for-bit equal to Stage 6.9.
    """

    def __init__(self, N: int = 400, L: float = 24.0, R: float = 1.6, v: float = 0.5,
                 params=None, *, social: str = "raw",
                 social_ref_degree: float = MOORE_DEGREE, cohesion: float = 0.0):
        if social not in SOCIAL_MODES:
            raise ValueError(f"social must be one of {SOCIAL_MODES}, got {social!r}")
        if cohesion < 0.0:
            raise ValueError("cohesion (fc_pos) must be >= 0")
        super().__init__(N=N, L=L, R=R, v=v, params=params)
        self.social = social
        self.social_ref_degree = float(social_ref_degree)
        self.cohesion = float(cohesion)

    # ------------------------------------------------------------------ core
    def _accumulate_G(self, recv, src, dvec, slot, z) -> np.ndarray:
        """Assemble G from an already-resolved live edge list.

        The `social == "raw" and cohesion == 0` path below is Stage 6.9's
        `compute_G` body verbatim, with no extra floating-point operation
        touching it, so the default reproduces 6.9 exactly rather than
        approximately.
        """
        G = np.zeros((self.N, 4))
        if len(recv) == 0:
            return G
        contrib = self.pm.G_table[slot, :] + self.pm.Risk_table[slot, :, z[src]]
        if self.cohesion > 0.0:
            # bearing to the partner, unit-normalized; the tiny epsilon only
            # guards exact coincidence, which the dynamics never produce but a
            # hand-built test configuration can.
            nrm = np.sqrt((dvec ** 2).sum(-1))
            bearing = dvec / np.maximum(nrm, 1e-12)[:, None]
            contrib = contrib + (2.0 * self.cohesion) * (bearing @ UV4.T)
        np.add.at(G, recv, contrib)
        if self.social == "normalized":
            deg = np.bincount(recv, minlength=self.N).astype(float)
            # degree 0 rows already have G = 0; leave them untouched rather
            # than dividing, so "no partners" stays "no evidence".
            nz = deg > 0
            G[nz] *= self.social_ref_degree / deg[nz][:, None]
        return G

    @staticmethod
    def _slots_from_dvec(dvec: np.ndarray) -> np.ndarray:
        ang = np.arctan2(dvec[:, 1], dvec[:, 0]) % (2 * np.pi)
        return OCTANT_TO_SLOT[np.round(ang / (np.pi / 4)).astype(int) % 8]

    def compute_G(self, r: np.ndarray, z: np.ndarray, live=None) -> np.ndarray:
        recv, src, dvec = self.live_edges(r, z) if live is None else live
        if len(recv) == 0:
            return np.zeros((self.N, 4))
        return self._accumulate_G(recv, src, dvec, self._slots_from_dvec(dvec), z)

    # `step` is inherited unchanged: it calls self.compute_G and then draws
    # exactly the two RNG samples Stage 6.9 draws, in the same order.

    def step_cached(self, cache: dict, z: np.ndarray, rng,
                    forced_actions: dict | None = None):
        """One step from a fixed-position cache. Identical to `step`."""
        d, near, slot = cache["d"], cache["near"], cache["slot"]
        vis = (d * UV4[z][:, None, :]).sum(-1) >= 0.0
        recv, src = np.nonzero(near & vis)
        G = self._accumulate_G(recv, src, d[recv, src], slot[recv, src], z)
        ut = policy_posterior(self.pm, G)
        applied = sample_categorical_rows(ut, rng)
        if forced_actions:
            for b, a in forced_actions.items():
                applied[int(b)] = int(a)
        z_new = sample_categorical_rows(self.pm.Bu[:, applied].T, rng)
        r_new = (cache["r"] + self.v * UV4[z_new]) % self.L
        return r_new, z_new, (recv, src)

    # ----------------------------------------------------------- diagnostics
    def in_degree(self, r: np.ndarray, z: np.ndarray) -> np.ndarray:
        """Live in-degree per bird (partners actually entering its G)."""
        recv, _, _ = self.live_edges(r, z)
        return np.bincount(recv, minlength=self.N)

    def policy(self, r: np.ndarray, z: np.ndarray) -> np.ndarray:
        """The policy posterior u_t this configuration produces. Diagnostic
        only -- `step` recomputes it, it is not cached."""
        return policy_posterior(self.pm, self.compute_G(r, z))


def describe(mf: MovingFlock611) -> str:
    return (f"MovingFlock611(N={mf.N}, L={mf.L}, R={mf.R}, v={mf.v}, "
            f"social={mf.social!r}, k_ref={mf.social_ref_degree}, "
            f"cohesion={mf.cohesion})")
