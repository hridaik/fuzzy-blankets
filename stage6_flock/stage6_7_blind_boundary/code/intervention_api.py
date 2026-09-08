"""EVALUATION-SIDE MODULE. Wraps stage6_5's exact (non-Monte-Carlo)
counterfactual propagator (`stage6_5/refinement/causal_redundancy/code/
exact_intervention.py`) behind a black-box intervention API, per task brief
section 12: "Use the existing exact counterfactual propagator if available,
but wrap it as a black-box intervention API. The inference code must not
inspect which neighbours the simulator used internally."

`InterventionOracle.do(...)` returns ONLY the numeric intervention effect
(joint KL over the interior's one-step distribution, and its per-target-bird
breakdown -- exactly `C_{j->i}^do`, task brief section 13). It deliberately
does NOT pass through `exact_intervention.interior_do_kl`'s
`n_neighboring_interior` field, which is topology-derived and would leak the
true graph to any inference-side caller holding a reference to this object.
`causal_discovery.py` (inference-side) receives an `InterventionOracle`
instance purely as a duck-typed callable and never imports `flock_sim` or
the lattice itself.
"""
from __future__ import annotations

import numpy as np

from exact_intervention import default_precomputed_model, interior_do_kl
from common_67 import lattice_100


class InterventionOracle:
    def __init__(self, pm=None, lattice=None):
        self.pm = pm or default_precomputed_model()
        self._lattice = lattice if lattice is not None else lattice_100()

    def do(self, I, j: int, z_prime: int, X_t: np.ndarray) -> dict:
        """I: interior bird ids. j: source bird id being intervened on.
        z_prime: alternative heading forced onto bird j. X_t: (n_bird,)
        current heading array (an OBSERVED state, drawn from the passive
        trajectory data -- never a simulator-internal privileged state).
        Returns dict(D_do_joint: float, per_bird_kl: {i: float}) -- nothing
        else."""
        res = interior_do_kl(self.pm, self._lattice, np.asarray(X_t), np.asarray(sorted(int(i) for i in I)),
                              int(j), int(z_prime))
        return dict(D_do_joint=res["D_do_joint"], per_bird_kl=res["per_bird_kl"])
