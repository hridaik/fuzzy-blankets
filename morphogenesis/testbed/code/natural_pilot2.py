"""Pilot 2: (i) dissolution time of unperturbed bodies under operating noise (from the 200-tu-spaced ensemble); (ii) decorrelation time of the FAST fluctuations (detrended ACF) from 1-tu frames."""
import sys, json, glob, os; sys.path.insert(0, '.')
from par import run_jobs
def fast_job(kind, seed, T=1500.0):
    from interface import Experiment, np
    ex = Experiment(kind, seed=seed, noise=0.02); w = ex.w; w.run(100.0); fr = []
    for _ in range(int(T)): w.run(1.0); fr.append(w.X.copy())
    X = np.array(fr)
    def align(A, B):
        a = A - A.mean(0); b = B - B.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        return (R @ a.T).T
    ref = X[0] - X[0].mean(0); D = np.stack([align(x, ref) for x in X]).reshape(len(X), -1)
    # detrend: subtract centred moving average (window 201)
    k = 201; ker = np.ones(k) / k; trend = np.stack([np.convolve(D[:, j], ker, mode='same') for j in range(D.shape[1])], 1)
    R_ = (D - trend)[k:-k]; var = (R_ ** 2).sum(1).mean(); acf = np.array([(R_[:len(R_) - l] * R_[l:]).sum(1).mean() / var for l in range(0, 120)])
    lag = int(np.argmax(acf < np.exp(-1))) if (acf < np.exp(-1)).any() else None
    return dict(kind=kind, seed=seed, acf=[float(a) for a in acf[::5]], lag_1_over_e=lag, resid_rms_per_coord=float(np.sqrt(var / D.shape[1])))
if __name__ == "__main__":
    import numpy as np
    sys.path.insert(0, '.')
    from asm import make_body
    import chiral as CH
    t = make_body('chiral'); out = {}
    for kind in ('L', 'R'):
        first_bad = []
        for f in sorted(glob.glob(f'../data/natural_v1/{kind}_cal_*.npz')) + sorted(glob.glob(f'../data/natural_v1/{kind}_val_*.npz')):
            d = np.load(f); X, C = d['X'], d['C']; fb = None
            for k in range(len(X)):
                lab, dL, dR = CH.classify(t, X[k], C[k])
                if lab == 'defect': fb = k; break
            first_bad.append(fb if fb is not None else 64)
        out[kind] = dict(first_defect_sample=first_bad, first_defect_time=[200 * b for b in first_bad], median_time=float(np.median(first_bad) * 200), frac_intact_at_1600=float(np.mean([b > 8 for b in first_bad])), frac_intact_at_3200=float(np.mean([b > 16 for b in first_bad])))
        print(kind, 'median first-defect time', out[kind]['median_time'], 'intact at 1600:', out[kind]['frac_intact_at_1600'], 'at 3200:', out[kind]['frac_intact_at_3200'])
    res = run_jobs(fast_job, [(k, s) for k in ('L', 'R') for s in (11, 12, 13, 14)], workers=8, label='fast'); out['fast'] = res
    for r in res: print(r['kind'], r['seed'], 'lag(1/e)', r['lag_1_over_e'], 'rms', round(r['resid_rms_per_coord'], 4))
    json.dump(out, open('../data/natural_pilot2.json', 'w'), indent=1)
