import numpy as np
import itertools
from scipy.linalg import expm
np.set_printoptions(precision=6, suppress=True, linewidth=200)

TOL = 1e-9  # numerical tolerance for "exact zero" comparisons, reported explicitly

# ---------------------------------------------------------------------------
# Part 1: Primary precision model
# ---------------------------------------------------------------------------
N = 8
idx = {k: k - 1 for k in range(1, 9)}  # 1-indexed node -> 0-indexed array position

W = np.zeros((N, N))

def add_edge(a, b, w):
    W[idx[a], idx[b]] += w
    W[idx[b], idx[a]] += w

# complete graph on {1,2,3}, weight 1
for a, b in itertools.combinations([1, 2, 3], 2):
    add_edge(a, b, 1.0)

# complete graph on {6,7,8}, weight 1
for a, b in itertools.combinations([6, 7, 8], 2):
    add_edge(a, b, 1.0)

# i--4 weight 1, i--5 weight 1/2 for i in {1,2,3}
for i in [1, 2, 3]:
    add_edge(i, 4, 1.0)
    add_edge(i, 5, 0.5)

# 4--j weight 1, 5--j weight 1/2 for j in {6,7,8}
for j in [6, 7, 8]:
    add_edge(4, j, 1.0)
    add_edge(5, j, 0.5)

# no 4-5 edge, no direct {1,2,3}-{6,7,8} edges: already true by construction

D = np.diag(W.sum(axis=1))
L = D - W
Omega0 = np.eye(N) + L

Omega0_expected = np.array([
    [4.5, -1, -1, -1, -0.5, 0, 0, 0],
    [-1, 4.5, -1, -1, -0.5, 0, 0, 0],
    [-1, -1, 4.5, -1, -0.5, 0, 0, 0],
    [-1, -1, -1, 7, 0, -1, -1, -1],
    [-0.5, -0.5, -0.5, 0, 4, -0.5, -0.5, -0.5],
    [0, 0, 0, -1, -0.5, 4.5, -1, -1],
    [0, 0, 0, -1, -0.5, -1, 4.5, -1],
    [0, 0, 0, -1, -0.5, -1, -1, 4.5],
])

err1 = np.max(np.abs(Omega0 - Omega0_expected))
print("=== Part 1 ===")
print(f"max|Omega0 - expected| = {err1:.3e}  (tol {TOL:.0e})  -> {'PASS' if err1 < TOL else 'FAIL'}")

eigvals = np.linalg.eigvalsh(Omega0)
print(f"Omega0 eigenvalues: {eigvals}")
pd = np.all(eigvals > TOL)
print(f"Positive definite: {pd}")

Sigma0 = np.linalg.inv(Omega0)
# sanity: Omega0 @ Sigma0 == I
resid = np.max(np.abs(Omega0 @ Sigma0 - np.eye(N)))
print(f"max|Omega0 Sigma0 - I| = {resid:.3e}")

np.save("/tmp/Omega0.npy", Omega0)
np.save("/tmp/Sigma0.npy", Sigma0)

# ---------------------------------------------------------------------------
# Part 2: Exact Gaussian conditional mutual information via precision blocks
# ---------------------------------------------------------------------------
def logdet(M):
    sign, ld = np.linalg.slogdet(M)
    if sign <= 0:
        raise ValueError(f"Non-positive-definite matrix, sign={sign}")
    return ld

def L_cmi(Omega, I_idx, B_idx, E_idx):
    """I,B,E are lists of 0-indexed node positions. Returns L(I,B,E)."""
    IE = I_idx + E_idx
    K = Omega[np.ix_(IE, IE)]
    nI = len(I_idx)
    A = K[:nI, :nI]
    G = K[nI:, nI:]
    ld_A = logdet(A)
    ld_G = logdet(G)
    ld_K = logdet(K)
    return 0.5 * (ld_A + ld_G - ld_K)

def L_cmi_cov(Sigma, I_idx, B_idx, E_idx):
    """Independent check via covariance/conditional-covariance formula.
    I(X_I;X_E|X_B) = 1/2 log( det(Sigma_{I|B}) det(Sigma_{E|B}) / det(Sigma_{IE|B}) )
    where Sigma_{S|B} is the Schur complement conditional covariance of block S given B.
    """
    def cond_cov(idxset, cond):
        if len(cond) == 0:
            return Sigma[np.ix_(idxset, idxset)]
        Sxx = Sigma[np.ix_(idxset, idxset)]
        Sxc = Sigma[np.ix_(idxset, cond)]
        Scc = Sigma[np.ix_(cond, cond)]
        Scx = Sigma[np.ix_(cond, idxset)]
        return Sxx - Sxc @ np.linalg.inv(Scc) @ Scx

    Sigma_I_B = cond_cov(I_idx, B_idx)
    Sigma_E_B = cond_cov(E_idx, B_idx)
    Sigma_IE_B = cond_cov(I_idx + E_idx, B_idx)
    ld_I = logdet(Sigma_I_B)
    ld_E = logdet(Sigma_E_B)
    ld_IE = logdet(Sigma_IE_B)
    return 0.5 * (ld_I + ld_E - ld_IE)

print("\n=== Part 2 ===")
I_idx = [0, 1, 2]
B_idx = []
E_idx = [3, 4, 5, 6, 7]
L_test = L_cmi(Omega0, I_idx, B_idx, E_idx)
L_test_cov = L_cmi_cov(Sigma0, I_idx, B_idx, E_idx)
expected = 0.5 * np.log(211 / 142)
print(f"L(empty) precision-form = {L_test:.11f}, cov-form = {L_test_cov:.11f}, expected = {expected:.11f}")
print(f"  diff precision-vs-expected = {abs(L_test-expected):.3e}, precision-vs-cov = {abs(L_test-L_test_cov):.3e}")

# ---------------------------------------------------------------------------
# Part 3: Fixed-interior exhaustive search, I = {1,2,3}
# ---------------------------------------------------------------------------
print("\n=== Part 3 ===")
I_nodes = [1, 2, 3]
I_idx = [idx[i] for i in I_nodes]
rest_nodes = [4, 5, 6, 7, 8]

results3 = []
for r in range(len(rest_nodes) + 1):
    for B_nodes in itertools.combinations(rest_nodes, r):
        B_nodes = list(B_nodes)
        E_nodes = [n for n in rest_nodes if n not in B_nodes]
        B_idx_ = [idx[n] for n in B_nodes]
        E_idx_ = [idx[n] for n in E_nodes]
        Lval = L_cmi(Omega0, I_idx, B_idx_, E_idx_)
        results3.append((tuple(B_nodes), tuple(E_nodes), len(B_nodes), Lval))

print(f"Total candidates: {len(results3)} (expected 32)")
print(f"{'B':<15}{'E':<15}{'|B|':<5}{'L':<15}")
for B, E, sB, Lval in results3:
    print(f"{str(B):<15}{str(E):<15}{sB:<5}{Lval:<15.10f}")

# spot checks
checks = {
    (): 0.5 * np.log(211/142),
    (4,): 0.5 * np.log(37/34),
    (5,): 0.5 * np.log(29/23),
    (4,5): 0.0,
}
print("\nSpot checks:")
for Bkey, expected in checks.items():
    val = next(v for b, e, s, v in results3 if b == Bkey)
    print(f"  B={Bkey}: computed={val:.11f} expected={expected:.11f} diff={abs(val-expected):.3e}")

# Pareto frontier: minimize (|B|, L) -- a point is on frontier if no other point
# dominates it (weakly smaller |B| and L, strictly smaller in at least one)
def pareto_frontier(pts, tol=TOL):
    # snap sub-tolerance L values to exact 0 before comparing, per stated tolerance policy
    def snap(v):
        return 0.0 if abs(v) < tol else v
    frontier = []
    for p in pts:
        _, _, sB_p, L_p_raw = p
        L_p = snap(L_p_raw)
        dominated = False
        for q in pts:
            if q is p:
                continue
            _, _, sB_q, L_q_raw = q
            L_q = snap(L_q_raw)
            if sB_q <= sB_p and L_q <= L_p and (sB_q < sB_p or L_q < L_p):
                dominated = True
                break
        if not dominated:
            frontier.append(p)
    return sorted(frontier, key=lambda x: x[2])

frontier3 = pareto_frontier(results3)
print("\nPareto frontier (fixed I):")
for B, E, sB, Lval in frontier3:
    print(f"  B={B}, |B|={sB}, L={Lval:.11f}")

expected_frontier = [(), (4,), (4,5)]
frontier_keys = [f[0] for f in frontier3]
print(f"Matches expected sequence {expected_frontier}: {frontier_keys == expected_frontier}")

# Delta_k(B) = I(X_I; X_k | X_B) = L(B) - L(B u {k})  verification for greedy steps
print("\nGreedy verification:")
def L_of_B(B_nodes):
    B_nodes = list(B_nodes)
    E_nodes = [n for n in rest_nodes if n not in B_nodes]
    return L_cmi(Omega0, I_idx, [idx[n] for n in B_nodes], [idx[n] for n in E_nodes])

# Step 0: B = {}
B_cur = []
L_cur = L_of_B(B_cur)
print(f"B={B_cur}, L={L_cur:.11f}")
for k in rest_nodes:
    Lk = L_of_B(B_cur + [k])
    delta = L_cur - Lk
    print(f"  candidate add {k}: L(B+{{{k}}})={Lk:.11f}, Delta_{k}={delta:.11f}")
best_k = min(rest_nodes, key=lambda k: L_of_B(B_cur + [k]))
print(f"  greedy picks: {best_k} (expected 4)")

# Step 1: B = {4}
B_cur = [4]
L_cur = L_of_B(B_cur)
print(f"B={B_cur}, L={L_cur:.11f}")
remaining = [n for n in rest_nodes if n not in B_cur]
for k in remaining:
    Lk = L_of_B(B_cur + [k])
    delta = L_cur - Lk
    print(f"  candidate add {k}: L(B+{{{k}}})={Lk:.11f}, Delta_{k}={delta:.11f}")
best_k = min(remaining, key=lambda k: L_of_B(B_cur + [k]))
print(f"  greedy picks: {best_k} (expected 5)")

# ---------------------------------------------------------------------------
# Part 4: Fully exhaustive tripartitions
# ---------------------------------------------------------------------------
print("\n=== Part 4 ===")
all_nodes = list(range(1, 9))
count = 0
results4 = []  # (I_nodes, B_nodes, E_nodes, L)
for assignment in itertools.product([0, 1, 2], repeat=8):  # 0=I,1=B,2=E
    I_nodes = [all_nodes[i] for i in range(8) if assignment[i] == 0]
    B_nodes = [all_nodes[i] for i in range(8) if assignment[i] == 1]
    E_nodes = [all_nodes[i] for i in range(8) if assignment[i] == 2]
    if len(I_nodes) == 0 or len(E_nodes) == 0:
        continue
    count += 1
    I_idx_ = [idx[n] for n in I_nodes]
    B_idx_ = [idx[n] for n in B_nodes]
    E_idx_ = [idx[n] for n in E_nodes]
    Lval = L_cmi(Omega0, I_idx_, B_idx_, E_idx_)
    results4.append((tuple(I_nodes), tuple(B_nodes), tuple(E_nodes), Lval))

print(f"Total labelled tripartitions (I!=empty, E!=empty): {count} (expected 6050)")

# quotient by I<->E symmetry: canonicalize as frozenset pair, keep one representative
seen = set()
results4_quot = []
for I_nodes, B_nodes, E_nodes, Lval in results4:
    key = frozenset([frozenset(I_nodes), frozenset(E_nodes)])
    if key not in seen:
        seen.add(key)
        results4_quot.append((I_nodes, B_nodes, E_nodes, Lval))
print(f"After quotienting by I<->E swap: {len(results4_quot)} (expected {6050//2}={3025})")

# exact L=0 partitions at eps=0, find minimum |B|
zero_parts = [r for r in results4_quot if abs(r[3]) < TOL]
print(f"Number of exact L=0 partitions (quotiented): {len(zero_parts)}")
min_B_size = min(len(r[1]) for r in zero_parts)
min_B_parts = [r for r in zero_parts if len(r[1]) == min_B_size]
print(f"Minimum |B| among exact L=0 partitions: {min_B_size}")
print(f"Number of minimum-|B| exact partitions: {len(min_B_parts)}")
for I_nodes, B_nodes, E_nodes, Lval in min_B_parts:
    print(f"  I={I_nodes}, B={B_nodes}, E={E_nodes}, L={Lval:.3e}")

expected_min = (tuple([1,2,3]), tuple([4,5]), tuple([6,7,8]))
match = any(
    (set(I) == {1,2,3} and set(B) == {4,5} and set(E) == {6,7,8}) or
    (set(E) == {1,2,3} and set(B) == {4,5} and set(I) == {6,7,8})
    for I, B, E, L in min_B_parts
)
print(f"Matches expected unique minimum {{1,2,3}}|{{4,5}}|{{6,7,8}}: {match}, count of minimal solutions = {len(min_B_parts)}")

# Semantically different near-zero partitions (small approximate leakage -> different system split)
print("\nNear-zero (but nonzero) partitions with small |B|, showing semantic ambiguity:")
near = sorted([r for r in results4_quot if abs(r[3]) > TOL], key=lambda r: (len(r[1]), r[3]))
for I_nodes, B_nodes, E_nodes, Lval in near[:8]:
    print(f"  I={I_nodes}, B={B_nodes}, E={E_nodes}, L={Lval:.6f}")

print("\nSmallest nonzero-L partitions at |B|=2 (illustrating near-degenerate alternatives to {4,5}):")
b2 = sorted([r for r in results4_quot if len(r[1]) == 2 and abs(r[3]) > TOL], key=lambda r: r[3])
for I_nodes, B_nodes, E_nodes, Lval in b2[:5]:
    print(f"  I={I_nodes}, B={B_nodes}, E={E_nodes}, L={Lval:.6f}")

# ---------------------------------------------------------------------------
# Part 5: Controlled graded violation via rank-one perturbation
# ---------------------------------------------------------------------------
print("\n=== Part 5 ===")
e3 = np.zeros(N); e3[idx[3]] = 1.0
e6 = np.zeros(N); e6[idx[6]] = 1.0
v = e3 - e6

def Omega_eps(eps):
    return Omega0 + eps * np.outer(v, v)

I_idx = [idx[n] for n in [1,2,3]]
B_idx_45 = [idx[n] for n in [4,5]]
E_idx_678 = [idx[n] for n in [6,7,8]]

eps_list = [0, 0.05, 0.1, 0.25, 0.5, 1]
print(f"{'eps':<8}{'r(eps)':<15}{'L_analytic':<18}{'L_computed':<18}{'diff':<12}")
for eps in eps_list:
    Oe = Omega_eps(eps)
    pd_e = np.all(np.linalg.eigvalsh(Oe) > 0)
    r = 14*eps/(55+14*eps)
    L_analytic = -0.5*np.log(1-r**2) if r < 1 else np.inf
    L_computed = L_cmi(Oe, I_idx, B_idx_45, E_idx_678)
    print(f"{eps:<8}{r:<15.10f}{L_analytic:<18.11f}{L_computed:<18.11f}{abs(L_analytic-L_computed):<12.3e}  PD={pd_e}")

# eps=1 expected L{4,5} ~ 0.02101960808
Oe1 = Omega_eps(1.0)
L_45_eps1 = L_cmi(Oe1, I_idx, B_idx_45, E_idx_678)
print(f"\nAt eps=1: L({{4,5}}) = {L_45_eps1:.11f}, expected 0.02101960808, diff={abs(L_45_eps1-0.02101960808):.3e}")

# fixed-I exhaustive search at eps=1
print("\nFixed-I (I={1,2,3}) exhaustive search at eps=1:")
rest_nodes = [4,5,6,7,8]
results5 = []
for r in range(len(rest_nodes)+1):
    for B_nodes in itertools.combinations(rest_nodes, r):
        B_nodes=list(B_nodes)
        E_nodes=[n for n in rest_nodes if n not in B_nodes]
        Lval = L_cmi(Oe1, I_idx, [idx[n] for n in B_nodes], [idx[n] for n in E_nodes])
        results5.append((tuple(B_nodes), tuple(E_nodes), len(B_nodes), Lval))
frontier5 = pareto_frontier(results5)
for B,E,sB,Lval in frontier5:
    print(f"  B={B}, |B|={sB}, L={Lval:.11f}")

expected5 = {(): 0.23611755277, (4,): 0.06758850002, (4,5): 0.02101960808, (4,5,6): 0.0}
print("\nChecks vs expected:")
for Bkey, expv in expected5.items():
    val = next(v for b,e,s,v in results5 if b==Bkey)
    print(f"  B={Bkey}: computed={val:.11f}, expected={expv:.11f}, diff={abs(val-expv):.3e}")

# verify {4,5,6} is the unique minimal exact blanket for eps>0
print("\nUnique minimal exact blanket check at eps=1 (over all fixed-I candidates with L~0):")
zero_at_eps1 = [(b,s) for b,e,s,v in results5 if abs(v) < TOL]
min_size = min(s for b,s in zero_at_eps1)
mins = [b for b,s in zero_at_eps1 if s==min_size]
print(f"  Minimum |B| with L=0: {min_size}, sets: {mins}")

# ---------------------------------------------------------------------------
# Part 6: Hessian-score cross-check
# ---------------------------------------------------------------------------
print("\n=== Part 6 ===")
def L_H(Omega, I_idx, B_idx, E_idx):
    H = -Omega
    IE = I_idx + E_idx
    K = H[np.ix_(IE, IE)]
    nI = len(I_idx)
    A = K[:nI, :nI]
    G = K[nI:, nI:]
    C = K[:nI, nI:]
    # A, G here are submatrices of H = -Omega restricted to (I,I) and (E,E);
    # note A_H = -A_Omega, so use matrix power via eigen-decomposition (sign doesn't
    # matter for A^{-1/2} C G^{-1/2} since we need the *precision* blocks' magnitude;
    # per task, H=-Omega, so A = -Omega_II, G = -Omega_EE, both negative definite blocks
    # of a negative definite-ish operator restricted... but Omega_II, Omega_EE are PD,
    # so A,G here are negative definite. Use matrix sqrt of A^{-1} etc via abs for stability.
    def inv_sqrt(M):
        w, Vv = np.linalg.eigh(M)
        return Vv @ np.diag(1.0/np.sqrt(np.abs(w))) @ Vv.T
    Ainvsqrt = inv_sqrt(A)
    Ginvsqrt = inv_sqrt(G)
    M = Ainvsqrt @ C @ Ginvsqrt
    return np.sum(M**2)  # Frobenius norm squared

I_idx = [idx[n] for n in [1,2,3]]
B_idx_45 = [idx[n] for n in [4,5]]
E_idx_678 = [idx[n] for n in [6,7,8]]

print(f"{'eps':<8}{'L_H':<15}{'r^2':<15}{'diff':<12}{'2L':<15}{'-log(1-L_H)':<15}{'2L/L_H':<10}")
for eps in [0, 1e-6, 1e-4, 0.01, 0.05, 0.1, 0.25, 0.5, 1]:
    Oe = Omega_eps(eps)
    LHval = L_H(Oe, I_idx, B_idx_45, E_idx_678)
    r = 14*eps/(55+14*eps)
    Lval = L_cmi(Oe, I_idx, B_idx_45, E_idx_678)
    ratio = (2*Lval/LHval) if LHval > 0 else float('nan')
    neglog = -0.5*np.log(1-LHval) if LHval < 1 else float('nan')
    print(f"{eps:<8}{LHval:<15.10f}{r**2:<15.10f}{abs(LHval-r**2):<12.3e}{2*Lval:<15.10f}{2*neglog:<15.10f}{ratio:<10.6f}")

# ---------------------------------------------------------------------------
# Part 7: Hidden-variable/representation test
# ---------------------------------------------------------------------------
print("\n=== Part 7 ===")
def marginalize(Omega, hidden_nodes, observed_nodes):
    H = [idx[n] for n in hidden_nodes]
    O = [idx[n] for n in observed_nodes]
    Omega_OO = Omega[np.ix_(O, O)]
    Omega_OH = Omega[np.ix_(O, H)]
    Omega_HO = Omega[np.ix_(H, O)]
    Omega_HH = Omega[np.ix_(H, H)]
    return Omega_OO - Omega_OH @ np.linalg.inv(Omega_HH) @ Omega_HO, O

# hide node 5
observed = [1,2,3,4,6,7,8]
Omega_obs5, O = marginalize(Omega0, [5], observed)
pos = {n: i for i, n in enumerate(observed)}
print("Hide node 5, observed boundary B={4}:")
print("Induced core-external entries (i in {1,2,3}, j in {6,7,8}):")
vals = []
for i in [1,2,3]:
    for j in [6,7,8]:
        v = Omega_obs5[pos[i], pos[j]]
        vals.append(v)
        print(f"  Omega_obs[{i},{j}] = {v:.10f}  (expected -1/16 = {-1/16:.10f})")
maxerr = max(abs(v - (-1/16)) for v in vals)
print(f"max deviation from -1/16: {maxerr:.3e}")

I_idx_o = [pos[n] for n in [1,2,3]]
B_idx_o = [pos[4]]
E_idx_o = [pos[n] for n in [6,7,8]]
L_hide5 = L_cmi(Omega_obs5, I_idx_o, B_idx_o, E_idx_o)
expected_hide5 = 0.5*np.log(1369/1360)
print(f"I(X_1:3;X_6:8|X_4) = {L_hide5:.11f}, expected {expected_hide5:.11f}, diff={abs(L_hide5-expected_hide5):.3e}")

# hide node 4
observed2 = [1,2,3,5,6,7,8]
Omega_obs4, O2 = marginalize(Omega0, [4], observed2)
pos2 = {n: i for i, n in enumerate(observed2)}
print("\nHide node 4, observed boundary B={5}:")
vals2 = []
for i in [1,2,3]:
    for j in [6,7,8]:
        v = Omega_obs4[pos2[i], pos2[j]]
        vals2.append(v)
        print(f"  Omega_obs[{i},{j}] = {v:.10f}  (expected -1/7 = {-1/7:.10f})")
maxerr2 = max(abs(v - (-1/7)) for v in vals2)
print(f"max deviation from -1/7: {maxerr2:.3e}")

I_idx_o2 = [pos2[n] for n in [1,2,3]]
B_idx_o2 = [pos2[5]]
E_idx_o2 = [pos2[n] for n in [6,7,8]]
L_hide4 = L_cmi(Omega_obs4, I_idx_o2, B_idx_o2, E_idx_o2)
expected_hide4 = 0.5*np.log(841/805)
print(f"I(X_1:3;X_6:8|X_5) = {L_hide4:.11f}, expected {expected_hide4:.11f}, diff={abs(L_hide4-expected_hide4):.3e}")

# ---------------------------------------------------------------------------
# Part 8: Ambiguity stress-test
# ---------------------------------------------------------------------------
print("\n=== Part 8 ===")
Wamb = np.zeros((N, N))
def add_edge_amb(a, b, w):
    Wamb[idx[a], idx[b]] += w
    Wamb[idx[b], idx[a]] += w

for a, b in itertools.combinations([1,2,3], 2):
    add_edge_amb(a, b, 1.0)
for a, b in itertools.combinations([6,7,8], 2):
    add_edge_amb(a, b, 1.0)
add_edge_amb(3, 4, 1.0)
add_edge_amb(4, 6, 1.0)
add_edge_amb(2, 5, 0.5)
add_edge_amb(5, 7, 0.5)

Damb = np.diag(Wamb.sum(axis=1))
Lamb = Damb - Wamb
Omega_amb = np.eye(N) + Lamb

Omega_amb_expected = np.array([
    [3, -1, -1, 0, 0, 0, 0, 0],
    [-1, 3.5, -1, 0, -0.5, 0, 0, 0],
    [-1, -1, 4, -1, 0, 0, 0, 0],
    [0, 0, -1, 3, 0, -1, 0, 0],
    [0, -0.5, 0, 0, 2, 0, -0.5, 0],
    [0, 0, 0, -1, 0, 4, -1, -1],
    [0, 0, 0, 0, -0.5, -1, 3.5, -1],
    [0, 0, 0, 0, 0, -1, -1, 3],
])
err8 = np.max(np.abs(Omega_amb - Omega_amb_expected))
print(f"max|Omega_amb - expected| = {err8:.3e} -> {'PASS' if err8 < TOL else 'FAIL'}")
eig_amb = np.linalg.eigvalsh(Omega_amb)
print(f"Omega_amb eigenvalues: {eig_amb}, PD: {np.all(eig_amb>0)}")

# anchor node 1 in I, node 8 in E; other 6 nodes {2,3,4,5,6,7} vary over I,B,E
free_nodes = [2,3,4,5,6,7]
results8 = []
for assignment in itertools.product([0,1,2], repeat=6):  # 0=I,1=B,2=E
    I_nodes = [1] + [free_nodes[i] for i in range(6) if assignment[i]==0]
    B_nodes = [free_nodes[i] for i in range(6) if assignment[i]==1]
    E_nodes = [8] + [free_nodes[i] for i in range(6) if assignment[i]==2]
    I_idx_ = [idx[n] for n in I_nodes]
    B_idx_ = [idx[n] for n in B_nodes]
    E_idx_ = [idx[n] for n in E_nodes]
    Lval = L_cmi(Omega_amb, I_idx_, B_idx_, E_idx_)
    results8.append((tuple(sorted(I_nodes)), tuple(sorted(B_nodes)), tuple(sorted(E_nodes)), len(B_nodes), Lval))

print(f"Total assignments: {len(results8)} (expected 3^6=729)")
zero8 = [r for r in results8 if abs(r[4]) < TOL]
min_size8 = min(r[3] for r in zero8)
mins8 = [r for r in zero8 if r[3]==min_size8]
print(f"Minimum |B| with exact L=0: {min_size8}")
print(f"Number of minimum-|B| exact separators (labelled, no I<->E quotient since anchors fix I vs E): {len(mins8)}")
distinct_B = sorted(set(r[1] for r in mins8))
print(f"Distinct boundary sets B at minimum: {len(distinct_B)}")
for b in distinct_B:
    print(f"  B={b}")

expected_boundaries = [(2,3),(2,4),(2,6),(3,5),(3,7),(4,5),(4,7),(5,6),(6,7)]
match8 = sorted(distinct_B) == sorted(expected_boundaries)
print(f"Matches expected 9 boundary sets: {match8}")

# ---------------------------------------------------------------------------
# Part 9: Linear stochastic dynamics
# ---------------------------------------------------------------------------
print("\n=== Part 9 ===")
e3v = np.zeros(N); e3v[idx[3]] = 1.0
e6v = np.zeros(N); e6v[idx[6]] = 1.0

def A_q(q):
    Qq = q * (np.outer(e3v, e6v) - np.outer(e6v, e3v))
    return (np.eye(N) + Qq) @ Omega0

q_list = [0, 0.1, 0.5, 1, 2, 5, -1, -2]
print(f"{'q':<8}{'min Re(eig(A_q))':<20}{'stable':<10}{'Lyapunov resid':<15}")
for q in q_list:
    Aq = A_q(q)
    eigs = np.linalg.eigvals(Aq)
    minre = np.min(eigs.real)  # dX=-A_q X stable iff ALL eig(A_q) have positive real part
    stable = minre > 0
    lyap_resid = np.max(np.abs(Aq @ Sigma0 + Sigma0 @ Aq.T - 2*np.eye(N)))
    print(f"{q:<8}{minre:<20.10f}{str(stable):<10}{lyap_resid:<15.3e}")

# Jacobian check J = -A_q, J_36 = -9/2 q, J_63 = +9/2 q
print("\nJacobian entries:")
for q in [0.1, 1, 2]:
    Aq = A_q(q)
    J = -Aq
    J36 = J[idx[3], idx[6]]
    J63 = J[idx[6], idx[3]]
    exp36 = -4.5*q
    exp63 = 4.5*q
    print(f"q={q}: J_36={J36:.6f} (expected {exp36:.6f}), J_63={J63:.6f} (expected {exp63:.6f})")

# ---------------------------------------------------------------------------
# Part 10: Predictive permeability
# ---------------------------------------------------------------------------
print("\n=== Part 10 ===")
I_nodes10 = [1,2,3]; B_nodes10 = [4,5]; E_nodes10 = [6,7,8]
I_idx10 = [idx[n] for n in I_nodes10]
B_idx10 = [idx[n] for n in B_nodes10]
E_idx10 = [idx[n] for n in E_nodes10]

def predictive_permeability(q, tau):
    Aq = A_q(q)
    Gamma_tau = expm(-Aq * tau) @ Sigma0   # Cov(X_{t+tau}, X_t) = e^{-A tau} Sigma0

    nI, nB, nE = len(I_idx10), len(B_idx10), len(E_idx10)
    # Build joint covariance over [X_{I,t+tau}, X_{I,t}, X_{B,t}, X_{E,t}]
    idx_future_I = I_idx10
    idx_t = I_idx10 + B_idx10 + E_idx10  # order I,B,E at time t

    # Cov(X_t, X_t) = Sigma0 block
    Sigma_tt = Sigma0[np.ix_(idx_t, idx_t)]
    # Cov(X_{I,t+tau}, X_t) = Gamma(tau)[I, :] restricted to idx_t columns
    Cov_fut_t = Gamma_tau[np.ix_(idx_future_I, idx_t)]
    # Cov(X_{I,t+tau}, X_{I,t+tau}) = Sigma0[I,I] (stationarity)
    Sigma_ff = Sigma0[np.ix_(idx_future_I, idx_future_I)]

    n_future = nI
    total = n_future + nI + nB + nE
    Sigma_joint = np.zeros((total, total))
    Sigma_joint[:n_future, :n_future] = Sigma_ff
    Sigma_joint[:n_future, n_future:] = Cov_fut_t
    Sigma_joint[n_future:, :n_future] = Cov_fut_t.T
    Sigma_joint[n_future:, n_future:] = Sigma_tt

    # local index blocks within Sigma_joint
    F = list(range(0, n_future))
    Itc = list(range(n_future, n_future+nI))
    Btc = list(range(n_future+nI, n_future+nI+nB))
    Etc = list(range(n_future+nI+nB, total))
    cond = Itc + Btc

    def cond_cov(target, cond_idx):
        if len(cond_idx) == 0:
            return Sigma_joint[np.ix_(target, target)]
        Sxx = Sigma_joint[np.ix_(target, target)]
        Sxc = Sigma_joint[np.ix_(target, cond_idx)]
        Scc = Sigma_joint[np.ix_(cond_idx, cond_idx)]
        Scx = Sigma_joint[np.ix_(cond_idx, target)]
        return Sxx - Sxc @ np.linalg.inv(Scc) @ Scx

    Sigma_F_cond = cond_cov(F, cond)
    Sigma_E_cond = cond_cov(Etc, cond)
    Sigma_FE_cond = cond_cov(F+Etc, cond)
    ld_F = logdet(Sigma_F_cond)
    ld_E = logdet(Sigma_E_cond)
    ld_FE = logdet(Sigma_FE_cond)
    return 0.5*(ld_F + ld_E - ld_FE)

print(f"{'q':<8}{'tau':<8}{'P_tau':<15}")
for q in [0, 0.5, 1, 2]:
    for tau in [0.0, 0.01, 0.1, 0.5, 1.0, 3.0]:
        if tau == 0.0:
            Ptau = 0.0  # instantaneous case is exactly the L({4,5})=0 blanket result
        else:
            Ptau = predictive_permeability(q, tau)
        print(f"{q:<8}{tau:<8}{Ptau:<15.10f}")
    print()

print("Note: P_tau > 0 for finite tau even at q=0 is EXPECTED (influence propagates")
print("through the blanket B over time even though the instantaneous blanket is exact).")
print("This is NOT a failure of the instantaneous Markov blanket / boundary result.")

# ---------------------------------------------------------------------------
# Part 11: Finite-sample stage
# ---------------------------------------------------------------------------
print("\n=== Part 11 ===")
I_idx = [idx[n] for n in [1,2,3]]
rest_nodes11 = [4,5,6,7,8]

candidates11 = {
    (): [],
    (4,): [idx[4]],
    (4,5): [idx[4], idx[5]],
}
E_for = {
    (): [idx[n] for n in rest_nodes11 if n not in ()],
    (4,): [idx[n] for n in rest_nodes11 if n not in (4,)],
    (4,5): [idx[n] for n in rest_nodes11 if n not in (4,5)],
}
true_vals = {
    (): 0.5*np.log(211/142),
    (4,): 0.5*np.log(37/34),
    (4,5): 0.0,
}

def sample_gaussian(n, seed):
    rng = np.random.default_rng(seed)
    L_chol = np.linalg.cholesky(Sigma0)
    Z = rng.standard_normal((n, N))
    return Z @ L_chol.T  # samples ~ N(0, Sigma0)

def plug_in_L(X, I_idx, B_idx, E_idx, shrinkage=0.0):
    n, p = X.shape
    S = np.cov(X.T, bias=False)
    if shrinkage > 0:
        S = (1 - shrinkage) * S + shrinkage * np.trace(S) / p * np.eye(p)
    def cond_cov(idxset, cond):
        if len(cond) == 0:
            return S[np.ix_(idxset, idxset)]
        Sxx = S[np.ix_(idxset, idxset)]
        Sxc = S[np.ix_(idxset, cond)]
        Scc = S[np.ix_(cond, cond)]
        Scx = S[np.ix_(cond, idxset)]
        return Sxx - Sxc @ np.linalg.inv(Scc) @ Scx
    Sigma_I_B = cond_cov(I_idx, B_idx)
    Sigma_E_B = cond_cov(E_idx, B_idx)
    Sigma_IE_B = cond_cov(I_idx+E_idx, B_idx)
    return 0.5*(logdet(Sigma_I_B)+logdet(Sigma_E_B)-logdet(Sigma_IE_B))

sample_sizes = [50, 200, 1000, 5000]
seeds = [0, 1, 2, 3, 4]

print(f"{'n':<8}{'B':<10}{'mean_est':<14}{'std_est':<12}{'true':<14}{'bias':<12}{'reg_needed':<10}")
for n in sample_sizes:
    for Bkey, B_idx_ in candidates11.items():
        ests = []
        reg_count = 0
        for seed in seeds:
            X = sample_gaussian(n, seed*1000+n)
            try:
                val = plug_in_L(X, I_idx, B_idx_, E_for[Bkey])
                if not np.isfinite(val):
                    raise np.linalg.LinAlgError
            except np.linalg.LinAlgError:
                val = plug_in_L(X, I_idx, B_idx_, E_for[Bkey], shrinkage=0.1)
                reg_count += 1
            ests.append(val)
        ests = np.array(ests)
        print(f"{n:<8}{str(Bkey):<10}{ests.mean():<14.6f}{ests.std():<12.6f}{true_vals[Bkey]:<14.6f}{ests.mean()-true_vals[Bkey]:<12.6f}{reg_count:<10}")

# Pareto ranking recovery: does estimated ranking B=() > B={4} > B={4,5} hold at each n?
print("\nRanking recovery check (fraction of seeds where estimated ranking matches true ordering):")
for n in sample_sizes:
    correct = 0
    for seed in seeds:
        X = sample_gaussian(n, seed*1000+n)
        vals = {}
        for Bkey, B_idx_ in candidates11.items():
            try:
                vals[Bkey] = plug_in_L(X, I_idx, B_idx_, E_for[Bkey])
            except np.linalg.LinAlgError:
                vals[Bkey] = plug_in_L(X, I_idx, B_idx_, E_for[Bkey], shrinkage=0.1)
        order = sorted(vals, key=lambda k: vals[k])
        if order == [(4,5), (4,), ()]:
            correct += 1
    print(f"  n={n}: {correct}/{len(seeds)} seeds recover true ordering (empty > {{4}} > {{4,5}})")
