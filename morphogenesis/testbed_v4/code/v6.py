"""V6 identity events under v4 (primary variant, median dish). Reports ORGANISM INTACT pieces, state, tail angle; cut fragments: state and angle each."""
import sys, json, time
from world4 import *
def aligned_cut(w, kind, sep=7.0):
    Tb = TM.Xs[:, w.perm0].T; mask = (Tb[:, 0] > 0) if kind == 'x' else (Tb[:, 1] > 0)
    a_ = Tb - Tb.mean(0); b_ = w.X - w.X.mean(0); U, S, Vt = np.linalg.svd(a_.T @ b_); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    return mask, R @ (np.array([sep, 0.0]) if kind == 'x' else np.array([0.0, sep]))
def job_replace(i, T=400.0):
    w = new_world('a', key=i); base = nbr_matrix(w.X); place = int(w.perm0[i]); w.replace(i, seed=i); t50 = None
    for _ in range(int(T / 2)):
        w.run(2.0)
        if t50 is None and w.rho()[i] > 0.5: t50 = w.time - 1e4
    d = describe4(w, base=base); d.update(cell=i, place=place, type=int(TM.types[0][place]), t50=t50, rho_new=float(w.rho()[i]), adopts=bool(w.rho()[i] > 0.5), material_intact=False); return d
def job_extrude(i, vec=8.0, T=300.0):
    w = new_world('a', key=i); base = nbr_matrix(w.X); place = int(w.perm0[i]); c = w.X.mean(0); u = w.X[i] - c; u /= np.linalg.norm(u) + 1e-9; w.extrude(i, vec * u); w.run(T)
    D = np.linalg.norm(w.X - w.X[i], axis=1); D[i] = 99; d = describe4(w, base=base); d.update(cell=i, place=place, rejoined=bool(D.min() < 1.6), rho_i=float(w.rho()[i]), material_intact=True); return d
def job_serial(seed, interval=100.0, settle=400.0):
    w = new_world('a', key=seed); base = nbr_matrix(w.X); order = np.random.default_rng(seed).permutation(24); traj = []
    for i in order: w.replace(int(i), seed=seed); w.run(interval); d = describe4(w, base=base); traj.append((int(i), d['n_components'], round(d['mean_rho'], 3), d['angle']))
    w.run(settle); d = describe4(w, base=base); d.update(seed=seed, all_new=bool((w.cell_id >= 24).all()), traj=traj); return d
def job_cut(kind, noise, seed, T=1500.0):
    w = new_world('a', noise=noise, key=seed); mask, vec = aligned_cut(w, kind); A = np.where(mask)[0]; B = np.where(~mask)[0]; w.cut(mask, vec); rows = []; t = 0.0
    for tt in (25, 100, 400, 1500):
        if tt > T: break
        w.run(tt - t); t = tt; dA, dB = describe4(w, A), describe4(w, B); rows.append((tt, dA['mean_rho'], dB['mean_rho'], dA['angle'], dB['angle'], dA['n_components'], dB['n_components']))
    return dict(kind=kind, noise=noise, seed=seed, nA=int(len(A)), nB=int(len(B)), rows=rows, fragA=describe4(w, A), fragB=describe4(w, B), baseline_angle=float(tail_angle(TM, w.X[:0] if False else np.array(settled(median_dish(), 'phi04', 'a')[0][0]), np.array(jax.nn.softmax(jnp.array(settled(median_dish(), 'phi04', 'a')[0][2]), 1)).argmax(1))))
def job_fuse(states, offset, noise, seed, T=2500.0):
    from engine4 import make_engine4
    wa = new_world(states[0], noise=noise, key=1 + seed); wb = new_world(states[1], noise=noise, key=2 + seed)
    m2 = wb.X.mean(0); X2 = wb.X - m2 + m2 + np.asarray(offset); cat = np.concatenate
    st = tuple(cat([getattr(wa, k), getattr(wb, k) if k != 'X' else X2]) for k in ('X', 'C', 'MU', 'L', 'D', 'E', 'U'))
    P = get_engine(median_dish(), 'phi04', noise=noise, gamma_on=False).P; e2 = make_engine4(TM, P, N=48); e2.dt = DT
    w = World4(e2, st, key=7000 + seed); g1 = np.arange(24); g2 = np.arange(24, 48); rows = []; t = 0.0
    for tt in (50, 200, 800, 2500):
        if tt > T: break
        w.run(tt - t); t = tt; r = w.rho(); rows.append((tt, float(r[g1].mean()), float(r[g2].mean()), float((r > 0.5).mean())))
    D = np.linalg.norm(w.X[g1][:, None] - w.X[g2][None], axis=-1).min(); nc = connected_components(csr_matrix(nbr_matrix(w.X)), directed=False)[0]
    return dict(states=states, offset=list(offset), noise=noise, seed=seed, rows=rows, min_inter=float(D), n_components=int(nc), A=describe4(w, g1), B=describe4(w, g2))
if __name__ == "__main__":
    from par4 import run_jobs; mode = sys.argv[1]; t0 = time.time()
    if mode == 'replace': res = run_jobs(job_replace, [(i,) for i in range(24)], label='v6a'); json.dump(res, open('../data/v6_replace.json', 'w'))
    elif mode == 'extrude': res = run_jobs(job_extrude, [(i,) for i in range(24)], label='v6b'); json.dump(res, open('../data/v6_extrude.json', 'w'))
    elif mode == 'serial': res = run_jobs(job_serial, [(s,) for s in range(4)], workers=4, label='v6c'); json.dump(res, open('../data/v6_serial.json', 'w'))
    elif mode == 'cut':
        args = [(k, False, 0) for k in ('x', 'y')] + [(k, True, s) for k in ('x', 'y') for s in range(3)]; res = run_jobs(job_cut, args, label='v6d'); json.dump(res, open('../data/v6_cut.json', 'w'))
    elif mode == 'fuse':
        offs = [[7.2, 0.0], [6.0, 0.0], [5.0, 0.0], [0.0, 3.0], [0.0, 2.0]]
        args = [(st, o, False, 0) for st in (('a', 'a'), ('a', 'b')) for o in offs] + [(('a', 'b'), o, True, s) for o in offs[1:4] for s in range(4)]
        res = run_jobs(job_fuse, args, label='v6e'); json.dump(res, open('../data/v6_fuse.json', 'w'))
    print('wall', time.time() - t0)
