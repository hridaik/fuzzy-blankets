"""Section 9 of the task brief: candidate-interior generation. A mixture of
five methods so the landscape is not biased toward one geometry; none of the
methods optimizes for any of the four metrics (task brief: "Do not optimize
candidates for a single metric" -- the one exception, `high_coherence`, only
biases toward same-heading growth, which is itself one of the four axes
being explored, not a proxy for the composite the brief forbids)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common_66 import structural_shell, is_connected, resize_to_k, spectral


@dataclass
class Candidate:
    nodes: np.ndarray     # sorted int array, size k
    source: str

    @property
    def key(self) -> frozenset:
        return frozenset(int(x) for x in self.nodes)


def _region_growing(lattice, k, rng) -> np.ndarray:
    start = int(rng.integers(0, lattice.nn))
    nodes = {start}
    while len(nodes) < k:
        shell = structural_shell(lattice, np.array(sorted(nodes)))
        if len(shell) == 0:
            start = int(rng.integers(0, lattice.nn))
            nodes = {start}
            continue
        nodes.add(int(rng.choice(shell)))
    return np.array(sorted(nodes), dtype=int)


def _weighted_region_growing(lattice, k, rng, z: np.ndarray, same_heading_weight: float = 5.0) -> np.ndarray:
    """Like _region_growing, but shell candidates matching the current majority
    interior heading are weighted more heavily -- produces high-C_I patches
    without literally maximizing C_I (task brief method 4, "high-current-
    coherence connected patches")."""
    start = int(rng.integers(0, lattice.nn))
    nodes = {start}
    while len(nodes) < k:
        shell = structural_shell(lattice, np.array(sorted(nodes)))
        if len(shell) == 0:
            start = int(rng.integers(0, lattice.nn))
            nodes = {start}
            continue
        counts = np.bincount(z[np.array(sorted(nodes))], minlength=4)
        majority_h = int(np.argmax(counts))
        weights = np.array([same_heading_weight if z[j] == majority_h else 1.0 for j in shell])
        weights = weights / weights.sum()
        nodes.add(int(rng.choice(shell, p=weights)))
    return np.array(sorted(nodes), dtype=int)


def _swap_move(lattice, nodes: set, rng) -> set | None:
    """One connectivity-preserving swap: remove a node whose removal keeps the
    remainder connected, add a uniformly random member of the new structural
    shell. Returns None if no removable node exists (should not happen for
    k>=2 on this lattice)."""
    removable = [n for n in nodes if is_connected(lattice, nodes - {n})]
    if not removable:
        return None
    rm = int(rng.choice(removable))
    remainder = nodes - {rm}
    shell = structural_shell(lattice, np.array(sorted(remainder)))
    shell = [s for s in shell if s != rm] or [rm]  # degenerate guard, effectively never hit
    add = int(rng.choice(shell))
    remainder.add(add)
    return remainder


def _mcmc_chain(lattice, k, rng, n_samples: int, n_burn: int = 50, thin: int = 4,
                 restart_every: int = 150) -> list[np.ndarray]:
    """Unbiased (uniform-acceptance) local boundary-swap MCMC: every
    connectivity-preserving swap is accepted, so the chain explores shapes
    without being pulled toward any metric. Occasional restarts from a fresh
    random region-growing seed increase coverage beyond what one chain's
    local moves reach in the sample budget."""
    out = []
    nodes = set(_region_growing(lattice, k, rng).tolist())
    step = 0
    for _ in range(n_burn):
        mv = _swap_move(lattice, nodes, rng)
        if mv is not None:
            nodes = mv
    while len(out) < n_samples:
        mv = _swap_move(lattice, nodes, rng)
        if mv is not None:
            nodes = mv
        step += 1
        if step % thin == 0:
            out.append(np.array(sorted(nodes), dtype=int))
        if step % restart_every == 0:
            nodes = set(_region_growing(lattice, k, rng).tolist())
    return out


def _perturb_I0(lattice, I0, k, rng, n_samples, max_swaps=6) -> list[np.ndarray]:
    out = []
    I0 = np.asarray(I0, dtype=int)
    for _ in range(n_samples):
        nodes = set(I0.tolist())
        n_swaps = int(rng.integers(1, max_swaps + 1))
        for _ in range(n_swaps):
            mv = _swap_move(lattice, nodes, rng)
            if mv is not None:
                nodes = mv
        out.append(np.array(sorted(nodes), dtype=int))
    return out


def _spectral_resized(lattice, z_window: np.ndarray, k, rng, n_samples) -> list[np.ndarray]:
    sr = spectral.analyze_window(z_window)
    bases = [b for b in (sr.core1_nodes, sr.core2_nodes) if len(b) > 0]
    if len(sr.boundary_nodes) > 0:
        bases.append(np.union1d(sr.core1_nodes, sr.boundary_nodes[:len(sr.boundary_nodes) // 2 or 1]))
    if not bases:
        bases = [np.array([int(rng.integers(0, lattice.nn))])]
    out = []
    for i in range(n_samples):
        base = bases[i % len(bases)]
        try:
            out.append(resize_to_k(lattice, base, k, rng=rng))
        except RuntimeError:
            out.append(_region_growing(lattice, k, rng))
    return out


def generate_candidate_landbank(lattice, z_snapshot: np.ndarray, z_window_for_spectral: np.ndarray,
                                 I0_reference: np.ndarray, k: int, target_total: int,
                                 rng: np.random.Generator,
                                 quotas: dict | None = None, max_attempts_factor: int = 8) -> list[Candidate]:
    """Returns a deduplicated list of Candidate, always including I0_reference
    first (source='seed_reference_I0'), then a mixture of the other four
    generation methods up to target_total unique candidates (best-effort: if
    dedup collisions prevent reaching target_total within the attempt budget,
    the shortfall is returned as-is and must be reported, not silently
    padded)."""
    quotas = quotas or dict(region_growing=0.35, mcmc_swap=0.25, perturb_I0=0.15,
                             high_coherence=0.15, spectral_resized=0.10)
    seen = set()
    out: list[Candidate] = []

    I0_key = frozenset(int(x) for x in I0_reference)
    seen.add(I0_key)
    out.append(Candidate(nodes=np.array(sorted(I0_reference), dtype=int), source="seed_reference_I0"))

    remaining_budget = target_total - 1
    counts = {name: max(1, int(round(frac * remaining_budget))) for name, frac in quotas.items()}

    def _add_many(nodes_list, source):
        for nodes in nodes_list:
            key = frozenset(int(x) for x in nodes)
            if key in seen:
                continue
            seen.add(key)
            out.append(Candidate(nodes=np.array(sorted(nodes), dtype=int), source=source))

    # region growing: cheap, generate with retries until quota met or budget exhausted
    want = counts["region_growing"]
    attempts = 0
    got = []
    while len(got) < want and attempts < want * max_attempts_factor:
        got.append(_region_growing(lattice, k, rng))
        attempts += 1
    _add_many(got, "region_growing")

    _add_many(_mcmc_chain(lattice, k, rng, n_samples=int(counts["mcmc_swap"] * 1.15)), "mcmc_swap")

    _add_many(_perturb_I0(lattice, I0_reference, k, rng, n_samples=int(counts["perturb_I0"] * 1.15)),
              "perturb_I0")

    want = counts["high_coherence"]
    attempts = 0
    got = []
    while len(got) < want and attempts < want * max_attempts_factor:
        got.append(_weighted_region_growing(lattice, k, rng, z_snapshot))
        attempts += 1
    _add_many(got, "high_coherence")

    _add_many(_spectral_resized(lattice, z_window_for_spectral, k, rng,
                                 n_samples=int(counts["spectral_resized"] * 1.15)), "spectral_resized")

    # top up with plain region-growing if dedup collisions left us short
    tries = 0
    while len(out) < target_total and tries < target_total * max_attempts_factor:
        cand = _region_growing(lattice, k, rng)
        key = frozenset(int(x) for x in cand)
        if key not in seen:
            seen.add(key)
            out.append(Candidate(nodes=cand, source="region_growing_topup"))
        tries += 1

    # trim any modest overshoot from the fixed-count generators above, keeping
    # I0 and a uniformly random subsample of the rest so the method mix stays
    # proportional (task brief: broad coverage, not biased toward one method).
    if len(out) > target_total:
        rest = out[1:]
        rng.shuffle(rest)
        out = [out[0]] + rest[: target_total - 1]

    return out
