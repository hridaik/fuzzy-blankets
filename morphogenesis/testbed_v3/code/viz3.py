"""Viewer exemplars for testbed v3. Each condition = two synced panels: (left) structure (cell colour = type), reporter (ring colour: red = high reporter) and dA heatmap;
(right) the paracrine RATIO field f = A/(A+B) on the arena (white = A-rich ... black = B-rich; 50 % grey = no information). Reuses morphogenesis/viz/build_viewer_testbed.py unmodified (strings patched in memory)."""
import sys, os, json; sys.path.insert(0, '.'); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'viz'))
from world3 import *
import build_viewer_testbed as V
V.TEMPLATE = V.TEMPLATE.replace('plan-B ring', 'reporter ring (red = reporter high)').replace('target overlay', 'template overlay').replace('memory-ligand heatmap', 'memory-ligand (A) heatmap')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'viewer'); os.makedirs(OUT, exist_ok=True)

def roll_from_frames(label, frames, t0, events=None):
    t = np.array([f['t'] - t0 for f in frames]); X = np.stack([f['X'] for f in frames]); C = np.stack([f['C'] for f in frames]); D = np.stack([f['D'] for f in frames]); E = np.stack([f['E'] for f in frames])
    L = np.stack([f['L'] for f in frames]); al = np.stack([f['alive'] for f in frames]); MU = np.stack([f['MU'] for f in frames]); types = np.stack([cell_types(c.T) * a for c, a in zip(C, al)]); rho = 1 / (1 + np.exp(-L))
    Xs = np.where(al[:, :, None], X, 0.0)
    r = dict(label=label, t=t, X=Xs, types=types, planB=np.clip(E, 0, 1) * al, role=MU.argmax(2), ligand=dict(kappa=1.0, C=D[:, :, 0] * al), series=dict(mean_rho=(rho * al).sum(1) / al.sum(1), mean_reporter_contrast=None))
    if events: r['events'] = events
    r['series'].pop('mean_reporter_contrast'); r['_raw'] = (X, D, al); return r

def ratio_image(raw, bounds, W=105, H=None):
    X, D, al = raw; x0, x1, y0, y1 = bounds; H = H or int(round(W * (y1 - y0) / (x1 - x0))); gx = np.linspace(x0, x1, W); gy = np.linspace(y1, y0, H); GX, GY = np.meshgrid(gx, gy); P = np.stack([GX.ravel(), GY.ravel()], 1); out = []
    for k in range(len(X)):
        a = al[k]; d = np.exp(-np.linalg.norm(P[:, None, :] - X[k][a][None], axis=-1)); A = d @ D[k][a][:, 0]; B = d @ D[k][a][:, 1]; f = (A + 5e-4) / (A + B + 1e-3); out.append((255 * f).reshape(H, W))
    return np.stack(out).astype(np.uint8)

def emit(name, title, rolls, sub=''):
    allx = np.concatenate([r['X'][r['types'] > 0] for r in rolls]); pad = 2.5; x0, x1 = allx[:, 0].min() - pad, allx[:, 0].max() + pad; y0, y1 = allx[:, 1].min() - pad, allx[:, 1].max() + pad; panels = []
    for r in rolls:
        raw = r.pop('_raw'); panels.append(r); img = dict(r); img = {k: v for k, v in r.items() if k not in ('ligand', 'events')}; img['label'] = r['label'] + ' | paracrine ratio f = A/(A+B)'
        img['img'] = ratio_image(raw, (x0, x1, y0, y1)); img['fov'] = float(max(x1 - x0, y1 - y0) / 2); panels.append(img)
    p = V.build_html(panels, os.path.join(OUT, name + '.html'), title, audit=True, sub=sub); print(p); return p

def roll_world(w, label, T, every, events=None):
    t0 = w.time; w.frames = []; w.snapshot(); w.run(T, save_every=every); return roll_from_frames(label, w.frames, t0, events)

def roll_ctl(state, label, centre, amp, dur, T, every, noise=0.0, sig_h=0.0, key=0, lit_override=None):
    from h3 import lit_set
    w = new_adult3(state, capacity=24, noise=noise, sig_h=sig_h, key=key); w.time = 0.0; tm = w.tm; lit = lit_set(tm, w.perm0, centre) if lit_override is None else lit_override
    n = 24; uM = np.zeros((n, 2)); uM[lit, 1 if state == 'a' else 0] = amp; z = zero_ctl(n); ctl = z[:3] + (jnp.array(uM),) + z[4:]; per = int(round(every / DT)); nst = int(round(T / DT / per)) * per
    fin, tr = w.eng.run_ctl(w.state(), 0.0, DT, nst, w.key, ctl, 0.0, dur, min(5.0, dur / 4), save_every=per)
    fr = [w._frame(0.0, w.state())] + [w._frame((k + 1) * per * DT, tuple(a[k] for a in tr)) for k in range(len(tr[0]))]
    return roll_from_frames(label, fr, 0.0, events=[dict(t0=0.0, t1=dur, cells=[int(i) for i in np.where(lit)[0]], label='lit')] if amp > 0 else None)

def main(which=None):
    tm = make_template2(); thr = {(x['state'], round(x['dur'], 2), x['centre']): x['thr'] for x in json.load(open('../data/h3_bisect.json')) if x['thr'] is not None}
    if which in (None, 'h1'):
        w = new_adult3('a', capacity=24, noise=0.02, sig_h=0.4, key=1000); w.time = 0.0
        emit('h1_structure', 'v3 H1 - structure durable under noise (memory module running)', [roll_world(w, 'H1 body (state a), noise 0.02, seed 0, 2000 tu (3 x 20000 tu: 0 dissolutions)', 2000.0, 20.0)], sub='fixed seed 0')
    if which in (None, 'h2'):
        rolls = []
        for st in 'ab':
            w = new_adult3(st, capacity=24, noise=0.02, sig_h=0.4, key=11); w.time = 0.0; rolls.append(roll_world(w, f'H2 body in the {"first" if st == "a" else "second"} stable state (noise incl. sigma_h = 0.4, seed 11)', 600.0, 6.0))
        w = new_adult3('a', capacity=24, noise=0.0, key=0); w.time = 0.0; w.frames = []; w.snapshot(); sched = list(np.linspace(0, 1.0, 21)); n = 24; z = zero_ctl(n)
        for s in sched:
            mb = jnp.array([0.0, s]); ctl = z[:10] + (mb,); w.run(40.0, save_every=10.0, ctl_extra=ctl)
        for s in sched[::-1][1:]:
            mb = jnp.array([0.0, s]); ctl = z[:10] + (mb,); w.run(40.0, save_every=10.0, ctl_extra=ctl)
        rolls.append(roll_from_frames('H2 bath sweep 0 -> 1.0 -> 0 on the B ligand (40 tu per step): jump near B_c = 0.64, stays switched on the way back', w.frames, 0.0))
        emit('h2_memory', 'v3 H2 - two stable states and the bath hysteresis', rolls, sub='left panel of each pair: cells (type colour), reporter ring, A-ligand heatmap; right: paracrine ratio f')
    if which in (None, 'q'):
        rolls = []; from world3 import settled3
        arr, perm = settled3('a', 0); Xp = tm.Xs[:, perm].T; cp = tm.Xs[:, 10]; order = np.argsort(np.linalg.norm(Xp - cp[None], axis=1))
        for nn in (2, 4, 8, 12):
            idx = order[:nn]; eng = make_engine3(tm, Params3(sig_x=.02, sig_c=.02, sig_mu=.02, sig_d=.02, sig_e=.02, sig_h=0.7), N=nn); eng.dt = DT; st = tuple(jnp.array(a[idx]) for a in arr)
            per = int(round(20.0 / DT)); nst = int(round(1500.0 / DT / per)) * per; fin, tr = eng.run_ctl(st, 0.0, DT, nst, jax.random.PRNGKey(5000 + nn), zero_ctl(nn), -1e30, 1e30, 1.0, save_every=per)
            fr = [dict(t=0.0, X=np.array(st[0]), C=np.array(st[1]), MU=np.array(st[2]), L=np.array(st[3]), D=np.array(st[4]), E=np.array(st[5]), alive=np.ones(nn, bool), cell_id=np.arange(nn))] + [dict(t=(k + 1) * per * DT, X=np.array(tr[0][k]), C=np.array(tr[1][k]), MU=np.array(tr[2][k]), L=np.array(tr[3][k]), D=np.array(tr[4][k]), E=np.array(tr[5][k]), alive=np.ones(nn, bool), cell_id=np.arange(nn)) for k in range(len(tr[0]))]
            rolls.append(roll_from_frames(f'H2 group of {nn} cells cut out of the body (sigma_h = 0.7, seed fixed): mean rho shown below', fr, 0.0))
        emit('h2_quorum', 'v3 H2 - memory lifetime grows with group size (quorum)', rolls, sub='sigma_h = 0.7 (not the declared 0.4) so that lifetimes are visible; fixed seed')
    if which in (None, 'h3'):
        d = 4 / 0.6; tb = thr[('a', round(d, 2), 10)]; far = int(np.argmax(np.linalg.norm(tm.Xs - tm.Xs[:, [10]], axis=0))); arr, perm = __import__('world3').settled3('a', 0)
        from h3 import lit_set
        nl = int(lit_set(tm, perm, 10).sum()); X = tm.Xs[:, perm].T; dd = np.linalg.norm(X - tm.Xs[:, far][None], axis=1); wl = np.zeros(24, bool); wl[np.argsort(dd)[:nl]] = True
        rolls = [roll_ctl('a', f'H3 light (B-ligand secretion) on place 10, amplitude 1.2x threshold ({1.2 * tb:.1f}), 6.7 tu', 10, 1.2 * tb, d, 80.0, 1.0),
                 roll_ctl('a', f'H3 same amplitude, same duration, same number of cells, WRONG location (place {far})', 10, 1.2 * tb, d, 80.0, 1.0, lit_override=wl),
                 roll_ctl('a', 'H3 sham (amplitude 0, same code path)', 10, 0.0, d, 80.0, 1.0),
                 roll_ctl('b', f'H3 reverse direction: light on place 10, 1.2x threshold, from the second state', 10, 1.2 * tb, d, 80.0, 1.0)]
        emit('h3_switch', 'v3 H3 - switch vs wrong location vs sham (structure unchanged in all panels)', rolls, sub='deterministic; dashed disc = lit cells; right of each: paracrine ratio f; ring colour = reporter')
    if which in (None, 'h4'):
        rolls = []
        w = new_adult3('a', capacity=24, noise=0.0, key=3); w.time = 0.0; w.replace(12, seed=12); rolls.append(roll_world(w, 'H4 single replacement (cell 12): newcomer adopts the state within 2 tu', 300.0, 5.0))
        Tb = None
        w = new_adult3('a', capacity=24, noise=0.0, key=0); w.time = 0.0; Tb = w.tm.Xs[:, w.perm0].T; mask = Tb[:, 0] > 0; a_ = Tb - Tb.mean(0); b_ = w.X - w.X.mean(0); U, S, Vt = np.linalg.svd(a_.T @ b_); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        w.cut(mask, R @ np.array([7.0, 0.0])); rolls.append(roll_world(w, 'H4 cut across the body (head / tail halves): both halves keep their state', 400.0, 5.0))
        for off, lab in (([6.0, 0.0], 'a + b, end-to-end overlap (6, 0)'), ([0.0, 2.0], 'a + b, strong overlap (0, 2): one state takes over')):
            a = new_adult3('a', capacity=24, noise=0.0, key=1); b = new_adult3('b', k=1, capacity=24, noise=0.0, key=2); wf = fuse3(a, b, off); wf.time = 0.0; rolls.append(roll_world(wf, 'H4 fusion ' + lab, 600.0, 10.0))
        emit('h4_events', 'v3 H4 - identity events with memory', rolls, sub='deterministic; ring = reporter; right of each: paracrine ratio')
if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else None)
