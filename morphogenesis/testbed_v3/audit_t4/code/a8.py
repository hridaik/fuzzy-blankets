"""A8: true within-state leakage of the analyst's variables from the analytic linear-noise covariance; true module structure and directed influence of the observable-projected Jacobian."""
import sys, json, itertools; sys.path.insert(0, '.')
from lib import *
from world3 import settled3, make_template2, make_engine3, Params3
import jax, jax.numpy as jnp
from scipy.linalg import schur, solve_continuous_lyapunov, expm
TM = make_template2(); n = 24; S = 24
OFF = dict(x=0, c=48, mu=144, l=720, d=744, e=792); NZ = 816
def setup(state):
    arr, perm = settled3(state, 0); eng = make_engine3(TM, Params3()); st = tuple(jnp.array(a) for a in arr); J = np.array(eng.jac_flat(st)); return arr, perm, J
def lna(J):
    T, U, sdim = schur(J, output='real', sort=lambda re, im: abs(re) < 1e-7); sig = dict(x=.02, c=.02, mu=.02, l=.4, d=.02, e=.02)
    q = np.zeros(NZ); q[0:48] = sig['x'] ** 2; q[48:144] = sig['c'] ** 2; q[720:744] = sig['l'] ** 2; q[744:792] = sig['d'] ** 2; q[792:816] = sig['e'] ** 2; Q = np.diag(q)
    for i in range(n): sl = slice(144 + i * S, 144 + (i + 1) * S); Q[sl, sl] = sig['mu'] ** 2 * (np.eye(S) - np.ones((S, S)) / S)
    U2 = U[:, sdim:]; C2 = solve_continuous_lyapunov(T[sdim:, sdim:], -U2.T @ Q @ U2); C2 = 0.5 * (C2 + C2.T); return U2 @ C2 @ U2.T, U2
def obs_matrix(arr, perm):
    """21 x 816 map: variable 3*j + r = region-r mean of the hidden quantity shown in package column c_j; region = tercile of the cell's place along head->tail"""
    xr = TM.Xs[0, perm]; order = np.argsort(xr); reg = np.zeros(n, int); reg[order[8:16]] = 1; reg[order[16:]] = 2; M = np.zeros((21, NZ)); lev = np.zeros((n, 7)); X, C, MU, L, D, E = arr; lev[:, :4] = C; lev[:, 4:6] = D; lev[:, 6] = E; ybar = np.zeros(21); Rv = np.zeros(21)
    for j in range(7):
        h = HNAME.index(PKGCOL[f'c{j}'])
        for r in range(3):
            cells = np.where(reg == r)[0]
            for i in cells:
                if h < 4: M[3 * j + r, OFF['c'] + i * 4 + h] = 1 / len(cells)
                elif h in (4, 5): M[3 * j + r, OFF['d'] + i * 2 + (h - 4)] = 1 / len(cells)
                else: M[3 * j + r, OFF['e'] + i] = 1 / len(cells)
            y = lev[cells, h]; ybar[3 * j + r] = y.mean(); Rv[3 * j + r] = 0.03 ** 2 * np.mean(y ** 2) / len(cells)
    return M, ybar, np.diag(Rv), reg
def Lgauss(C, I, B, E):
    ld = lambda idx: np.linalg.slogdet(C[np.ix_(idx, idx)])[1] if len(idx) else 0.0
    return 0.5 * (ld(I + B) + ld(E + B) - ld(B) - ld(I + B + E))
def var(chs): return [3 * int(c[1]) + r for c in chs for r in range(3)]
def partitions():
    P = {}
    for nm, (I, B, E) in dict(chanA=(['c4', 'c5'], ['c6'], ['c0', 'c1', 'c2', 'c3']), chanB=(['c0', 'c1', 'c2', 'c3'], ['c6'], ['c4', 'c5']), chanC=(['c4', 'c5'], ['c0', 'c1', 'c2', 'c3'], ['c6']), chanD=(['c6'], ['c0', 'c1', 'c2', 'c3'], ['c4', 'c5']),
                              chanE=(['c0', 'c1', 'c2', 'c3'], ['c4', 'c5'], ['c6']), chanF=(['c6'], ['c4', 'c5'], ['c0', 'c1', 'c2', 'c3'])).items(): P[nm] = (var(I), var(B), var(E))
    allv = list(range(21)); P['louvain(c0-3,c6 | c4,c5)'] = (var(['c0', 'c1', 'c2', 'c3', 'c6']), [], var(['c4', 'c5']))
    for perm in itertools.permutations(range(3)):
        P[f'region I={perm[0]} B={perm[1]} E={perm[2]}'] = tuple([3 * j + perm[k] for j in range(7)] for k in range(3))
    # truth-based module split: memory module (package columns showing d_A, d_B, reporter e) vs structural
    P['TRUE module split (c0,c4,c5 | c1,c2,c3,c6)'] = (var(['c1', 'c2', 'c3', 'c6']), [], var(['c0', 'c4', 'c5']))
    return P
def main():
    out = {}
    for state in 'ab':
        arr, perm, J = setup(state); C, U2 = lna(J); M, ybar, R, reg = obs_matrix(arr, perm); Cy = M @ C @ M.T + R; Cy0 = M @ C @ M.T; rng = np.random.default_rng(0); P = partitions()
        res = {}
        for nm, (I, B, E) in P.items():
            nulls = []
            for _ in range(500):
                pm = rng.permutation(21); a = pm[:len(I)].tolist(); b = pm[len(I):len(I) + len(B)].tolist(); e = pm[len(I) + len(B):].tolist(); nulls.append(Lgauss(Cy, a, b, e))
            L = Lgauss(Cy, I, B, E); res[nm] = dict(L_true_within=float(L), L_state_noise_free_obs=float(Lgauss(Cy0, I, B, E)), null_median=float(np.median(nulls)), null_percentile=float(np.mean(np.array(nulls) < L)))
        out[state] = dict(partitions=res, ybar=ybar.tolist(), Cy_diag_sd=np.sqrt(np.diag(Cy)).tolist(), cond_Cy=float(np.linalg.cond(Cy)))
        if state == 'a': ya = ybar; Ca = Cy; Ma = M; Ja = J
        else:
            d = ya - ybar; Cp = 0.5 * (Ca + Cy) + 0.25 * np.outer(d, d)                                                                  # pooled two-state mixture (equal weights), population
            for nm, (I, B, E) in P.items(): out['a'].setdefault('pooled', {})[nm] = float(Lgauss(Cp, I, B, E))
    # module structure and directed influence (state a Jacobian)
    arr, perm, J = setup('a'); M, ybar, R, reg = obs_matrix(arr, perm)
    blocks = dict(x=slice(0, 48), c=slice(48, 144), mu=slice(144, 720), mem=np.r_[720:816])
    idx = lambda b: np.arange(NZ)[blocks[b]] if isinstance(blocks[b], slice) else blocks[b]
    mod = {}
    for a, b in itertools.product(('x', 'c', 'mu', 'mem'), repeat=2):
        if a != b: mod[f'dF[{a}]/d[{b}] (norm)'] = float(np.linalg.norm(J[np.ix_(idx(a), idx(b))]))
    out['module_structure'] = mod
    Mp = np.linalg.pinv(M); G0 = M @ J @ Mp; G100 = M @ expm(100 * J) @ Mp; groups = dict(memlig=var(['c4', 'c5']), reporter=var(['c0']), types=var(['c1', 'c2', 'c3']), axial=var(['c6']))
    infl = {}
    for nm, G in (('native (Jacobian, per tu)', G0), ('lag 100 tu (expm(100J))', G100)):
        t = {}
        for a, b in itertools.permutations(groups, 2): t[f'{a}->{b}'] = float(np.linalg.norm(G[np.ix_(groups[b], groups[a])]))
        infl[nm] = t
    out['directed_influence_observable'] = infl; json.dump(out, open(os.path.join(AUD, 'data', 'a8_info.json'), 'w'), indent=1)
    print('module structure (Jacobian block norms)', {k: round(v, 4) for k, v in mod.items()})
    print('\nLeakage (nats) state a: partition: true within-state L | with noise-free obs | random-partition null median [percentile] | pooled two-state mixture')
    for nm, v in out['a']['partitions'].items(): print(f'{nm:42s} {v["L_true_within"]:.4f} | {v["L_state_noise_free_obs"]:.4f} | {v["null_median"]:.4f} [{v["null_percentile"]:.3f}] | pooled {out["a"]["pooled"][nm]:.4f}')
    print('\ndirected influence between groups', json.dumps({k: {a: round(b, 4) for a, b in v.items()} for k, v in infl.items()}, indent=0)[:1800])
if __name__ == "__main__": main()
