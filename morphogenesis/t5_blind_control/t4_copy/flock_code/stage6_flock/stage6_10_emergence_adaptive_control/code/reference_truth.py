"""Stage 6.10 Part B -- three INDEPENDENT reference/truth modules.

EVALUATION-SIDE. These are the reference layer the whole stage is judged
against, so the first two are written to be independent implementations of the
same object and are cross-validated in tests/test_reference_truth.py. If they
disagree materially the stage stops.

  1. structural_interface   B_t^struct(I)  -- read from the simulator's
     transition dependencies (which sources enter which bird's update).
  2. exact_do_interface     B_{t,eps}^do   -- computed WITHOUT the structural
     graph, by perturbing every exterior source through all admissible headings
     and comparing exact next-state distributions.
  3. task_authority         A_j^{h*,tau}   -- expected change in TARGET
     ALIGNMENT at horizon tau under do(u_j = h*), plus pair terms S_jk.

(3) is deliberately not a function of (1) or (2): a large KL influence is a
statement about how much a source perturbs the interior's distribution in ANY
direction, and says nothing about whether it moves the interior TOWARD the
target. Stage 6.8's `adaptive_oracle` conflated the two; keeping them separate
here is the point of the module.
"""
from __future__ import annotations

import numpy as np

from common_610 import NU, UV4, policy_posterior

EPS_DEFAULT = 1e-9


# ------------------------------------------------- batched CRN rollouts -----
def _batched_G(sim, Z):
    """Expected free energy for a BATCH of states. Z: (R, nn) -> (R, nn, NU).
    The same masked sum as `FovSimulator.compute_G_masked`, vectorised over the
    rollout axis so one subset evaluation is a single numpy pass instead of R
    sequential simulator steps."""
    R, nn = Z.shape
    recv, slot, src = sim.recv, sim.slot, sim.src
    E = len(recv)
    vis = sim.VIS[slot[None, :], Z[:, recv]]                     # (R, E)
    contrib = sim.pm.G_table[slot][None, :, :] \
        + sim.pm.Risk_table[slot[None, :], :, Z[:, src]]         # (R, E, NU)
    contrib *= vis[:, :, None]
    # scatter-add by bincount, which is far faster than np.add.at here
    flat = (np.arange(R)[:, None] * nn + recv[None, :]).ravel()
    G = np.empty((R * nn, NU))
    for c in range(NU):
        G[:, c] = np.bincount(flat, weights=contrib[:, :, c].ravel(), minlength=R * nn)
    return G.reshape(R, nn, NU)


def _sample_u(probs, u):
    """Categorical sampling from PRE-DRAWN uniforms -- the mechanism that makes
    common random numbers exact: the same `u` is reused for the baseline and for
    every candidate actuator subset evaluated at a given state."""
    cdf = np.cumsum(probs, axis=-1)
    cdf[..., -1] = 1.0
    return (u[..., None] > cdf).sum(-1).clip(max=probs.shape[-1] - 1)


def rollout_alignment(sim, z, I, h_star, tau, forced, seed, n_roll, hold=1):
    """E[H*(I, t+tau)] under do(u_j = h* for j in `forced`), by batched rollout
    under common random numbers.

    `hold` is how many leading rollout steps the intervention is applied for.

      hold = 1    a ONE-SHOT intervention: force at t, then release. This is the
                  definition of task authority A_j^{h*,tau}, and it is the
                  default, so Part B's authority numbers are unaffected by
                  anything below.
      hold = tau  the actuators are HELD for the whole planning horizon. This is
                  what a controller actually does -- `sim.step` is called with
                  `forced_actions` on every step between re-plans -- so a
                  benchmark that optimizes the objective must model it this way.
                  Planning with hold=1 while executing with hold=tau makes the
                  benchmark strictly weaker than the controller it represents,
                  which would bias a controllability gate toward declaring tasks
                  unsteerable.
    """
    z = np.asarray(z); I = np.asarray(sorted(int(x) for x in I))
    nn = sim.nn
    U = np.random.default_rng(seed).random((tau, 2, n_roll, nn))
    Z = np.tile(z, (n_roll, 1))
    f = np.asarray(sorted(int(x) for x in forced), dtype=int) if len(forced) else None
    for s in range(tau):
        G = _batched_G(sim, Z)
        ut = policy_posterior(sim.pm, G.reshape(-1, NU)).reshape(n_roll, nn, NU)
        a = _sample_u(ut, U[s, 0])
        if s < hold and f is not None:
            a[:, f] = int(h_star)
        Z = _sample_u(sim.pm.Bu.T[a], U[s, 1])
    return float((Z[:, I] == int(h_star)).mean())


# ---------------------------------------------------------------- (1) ------
def structural_interface(sim, z, I) -> np.ndarray:
    """B_t^struct(I): exterior sources that ENTER some interior bird's update.

    Read straight off the simulator's dependency structure -- the live edge
    mask -- with no interventional computation of any kind.
    """
    I = np.asarray(sorted(int(x) for x in I))
    mask = sim.visible_mask(np.asarray(z))
    return sim.oracle_B_D(mask, I)


# ---------------------------------------------------------------- (2) ------
def _next_dist(sim, z):
    """Exact one-step next-heading marginals for every bird, (nn, NU)."""
    z = np.asarray(z)
    G = sim.compute_G_masked(z, sim.visible_mask(z))
    return policy_posterior(sim.pm, G) @ sim.pm.Bu.T


def do_influence(sim, z, I, j, agg="mean") -> tuple[float, dict]:
    """C^do_{j->i}(x_t): exact KL of the interior's one-step marginals under
    do(z_j = z'), averaged over all admissible z' != z_j.

    Computed only from next-state distributions -- the structural graph is
    never consulted.
    """
    z = np.asarray(z)
    I = np.asarray(sorted(int(x) for x in I))
    base = _next_dist(sim, z)[I]
    alts = [h for h in range(NU) if h != int(z[int(j)])]
    acc = np.zeros(len(I))
    for zp in alts:
        zd = z.copy(); zd[int(j)] = zp
        p = _next_dist(sim, zd)[I]
        acc += (p * (np.log(np.clip(p, 1e-300, 1)) - np.log(np.clip(base, 1e-300, 1)))).sum(1)
    acc /= len(alts)
    per = {int(i): float(v) for i, v in zip(I, acc)}
    return (float(acc.sum()) if agg == "sum" else float(acc.mean())), per


def exact_do_interface(sim, z, I, candidates=None, eps=EPS_DEFAULT):
    """B_{t,eps}^do: exterior sources whose exact one-step interventional effect
    on the interior exceeds eps. No structural information is used."""
    z = np.asarray(z)
    Iset = set(int(x) for x in I)
    cands = [j for j in range(sim.nn) if j not in Iset] if candidates is None \
        else [int(j) for j in candidates if int(j) not in Iset]
    vals = {}
    for j in cands:
        tot, _ = do_influence(sim, z, I, j, agg="sum")
        vals[int(j)] = tot
    return np.array(sorted(j for j, v in vals.items() if v > eps), dtype=int), vals


# ---------------------------------------------------------------- (3) ------
def _expected_alignment_after(sim, z, I, h_star, tau, forced, rng_seed, n_roll,
                              hold=1):
    """E[H*(I, t+tau)] under do(u_j = h_star for j in `forced`).

    ACTION SEMANTICS, and they matter for the whole audit. The controller sets a
    bird's ACTION at time t (`forced_actions`), which fixes that bird's HEADING
    at t+1. An interior bird's heading at t+1 is computed from the state at t,
    so forcing an EXTERIOR bird cannot change the interior at t+1 at all:

        A_j^{h*, tau=1} == 0 exactly, for every exterior j.

    The first horizon at which an exterior actuator can move the interior is
    tau = 2. This is a structural fact about the model, asserted in
    tests/test_reference_truth.py, and it is the reason a ONE-STEP influence
    score cannot by itself be a task-authority score for an exterior actuator.

    tau = 1 is exact (closed form). tau > 1 uses rollouts under COMMON RANDOM
    NUMBERS: the same `rng_seed` drives every variant compared, so the paired
    difference removes the shared sampling noise.
    """
    z = np.asarray(z)
    I = np.asarray(sorted(int(x) for x in I))
    if tau == 1:
        zf = z.copy()
        G = sim.compute_G_masked(zf, sim.visible_mask(zf))
        ut = policy_posterior(sim.pm, G)
        p = ut @ sim.pm.Bu.T
        # a forced bird takes action h_star deterministically
        if forced:
            f = np.asarray(sorted(int(x) for x in forced))
            p = p.copy()
            p[f] = sim.pm.Bu[:, int(h_star)]
        return float(p[I, int(h_star)].mean())
    return rollout_alignment(sim, z, I, h_star, tau, forced, rng_seed, n_roll,
                             hold=hold)


def task_authority(sim, z, I, h_star, j, tau=2, rng_seed=0, n_roll=64) -> float:
    """A_j^{h*,tau} = E[H*_{t+tau} | do(u_j=h*)] - E[H*_{t+tau} | baseline]."""
    a = _expected_alignment_after(sim, z, I, h_star, tau, [int(j)], rng_seed, n_roll)
    b = _expected_alignment_after(sim, z, I, h_star, tau, [], rng_seed, n_roll)
    return float(a - b)


def set_authority(sim, z, I, h_star, A, tau=2, rng_seed=0, n_roll=64) -> float:
    """A_S for an actuator SET -- the quantity a controller should maximize."""
    a = _expected_alignment_after(sim, z, I, h_star, tau, list(A), rng_seed, n_roll)
    b = _expected_alignment_after(sim, z, I, h_star, tau, [], rng_seed, n_roll)
    return float(a - b)


def pair_synergy(sim, z, I, h_star, j, k, tau=2, rng_seed=0, n_roll=64) -> float:
    """S_jk = A_{j,k} - A_j - A_k. Nonzero means the additive/multicover
    ranking the Stage 6.8 policy uses cannot be exactly right."""
    ajk = set_authority(sim, z, I, h_star, [j, k], tau, rng_seed, n_roll)
    aj = task_authority(sim, z, I, h_star, j, tau, rng_seed, n_roll)
    ak = task_authority(sim, z, I, h_star, k, tau, rng_seed, n_roll)
    return float(ajk - aj - ak)
