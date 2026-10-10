"""H5 natural ensembles: decorrelation pilot (structure shape, per-cell l vector, reporter vector, mean l)."""
import sys, json, time; sys.path.insert(0, '.')
from world3 import *
def acf_job(state, T=1200.0, burn=150.0):
    ex = Experiment3(state, seed=5, noise=0.02, sig_h=0.4, form_seed=5); w = ex.w; w.time = 0.0; w.run(burn); Xs, Ls, Es, Ml = [], [], [], []
    for _ in range(int(T)):
        w.run(1.0); Xs.append(w.X.copy()); Ls.append(w.L.copy()); Es.append(w.E.copy()); Ml.append(w.L.mean())
    X = np.array(Xs); Xm = X.mean(0)
    def align(A, B):
        a = A - A.mean(0); b = B - B.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        return (R @ a.T).T
    ref = Xm - Xm.mean(0); Ds = np.stack([align(x, ref) - ref for x in X]).reshape(len(X), -1)
    def acf(M, nl=400):
        M = M.reshape(len(M), -1); M = M - M.mean(0); var = (M ** 2).sum(1).mean(); return np.array([(M[:len(M) - l] * M[l:]).sum(1).mean() / var for l in range(nl)])
    out = {}
    for nm, M in (('structure', Ds), ('l_vec', np.array(Ls)), ('reporter', np.array(Es)), ('mean_l', np.array(Ml)[:, None])):
        a = acf(M); l_e = int(np.argmax(a < np.exp(-1))) if (a < np.exp(-1)).any() else len(a); zc = int(np.argmax(a < 0)) if (a < 0).any() else len(a); tau_int = float(1 + 2 * a[1:max(zc, 2)].sum()); out[nm] = dict(lag_1e=l_e, tau_int=tau_int)
    return dict(state=state, **out)
if __name__ == "__main__":
    from par import run_jobs; res = run_jobs(acf_job, [('a',), ('b',)], workers=2, label='acf'); json.dump(res, open('../data/natural_pilot.json', 'w'), indent=1)
    for r in res: print(r)
