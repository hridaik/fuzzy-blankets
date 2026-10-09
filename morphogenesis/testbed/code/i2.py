"""Part I2 behaviour checks: replacement, serial replacement (Ship of Theseus), extrusion, cut, fusion. v2-style taxonomy adapted:
shape class (L/R/DEFECT/OTHER or fragment), slot completeness (slots filled exactly once / duplicated / vacant), roles (argmax slot, relabelled fraction), events."""
import sys, json; sys.path.insert(0, '.')
from par import run_jobs

def describe(w, group=None):
    """descriptor of a set of alive cells (default all alive)"""
    from world import np, jax, jnp, CH
    from exports import component_labels
    g = np.where(w.alive)[0] if group is None else np.array(group)
    X = w.X[g]; p = np.array(jax.nn.softmax(jnp.array(w.MU[g]), axis=1)); slot = p.argmax(1)
    cnt = np.bincount(slot, minlength=w.t.n); comp = component_labels(X, 1.6); D = np.linalg.norm(X[:, None] - X[None], axis=-1) + 9 * np.eye(len(g))
    d = dict(n=int(len(g)), n_components=int(comp.max() + 1), n_isolated=int((D.min(1) > 1.6).sum()), slots_once=int((cnt == 1).sum()), slots_vacant=int((cnt == 0).sum()), slots_dup=int((cnt > 1).sum()),
             min_maxbel=float(p.max(1).min()), mean_maxbel=float(p.max(1).mean()))
    if len(g) == w.t.n:
        lab, dL, dR = CH.classify(w.t, X, w.C[g]); d.update(shape=lab, dL=float(dL), dR=float(dR))
        if lab in 'LR' and (cnt != 1).any(): d['shape'] = 'DEFECT'; d['reason'] = 'incomplete'
        if d['n_components'] > 1 or d['n_isolated']: d['shape'] = 'DEFECT'; d['reason'] = 'split/extrusion'
    else: d['shape'] = 'fragment'
    return d

def spec_time(w, j, slot, T, every=5.0):
    """run, return first time the cell at array index j has belief on `slot` > 0.5 and > 0.9"""
    from world import np, jax, jnp
    t50 = t90 = None; t_start = w.time
    for _ in range(int(T / every)):
        w.run(every); pj = np.array(jax.nn.softmax(jnp.array(w.MU[j])))
        if t50 is None and pj[slot] > 0.5: t50 = w.time - t_start
        if t90 is None and pj[slot] > 0.9: t90 = w.time - t_start
    return t50, t90

def job_replace(i, T=400.0):
    from world import new_adult, np
    w = new_adult('L', capacity=24, key=i); slot = int(w.perm0[i]); before = describe(w)
    w.replace(i, seed=i); t50, t90 = spec_time(w, i, slot, T)
    a = describe(w); return dict(cell=i, slot=slot, type=int(__import__('asm').type_vector(w.t)[slot]), t50=t50, t90=t90, after=a, before_shape=before['shape'], events=w.events)

def job_serial(seed, interval, T_settle=400.0):
    from world import new_adult, np
    w = new_adult('L', capacity=24, key=seed); rng = np.random.default_rng(seed); order = rng.permutation(24); traj = []
    for i in order:
        w.replace(int(i), seed=seed); w.run(interval); d = describe(w); traj.append((int(i), d['shape'], d['slots_once'], d['n_components']))
    w.run(T_settle); fin = describe(w)
    return dict(seed=seed, interval=interval, final=fin, traj=traj, all_new=bool((w.cell_id >= 24).all()), n_events=len(w.events), n_unique_ids=int(len(set(w.cell_id.tolist()))))

def job_extrude(i, vec, T=300.0):
    from world import new_adult, np
    w = new_adult('L', capacity=24, key=i); slot = int(w.perm0[i]); c = w.X[w.alive].mean(0); u = w.X[i] - c; u = u / (np.linalg.norm(u) + 1e-9)
    w.extrude(i, np.asarray(vec) * u); w.run(T); d = describe(w); X = w.X; D = np.linalg.norm(X - X[i], axis=1); D[i] = 99
    return dict(cell=i, slot=slot, type=int(__import__('asm').type_vector(w.t)[slot]), dist_after=float(D.min()), rejoined=bool(D.min() < 1.6), after=d, vec=float(np.linalg.norm(vec)))

def job_cut(kind, sep=7.0, T=400.0):
    from world import new_adult, np
    w = new_adult('L', capacity=24, key=0); Tb = w.t.Xs[0][:, w.perm0].T
    if kind == 'y': mask = Tb[:, 1] > 0.0; vec = np.array([0.0, sep])
    else: mask = Tb[:, 0] > 0.0; vec = np.array([sep, 0.0])
    # body-frame axes are not the arena axes after rigid motion: displace along the arena direction of the body axis (estimated by Procrustes of current positions)
    X = w.X; a = Tb - Tb.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
    if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
    w.cut(mask, R @ vec); w.run(T)
    A = np.where(mask)[0]; B = np.where(~mask)[0]
    DA = np.linalg.norm(w.X[A][:, None] - w.X[B][None], axis=-1).min()
    return dict(kind=kind, sep=sep, fragA=describe(w, A), fragB=describe(w, B), min_inter_fragment_distance=float(DA), reunited=bool(DA < 1.6), whole=describe(w))

def job_fuse(kinds, offset, T=400.0):
    from world import new_adult, fuse, np
    a = new_adult(kinds[0], capacity=24, key=1); b = new_adult(kinds[1], capacity=24, key=2); w = fuse(a, b, offset)
    w.run(T); g1 = np.arange(24); g2 = np.arange(24, 48)
    return dict(kinds=kinds, offset=offset, A=describe(w, g1), B=describe(w, g2), whole=describe(w), merged=bool(describe(w)['n_components'] == 1),
                min_inter_body=float(np.linalg.norm(w.X[g1][:, None] - w.X[g2][None], axis=-1).min()))

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == 'a':
        res = run_jobs(job_replace, [(i,) for i in range(24)], workers=8, label='i2a'); json.dump(res, open('../data/i2a_replace.json', 'w'))
        t50 = [r['t50'] for r in res]; print('success (t50 within 400):', sum(x is not None for x in t50), '/24; median t50', sorted([x for x in t50 if x is not None])[len([x for x in t50 if x is not None]) // 2] if any(x is not None for x in t50) else None)
        print('final shapes', [r['after']['shape'] for r in res])
    elif mode == 'b':
        iv = float(sys.argv[2]); res = run_jobs(job_serial, [(s, iv) for s in range(4)], workers=4, label='i2b'); json.dump(res, open('../data/i2b_serial.json', 'w'))
        for r in res: print(r['seed'], r['final'], r['all_new'], r['n_unique_ids'])
    elif mode == 'c':
        slots = [0, 3, 8, 11, 12, 15, 16, 23]; res = run_jobs(job_extrude, [(i, [8.0, 0.0]) for i in range(24) if True][:0] + [(int(i), [8.0, 0.0]) for i in range(24)], workers=8, label='i2c'); json.dump(res, open('../data/i2c_extrude.json', 'w'))
        print('rejoined', sum(r['rejoined'] for r in res), '/24'); print([ (r['type'], r['rejoined'], r['after']['shape']) for r in res])
    elif mode == 'd':
        res = run_jobs(job_cut, [('y',), ('x',)], workers=2, label='i2d'); json.dump(res, open('../data/i2d_cut.json', 'w'))
        for r in res: print(r['kind'], r['reunited'], r['fragA'], r['fragB'])
    elif mode == 'e':
        res = run_jobs(job_fuse, [(('L', 'L'), [9.0, 0.0]), (('L', 'R'), [9.0, 0.0]), (('L', 'L'), [8.0, 0.0]), (('L', 'R'), [8.0, 0.0]), (('L', 'L'), [8.0, 3.0]), (('L', 'R'), [8.0, 3.0])], workers=6, label='i2e'); json.dump(res, open('../data/i2e_fuse.json', 'w'))
        for r in res: print(r['kinds'], r['offset'], 'merged', r['merged'], 'A', r['A']['shape'], r['A']['slots_once'], 'B', r['B']['shape'], r['B']['slots_once'], 'min dist', round(r['min_inter_body'], 2))
