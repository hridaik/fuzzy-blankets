"""Black-box intervention API for the moving flock (task brief §34).

EVALUATION-SIDE. Imports the simulator because it must actually run
interventions; exposes ONLY numeric effect estimates. Stage 6.8's
`probing.py` is inference-side and generic — it calls `probe(I, j, z', z_t)`
and nothing else — so it is imported read-only and reused verbatim here.

`FiniteProbeMoving` runs paired one-step rollouts under common random numbers
from the real observed state `(r_t, z_t)`. Because the moving model's positions
are deterministic given headings, a bird whose live in-edges are unchanged by
`do(Z_j = z')` produces an identical draw in both arms, so its contribution to
the KL is exactly zero — the same variance-cancellation property the Stage 6.8
probe relies on.
"""
from __future__ import annotations

import numpy as np

EPS = 1e-12
NU = 4


def _kl(p, q):
    p = np.clip(p, EPS, 1.0)
    q = np.clip(q, EPS, 1.0)
    return (p * (np.log(p) - np.log(q))).sum(axis=-1)


class ExactPropagatorMoving:
    """Closed-form one-step interventional effect under the true live graph."""

    def __init__(self, mf, r_t):
        self._mf = mf
        self._r = np.asarray(r_t)

    def _dist(self, z):
        from flock_sim.active_inference import policy_posterior
        G = self._mf.compute_G(self._r, np.asarray(z))
        return policy_posterior(self._mf.pm, G) @ self._mf.pm.Bu.T

    # (the exact propagator is called far less often than the probe, so it does
    #  not use the position cache; both act on the same live graph)

    def exact(self, I, j, z_prime, z_t) -> dict:
        I = np.asarray(sorted(int(i) for i in I))
        p_nat = self._dist(z_t)[I]
        z_do = np.asarray(z_t).copy()
        z_do[int(j)] = int(z_prime)
        kls = _kl(self._dist(z_do)[I], p_nat)
        return dict(D_do_joint=float(kls.sum()),
                    per_bird_kl={int(i): float(k) for i, k in zip(I, kls)})


class FiniteProbeMoving:
    """Finite active probing with paired common-random-number rollouts."""

    def __init__(self, mf, r_t, n_rollouts: int = 40, seed: int = 0):
        self._mf = mf
        self._r = np.asarray(r_t)
        # positions are held fixed for a one-step probe, so everything that
        # depends only on them is computed once (pure speedup, asserted exact)
        self._cache = mf.position_cache(self._r)
        self.n_rollouts = int(n_rollouts)
        self._rng = np.random.default_rng(seed)
        self.n_calls = 0
        self.n_rollouts_used = 0

    def _rollouts(self, z_t, I, crn) -> np.ndarray:
        """(n_rollouts, |I|) realized next headings under common random numbers."""
        rng = np.random.default_rng(crn)
        out = np.zeros((self.n_rollouts, len(I)), dtype=int)
        for k in range(self.n_rollouts):
            _, z_new, _ = self._mf.step_cached(self._cache, np.asarray(z_t), rng)
            out[k] = z_new[I]
        return out

    @staticmethod
    def _freq(rolls, nu=NU):
        n = rolls.shape[0]
        counts = np.zeros((rolls.shape[1], nu))
        for c in range(rolls.shape[1]):
            counts[c] = np.bincount(rolls[:, c], minlength=nu)
        return counts / n

    def probe(self, I, j, z_prime, z_t, alpha: float = 0.5) -> dict:
        """Paired common-random-number probe.

        The reported effect is the PAIRED DISCREPANCY RATE -- the fraction of
        matched rollouts in which bird i's realized next heading differs between
        the factual and counterfactual arms:

            Chat^do_{j->i} = (1/n) sum_k 1[ z_i^{do}(k) != z_i^{nat}(k) ]

        rather than the KL between the two marginal histograms. Both are
        estimated from exactly the same rollouts and the KL is still returned
        (`D_do_joint_kl`), but the paired rate is the statistic the common
        random numbers actually afford, and at this model's internal order it is
        the only one with usable power: a highly polarized collective has a
        near-saturated policy posterior, so one source shifts an interior bird's
        next-heading MARGINAL by far less than the sampling noise of two
        independent histograms, while the PAIRED difference is exactly zero for
        every unaffected bird and strictly positive for an affected one. This
        change was made because the marginal-KL estimator returned all-zero
        samples -- a fact visible in the probe's own output, with no reference
        to any oracle quantity -- and it is disclosed rather than silently
        substituted.
        """
        I = np.asarray(sorted(int(i) for i in I))
        crn = int(self._rng.integers(0, 2 ** 31 - 1))
        z_do = np.asarray(z_t).copy()
        z_do[int(j)] = int(z_prime)
        n = self.n_rollouts
        r_nat = self._rollouts(z_t, I, crn)
        r_do = self._rollouts(z_do, I, crn)
        disc = (r_do != r_nat).mean(axis=0)                 # (|I|,) paired rate
        p_nat = (self._freq(r_nat) * n + alpha) / (n + alpha * NU)
        p_do = (self._freq(r_do) * n + alpha) / (n + alpha * NU)
        kls = _kl(p_do, p_nat)
        self.n_calls += 1
        self.n_rollouts_used += 2 * n
        return dict(D_do_joint=float(disc.sum()),
                    per_bird_kl={int(i): float(d) for i, d in zip(I, disc)},
                    D_do_joint_kl=float(kls.sum()))

    def budget(self):
        return dict(n_probe_calls=self.n_calls, n_rollouts=self.n_rollouts_used)


def near_exterior(mf, r_t, I, radius_factor: float = 1.6):
    """Exterior birds within `radius_factor * R` of the collective, in OBSERVED
    torus position. A disclosed compute restriction, wider than the interaction
    radius, exactly as at Stage 6.8."""
    I = np.asarray(sorted(int(x) for x in I))
    ext = np.setdiff1d(np.arange(mf.N), I)
    d = np.abs(r_t[ext][:, None, :] - r_t[I][None, :, :])
    d = np.minimum(d, mf.L - d)
    dmin = np.sqrt((d ** 2).sum(-1)).min(axis=1)
    return [int(j) for j, x in zip(ext, dmin) if x <= radius_factor * mf.R]
