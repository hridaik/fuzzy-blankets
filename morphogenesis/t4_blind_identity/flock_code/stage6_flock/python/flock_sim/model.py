"""Generative model for the (no-predator) flocking scenario, ported from
buildA / compAexceps / softmaxA in flocking_AIF_simulation.m (heading factor only;
see METHODS_AUDIT.md section 4/13 for the documented scope reduction: the
danger/stress factor, whose transition is exogenous and irrelevant to Experiment 1,
is not implemented here).

State encoding (nu=4, default; matches uv rows 1-4 in buildA):
    0 = up    (0, 1)
    1 = down  (0,-1)
    2 = left  (-1,0)
    3 = right (1, 0)

R(i,j) base matrix (Eq. 4) and its 8 geometric-slot overrides (Eq. 4's
collision-avoidance/flock-centering branch) were derived directly from
compAexceps's switch-case (see METHODS_AUDIT.md section 4/13 derivation notes)
rather than re-derived from the manuscript's angle formula, to guarantee fidelity
to what the released code actually computes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

UV4 = np.array([[0.0, 1.0], [0.0, -1.0], [-1.0, 0.0], [1.0, 0.0]])  # up, down, left, right

# IMPORTANT: state indices 0..3 = {up, down, left, right} are the order used
# throughout buildA's uv table -- they are NOT arranged as a rotational cycle
# (index+1 mod 4 alternates between a 180-degree flip and a genuine 90-degree
# turn depending on the starting index). "Adjacent cardinal heading" (a 90-
# degree turn) must use one of these two geometry-derived permutations, never
# raw (h+1)%4 arithmetic. Discovered via an anomalous Phase-3 positive-control
# baseline rate; see PORT_VALIDATION.md addendum and PROTOCOL_V1.md section 1a.
ROT_CW = np.array([3, 2, 0, 1])   # up->right, down->left, left->up, right->down
ROT_CCW = np.array([2, 3, 1, 0])  # up->left,  down->right, left->down, right->up


def rotate_cw(h: int) -> int:
    return int(ROT_CW[h])


def rotate_ccw(h: int) -> int:
    return int(ROT_CCW[h])

# Per-slot (o, s) override pairs, 0-based, set to -ca instead of the base fc*dot value.
# Slot order matches lattice.py's neighbor_slot convention (top,down,left,right,
# topleft,downright,downleft,topright), transcribed 1:1 from compAexceps's
# `case 1` (d==1, "Ab"/no-danger) branch, restricted to nu=4 (rows/cols 1..4).
SLOT_OVERRIDES: list[list[tuple[int, int]]] = [
    [(1, 0)],           # slot 0 top:       Aa(2*2-1,1) -> (o=2,s=1) 1-based -> (1,0) 0-based
    [(0, 1)],           # slot 1 down:      Aa(2*1-1,2) -> (o=1,s=2) -> (0,1)
    [(3, 2)],           # slot 2 left:      Aa(2*4-1,3) -> (3,2)
    [(2, 3)],           # slot 3 right:     Aa(2*3-1,4) -> (2,3)
    [(3, 0), (1, 2)],   # slot 4 topleft:   (4,1),(2,3) 1-based -> (3,0),(1,2)
    [(0, 3), (2, 1)],   # slot 5 downright: (1,4),(3,2) -> (0,3),(2,1)
    [(0, 2), (3, 1)],   # slot 6 downleft:  (1,3),(4,2) -> (0,2),(3,1)
    [(2, 0), (1, 3)],   # slot 7 topright:  (3,1),(2,4) -> (2,0),(1,3)
]


@dataclass
class ModelParams:
    nu: int = 4
    vm: float = 4.0
    ca: float = 2.0
    fc: float = 1.0
    beta: float = 1.0     # precAbird: observation-likelihood precision
    precB: float = 15.0   # rho: heading-transition precision (code default; NOT 1, see audit)
    precC: float = 3.0    # omega: preference precision (code default; NOT 1, see audit)
    alpha: float = 8.0    # SPM generic-solver policy precision hyperparameter
    spm_beta: float = 4.0  # SPM generic-solver beta (distinct from the flocking 'beta' above)
    n_iter: int = 4        # number of precision self-tuning iterations
    n_lookahead: int = 2   # T in upstream (policy length / lookahead horizon)


def base_R(vm: float, fc: float) -> np.ndarray:
    """nu x nu matrix R[o, s] for o,s in {up,down,left,right}, before slot overrides."""
    dots = UV4 @ UV4.T
    R = fc * dots
    np.fill_diagonal(R, vm)
    return R


def neighbor_R(slot: int, vm: float, ca: float, fc: float) -> np.ndarray:
    R = base_R(vm, fc).copy()
    for (o, s) in SLOT_OVERRIDES[slot]:
        R[o, s] = -ca
    return R


def softmax_cols(x: np.ndarray, precision: float) -> np.ndarray:
    """Column-wise softmax with inverse-temperature `precision`, matching
    upstream spm_softmax(x, k) = exp(k*x - max) / sum(...), applied per column."""
    z = precision * x
    z = z - z.max(axis=0, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=0, keepdims=True)


def neighbor_likelihood(slot: int, params: ModelParams) -> np.ndarray:
    """P(observed_neighbor_heading = row | my_heading = col), nu x nu, column-stochastic.
    This is Eq. 3 restricted to the no-danger branch (softmaxA(...,precAbird,0) with the
    danger slice discarded), matching buildA(...)(:,:,1) odd rows -> softmaxA slice 1."""
    R = neighbor_R(slot, params.vm, params.ca, params.fc)
    return softmax_cols(R, params.beta)


def transition_matrix(params: ModelParams) -> np.ndarray:
    """B(:,:,u): nu x nu, column u is softmax(precB * one_hot(u)) -> every column of
    B[:,:,u] is identical (constant across "previous state"), matching Eq. 5 / the
    audit finding that action u IS (up to softmax noise) the commanded next heading."""
    nu = params.nu
    B = np.zeros((nu, nu, nu))
    for u in range(nu):
        col = np.zeros(nu)
        col[u] = 1.0
        soft = softmax_cols(col.reshape(nu, 1), params.precB).flatten()
        B[:, :, u] = soft.reshape(nu, 1)  # identical across all "previous state" columns
    return B


def preference_vector(neighbor_heading: int, params: ModelParams) -> np.ndarray:
    """C{i}{neighbor}: nu-vector preference over this neighbor's observed heading,
    peaked at the neighbor's last-observed heading (Eq. "goal prior" in A.2)."""
    vec = np.zeros(params.nu)
    vec[neighbor_heading] = 1.0
    z = params.precC * vec
    z = z - z.max()
    e = np.exp(z)
    return e / e.sum()
