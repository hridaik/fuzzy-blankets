"""Out-of-model synthetic generator: a real local-alignment (Vicsek-style)
multi-agent simulation, deliberately violating the elliptical-mixture
observation model's conditional-independence and elliptical-shape
assumptions (VALIDATION_PROTOCOL.md §1's "out-of-model tests").

Ground truth here is intentionally weaker than the matched-model
generator's: since real multi-agent dynamics do not have an authored
genealogy, ground truth is the FIXED initial bird-id partition each bird
started in (which subgroup it was seeded into), not an evolving authored
label timeline. This is a disclosed scope simplification -- these
scenarios test whether a tracker's inferred labels track the original
subgroup partition reasonably well under real (non-elliptical, correlated)
dynamics, not whether it recovers a full authored event log.
"""
from __future__ import annotations

import numpy as np

UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])


def torus_delta(a, b, L):
    return (a - b + L / 2.0) % L - L / 2.0


def torus_wrap(x, L):
    return np.mod(x, L)


def _vicsek_run(N, L, T, seed, speed, radius, noise, init_fn):
    rng = np.random.default_rng(seed)
    r, z, groups = init_fn(N, L, rng)
    frames = []
    for t in range(T):
        frames.append((r.copy(), z.copy()))
        d = torus_delta(r[:, None, :], r[None, :, :], L)
        D = np.sqrt((d ** 2).sum(-1))
        adj = D <= radius
        np.fill_diagonal(adj, True)
        headings_vec = UV4[z]
        new_z = np.zeros_like(z)
        for i in range(N):
            nbrs = np.where(adj[i])[0]
            mean_vec = headings_vec[nbrs].mean(axis=0)
            if rng.random() < noise:
                new_z[i] = rng.integers(0, 4)
            else:
                new_z[i] = int(np.argmax(UV4 @ mean_vec))
        z = new_z
        r = torus_wrap(r + speed * UV4[z], L)
    return frames, groups


def generate_vicsek(scenario_name: str, seed: int):
    L = 24.0
    if scenario_name == "crossing":
        N, T = 120, 60

        def init_fn(N, L, rng):
            r = np.zeros((N, 2))
            z = np.zeros(N, dtype=int)
            groups = {"A": list(range(60)), "B": list(range(60, 120))}
            r[:60] = rng.normal([L * 0.15, L * 0.5], 1.0, size=(60, 2))
            z[:60] = 3
            r[60:] = rng.normal([L * 0.5, L * 0.15], 1.0, size=(60, 2))
            z[60:] = 0
            return torus_wrap(r, L), z, groups
        frames, groups = _vicsek_run(N, L, T, seed, speed=0.28, radius=1.6, noise=0.05, init_fn=init_fn)
    elif scenario_name == "actual_merger":
        N, T = 100, 60

        def init_fn(N, L, rng):
            r = np.zeros((N, 2))
            z = np.zeros(N, dtype=int)
            groups = {"A": list(range(50)), "B": list(range(50, 100))}
            r[:50] = rng.normal([L * 0.35, L * 0.5], 1.0, size=(50, 2))
            z[:50] = 3
            r[50:] = rng.normal([L * 0.65, L * 0.5], 1.0, size=(50, 2))
            z[50:] = 2
            return torus_wrap(r, L), z, groups
        frames, groups = _vicsek_run(N, L, T, seed, speed=0.2, radius=2.2, noise=0.03, init_fn=init_fn)
    elif scenario_name == "full_turnover":
        N, T = 100, 60

        def init_fn(N, L, rng):
            r = rng.normal([L * 0.15, L * 0.5], 1.2, size=(N, 2))
            z = np.full(N, 3)
            groups = {"A": list(range(N))}
            return torus_wrap(r, L), z, groups
        frames, groups = _vicsek_run(N, L, T, seed, speed=0.28, radius=1.8, noise=0.15, init_fn=init_fn)
    elif scenario_name == "shape_elongated":
        N, T = 90, 40

        def init_fn(N, L, rng):
            offsets = rng.normal([0, 0], [2.5, 0.4], size=(N, 2))
            r = torus_wrap(np.array([L / 2, L / 2]) + offsets, L)
            z = np.full(N, 3)
            groups = {"A": list(range(N))}
            return r, z, groups
        frames, groups = _vicsek_run(N, L, T, seed, speed=0.1, radius=1.4, noise=0.05, init_fn=init_fn)
    else:
        raise ValueError(scenario_name)

    truth = [{lid: set(ids) for lid, ids in groups.items()} for _ in frames]
    return dict(scenario=scenario_name, mode="vicsek", seed=seed, L=L, N=N, T=T,
                frames=frames, truth=truth, events=[])
