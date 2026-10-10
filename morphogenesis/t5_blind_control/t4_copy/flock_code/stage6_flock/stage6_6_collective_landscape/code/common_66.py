"""Shared utilities for Stage 6.6, self-contained. Imports flock_sim from the
frozen ../../python tree, and a handful of Stage 6 / 6.5 helpers, all
unmodified (see PLAN.md "Reused, unmodified")."""
from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path

import numpy as np

STAGE_DIR = Path(__file__).resolve().parents[1]      # stage6_6_collective_landscape/
ROOT = STAGE_DIR.parent                                # stage6_flock/
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "v1_mechanism_audit" / "code"))
sys.path.insert(0, str(ROOT / "v2_interface_control" / "code"))
sys.path.insert(0, str(ROOT / "stage6_5" / "boundary_inference" / "code"))

from flock_sim.lattice import Lattice  # noqa: E402
from flock_sim.model import ModelParams, rotate_cw, rotate_ccw  # noqa: E402
from flock_sim.simulation import run_simulation  # noqa: E402
from flock_sim.interventions import make_pulse  # noqa: E402
from flock_sim.metrics import coherence  # noqa: E402
import flock_sim.spectral as spectral  # noqa: E402

from dynamical_shell import one_hop_neighbors, k_hop_shell, graph_distance_from_set  # noqa: E402
from common_v2 import find_flock, T_U, T_R  # noqa: E402
from nodewise_model import NodewiseModel  # noqa: E402

# ---- Frozen Stage 6.6 primary constants (task brief sections 1, 4, 6, 12) ----
K_INTERIOR = 20          # |I|
K_BOUNDARY_BUDGET = 12   # K, fixed boundary budget for L
W_WINDOW = 10            # local regime window length (in states)
R_REPLICATES = 100       # paired simulation replicates
PRIMARY_SEEDS = [2, 3, 4]
BETA, RHO, OMEGA = 1.0, 15.0, 3.0   # == ModelParams() defaults; asserted below
NU = 4

_MODEL_PARAMS = ModelParams()
assert _MODEL_PARAMS.beta == BETA and _MODEL_PARAMS.precB == RHO and _MODEL_PARAMS.precC == OMEGA, (
    "flock_sim.model.ModelParams defaults drifted from the frozen beta/rho/omega "
    "this stage assumes (task brief section 12)."
)
assert T_U == 20 and T_R == 20


def dump_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=_json_default)


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, frozenset):
        return sorted(o)
    raise TypeError(f"not JSON serializable: {type(o)}")


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lattice_100() -> Lattice:
    return Lattice(nn=100, nh=8)


def is_connected(lattice: Lattice, nodes) -> bool:
    """Connectivity under the model's Moore-neighbour interaction graph."""
    nodes = set(int(n) for n in nodes)
    if not nodes:
        return True
    start = next(iter(nodes))
    seen = {start}
    frontier = [start]
    while frontier:
        nxt = []
        for i in frontier:
            for j in lattice.neighbor_ids[i]:
                j = int(j)
                if j in nodes and j not in seen:
                    seen.add(j)
                    nxt.append(j)
        frontier = nxt
    return seen == nodes


def structural_shell(lattice: Lattice, I: np.ndarray) -> np.ndarray:
    """S(I): non-I birds adjacent to some I member. Identical definition to
    v1_mechanism_audit/code/dynamical_shell.py:one_hop_neighbors (reused directly)."""
    return one_hop_neighbors(lattice, np.asarray(sorted(I), dtype=int))


def near_exterior(lattice: Lattice, I: np.ndarray, nn: int = 100) -> np.ndarray:
    """E_near(I): second Moore-graph ring, {j : d_G(j, I) == 2}."""
    dist = graph_distance_from_set(lattice, np.asarray(sorted(I), dtype=int), nn=nn)
    return np.where(dist == 2)[0]


def distant_exterior(lattice: Lattice, I: np.ndarray, nn: int = 100) -> np.ndarray:
    """Everything at graph distance >= 3 from I (or unreachable, dist==-1 impossible
    on this connected lattice, but guarded anyway)."""
    dist = graph_distance_from_set(lattice, np.asarray(sorted(I), dtype=int), nn=nn)
    return np.where((dist >= 3) | (dist == -1))[0]


def largest_connected_component(lattice: Lattice, nodes) -> np.ndarray:
    """Spectral/community proposals need not be spatially contiguous (a
    Fiedler bipartition is a graph cut, not a guarantee of geometric
    connectedness). Used as a pre-step before resize_to_k so "resized to
    k=20 while preserving connectedness" (task brief section 9) is always
    well-defined: resize a genuinely connected seed, documented as "where
    possible" per the brief's own qualifier."""
    remaining = set(int(n) for n in nodes)
    best: set = set()
    while remaining:
        start = next(iter(remaining))
        comp = {start}
        frontier = [start]
        while frontier:
            nxt = []
            for i in frontier:
                for j in lattice.neighbor_ids[i]:
                    j = int(j)
                    if j in remaining and j not in comp:
                        comp.add(j)
                        nxt.append(j)
            frontier = nxt
        remaining -= comp
        if len(comp) > len(best):
            best = comp
    return np.array(sorted(best), dtype=int)


def resize_to_k(lattice: Lattice, nodes, k: int, rng: np.random.Generator | None = None) -> np.ndarray:
    """Connectivity-preserving resize of a candidate node set to exactly k members.

    If len(nodes) < k: grow by repeatedly adding a uniformly-random member of the
    current structural shell S(I) (always connectivity-preserving by construction).
    If len(nodes) > k: trim by repeatedly removing a uniformly-random node whose
    removal leaves the remaining set connected (a "leaf" of the induced subgraph;
    on this lattice every connected set of size >= 2 has at least one non-cut node,
    so this always terminates), preferring boundary-most nodes deterministically
    is unnecessary here since draws are seeded (see task brief section 9's
    "resized to k=20 while preserving connectedness").
    """
    rng = rng or np.random.default_rng(0)
    nodes = set(int(n) for n in nodes)
    if not is_connected(lattice, nodes):
        nodes = set(largest_connected_component(lattice, nodes).tolist())
    if len(nodes) == k:
        return np.array(sorted(nodes), dtype=int)
    if len(nodes) < k:
        while len(nodes) < k:
            shell = structural_shell(lattice, np.array(sorted(nodes)))
            if len(shell) == 0:
                raise RuntimeError("cannot grow candidate further: exhausted lattice")
            add = int(rng.choice(shell))
            nodes.add(add)
        return np.array(sorted(nodes), dtype=int)
    # shrink, one non-cut node at a time
    while len(nodes) > k:
        removable = [n for n in nodes if is_connected(lattice, nodes - {n})]
        if not removable:
            raise RuntimeError("cannot shrink candidate further without disconnecting it")
        rm = int(rng.choice(removable))
        nodes.discard(rm)
    return np.array(sorted(nodes), dtype=int)


def avg_internal_degree(lattice: Lattice, I) -> float:
    """Mean number of Moore-neighbours each interior bird has WITHIN I.
    A chain that is connected only through diagonal moves (valid Moore
    adjacency, but visually a scattered "snake" rather than a blob) has
    average internal degree close to 2; a compact blob is markedly higher.
    Used only for figure/example selection (face-validity, task brief
    section 32) -- never as a metric or a filter on candidate generation
    itself, which must stay unbiased toward shape (task brief section 9)."""
    I = list(int(i) for i in I)
    I_set = set(I)
    if not I:
        return 0.0
    degs = [len(set(int(j) for j in lattice.neighbor_ids[i]) & I_set) for i in I]
    return float(np.mean(degs))


def unit_heading_vectors() -> np.ndarray:
    """Same UV4 cardinal mapping as flock_sim.model.UV4: 0=up,1=down,2=left,3=right."""
    return np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])


def heading_pmf(z: np.ndarray, nodes: np.ndarray, nu: int = NU) -> np.ndarray:
    """p(h) over headings {0..nu-1} for the given node subset. Empty subset -> uniform
    (documented convention; only relevant for pathological zero-size exteriors, which
    do not occur for k=20 on a 10x10 lattice but are guarded for robustness)."""
    if len(nodes) == 0:
        return np.full(nu, 1.0 / nu)
    counts = np.bincount(z[nodes], minlength=nu).astype(float)
    return counts / counts.sum()
