"""H4 identity events with memory outcomes (v2 protocols)."""
import sys, json, time; sys.path.insert(0, '.')
from world3 import *
def adopt_time(w, j, T, every=2.0, thr=0.9):
    t0 = w.time; t50 = t90 = None
    for _ in range(int(T / every)):
        w.run(every); r = float(w.rho()[j])
        if t50 is None and r > 0.5: t50 = w.time - t0
        if t90 is None and r > thr: t90 = w.time - t0
    return t50, t90
def job_replace(i, T=400.0):
    w = new_adult3('a', capacity=24, noise=0.0, key=i); place = int(w.perm0[i]); w.replace(i, seed=i); t50, t90 = adopt_time(w, i, T); d = describe3(w)
    return dict(cell=i, place=place, type=int(w.tm.types[0][place]), t50=t50, t90=t90, rho_new=float(w.rho()[i]), after=d, adopts=bool(w.rho()[i] > 0.5))
def job_serial(seed, interval=100.0, T_settle=400.0):
    w = new_adult3('a', capacity=24, noise=0.0, key=seed); order = np.random.default_rng(seed).permutation(24); traj = []
    for i in order: w.replace(int(i), seed=seed); w.run(interval); d = describe3(w); traj.append((int(i), d['shape'], round(d['mean_rho'], 3), d['n_components']))
    w.run(T_settle); return dict(seed=seed, final=describe3(w), traj=traj, all_new=bool((w.cell_id >= 24).all()), n_unique=int(len(set(w.cell_id.tolist()))))
def job_extrude(i, vec=(8.0, 0.0), T=300.0):
    w = new_adult3('a', capacity=24, noise=0.0, key=i); place = int(w.perm0[i]); c = w.X.mean(0); u = w.X[i] - c; u = u / (np.linalg.norm(u) + 1e-9); w.extrude(i, np.asarray(vec) * u); w.run(T)
    D = np.linalg.norm(w.X - w.X[i], axis=1); D[i] = 99; return dict(cell=i, place=place, type=int(w.tm.types[0][place]), rejoined=bool(D.min() < 1.6), after=describe3(w), rho_i=float(w.rho()[i]))
def cut_masks(w, kind):
    Tb = w.tm.Xs[:, w.perm0].T; return (Tb[:, 1] > 0) if kind == 'yp' else ((Tb[:, 0] > 0) if kind == 'x' else (Tb[:, 1] > 0))
def job_cut(kind, state='a', noise=0.0, sig_h=0.0, seed=0, sep=7.0, T=1500.0):
    w = new_adult3(state, capacity=24, noise=noise, sig_h=sig_h, key=seed); Tb = w.tm.Xs[:, w.perm0].T; mask = (Tb[:, 0] > 0) if kind == 'x' else (Tb[:, 1] > 0)
    a_ = Tb - Tb.mean(0); b_ = w.X - w.X.mean(0); U, S, Vt = np.linalg.svd(a_.T @ b_); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    A = np.where(mask)[0]; B = np.where(~mask)[0]; w.cut(mask, R @ (np.array([sep, 0.0]) if kind == 'x' else np.array([0.0, sep]))); rows = []; t = 0.0
    for tt in (25, 50, 100, 200, 400, 800, 1500, 2500, 4000):
        if tt > T: break
        w.run(tt - t); t = tt; r = w.rho(); rows.append((tt, float(r[A].mean()), float(r[B].mean()), describe3(w, A)['n_components'], describe3(w, B)['n_components']))
    X = w.X; D = np.linalg.norm(X[A][:, None] - X[B][None], axis=-1).min()
    return dict(kind=kind, state=state, noise=noise, seed=seed, nA=int(len(A)), nB=int(len(B)), rows=rows, min_inter=float(D), fragA=describe3(w, A), fragB=describe3(w, B))
def job_fuse(states, offset, noise=0.0, sig_h=0.0, T=2500.0, angle=0.0, seed=0):
    a = new_adult3(states[0], capacity=24, noise=noise, sig_h=sig_h, key=1 + seed); b = new_adult3(states[1], k=1, capacity=24, noise=noise, sig_h=sig_h, key=2 + seed); w = fuse3(a, b, offset, angle); w.key = jax.random.PRNGKey(7000 + seed); g1 = np.arange(24); g2 = np.arange(24, 48); rows = []; t = 0.0
    for tt in (10, 25, 50, 100, 200, 400, 800, 1500, 2500):
        if tt > T: break
        w.run(tt - t); t = tt; r = w.rho(); rows.append((tt, float(r[g1].mean()), float(r[g2].mean()), float((r > 0.5).mean())))
    r = w.rho(); X = w.X; dmin = float(np.linalg.norm(X[g1][:, None] - X[g2][None], axis=-1).min()); comp = int(component_labels(X, 1.6).max() + 1)
    wall = bool(0.1 < (r > 0.5).mean() < 0.9); return dict(states=states, offset=offset, noise=noise, seed=seed, rows=rows, min_inter=dmin, n_components=comp, wall_persists=wall, whole=describe3(w), A=describe3(w, g1), B=describe3(w, g2))
if __name__ == "__main__":
    from par import run_jobs; mode = sys.argv[1]; t0 = time.time()
    if mode == 'a': res = run_jobs(job_replace, [(i,) for i in range(24)], workers=8, label='h4a'); json.dump(res, open('../data/h4a_replace.json', 'w'))
    elif mode == 'b': res = run_jobs(job_serial, [(s,) for s in range(4)], workers=4, label='h4b'); json.dump(res, open('../data/h4b_serial.json', 'w'))
    elif mode == 'c': res = run_jobs(job_extrude, [(i,) for i in range(24)], workers=8, label='h4c'); json.dump(res, open('../data/h4c_extrude.json', 'w'))
    elif mode == 'd':
        args = [(k, 'a', 0.0, 0.0, 0) for k in ('x', 'y')] + [(k, 'a', 0.02, 0.4, s) for k in ('x', 'y') for s in range(3)]
        res = run_jobs(job_cut, args, workers=8, label='h4d'); json.dump(res, open('../data/h4d_cut.json', 'w'))
    elif mode == 'e2':
        offs = [[6.0, 0.0], [5.0, 0.0], [0.0, 3.0], [0.0, 2.0]]
        args = [(('a', 'b'), o, 0.02, 0.4, 2500.0, 0.0, s) for o in offs for s in range(8)]
        res = run_jobs(job_fuse, args, workers=8, label='h4e2'); json.dump(res, open('../data/h4e2_fuse_noisy.json', 'w'))
    elif mode == 'e':
        offs = [[7.2, 0.0], [6.0, 0.0], [5.0, 0.0], [0.0, 3.0], [0.0, 2.0]]
        args = [(st, o, 0.0, 0.0) for st in (('a', 'a'), ('a', 'b')) for o in offs] + [(('a', 'b'), o, 0.02, 0.4, 2500.0, 0.0, s) for o in offs[1:4] for s in range(2)]
        res = run_jobs(job_fuse, args, workers=8, label='h4e'); json.dump(res, open('../data/h4e_fuse.json', 'w'))
    print('wall', time.time() - t0)
