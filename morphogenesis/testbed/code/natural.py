"""T3.3 natural ensembles for L and R at operating noise; pilot decorrelation time first."""
import sys, json, os; sys.path.insert(0, '.')
from par import run_jobs

def acf_job(kind, T=900.0, burn=100.0):
    from interface import Experiment, np
    from asm import jax
    ex = Experiment(kind, seed=5, noise=0.02, private={}); w = ex.w; frames = []
    w.run(burn)
    for _ in range(int(T)): w.run(1.0); frames.append(w.X.copy())
    X = np.array(frames); Xm = X.mean(0); out = []
    def align(A, B):
        a = A - A.mean(0); b = B - B.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        return (R @ a.T).T
    ref = Xm - Xm.mean(0); D = np.stack([align(x, ref) - ref for x in X]).reshape(len(X), -1)
    D = D - D.mean(0); var = (D ** 2).sum(1).mean()
    acf = np.array([(D[:len(D) - l] * D[l:]).sum(1).mean() / var for l in range(0, 150)])
    l_e = int(np.argmax(acf < np.exp(-1))); tau_int = float(1 + 2 * acf[1:np.argmax(acf < 0) if (acf < 0).any() else 150].sum())
    # belief-block "decorrelation": drift of logits over the run
    return dict(kind=kind, acf_1_over_e_lag=l_e, tau_int=tau_int, acf_samples=[float(a) for a in acf[::10]], rms_dev=float(np.sqrt(var / w.t.n / 2)))

def body_job(kind, seed, n_samples, spacing, burn=100.0, tag='cal'):
    from interface import Experiment, np, OBS_EVERY
    ex = Experiment(kind, seed=seed, noise=0.02, private={}); w = ex.w; w.run(burn); t_ex = []
    xs, cs = [], []
    for k in range(n_samples):
        w.run(spacing); xs.append(w.X.copy()); cs.append(w.C.copy())
    os.makedirs('../data/natural_v1', exist_ok=True); p = f'../data/natural_v1/{kind}_{tag}_{seed:03d}.npz'
    np.savez_compressed(p, X=np.array(xs), C=np.array(cs), spacing=spacing, cell_id=w.cell_id)
    return p

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == 'pilot':
        res = run_jobs(acf_job, [('L',), ('R',)], workers=2, label='acf'); json.dump(res, open('../data/natural_pilot.json', 'w'), indent=1)
        for r in res: print(r['kind'], 'lag(1/e)', r['acf_1_over_e_lag'], 'tau_int', round(r['tau_int'], 2), 'rms_dev', round(r['rms_dev'], 4))
    elif mode == 'ens':
        spacing = float(sys.argv[2]); ns = int(sys.argv[3])
        args = [(kind, seed, ns, spacing, 100.0, tag) for kind in ('L', 'R') for tag, seeds in (('cal', range(100, 320)), ('val', range(400, 460))) for seed in seeds]
        res = run_jobs(body_job, args, workers=8, label='nat'); json.dump(dict(spacing=spacing, n_samples_per_body=ns, files=res), open('../data/natural_v1/manifest.json', 'w'))
