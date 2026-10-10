"""Stage 6.8 L2/L3 simulator: heading-dependent field of view, and (L3)
persistent stochastic gating of the visible directed edges.

EVALUATION-SIDE / SIMULATOR module. This *is* the ground truth; inference code
must never import it (enforced by tests/test_no_topology_leakage_68.py).

Relationship to the frozen Stage 6-6.7 model
--------------------------------------------
`flock_sim.active_inference.compute_G` computes, for every bird i,

    G[i, a] = sum over Moore neighbours j of
              ( G_table[slot(i,j), a] + Risk_table[slot(i,j), a, z_j] )

`compute_G_fov` below is that same sum restricted to a per-timestep edge mask.
With an all-ones mask it is numerically identical to `compute_G` (asserted in
tests/test_fov_reduces_to_l0.py), so L2 is a strict, transparent restriction of
the frozen model -- not a reparameterization of it. Nothing in `python/` is
modified or re-fit.

L2 -- field of view (task brief section 3)
------------------------------------------
Bird i sees geometric Moore neighbour j iff

    (r_j - r_i) . d_i(t) >= 0

with d_i(t) the receiver's CURRENT cardinal heading. The three Moore
neighbours strictly behind i are excluded. The resulting relation is directed
(`j -> i` means "j enters i's next-state update") and is NOT symmetrized.
At lattice boundaries only the geometrically available neighbours are used.

Note the mechanism this introduces, which L0/L1 lack entirely: in the frozen
model `compute_G` never reads `z[i]`, so a bird's next heading is independent
of its own current heading. Under FOV, `z[i]` selects *which* sources are live.
The interaction interface therefore becomes state-dependent, which is the
whole point of Stage 6.8.

L3 -- persistent stochastic edge availability (task brief section 5)
--------------------------------------------------------------------
    A_{j->i}(t) = V_{j->i}(t) * G_{j->i}(t)

with V the deterministic FOV visibility above and G an independent two-state
Markov process per DIRECTED Moore edge (off->on w.p. p01, on->off w.p. p10),
evolving whether or not the edge is currently visible (it is a property of the
channel, not of the geometry). Stationary on-probability p01/(p01+p10); mean
on-run 1/p10, mean off-run 1/p01.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common_68 import (ModelParams, Lattice, build_model, flatten_edges,
                       visibility_table, lattice_positions, NU)
from flock_sim.active_inference import policy_posterior, sample_categorical_rows
from flock_sim.simulation import init_headings


@dataclass
class GateParams:
    """Two-state Markov gate on each directed Moore edge (L3 only)."""
    p01: float          # P(off -> on)
    p10: float          # P(on  -> off)

    @property
    def stationary_on(self) -> float:
        return self.p01 / (self.p01 + self.p10)

    @property
    def mean_on_run(self) -> float:
        return 1.0 / self.p10

    @property
    def mean_off_run(self) -> float:
        return 1.0 / self.p01


@dataclass
class FovResult:
    z_hist: np.ndarray               # (nt+1, nn)
    natural_action_hist: np.ndarray  # (nt, nn)
    applied_action_hist: np.ndarray  # (nt, nn)
    overridden_hist: np.ndarray      # (nt, nn) bool
    active_mask_hist: np.ndarray | None   # (nt+1, E) bool -- ORACLE, validation only
    gate_hist: np.ndarray | None          # (nt+1, E) bool -- ORACLE, validation only
    n_blind_birds: np.ndarray        # (nt+1,) birds with zero live in-edges
    edges: tuple                     # (recv, slot, src)
    params: ModelParams
    gate_params: GateParams | None
    seed: int


class FovSimulator:
    """Holds everything static: lattice, precomputed model tables, edge list,
    visibility table, positions."""

    def __init__(self, params: ModelParams | None = None, lattice: Lattice | None = None,
                 nn: int = 100):
        self.params = params or ModelParams()
        self.lattice = lattice or Lattice(nn=nn, nh=8)
        self.nn = self.lattice.nn
        self.pm = build_model(self.params)
        self.recv, self.slot, self.src = flatten_edges(self.lattice)
        self.n_edges = len(self.recv)
        self.VIS = visibility_table()                   # (8, 4)
        self.positions = lattice_positions(self.nn)

    # ------------------------------------------------------------------ core
    def visible_mask(self, z: np.ndarray) -> np.ndarray:
        """(E,) bool: FOV visibility of every directed edge at this state."""
        return self.VIS[self.slot, z[self.recv]]

    def compute_G_masked(self, z: np.ndarray, edge_mask: np.ndarray) -> np.ndarray:
        pm = self.pm
        contrib = pm.G_table[self.slot, :] + pm.Risk_table[self.slot, :, z[self.src]]  # (E, nu)
        contrib = contrib * edge_mask[:, None]
        G = np.zeros((self.nn, NU))
        np.add.at(G, self.recv, contrib)
        return G

    # -------------------------------------------------------------- rollouts
    def next_state_dist(self, z: np.ndarray, edge_mask: np.ndarray) -> np.ndarray:
        """Exact one-step next-heading marginals, (nn, nu). Same derivation as
        stage6_5's `exact_intervention.next_heading_dist_all`, restricted to the
        masked edge set: actions are sampled independently across birds given
        z_t, and Bu does not depend on z_t."""
        G = self.compute_G_masked(z, edge_mask)
        ut = policy_posterior(self.pm, G)
        return ut @ self.pm.Bu.T

    def step(self, z: np.ndarray, rng: np.random.Generator, gate: np.ndarray | None = None,
             forced_actions: dict[int, int] | None = None):
        vis = self.visible_mask(z)
        mask = vis if gate is None else (vis & gate)
        G = self.compute_G_masked(z, mask)
        ut = policy_posterior(self.pm, G)
        natural_action = sample_categorical_rows(ut, rng)
        applied = natural_action.copy()
        overridden = np.zeros(self.nn, dtype=bool)
        if forced_actions:
            for b, a in forced_actions.items():
                applied[int(b)] = int(a)
                overridden[int(b)] = True
        z_new = sample_categorical_rows(self.pm.Bu[:, applied].T, rng)
        n_blind = int(np.sum(np.bincount(self.recv, weights=mask.astype(float),
                                         minlength=self.nn) == 0))
        return dict(z_new=z_new, natural_action=natural_action, applied_action=applied,
                    was_overridden=overridden, active_mask=mask, n_blind=n_blind)

    def advance_gates(self, gate: np.ndarray, gp: GateParams, rng: np.random.Generator) -> np.ndarray:
        u = rng.random(self.n_edges)
        flip_on = (~gate) & (u < gp.p01)
        flip_off = gate & (u < gp.p10)
        out = gate.copy()
        out[flip_on] = True
        out[flip_off] = False
        return out

    def init_gates(self, gp: GateParams, rng: np.random.Generator) -> np.ndarray:
        return rng.random(self.n_edges) < gp.stationary_on

    # ------------------------------------------------------------------- run
    def run(self, nt: int = 120, seed: int = 0, init_z: np.ndarray | None = None,
            gate_params: GateParams | None = None,
            interventions: dict | None = None,
            record_oracle: bool = False) -> FovResult:
        rng = np.random.default_rng(seed)
        z = init_z.copy() if init_z is not None else init_headings(self.nn, NU, rng)
        gate = self.init_gates(gate_params, rng) if gate_params is not None else None

        z_hist = np.zeros((nt + 1, self.nn), dtype=int); z_hist[0] = z
        nat = np.zeros((nt, self.nn), dtype=int)
        app = np.zeros((nt, self.nn), dtype=int)
        ovr = np.zeros((nt, self.nn), dtype=bool)
        blind = np.zeros(nt + 1, dtype=int)
        amask = np.zeros((nt + 1, self.n_edges), dtype=bool) if record_oracle else None
        ghist = np.zeros((nt + 1, self.n_edges), dtype=bool) if (record_oracle and gate is not None) else None

        interventions = interventions or {}
        for t in range(nt):
            out = self.step(z, rng, gate=gate, forced_actions=interventions.get(t))
            if record_oracle:
                amask[t] = out["active_mask"]
                if ghist is not None:
                    ghist[t] = gate
            blind[t] = out["n_blind"]
            z = out["z_new"]
            z_hist[t + 1] = z
            nat[t], app[t], ovr[t] = out["natural_action"], out["applied_action"], out["was_overridden"]
            if gate is not None:
                gate = self.advance_gates(gate, gate_params, rng)
        if record_oracle:
            vis = self.visible_mask(z)
            amask[nt] = vis if gate is None else (vis & gate)
            if ghist is not None:
                ghist[nt] = gate
            blind[nt] = int(np.sum(np.bincount(self.recv, weights=amask[nt].astype(float),
                                               minlength=self.nn) == 0))
        return FovResult(z_hist=z_hist, natural_action_hist=nat, applied_action_hist=app,
                         overridden_hist=ovr, active_mask_hist=amask, gate_hist=ghist,
                         n_blind_birds=blind, edges=(self.recv, self.slot, self.src),
                         params=self.params, gate_params=gate_params, seed=seed)

    # ---------------------------------------------- oracle graph accessors --
    def active_in_edges(self, active_mask: np.ndarray, i: int) -> np.ndarray:
        """Sources j with a live edge j -> i. ORACLE; validation code only."""
        sel = (self.recv == i) & active_mask
        return np.unique(self.src[sel])

    def oracle_B_D(self, active_mask: np.ndarray, I: np.ndarray) -> np.ndarray:
        """B_t^D = {j not in I : j -> i for some i in I} (task brief section 4).
        ORACLE; validation code only."""
        Iset = set(int(x) for x in I)
        sel = active_mask & np.isin(self.recv, list(Iset))
        return np.array(sorted({int(j) for j in self.src[sel] if j not in Iset}), dtype=int)
