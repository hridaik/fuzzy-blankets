"""Stage 6.10 Part G -- the standardized weak directional probe and the
susceptibility curve chi_tau.

Used ONLY for regime characterization. It is not a controller, it is never
scored for success, and no controller comparison may use it. Its job is to
answer one question about a candidate operating regime:

    if you nudge this collective weakly through its own exterior, does anything
    measurable happen -- and does the response still have headroom, or is it
    already saturated?

Probe: draw `k` birds uniformly from the candidate's exact causal interface,
force them to `h*` for ONE step, and measure the change in target alignment at
horizon tau against a common-random-number baseline. Averaged over independent
probe draws.

Reporting chi at several k gives the susceptibility CURVE, which is what
distinguishes "responsive" from "saturated": a saturated regime's chi is flat
in k (nothing moves) and a locked-in regime's chi jumps to its ceiling at the
smallest k.
"""
from __future__ import annotations

import numpy as np

import reference_truth as rt

PROBE_KS = (2, 4, 8, 16)
PROBE_DRAWS = 6
PROBE_TAU = 4
PROBE_ROLL = 96


def susceptibility(sim, z, I, h_star, interface, ks=PROBE_KS, draws=PROBE_DRAWS,
                   tau=PROBE_TAU, n_roll=PROBE_ROLL, seed=0):
    """chi_tau(k): mean gain in target alignment from forcing k random interface
    birds to h* for one step. Returns the curve and its saturation diagnostics."""
    interface = [int(j) for j in interface]
    if not interface:
        return dict(curve={}, chi_max=0.0, saturating=None, n_interface=0)
    rng = np.random.default_rng(seed)
    base = rt.rollout_alignment(sim, z, I, h_star, tau, [], seed, n_roll)
    curve = {}
    for k in ks:
        if k > len(interface):
            continue
        vals = []
        for d in range(draws):
            S = rng.choice(interface, size=k, replace=False)
            vals.append(rt.rollout_alignment(sim, z, I, h_star, tau, S, seed, n_roll) - base)
        curve[k] = dict(mean=float(np.mean(vals)), sd=float(np.std(vals)), n=len(vals))
    if not curve:
        return dict(curve={}, chi_max=0.0, saturating=None, n_interface=len(interface))
    ks_sorted = sorted(curve)
    means = [curve[k]["mean"] for k in ks_sorted]
    chi_max = float(max(means))
    # "saturating" == the curve has stopped rising: the last increment adds
    # less than 15% of the total. Flat-at-zero is reported separately as dead.
    rising = means[-1] - means[-2] if len(means) > 1 else float("nan")
    return dict(curve={str(k): curve[k] for k in ks_sorted},
                baseline=float(base), chi_max=chi_max,
                last_increment=float(rising) if rising == rising else None,
                dead=bool(chi_max < 0.01),
                saturating=bool(chi_max > 0.01 and rising < 0.15 * chi_max)
                if rising == rising else None,
                n_interface=len(interface))


def policy_saturation(sim, z) -> dict:
    """How numerically locked is the decision rule at this state? A regime where
    almost every bird's policy posterior is 1.0 to machine precision cannot be
    steered by anything, which is what Stage 6.8's operating point turned out
    to be (88.7% locked)."""
    from common_610 import policy_posterior
    G = sim.compute_G_masked(np.asarray(z), sim.visible_mask(np.asarray(z)))
    ut = policy_posterior(sim.pm, G)
    mx = ut.max(axis=1)
    gs = np.sort(G, axis=1)
    return dict(frac_locked=float(np.mean(mx > 0.999)),
                median_max_ut=float(np.median(mx)),
                median_G_gap=float(np.median(gs[:, -1] - gs[:, -2])))
