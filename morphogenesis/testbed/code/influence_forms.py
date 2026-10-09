"""T3.5: influence-matrix exports (autodiff Jacobian block norms, kernel weights, distances) at the L and R adult states (declared frames: settled adult at t = 1e4; and 3 frames of the noisy run)."""
import sys, json; sys.path.insert(0, '.')
from s3common import *
from exports import influence_norms
out = {}
for kind in ('L', 'R'):
    t, eng = setup(sig=0.02); fin, perm = adult(t, eng, 0, mirror=(kind == 'R'), settle=400.0)
    frames = [fin]; st = fin
    for k in range(3):
        st = eng.run_final(st, 1e4 + 100 * k, eng.dt, int(100 / eng.dt), jax.random.PRNGKey(7 + k), None, 0); frames.append(st)
    N = np.stack([influence_norms(eng, f) for f in frames]); X = np.stack([np.array(f[0]) for f in frames]); D = np.linalg.norm(X[:, :, None] - X[:, None], axis=-1)
    K = np.exp(-D) * (1 - np.eye(t.n))
    np.savez_compressed(f'../data/influence_{kind}.npz', influence_norm=N, positions=X, distance=D, kernel=K, perm_cell_to_slot=perm)
    iu = np.triu_indices(t.n, 1); c = np.corrcoef(N[0][iu] + N[0].T[iu], K[0][iu])[0, 1]
    out[kind] = dict(n_frames=len(frames), corr_influence_vs_kernel_weight_frame0=float(c), median_influence_over_nearest10pct=float(np.median(N[0][D[0] < np.percentile(D[0], 10)])), median_influence_beyond_5=float(np.median(N[0][D[0] > 5])))
    print(kind, out[kind])
json.dump(out, open('../data/influence_summary.json', 'w'), indent=1)
