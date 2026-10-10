"""Hidden truth extras: influence matrices and linear-noise stationary covariance at both states (settled adult, seed 0).
Covariance: ordered real Schur decomposition J = U T U^T with the neutral cluster (|Re| < 1e-7) first; the non-neutral coordinates y = U2^T x obey dy = T22 y + U2^T dW exactly (closed), so C2 solves T22 C2 + C2 T22^T + U2^T Q U2 = 0."""
import sys, json; sys.path.insert(0, '.')
from world3 import *
from scipy.linalg import schur, solve_continuous_lyapunov
def run():
    out = {}; tm = make_template2(); S = 24; n = 24
    sig = dict(x=.02, c=.02, mu=.02, l=.4, d=.02, e=.02); sizes = [('x', 2), ('c', 4), ('mu', S), ('l', 1), ('d', 2), ('e', 1)]; offs = np.cumsum([0] + [n * s for _, s in sizes])
    idx = lambda i: np.concatenate([offs[b] + i * sizes[b][1] + np.arange(sizes[b][1]) for b in range(6)])
    for st in 'ab':
        arr, perm = settled3(st, 0); eng = make_engine3(tm, Params3()); state = tuple(jnp.array(a) for a in arr); J = np.array(eng.jac_flat(state)); I = [idx(i) for i in range(n)]
        infl = np.zeros((n, n)); dl = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i != j: infl[i, j] = np.linalg.norm(J[np.ix_(I[i], I[j])]); dl[i, j] = np.linalg.norm(J[offs[3] + i, I[j]])
        T, U, sdim = schur(J, output='real', sort=lambda re, im: abs(re) < 1e-7); T22 = T[sdim:, sdim:]; U2 = U[:, sdim:]
        q = np.zeros(J.shape[0])
        for b, (nm, s) in enumerate(sizes): q[offs[b]:offs[b + 1]] = sig[nm] ** 2
        Q = np.diag(q)
        mu0, mu1 = offs[2], offs[3]                                       # the place-logit noise is projected on zero-mean per cell
        for i in range(n):
            sl = slice(mu0 + i * S, mu0 + (i + 1) * S); Q[sl, sl] = sig['mu'] ** 2 * (np.eye(S) - np.ones((S, S)) / S)
        C2 = solve_continuous_lyapunov(T22, -U2.T @ Q @ U2); C2 = 0.5 * (C2 + C2.T); ev = np.linalg.eigvalsh(C2); C = U2 @ C2 @ U2.T
        ev_pos = ev[ev > 0]; sd = np.sqrt(np.maximum(np.diag(C), 0)); lsd = sd[offs[3]:offs[4]]
        ew = np.linalg.eigvals(T22)
        out[st] = dict(n_neutral=int(sdim), n_nonneutral=int(T22.shape[0]), max_re_nonneutral=float(ew.real.max()), slowest_nonneutral=float(np.sort(np.abs(ew.real))[0]), cov_eig_min=float(ev.min()), cov_eig_max=float(ev.max()), n_negative_eigs=int((ev < 0).sum()), cond=float(ev.max() / ev[ev > 0].min()),
                       l_std_lna_median=float(np.median(lsd)), l_std_lna_range=[float(lsd.min()), float(lsd.max())], x_std_median=float(np.median(sd[offs[0]:offs[1]])), e_std_median=float(np.median(sd[offs[5]:offs[6]])))
        np.savez_compressed(f'../data/hidden_influence_{st}.npz', influence=infl, dl_dcell=dl, cov_diag=np.diag(C), perm=perm)
    json.dump(out, open('../data/hidden_covariance.json', 'w'), indent=1); print(json.dumps(out, indent=1))
if __name__ == "__main__": run()
