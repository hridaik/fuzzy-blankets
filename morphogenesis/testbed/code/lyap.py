"""T3.5 analytic linear-noise stationary covariance at the L and R fixed points (Lyapunov equation from the autodiff Jacobian and the noise covariance).
state z = (x, c, mu) of all cells; dz = J z dt + G dW, G = diag(sigma on x and c, sigma_mu on mu). Neutral modes (rigid motion; |Re lambda| < 1e-7) have no stationary law: they are projected out and reported."""
import sys, json; sys.path.insert(0, '.')
from s3common import *

def lna(kind, k=0, sig=0.02, smu=0.0):
    t, eng = setup(sig=sig, smu=smu); fin, perm = adult(t, eng, k, mirror=(kind == 'R'), settle=400.0)
    n, nc, S = t.n, t.nc, t.n
    J = np.array(eng.jac_flat(fin, 1e4)); m = n * (2 + nc + S); J = J[:m, :m]
    g = np.concatenate([np.full(n * 2, sig), np.full(n * nc, sig), np.full(n * S, smu)]); Q = np.diag(g ** 2)
    lam, V = np.linalg.eig(J); Vi = np.linalg.inv(V)
    stable = lam.real < -1e-7; Qt = Vi @ Q @ Vi.conj().T
    den = -(lam[:, None] + lam[None, :].conj()); mask = stable[:, None] & stable[None, :]
    Sg = np.where(mask, Qt / np.where(mask, den, 1.0), 0.0); Sigma = (V @ Sg @ V.conj().T).real
    px = Sigma[:n * 2, :n * 2]; pc = Sigma[n * 2:n * (2 + nc), n * 2:n * (2 + nc)]
    fast = stable & (lam.real < -1e-2)
    Sgf = np.where(fast[:, None] & fast[None, :], Qt / np.where(mask, den, 1.0), 0.0); Sf = (V @ Sgf @ V.conj().T).real
    return dict(kind=kind, n_neutral=int((~stable & (np.abs(lam.real) < 1e-7)).sum()), n_unstable=int((lam.real > 1e-7).sum()), n_stable=int(stable.sum()), slowest_stable=float(lam.real[stable].max()),
                mean_pos_var_per_coord=float(np.trace(px) / (2 * n)), mean_pos_var_fastmodes=float(np.trace(Sf[:n * 2, :n * 2]) / (2 * n)), mean_c_var=float(np.trace(pc) / (n * nc)), Sigma=Sigma, J=J, fixed_point=np.concatenate([np.array(a).ravel() for a in fin[:3]]))

if __name__ == "__main__":
    out = {}
    for kind in ('L', 'R'):
        r = lna(kind); np.savez_compressed(f'../data/lna_{kind}.npz', Sigma=r['Sigma'], J=r['J'], fixed_point=r['fixed_point'])
        out[kind] = {k: v for k, v in r.items() if k not in ('Sigma', 'J', 'fixed_point')}; print(out[kind])
    json.dump(out, open('../data/lna_summary.json', 'w'), indent=1)
