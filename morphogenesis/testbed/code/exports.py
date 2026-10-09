"""T2f: OBSERVABLE / HIDDEN tier exports + loader that refuses hidden access without an audit flag."""
import os, sys, numpy as np; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import *

OBS_KEYS = ['t', 'X', 'C', 'types']                     # what an outside observer sees: positions, secreted signals, colour type
HID_KEYS = ['alive', 'cell_id', 'membership', 'component', 'role', 'belief', 'planB', 'free_energy', 'influence_frames', 'influence_norm', 'extruded']

def component_labels(X, radius=1.6):
    n = len(X); D = np.linalg.norm(X[:, None] - X[None], axis=-1) < radius; lab = -np.ones(n, int); k = 0
    for s in range(n):
        if lab[s] >= 0: continue
        st = [s]; lab[s] = k
        while st:
            u = st.pop()
            for v in np.where(D[u] & (lab < 0))[0]: lab[v] = k; st.append(v)
        k += 1
    return lab

def influence_norms(eng, state, t=1e9):
    """(n,n) Frobenius norm of the Jacobian block d f_i / d state_j (f_i: cell i's whole flow; state_j: x_j,c_j,mu_j,zeta_j), i != j; autodiff."""
    n, nc, K = eng.n, eng.nc, eng.K; S = eng.S
    J = np.array(eng.jac_flat(state, t)); sizes = [2, nc, S, K]; offs = np.cumsum([0] + [n * s for s in sizes])
    def idx(i):  # flat indices of cell i's variables
        return np.concatenate([offs[b] + i * sizes[b] + np.arange(sizes[b]) for b in range(4)])
    I = [idx(i) for i in range(n)]
    N = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j: N[i, j] = np.linalg.norm(J[np.ix_(I[i], I[j])])
    return N

def export_run(path, eng, tmpl, frames, t, plan_for_types=0, influence_every=None, kernel_radius=1.6):
    """frames: tuple of arrays (T,n,2),(T,n,nc),(T,n,n),(T,n,K) saved states. Writes <path>_obs.npz and <path>_hid.npz"""
    X, C, MU, ZE = [np.asarray(a) for a in frames]; T, n = X.shape[:2]
    types = np.stack([cell_types(C[k].T) for k in range(T)])
    p = np.array(jax.nn.softmax(jnp.array(MU), axis=2)); role = p.argmax(2)
    comp = np.stack([component_labels(X[k], kernel_radius) for k in range(T)])
    ncomp = comp.max(1) + 1
    planB = np.array(jax.nn.softmax(jnp.array(ZE), axis=2))[:, :, -1] if tmpl.K > 1 else np.zeros((T, n))
    F = np.stack([np.array(eng.free_energy((jnp.array(X[k]), jnp.array(C[k]), jnp.array(MU[k]), jnp.array(ZE[k])))) for k in range(T)])
    infl_frames = np.arange(0, T, influence_every or max(1, T // 4)); infl = np.stack([influence_norms(eng, (jnp.array(X[k]), jnp.array(C[k]), jnp.array(MU[k]), jnp.array(ZE[k]))) for k in infl_frames])
    extr = np.array([(np.linalg.norm(X[k][:, None] - X[k][None], axis=-1) + 9 * np.eye(n)).min(1) > kernel_radius for k in range(T)])
    np.savez_compressed(path + '_obs.npz', t=np.asarray(t), X=X, C=C, types=types)
    np.savez_compressed(path + '_hid.npz', alive=np.ones((T, n), bool), cell_id=np.tile(np.arange(n), (T, 1)), membership=np.ones((T, n), bool), component=comp,
                        n_components=ncomp, role=role, belief=p, planB=planB, free_energy=F, influence_frames=infl_frames, influence_norm=infl, extruded=extr)
    return path

def load_tier(path, tier='obs', audit=False):
    """tier 'obs' always allowed; 'hid' requires audit=True (explicit flag) -- the analogue of the flock programme's no-leakage tests"""
    if tier == 'hid' and not audit:
        raise PermissionError('HIDDEN tier requested without audit=True: refusing (blind analyses must use the OBSERVABLE tier only)')
    f = path + ('_hid.npz' if tier == 'hid' else '_obs.npz')
    return dict(np.load(f))
