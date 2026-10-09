import numpy as np, glob, json, os
def align(A, B):
    a = A - A.mean(0); b = B - B.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    return (R @ a.T).T
out = {}
lna = json.load(open('../data/lna_summary.json'))
for kind in ('L', 'R'):
    for tag in ('cal', 'val'):
        fs = sorted(glob.glob(f'../data/natural_v1/{kind}_{tag}_*.npz')); acs = []; vars_ = []; n = 0
        for f in fs:
            d = np.load(f); X = d['X']; n += len(X); ref = X.mean(0) - X.mean(0).mean(0)
            D = np.stack([align(x, ref) - ref for x in X]).reshape(len(X), -1); D = D - D.mean(0)
            v = (D ** 2).sum(1).mean(); vars_.append(v / (X.shape[1] * 2))
            acs.append((D[:-1] * D[1:]).sum(1).mean() / v)
        out[f'{kind}_{tag}'] = dict(n_bodies=len(fs), n_samples=n, lag1_autocorr_at_spacing=float(np.mean(acs)), lag1_sd=float(np.std(acs)), var_per_coord_mean=float(np.mean(vars_)), n_eff_approx=float(n * (1 - np.mean(acs)) / (1 + np.mean(acs))))
        print(kind, tag, out[f'{kind}_{tag}'])
out['lna_fast_modes_var_per_coord'] = {k: lna[k]['mean_pos_var_fastmodes'] for k in lna}; out['lna_all_stable_var_per_coord'] = {k: lna[k]['mean_pos_var_per_coord'] for k in lna}
json.dump(out, open('../data/natural_stats.json', 'w'), indent=1); print(out['lna_fast_modes_var_per_coord'], out['lna_all_stable_var_per_coord'])
