"""
Stage 5, Section 4: graded integrity quantities Lambda_K, K_delta, computed from
either a precision matrix Omega or a covariance matrix Sigma (Gaussian CMI is
computable from either; both paths are provided so dynamics.py, which propagates
moments (m,Sigma), and core5.py, which works from Omega(z), share this module).

Boundary sets never include node 8 (fixed external anchor; see core5.CAND_POOL).
All minimizing/near-minimizing boundaries within a declared tie tolerance are kept,
not just an arbitrary argmin -- Lambda_K is a number, B_t^* is a SET of tied sets.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import core
import core5

TIE_TOL = 1e-6  # declared numerical tie tolerance for "co-minimizing" boundaries

ALL_CANDIDATES = core5.enumerate_candidates()  # all subsets of {4,5,6,7}, size 0..4
CANDIDATES_BY_SIZE = {k: [B for B in ALL_CANDIDATES if len(B) == k] for k in range(0, 5)}


def L_of_B_from_Omega(Omega, B, I_idx=core5.I_IDX):
    E = tuple(n for n in core5.U_NODES if n not in B)
    return core5.L_cmi(Omega, I_idx, list(B), list(E))


def L_of_B_from_Sigma(Sigma, B, I_idx=core5.I_IDX):
    B_idx = [core5.idx[n] for n in B]
    E_idx = [core5.idx[n] for n in core5.U_NODES if n not in B]
    return core.L_cmi_cov_joint(Sigma, I_idx, B_idx, E_idx)


def leakage_table(mat, from_precision, I_idx=core5.I_IDX, candidates=ALL_CANDIDATES):
    f = L_of_B_from_Omega if from_precision else L_of_B_from_Sigma
    return [(B, f(mat, B, I_idx)) for B in candidates]


def Lambda_K(mat, K, from_precision=True, tie_tol=TIE_TOL):
    """Returns (Lambda_K value, list of all (near-)minimizing B with |B|<=K)."""
    cands = [B for B in ALL_CANDIDATES if len(B) <= K]
    table = leakage_table(mat, from_precision, candidates=cands)
    Lmin = min(L for _, L in table)
    winners = [B for B, L in table if L <= Lmin + tie_tol]
    return Lmin, winners


def K_delta(mat, delta, from_precision=True, tie_tol=TIE_TOL):
    """Minimum |B| (0..4) such that L_B <= delta. Returns (K, list of achieving B)."""
    for K in range(0, 5):
        val, winners_at_K = Lambda_K(mat, K, from_precision, tie_tol=0.0)  # exact min at this K
        if val <= delta:
            table = leakage_table(mat, from_precision, candidates=CANDIDATES_BY_SIZE[K])
            achievers = [B for B, L in table if L <= delta]
            return K, achievers
    return None, []  # not achievable with B subset of {4,5,6,7} even at |B|=4


def all_K_summary(mat, from_precision=True, tie_tol=TIE_TOL, Ks=(1, 2, 3)):
    return {K: Lambda_K(mat, K, from_precision, tie_tol) for K in Ks}


if __name__ == "__main__":
    log = []
    def p(s=""):
        print(s); log.append(s)

    p("=== Stage 5, Section 4: Lambda_K / K_delta sanity at endpoints and mid-interpolation ===")
    deltas = [0.005, 0.01, 0.02, 0.05]
    for z in [-1.0, -0.5, 0.0, 0.5, 1.0]:
        Om = core5.Omega_of_z(z)
        p(f"\n--- z={z:+.2f} ---")
        for K in (1, 2, 3):
            val, winners = Lambda_K(Om, K)
            p(f"  Lambda_{K} = {val:.10f}  argmin(s) = {winners}")
        for d in deltas:
            K, achievers = K_delta(Om, d)
            p(f"  K_delta(delta={d}) = {K}  achieving B: {achievers}")

    np.savez(os.path.join(os.path.dirname(__file__), "data", "part4_integrity_sanity.npz"),
             deltas=np.array(deltas))
    with open(os.path.join(os.path.dirname(__file__), "data", "part4_log.txt"), "w") as f:
        f.write("\n".join(log))
    p("\nSaved Section 4 sanity log.")
