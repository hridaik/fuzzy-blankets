"""G4 identity events under v2 (v1 Part I protocols, deterministic) + handedness readout."""
import sys, json, time; sys.path.insert(0, '.')
def hand(w, g):
    from world2 import np
    r = w.rho()[g]; return dict(mean_rho=float(r.mean()), frac_L=float((r > 0.5).mean()), n=int(len(g)))
def body_row_hand(w, g):
    """handedness read from morphology (body-row cell types): fraction of body-row cells whose secreted code is closer to L than R code of the place they hold (argmax place)"""
    from world2 import np, jax, jnp
    tm = w.tm; q = np.array(jax.nn.softmax(jnp.array(w.MU[g]), axis=1)); pl = q.argmax(1); br = (tm.CL != tm.CR).any(0); sel = br[pl]
    if sel.sum() == 0: return dict(n_br=0, frac_L=None)
    C = w.C[g][sel]; dL = np.linalg.norm(C - tm.CL[:, pl[sel]].T, axis=1); dR = np.linalg.norm(C - tm.CR[:, pl[sel]].T, axis=1)
    return dict(n_br=int(sel.sum()), frac_L=float((dL < dR).mean()))
def job_replace(i, T=400.0):
    from world2 import new_adult2, describe2, np, jax, jnp
    w = new_adult2('L', capacity=24, noise=0, key=i); place = int(w.perm0[i]); before = describe2(w); w.replace(i, seed=i); t50 = t90 = None; t0 = w.time
    for _ in range(int(T / 5)):
        w.run(5.0); p = np.array(jax.nn.softmax(jnp.array(w.MU[i])))
        if t50 is None and p[place] > 0.5: t50 = w.time - t0
        if t90 is None and p[place] > 0.9: t90 = w.time - t0
    d = describe2(w); return dict(cell=i, place=place, type=int(w.tm.types[0][place]), t50=t50, t90=t90, after=d, rho_new_cell=float(w.rho()[i]), body_row_hand=body_row_hand(w, np.arange(24)))
def job_serial(seed, interval, T_settle=400.0):
    from world2 import new_adult2, describe2, np
    w = new_adult2('L', capacity=24, noise=0, key=seed); order = np.random.default_rng(seed).permutation(24); traj = []
    for i in order:
        w.replace(int(i), seed=seed); w.run(interval); d = describe2(w); traj.append((int(i), d['shape'], d['slots_once'], d['n_components'], round(d['mean_rho'], 3)))
    w.run(T_settle); fin = describe2(w)
    return dict(seed=seed, interval=interval, final=fin, traj=traj, all_new=bool((w.cell_id >= 24).all()), n_unique_ids=int(len(set(w.cell_id.tolist()))), body_row_hand=body_row_hand(w, np.arange(24)))
def job_extrude(i, vec, T=300.0):
    from world2 import new_adult2, describe2, np
    w = new_adult2('L', capacity=24, noise=0, key=i); place = int(w.perm0[i]); c = w.X[w.alive].mean(0); u = w.X[i] - c; u = u / (np.linalg.norm(u) + 1e-9)
    w.extrude(i, np.asarray(vec) * u); w.run(T); d = describe2(w); D = np.linalg.norm(w.X - w.X[i], axis=1); D[i] = 99
    return dict(cell=i, place=place, type=int(w.tm.types[0][place]), dist_after=float(D.min()), rejoined=bool(D.min() < 1.6), after=d)
def job_cut(kind, form='L', sep=7.0, T=400.0, Tpost=1500.0):
    from world2 import new_adult2, describe2, np
    w = new_adult2(form, capacity=24, noise=0, key=0); Tb = w.tm.Xs[:, w.perm0].T
    if kind == 'y': mask = Tb[:, 1] > 0.0; vec = np.array([0.0, sep])
    else: mask = Tb[:, 0] > 0.0; vec = np.array([sep, 0.0])
    X = w.X; a = Tb - Tb.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    A = np.where(mask)[0]; B = np.where(~mask)[0]; h0 = (hand(w, A), hand(w, B)); w.cut(mask, R @ vec); w.run(T)
    DA = np.linalg.norm(w.X[A][:, None] - w.X[B][None], axis=-1).min()
    out = dict(kind=kind, form=form, sep=sep, fragA=describe2(w, A), fragB=describe2(w, B), hand0=h0, handA=hand(w, A), handB=hand(w, B), min_inter_fragment_distance=float(DA), reunited=bool(DA < 1.6), whole=describe2(w))
    w.run(Tpost); out['hand_late'] = (hand(w, A), hand(w, B)); out['whole_late'] = describe2(w); return out
def job_fuse(kinds, offset, T=400.0, Tpost=1500.0):
    from world2 import new_adult2, fuse2, describe2, np
    a = new_adult2(kinds[0], capacity=24, noise=0, key=1); b = new_adult2(kinds[1], capacity=24, noise=0, key=2, form_seed=0) if False else new_adult2(kinds[1], k=1, capacity=24, noise=0, key=2); w = fuse2(a, b, offset)
    g1 = np.arange(24); g2 = np.arange(24, 48); h0 = (hand(w, g1), hand(w, g2)); w.run(T)
    out = dict(kinds=kinds, offset=offset, A=describe2(w, g1), B=describe2(w, g2), whole=describe2(w), hand0=h0, handA=hand(w, g1), handB=hand(w, g2), handWhole=hand(w, np.arange(48)),
               merged=bool(describe2(w)['n_components'] == 1), min_inter_body=float(np.linalg.norm(w.X[g1][:, None] - w.X[g2][None], axis=-1).min()))
    w.run(Tpost); out['hand_late'] = (hand(w, g1), hand(w, g2)); out['whole_late'] = describe2(w); return out
if __name__ == "__main__":
    from par import run_jobs; mode = sys.argv[1]; t0 = time.time()
    if mode == 'a': res = run_jobs(job_replace, [(i,) for i in range(24)], workers=8, label='g4a'); json.dump(res, open('../data/g4a_replace.json', 'w'))
    elif mode == 'b': res = run_jobs(job_serial, [(s, 100.0) for s in range(4)], workers=4, label='g4b'); json.dump(res, open('../data/g4b_serial.json', 'w'))
    elif mode == 'c': res = run_jobs(job_extrude, [(i, [8.0, 0.0]) for i in range(24)], workers=8, label='g4c'); json.dump(res, open('../data/g4c_extrude.json', 'w'))
    elif mode == 'd': res = run_jobs(job_cut, [('y', 'L'), ('x', 'L'), ('y', 'R'), ('x', 'R')], workers=4, label='g4d'); json.dump(res, open('../data/g4d_cut.json', 'w'))
    elif mode == 'e': res = run_jobs(job_fuse, [((a, b), off) for (a, b) in (('L', 'L'), ('L', 'R')) for off in ([9.0, 0.0], [8.0, 0.0], [8.0, 3.0])], workers=6, label='g4e'); json.dump(res, open('../data/g4e_fuse.json', 'w'))
    print('wall', time.time() - t0)
