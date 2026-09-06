"""
Stage 5, Parts 1-3: endpoint A (reconstructed from the verified Stage-1 graph),
endpoint B (constructed ONLY by permuting endpoint A's node labels 4<->6), the
continuous interface interpolation Omega(z), and exhaustive minimum-separator
verification at both endpoints and across the z sweep.

Stage 1-4 are read-only dependencies. This module imports core.py (top-level,
already self-verified against benchmark.py) for the exact W_A construction and
for the shared exact-CMI machinery; nothing in stage1-4 is modified.
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import core  # top-level, read-only Stage-1 dependency

TOL_ZERO = 1e-9      # "exact zero" / exact-separator tolerance (population level)
TOL_BYTE = 1e-12     # near-bit-identity tolerance for Omega_A vs core.Omega0

N = 8
idx = core.idx  # 1-indexed label -> 0-indexed array position, {1:0,...,8:7}

I_NODES = [1, 2, 3]
I_IDX = [idx[n] for n in I_NODES]
U_NODES = [4, 5, 6, 7, 8]         # "not interior" universe
CAND_POOL = [4, 5, 6, 7]          # node 8 is a fixed external anchor: never a candidate
                                   # blanket member, always retained on the exterior side
ANCHOR = 8


def _add_edge(W, a, b, w):
    W[idx[a], idx[b]] += w
    W[idx[b], idx[a]] += w


def build_W_A():
    """Independent reconstruction of the Stage-1 planted-partition weighted graph
    (I={1,2,3}, B_A={4,5}, E_A={6,7,8}), duplicating core.build_Omega0()'s edge set
    but returning the weighted adjacency matrix W itself (core.py only exposes Omega)."""
    W = np.zeros((N, N))
    for a, b in itertools.combinations([1, 2, 3], 2):
        _add_edge(W, a, b, 1.0)
    for a, b in itertools.combinations([6, 7, 8], 2):
        _add_edge(W, a, b, 1.0)
    for i in [1, 2, 3]:
        _add_edge(W, i, 4, 1.0)
        _add_edge(W, i, 5, 0.5)
    for j in [6, 7, 8]:
        _add_edge(W, 4, j, 1.0)
        _add_edge(W, 5, j, 0.5)
    return W


def laplacian(W):
    D = np.diag(W.sum(axis=1))
    return D - W


def Omega_of_W(W):
    return np.eye(N) + laplacian(W)


W_A = build_W_A()
Omega_A = Omega_of_W(W_A)

# --- Section 1: byte/numerically-identical check against the previously verified Omega0 ---
_diff_A = np.max(np.abs(Omega_A - core.Omega0))
assert _diff_A < TOL_BYTE, f"Omega_A does not reproduce core.Omega0! max diff={_diff_A:.3e}"

# --- Section 2: endpoint B by permutation only (swap labels 4 and 6) ---
def build_P_swap(a, b):
    P = np.eye(N)
    ia, ib = idx[a], idx[b]
    P[[ia, ib]] = P[[ib, ia]]
    return P


P_46 = build_P_swap(4, 6)
W_B = P_46 @ W_A @ P_46.T
Omega_B = Omega_of_W(W_B)
_diff_sym = np.max(np.abs(Omega_B - Omega_B.T))
assert _diff_sym < TOL_BYTE, "Omega_B not symmetric"


def L_cmi(Omega, I_idx, B_nodes, E_nodes):
    """Exact population CMI I(X_I; X_E | X_B) from the precision matrix."""
    B_idx = [idx[n] for n in B_nodes]
    E_idx = [idx[n] for n in E_nodes]
    return core.L_cmi_precision(Omega, I_idx, B_idx, E_idx)


def enumerate_candidates(pool=CAND_POOL):
    """All subsets B of `pool` (node-8 excluded, exterior always nonempty since
    8 in U_NODES is never in B)."""
    out = []
    for k in range(0, len(pool) + 1):
        for combo in itertools.combinations(pool, k):
            out.append(tuple(sorted(combo)))
    return out


def exhaustive_min_separators(Omega, I_idx=I_IDX, tol=TOL_ZERO, pool=CAND_POOL):
    """Returns (min_size, list_of_min_exact_separators, full_table).
    full_table: list of dicts {B, size, L} for every candidate."""
    table = []
    for B in enumerate_candidates(pool):
        E = tuple(n for n in U_NODES if n not in B)
        L = L_cmi(Omega, I_idx, list(B), list(E))
        table.append(dict(B=B, size=len(B), L=L, E=E))
    exact = [r for r in table if r["L"] < tol]
    if not exact:
        return None, [], table
    min_size = min(r["size"] for r in exact)
    winners = [r["B"] for r in exact if r["size"] == min_size]
    return min_size, winners, table


# --- Section 3: continuous interface interpolation ---
def alpha_A(z):
    return (1 - z) / 2.0


def alpha_B(z):
    return (1 + z) / 2.0


def W_of_z(z):
    return alpha_A(z) * W_A + alpha_B(z) * W_B


def Omega_of_z(z):
    return Omega_of_W(W_of_z(z))


def is_pd(M, tol=1e-10):
    ev = np.linalg.eigvalsh(M)
    return ev.min() > tol, ev.min()


if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s)
        log.append(s)

    p("=== Stage 5, Section 1: endpoint A reconstruction ===")
    p(f"max|Omega_A - core.Omega0| = {_diff_A:.3e}  (tol {TOL_BYTE:.0e})  -> IDENTICAL")
    ev0 = np.linalg.eigvalsh(Omega_A)
    p(f"Omega_A eigenvalues: min={ev0.min():.6f}, max={ev0.max():.6f} (PD: {ev0.min() > 0})")

    p("\nExhaustive minimum-separator search at endpoint A (I={1,2,3}, node 8 anchored external):")
    min_size_A, winners_A, table_A = exhaustive_min_separators(Omega_A)
    for r in sorted(table_A, key=lambda r: (r["size"], r["B"])):
        tag = " <-- EXACT" if r["L"] < TOL_ZERO else ""
        p(f"  B={str(r['B']):<18} size={r['size']}  L={r['L']:.10f}{tag}")
    p(f"Minimum exact separator size: {min_size_A}, winners: {winners_A}")
    assert min_size_A == 2 and winners_A == [(4, 5)], f"UNEXPECTED: endpoint-A minimum separator(s) = {winners_A}"
    p("Confirmed unique minimum exact separator B_A = {4,5}.")

    p("\n=== Stage 5, Section 2: endpoint B by permutation (swap labels 4,6) ===")
    p(f"P_46 permutes rows/cols 4<->6, identity elsewhere. max|W_B - W_B^T| = "
      f"{np.max(np.abs(W_B - W_B.T)):.3e}")
    p(f"max|Omega_B - Omega_B^T| = {_diff_sym:.3e}")
    ev_B = np.linalg.eigvalsh(Omega_B)
    p(f"Omega_B eigenvalues: min={ev_B.min():.6f}, max={ev_B.max():.6f} (PD: {ev_B.min() > 0})")

    p("\nExhaustive minimum-separator search at endpoint B (I={1,2,3}, node 8 anchored external):")
    min_size_B, winners_B, table_B = exhaustive_min_separators(Omega_B)
    for r in sorted(table_B, key=lambda r: (r["size"], r["B"])):
        tag = " <-- EXACT" if r["L"] < TOL_ZERO else ""
        p(f"  B={str(r['B']):<18} size={r['size']}  L={r['L']:.10f}{tag}")
    p(f"Minimum exact separator size: {min_size_B}, winners: {winners_B}")
    assert min_size_B == 2 and winners_B == [(5, 6)], f"UNEXPECTED: endpoint-B minimum separator(s) = {winners_B}"
    p("Confirmed unique minimum exact separator B_B = {5,6}. Interior I={1,2,3} unchanged.")

    p("\n=== Stage 5, Section 3: continuous interface interpolation Omega(z) ===")
    z_grid = np.linspace(-1, 1, 401)
    min_eigs = []
    for z in z_grid:
        pd_ok, mineig = is_pd(Omega_of_z(z))
        min_eigs.append(mineig)
        assert pd_ok, f"Omega(z) not PD at z={z}: min eig={mineig}"
    min_eigs = np.array(min_eigs)
    p(f"PD verified over {len(z_grid)} points in [-1,1]. min eigenvalue over grid = {min_eigs.min():.6f} "
      f"(at z={z_grid[np.argmin(min_eigs)]:.3f})")
    p("Analytic note: Omega(z) = I + L_{W(z)} with W(z) = alpha_A(z) W_A + alpha_B(z) W_B a "
      "nonnegative combination of two nonnegative-weight graphs for z in [-1,1] (alpha_A,alpha_B>=0), "
      "so L_{W(z)} is a graph Laplacian (PSD, since it is a nonneg. combination of edge Laplacians "
      "vv^T*w >= 0), hence Omega(z) = I + PSD is PD with eigenvalues >= 1.")

    p("\nExhaustive candidate-boundary CMI table at z in {-1, -0.5, 0, 0.5, 1}:")
    expected_2 = {0.0: 0.02983839764, 0.5: 0.00830386820, -0.5: 0.00830386820}
    results_by_z = {}
    for z in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        Om = Omega_of_z(z)
        min_size, winners, table = exhaustive_min_separators(Om)
        size2 = [r for r in table if r["size"] == 2]
        Lmin2 = min(r["L"] for r in size2)
        winners2 = [r["B"] for r in size2 if abs(r["L"] - Lmin2) < 1e-9]
        results_by_z[z] = dict(min_size=min_size, winners=winners, table=table,
                                Lmin2=Lmin2, winners2=winners2)
        p(f"\n z={z:+.2f}: min exact-separator size={min_size}, winners={winners}")
        p(f"   size-2 minimum leakage L_min,|B|=2 = {Lmin2:.11f}  argmin={winners2}")
        if z in expected_2:
            p(f"   expected ~{expected_2[z]:.11f}  diff={abs(Lmin2-expected_2[z]):.2e}")
        for r in sorted(table, key=lambda r: (r["size"], r["L"])):
            p(f"     B={str(r['B']):<18} size={r['size']}  L={r['L']:.10f}")

    assert results_by_z[-1.0]["min_size"] == 2 and results_by_z[-1.0]["winners"] == [(4, 5)]
    assert results_by_z[1.0]["min_size"] == 2 and results_by_z[1.0]["winners"] == [(5, 6)]
    for z in [-0.5, 0.0, 0.5]:
        r = results_by_z[z]
        p(f"\nz={z}: min exact-separator size = {r['min_size']} (expect 3), winners = {r['winners']} (expect [(4,5,6)] unless ties)")
    p("\nSaved endpoint/interpolation verification. (see data/part1_3_endpoints.npz)")

    np.savez(os.path.join(os.path.dirname(__file__), "data", "part1_3_endpoints.npz"),
             W_A=W_A, Omega_A=Omega_A, W_B=W_B, Omega_B=Omega_B, P_46=P_46,
             z_grid=z_grid, min_eigs=min_eigs)

    with open(os.path.join(os.path.dirname(__file__), "data", "part1_3_log.txt"), "w") as f:
        f.write("\n".join(log))
    p("\nAll Section 1-3 checks PASSED.")
