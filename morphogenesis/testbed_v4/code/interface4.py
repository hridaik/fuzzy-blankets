"""v4 experimenter interface: Experiment4 (adapted from testbed_v3/code/world3.py Experiment3 / world4.py). Lights (private channel map), pipettes, baths, surgery, tweezers.
Per-dish hidden parameters (g, gamma) are part of the dish dict. Hidden tier records the ORGANISM INTACT flag per observed frame."""
from world4 import *
CHUNK = 0.5; OBS_EVERY = 5.0
CH = {'MA': ('mem', 0), 'MB': ('mem', 1), 'SEC': ('sec', 0), 'RG': ('rg', 0), 'MIG': ('mig', 0)}
class Mask:
    def __init__(self, shapes): self.shapes = shapes
    def __call__(self, X, exp=None):
        m = np.zeros(len(X))
        for s in self.shapes:
            if s[0] == 'disc': v = 1 / (1 + np.exp(-(s[3] - np.linalg.norm(X - np.array(s[1:3]), axis=1)) / 0.15))
            elif s[0] == 'place': c = exp.place_in_arena(s[1]); v = 1 / (1 + np.exp(-(s[2] - np.linalg.norm(X - c, axis=1)) / 0.15))
            elif s[0] == 'all': v = np.ones(len(X))
            else: v = 1 / (1 + np.exp(-((X @ np.array(s[1:3])) - s[3]) / 0.15))
            m = m + s[-1] * v
        return m
def obs_schedule(T, dense=None, base=1.0, fine=0.5):
    ts = set(np.round(np.arange(base, T + 1e-9, base), 6).tolist())
    if dense is not None: ts |= set(np.round(np.arange(max(fine, dense[0]), min(T, dense[1]) + 1e-9, fine), 6).tolist())
    return sorted(ts)
def fuse_worlds(w1, w2, offset):
    from engine4 import make_engine4
    cat = np.concatenate; m2 = w2.X.mean(0); X2 = w2.X - m2 + m2 + np.asarray(offset)
    st = tuple(cat([getattr(w1, k), X2 if k == 'X' else getattr(w2, k)]) for k in ('X', 'C', 'MU', 'L', 'D', 'E', 'U')); ids = cat([w1.cell_id, w2.cell_id + w1.next_id])
    e2 = make_engine4(TM, w1.eng.P, N=48); e2.dt = DT; w = World4(e2, st, alive=cat([w1.alive, w2.alive]), cell_id=ids, key=0); w.next_id = int(ids.max() + 1); w.log('fuse', offset=[float(o) for o in offset]); return w
class Experiment4:
    def __init__(self, state='a', seed=0, noise=True, dish=None, variant='phi04', private=None, form_seed=0, gamma_on=True):
        self.dish = dish or median_dish(); self.variant = variant; e = get_engine(self.dish, variant, noise=bool(noise), gamma_on=gamma_on); arr, perm = settled(self.dish, variant, state, k=form_seed)
        self.w = World4(e, arr, key=seed, perm=perm); self.state0 = state; self.private = private or {}; self.seed = seed; self.noise = noise
        rng = np.random.default_rng(31_000 + seed); th = rng.uniform(0, 2 * np.pi); sh = rng.uniform(-3, 3, 2); c, s = np.cos(th), np.sin(th); R = np.array([[c, -s], [s, c]]); cen = self.w.X.mean(0); self.w.X = (self.w.X - cen) @ R.T + sh
        self.hidden_pose = dict(angle=float(th), shift=[float(x) for x in sh]); self.dose = {}; self.t0 = self.w.time; self.obs = []; self.log = []; self.base_nbr = nbr_matrix(self.w.X); self.n0 = int(self.w.alive.sum())
    def place_in_arena(self, k):
        w = self.w; T = TM.Xs[:, w.perm0].T; X = w.X; a = T - T.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        return R @ (TM.Xs[:, k] - T.mean(0)) + X.mean(0)
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
        c = list(zero_ctl(w.eng)); c[0], c[1], c[2], c[3] = jnp.array(ext), jnp.array(rg), jnp.array(mig), jnp.array(uM); c[4] = jnp.array(w.alive.astype(float)); c[5], c[6], c[7], c[8], c[9], c[10] = jnp.array(sp), jnp.array(sa), jnp.array(bath), jnp.array(mp), jnp.array(ma), jnp.array(mb)
        return tuple(c)
    def run_sched(self, T, actions=(), sham=False, obs_times=()):
        w = self.w; acts = [dict(a, amp=(0.0 if sham else a.get('amp', 0.0))) for a in actions]
        pending = sorted([a for a in acts if a['type'] in ('tweezers', 'surgery', 'kick')], key=lambda a: a['t']); cont = [a for a in acts if a['type'] not in ('tweezers', 'surgery', 'kick')]
        obs = set(round(t, 6) for t in obs_times); tend = w.time + T
        while w.time < tend - 1e-9:
            t_rel = w.time - self.t0
            for a in [a for a in pending if a['t'] <= t_rel + 1e-9]: self._instant(a, sham); pending.remove(a)
            ctl = self._amps(cont, t_rel + 0.5 * CHUNK); w.run(CHUNK, ctl_extra=ctl)
            if round(w.time - self.t0, 6) in obs: self._observe()
    def run(self, T, actions=(), sham=False, observe=True):
        self.run_sched(T, actions, sham, obs_times=([] if not observe else [round(t, 6) for t in np.arange(OBS_EVERY, T + 1e-9, OBS_EVERY)]))
    def _nearest(self, pos): d = np.linalg.norm(self.w.X - np.asarray(pos), axis=1); d[~self.w.alive] = 1e9; return int(d.argmin())
    def _instant(self, a, sham):
        w = self.w
        if sham: self.log.append(dict(t=float(w.time), kind='sham_' + a['type'])); return
        if a['type'] == 'tweezers': w.extrude(self._nearest(a['pos']), a['vec'])
        elif a['type'] == 'kick': w.L[np.asarray(a['cells'])] += a['dl']
        elif a['op'] == 'remove': w.remove(self._nearest(a['pos']))
        elif a['op'] == 'insert': w.insert(a['pos'])
        elif a['op'] == 'replace': w.replace(self._nearest(a['pos']))
        elif a['op'] == 'cut': n_ = np.array(a['normal']); side = (w.X @ n_ > a['d']) & w.alive; w.cut(side, np.array(a['vec']))
    def _observe(self):
        w = self.w; self.obs.append(dict(t=float(w.time - self.t0), X=w.X.copy(), C=w.C.copy(), D=w.D.copy(), E=w.E.copy(), alive=w.alive.copy(), cell_id=w.cell_id.copy(), MU=w.MU.copy(), L=w.L.copy(), U=w.U.copy()))
    def intact_series(self, tau=None):
        """hidden: ORGANISM INTACT per observed frame (material, one component, orbit-complete fill, neighbour Jaccard >= tau). Material: no remove/insert/fuse event and all original cells alive."""
        tau = tauJ() if tau is None else tau; material = not any(e['kind'] in ('remove', 'insert', 'fuse') for e in self.w.events) and len(self.obs) > 0 and self.obs[0]['alive'].shape[0] == 24; out = []
        for f in self.obs:
            if f['alive'].shape[0] != 24 or not f['alive'].all(): out.append(False); continue
            fs = frame_stats(f['X'], f['MU'], f['L'], self.base_nbr); out.append(bool(material and fs['ncomp'] == 1 and fs['fill_ok'] and fs['jac'] >= tau))
        return out
    def hidden(self):
        w = self.w; return dict(events=w.events + self.log, pose=self.hidden_pose, dose=self.dose, private=self.private, kind=self.state0, dish=self.dish, variant=self.variant, intact=self.intact_series(), tau_J=tauJ())
