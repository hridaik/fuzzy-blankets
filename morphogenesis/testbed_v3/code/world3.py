"""v3 identity-event world + experimenter interface (adapted from testbed_v2/code/world2.py, interface2.py)."""
import sys, os, json, hashlib; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an3 import *
from shape import cell_types
from world2 import component_labels            # v2 code, read-only
HERE = os.path.dirname(os.path.abspath(__file__)); ADULTS = os.path.join(HERE, '..', 'data', 'adults'); DT = 0.0125
LSTAR = 2.292

def settled3(state, k=0, T=1500.0, cfg=None):
    cfg = cfg or {}; os.makedirs(ADULTS, exist_ok=True); tag = f"{state}_{k}_{hashlib.md5(json.dumps(sorted(cfg.items())).encode()).hexdigest()[:6]}"; p = os.path.join(ADULTS, tag + '.npz')
    if os.path.exists(p): z = np.load(p); return tuple(z[f'a{i}'] for i in range(6)), z['perm']
    tm = make_template2(); eng = make_engine3(tm, Params3(**cfg)); eng.dt = DT; st, perm = seeded_start3(tm, k, state, lstar=LSTAR); fin = run_plain(eng, st, 0, T, jax.random.PRNGKey(0))
    arr = tuple(np.array(a) for a in fin); np.savez(p, perm=perm, **{f'a{i}': a for i, a in enumerate(arr)}); return arr, perm

class World3:
    def __init__(self, tm, eng, state, perm, alive=None, cell_id=None, key=0):
        self.tm, self.eng = tm, eng; self.X, self.C, self.MU, self.L, self.D, self.E = [np.array(a) for a in state]; self.N = len(self.X)
        self.alive = np.ones(self.N, bool) if alive is None else np.array(alive, bool); self.cell_id = np.arange(self.N) if cell_id is None else np.array(cell_id)
        self.next_id = int(self.cell_id.max() + 1); self.events = []; self.time = 1e4; self.step_count = 0; self.key = jax.random.PRNGKey(key); self.frames = []; self.perm0 = perm
    def state(self): return tuple(jnp.array(a) for a in (self.X, self.C, self.MU, self.L, self.D, self.E))
    def set_state(self, s): self.X, self.C, self.MU, self.L, self.D, self.E = [np.array(a) for a in s]
    def default_ctl(self): c = list(zero_ctl(self.eng.n)); c[4] = jnp.array(self.alive.astype(float)); return tuple(c)
    def _frame(self, t, s): return dict(t=t, X=np.array(s[0]), C=np.array(s[1]), MU=np.array(s[2]), L=np.array(s[3]), D=np.array(s[4]), E=np.array(s[5]), alive=self.alive.copy(), cell_id=self.cell_id.copy())
    def run(self, T, save_every=None, ctl_extra=None):
        dt = self.eng.dt; ctl = self.default_ctl() if ctl_extra is None else ctl_extra
        if save_every:
            per = int(round(save_every / dt)); nst = per * int(round(T / (per * dt)))
            fin, tr = self.eng.run_ctl(self.state(), self.time, dt, nst, self.key, ctl, -1e30, 1e30, 1.0, step0=self.step_count, save_every=per)
            for k in range(len(tr[0])): self.frames.append(self._frame(self.time + (k + 1) * per * dt, tuple(a[k] for a in tr)))
        else:
            nst = int(round(T / dt)); fin = self.eng.run_ctl(self.state(), self.time, dt, nst, self.key, ctl, -1e30, 1e30, 1.0, step0=self.step_count)
        self.set_state(fin); self.time += nst * dt; self.step_count += nst
    def snapshot(self): self.frames.append(self._frame(self.time, self.state()))
    def log(self, kind, **kw): self.events.append(dict(t=float(self.time), kind=kind, **kw))
    def remove(self, i): self.log('remove', index=int(i), cell_id=int(self.cell_id[i])); self.alive[i] = False
    def insert(self, pos, j=None, seed=0):
        j = int(np.where(~self.alive)[0][0]) if j is None else j; rng = np.random.default_rng(10_000 + self.next_id + seed)
        self.X[j] = pos; self.C[j] = 0.0; self.D[j] = 0.0; self.E[j] = 0.0; self.MU[j] = rng.standard_normal(self.MU.shape[1]) / 8; self.L[j] = 0.0
        self.cell_id[j] = self.next_id; self.alive[j] = True; self.log('insert', index=int(j), cell_id=int(self.next_id), pos=[float(x) for x in pos]); self.next_id += 1; return j
    def replace(self, i, seed=0):
        pos = self.X[i].copy(); old = int(self.cell_id[i]); self.remove(i); j = self.insert(pos, j=i, seed=seed); self.events[-1]['replaces'] = old; self.log('replace', index=int(i), old_id=old, new_id=int(self.cell_id[i])); return j
    def extrude(self, i, vec): self.X[i] = self.X[i] + np.asarray(vec); self.log('extrude', index=int(i), cell_id=int(self.cell_id[i]), vec=[float(v) for v in vec])
    def cut(self, side_mask, vec):
        idxs = np.where(side_mask & self.alive)[0]; self.X[idxs] += np.asarray(vec); self.log('cut', cells=[int(self.cell_id[i]) for i in idxs], vec=[float(v) for v in vec])
    def kick_l(self, idxs, dl): self.L[np.asarray(idxs)] += dl; self.log('kick_l', cells=[int(self.cell_id[i]) for i in np.asarray(idxs)], dl=float(dl))
    def rho(self): return 1 / (1 + np.exp(-self.L))

def fuse3(w1, w2, offset, angle=0.0):
    c, s = np.cos(angle), np.sin(angle); R = np.array([[c, -s], [s, c]]); m2 = w2.X[w2.alive].mean(0); X2 = (w2.X - m2) @ R.T + m2 + np.asarray(offset); cat = np.concatenate
    st = (cat([w1.X, X2]), cat([w1.C, w2.C]), cat([w1.MU, w2.MU]), cat([w1.L, w2.L]), cat([w1.D, w2.D]), cat([w1.E, w2.E])); ids = cat([w1.cell_id, w2.cell_id + w1.next_id])
    eng2 = make_engine3(w1.tm, w1.eng.P, N=len(st[0])); eng2.dt = w1.eng.dt; w = World3(w1.tm, eng2, st, None, alive=cat([w1.alive, w2.alive]), cell_id=ids, key=0); w.next_id = int(ids.max() + 1)
    w.log('fuse', n1=int(len(w1.X)), n2=int(len(w2.X)), offset=[float(o) for o in offset], angle=float(angle)); return w

def new_adult3(state='a', k=0, capacity=24, noise=0.0, sig_h=0.0, key=0, cfg=None):
    cfg = dict(cfg or {}); arr, perm = settled3(state, k, cfg=cfg); tm = make_template2()
    P = Params3(sig_x=noise, sig_c=noise, sig_mu=noise, sig_d=noise, sig_e=noise, sig_h=sig_h, **cfg) if noise else Params3(**cfg)
    eng = make_engine3(tm, P, N=capacity if capacity > 24 else None); eng.dt = DT; X, C, MU, L, D, E = [a.copy() for a in arr]
    if capacity > 24:
        pad = capacity - 24; z = lambda a, shp: np.concatenate([a, np.zeros((pad,) + shp)])
        X = np.concatenate([X, np.full((pad, 2), 1e3)]); C = z(C, (4,)); MU = z(MU, (24,)); L = z(L, ()); D = z(D, (2,)); E = z(E, ())
        w = World3(tm, eng, (X, C, MU, L, D, E), perm, alive=np.r_[np.ones(24, bool), np.zeros(pad, bool)], cell_id=np.arange(capacity), key=key); w.next_id = 24; w.cell_id[24:] = -1
    else: w = World3(tm, eng, (X, C, MU, L, D, E), perm, key=key)
    return w

def describe3(w, group=None):
    g = np.where(w.alive)[0] if group is None else np.array(group); tm = w.tm; S = tm.S; X = w.X[g]; q = np.array(jax.nn.softmax(jnp.array(w.MU[g]), axis=1)); slot = q.argmax(1)
    orb = orbits(tm, PI_C, PI_L); no = orb.max() + 1; ocnt = np.bincount(orb[slot], minlength=no); oexp = np.bincount(orb, minlength=no)
    comp = component_labels(X, 1.6); D = np.linalg.norm(X[:, None] - X[None], axis=-1) + 9 * np.eye(len(g)); rho = w.rho()[g]
    d = dict(n=int(len(g)), n_components=int(comp.max() + 1), n_isolated=int((D.min(1) > 1.6).sum()), orbit_ok=bool((ocnt == oexp).all()), min_maxbel=float(q.max(1).min()), mean_rho=float(rho.mean()), frac_a=float((rho > 0.5).mean()))
    if len(g) == S:
        lab, dL, dR = classify_shape(tm, X, w.C[g]); d.update(shape=lab, dL=float(dL))
        if lab == 'L' and not d['orbit_ok']: d['shape'] = 'DEFECT'; d['reason'] = 'incomplete'
        if d['n_components'] > 1 or d['n_isolated']: d['shape'] = 'DEFECT'; d['reason'] = 'split/extrusion'
    else: d['shape'] = 'fragment'
    return d

# ---------------------------------------------------------------- interface
CHUNK = 1.0; OBS_EVERY = 5.0
class Mask:
    def __init__(self, shapes): self.shapes = shapes
    def __call__(self, X, exp=None):
        m = np.zeros(len(X))
        for s in self.shapes:
            if s[0] == 'disc': v = 1 / (1 + np.exp(-(s[3] - np.linalg.norm(X - np.array(s[1:3]), axis=1)) / 0.15))
            elif s[0] == 'place': c = exp.place_in_arena(s[1]); v = 1 / (1 + np.exp(-(s[2] - np.linalg.norm(X - c, axis=1)) / 0.15))
            else: v = 1 / (1 + np.exp(-((X @ np.array(s[1:3])) - s[3]) / 0.15))
            m = m + s[-1] * v
        return m

class Experiment3:
    """private effect kinds: ('mem', 0|1) memory-secretion light (column of uM: 0 = A, 1 = B); ('sec', 0..3); ('rg', 0..3); ('mig', 0)"""
    def __init__(self, state='a', seed=0, noise=0.02, sig_h=0.0, private=None, capacity=24, form_seed=0):
        self.w = new_adult3(state, k=form_seed, capacity=capacity, noise=noise, sig_h=sig_h, key=seed); self.state0 = state; self.private = private or {}; self.noise = noise; self.seed = seed
        rng = np.random.default_rng(31_000 + seed); th = rng.uniform(0, 2 * np.pi); sh = rng.uniform(-3, 3, 2); c, s = np.cos(th), np.sin(th); R = np.array([[c, -s], [s, c]]); al = self.w.alive
        cen = self.w.X[al].mean(0); self.w.X[al] = (self.w.X[al] - cen) @ R.T + sh; self.hidden_pose = dict(angle=float(th), shift=[float(x) for x in sh]); self.dose = {}; self.t0 = self.w.time; self.obs = []; self.log = []
    def place_in_arena(self, k):
        w = self.w; al = w.alive; T = w.tm.Xs[:, w.perm0].T[al[:len(w.perm0)]]; X = w.X[al]; a = T - T.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        return R @ (w.tm.Xs[:, k] - T.mean(0)) + X.mean(0)
    def _amps(self, actions, t):
        w = self.w; n = w.eng.n; ext = np.zeros((n, 4)); rg = np.zeros((n, 4)); mig = np.zeros(n); uM = np.zeros((n, 2)); sp = np.zeros((1, 2)); sa = np.zeros((1, 4)); bath = np.zeros(4)
        mp = np.zeros((1, 2)); ma = np.zeros((1, 2)); mb = np.zeros(2); srcs = []; msrcs = []; lit_total = 0.0
        for k, a in enumerate(actions):
            ph = float(w.eng.window(t, a['t_on'], a['t_off'], a['ramp'])); amp = a.get('amp', 0.0) * ph
            if a['type'] == 'light':
                m = a['mask'](w.X, self) * w.alive; lit_total += float((np.abs(m) > 0.5).sum()) * abs(amp) * CHUNK; kind, par = self.private[a['channel']]
                if kind == 'mem': uM[:, par] += amp * m
                elif kind == 'sec': ext[:, par] += amp * m
                elif kind == 'rg': rg[:, par] += amp * m
                elif kind == 'mig': mig += amp * m
            elif a['type'] == 'pipette': srcs.append((a['pos'], np.eye(4)[a['ligand_index']] * amp)); lit_total += abs(amp) * CHUNK
            elif a['type'] == 'mpipette': msrcs.append((a['pos'], np.eye(2)[a['ligand_index']] * amp)); lit_total += abs(amp) * CHUNK
            elif a['type'] == 'bath': bath[a['ligand_index']] += amp; lit_total += abs(amp) * CHUNK * float(w.alive.sum())
            elif a['type'] == 'mbath': mb[a['ligand_index']] += amp; lit_total += abs(amp) * CHUNK * float(w.alive.sum())
            if k == len(actions) - 1: self.dose[k] = self.dose.get(k, 0.0) + lit_total
        if srcs: sp = np.array([s[0] for s in srcs]); sa = np.array([s[1] for s in srcs])
        if msrcs: mp = np.array([s[0] for s in msrcs]); ma = np.array([s[1] for s in msrcs])
        return tuple(jnp.array(x) for x in (ext, rg, mig, uM, w.alive.astype(float), sp, sa, bath, mp, ma, mb))
    def run(self, T, actions=(), sham=False, observe=True):
        w = self.w; acts = [dict(a, amp=(0.0 if sham else a.get('amp', 0.0))) for a in actions]
        pending = sorted([a for a in acts if a['type'] in ('tweezers', 'surgery', 'kick')], key=lambda a: a['t']); cont = [a for a in acts if a['type'] not in ('tweezers', 'surgery', 'kick')]; tend = w.time + T
        while w.time < tend - 1e-9:
            for a in [a for a in pending if a['t'] <= w.time - self.t0 + 1e-9]: self._instant(a, sham); pending.remove(a)
            amps = self._amps(cont, w.time - self.t0 + 0.5 * CHUNK); w.run(CHUNK, ctl_extra=amps)
            if observe and abs((w.time - self.t0) / OBS_EVERY - round((w.time - self.t0) / OBS_EVERY)) < 1e-6: self._observe()
    def _nearest(self, pos): d = np.linalg.norm(self.w.X - np.asarray(pos), axis=1); d[~self.w.alive] = 1e9; return int(d.argmin())
    def _instant(self, a, sham):
        w = self.w
        if sham: self.log.append(dict(t=float(w.time), kind='sham_' + a['type'])); return
        if a['type'] == 'tweezers': w.extrude(self._nearest(a['pos']), a['vec'])
        elif a['type'] == 'kick': w.kick_l(a['cells'], a['dl'])
        elif a['op'] == 'remove': w.remove(self._nearest(a['pos']))
        elif a['op'] == 'insert': w.insert(a['pos'])
        elif a['op'] == 'replace': w.replace(self._nearest(a['pos']))
        elif a['op'] == 'cut': n_ = np.array(a['normal']); side = (w.X @ n_ > a['d']) & w.alive; w.cut(side, np.array(a['vec']))
    def _observe(self):
        w = self.w; self.obs.append(dict(t=float(w.time - self.t0), X=w.X.copy(), C=w.C.copy(), D=w.D.copy(), E=w.E.copy(), alive=w.alive.copy(), cell_id=w.cell_id.copy(), MU=w.MU.copy(), L=w.L.copy()))
    def hidden(self): w = self.w; return dict(events=w.events + self.log, pose=self.hidden_pose, dose=self.dose, private=self.private, kind=self.state0)
