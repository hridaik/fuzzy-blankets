"""Section 17 of the task brief: recompute G_blind, L_blind for the 300
primary candidates using Bhat^pred(I) in place of Stage 6.6's oracle-
S(I)-constrained B*, so the (C,G,L,D) landscape coordinates can be compared
oracle-vs-blind. Uses `blind_cache.py` (unrestricted conditioning masks), NOT
`stage6_6_collective_landscape/code/predictive_cache.py` (which intersects
every mask with the bird's TRUE lattice neighbours and would silently drop
any false-positive member of Bhat^pred before scoring it).

Definitions (mirroring stage6_6/code/predictive_cache.py's G_i/L_i, but with
"full" redefined as M_all = all observed exterior birds, since a fully-blind
pipeline has no oracle-restricted "true full neighbour set" to fall back on
-- this IS exactly section 7's Delta-ell(Bhat), applied per-bird before
averaging):

  G_blind_i = ell_i(Bhat)      - ell_i(I union Bhat)
  L_blind_i = ell_i(I union Bhat) - ell_i(M_all)

C, D are read verbatim from Stage 6.6's existing rows (unchanged, per the
brief) -- this module does not recompute them.
"""
from __future__ import annotations

import numpy as np

from blind_cache import BlindCache, clamp_machine_eps


def blind_G_and_L(cache: BlindCache, I, B_hat, n_bird: int) -> dict:
    I_sorted = sorted(int(x) for x in I)
    I_set = set(I_sorted)
    B_sorted = sorted(int(b) for b in B_hat)
    all_exterior = [j for j in range(n_bird) if j not in I_set]

    per_bird = {}
    for i in I_sorted:
        ell_B = cache.get_loss(i, B_sorted)
        ell_IB = cache.get_loss(i, sorted(I_set | set(B_sorted)))
        ell_full = cache.get_loss(i, all_exterior)
        per_bird[i] = dict(G_i=clamp_machine_eps(ell_B - ell_IB), L_i=clamp_machine_eps(ell_IB - ell_full))

    G_blind = float(np.mean([v["G_i"] for v in per_bird.values()]))
    L_blind = float(np.mean([v["L_i"] for v in per_bird.values()]))
    n_negative_G = sum(1 for v in per_bird.values() if v["G_i"] < 0)
    n_negative_L = sum(1 for v in per_bird.values() if v["L_i"] < 0)
    return dict(G_blind=G_blind, L_blind=L_blind, per_bird=per_bird,
                n_negative_G_i=n_negative_G, n_negative_L_i=n_negative_L)
