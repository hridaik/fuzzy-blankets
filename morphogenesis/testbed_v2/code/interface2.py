"""v2 experimenter-level interface (adapted from testbed/code/interface.py).  Arena coordinates; hidden rigid pose; opaque light channels mapped privately to effects.
private effect kinds: ('sec', ligand_index 0..5)  extra secretion of a ligand (indices 4,5 = memory ligands mL, mR);  ('rg', ligand_index) receptor gain;  ('mig', 0) migration gain.
Light masks: ('disc', cx, cy, r, sign) / ('halfplane', nx, ny, d, sign) in ARENA coordinates, or ('place', k, r, sign): white-box disc of radius r around template place k, tracked in the arena through the body's current alignment (uses hidden ground truth)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world2 import *
from scipy.ndimage import gaussian_filter
OBS_EVERY = 5.0; CHUNK = 1.0; FOV = 12.0; IMG_PX = 96; PSF_SIGMA = 0.5; SNR = 20.0; POS_NOISE = 0.02; LEVEL_NOISE = 0.03

class Mask:
    def __init__(self, shapes): self.shapes = shapes
    def __call__(self, X, exp=None):
        m = np.zeros(len(X))
        for s in self.shapes:
            if s[0] == 'disc': v = 1 / (1 + np.exp(-(s[3] - np.linalg.norm(X - np.array(s[1:3]), axis=1)) / 0.15))
            elif s[0] == 'place':
                c = exp.place_in_arena(s[1]); v = 1 / (1 + np.exp(-(s[2] - np.linalg.norm(X - c, axis=1)) / 0.15))
            else: v = 1 / (1 + np.exp(-((X @ np.array(s[1:3])) - s[3]) / 0.15))
            m = m + s[-1] * v
        return m

class Experiment2:
    def __init__(self, kind='L', seed=0, noise=0.02, sig_h=0.0, private=None, capacity=24, cfg=None, form_seed=0):
        self.w = new_adult2(kind, k=form_seed, capacity=capacity, noise=noise, sig_h=sig_h, key=seed, cfg=cfg); self.kind = kind; self.private = private or {}; self.noise = noise; self.seed = seed
        rng = np.random.default_rng(31_000 + seed); th = rng.uniform(0, 2 * np.pi); sh = rng.uniform(-3, 3, 2)
        c, s = np.cos(th), np.sin(th); R = np.array([[c, -s], [s, c]]); al = self.w.alive; cen = self.w.X[al].mean(0)
        self.w.X[al] = (self.w.X[al] - cen) @ R.T + sh; self.hidden_pose = dict(angle=float(th), shift=[float(x) for x in sh])
        self.dose = {}; self.t0 = self.w.time; self.obs = []; self.log = []
    def place_in_arena(self, k):
        """white-box: rigid (proper rotation) alignment of the template places held by the cells onto the current arena positions"""
        w = self.w; al = w.alive; T = w.tm.Xs[:, w.perm0].T[al[:len(w.perm0)]] if w.perm0 is not None else None
        X = w.X[al]; a = T - T.mean(0); b = X - X.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        return R @ (w.tm.Xs[:, k] - T.mean(0)) + X.mean(0)
    def _amps(self, actions, t):
        w = self.w; n, S = w.eng.n, w.eng.S; ext = np.zeros((n, NL)); rg = np.zeros((n, NL)); mig = np.zeros(n); fb = np.zeros((n, S)); lit_total = 0.0
        src_pos = np.zeros((1, 2)); src_amp = np.zeros((1, NL)); bath = np.zeros(NL); srcs = []
        for k, a in enumerate(actions):
            ph = float(w.eng.window(t, a['t_on'], a['t_off'], a['ramp'])); amp = a.get('amp', 0.0) * ph
            if a['type'] == 'light':
                m = a['mask'](w.X, self) * w.alive; lit_total += float((np.abs(m) > 0.5).sum()) * abs(amp) * CHUNK
                kind, par = self.private[a['channel']]
                if kind == 'sec': ext[:, par] += amp * m
                elif kind == 'rg': rg[:, par] += amp * m
                elif kind == 'mig': mig += amp * m
            elif a['type'] == 'pipette': srcs.append((a['pos'], np.eye(NL)[a['ligand_index']] * amp)); lit_total += abs(amp) * CHUNK
            elif a['type'] == 'bath': bath[a['ligand_index']] += amp; lit_total += abs(amp) * CHUNK * float(w.alive.sum())
            self.dose[k] = self.dose.get(k, 0.0) + lit_total if k == len(actions) - 1 else self.dose.get(k, 0.0)
        if srcs: src_pos = np.array([s[0] for s in srcs]); src_amp = np.array([s[1] for s in srcs])
        return tuple(jnp.array(x) for x in (ext, rg, mig, fb, w.alive.astype(float), src_pos, src_amp, bath))
    def run(self, T, actions=(), sham=False, label='', observe=True):
        w = self.w; acts = [dict(a, amp=(0.0 if sham else a.get('amp', 0.0))) for a in actions]
        pending = sorted([a for a in acts if a['type'] in ('tweezers', 'surgery')], key=lambda a: a['t']); cont = [a for a in acts if a['type'] not in ('tweezers', 'surgery')]
        tend = w.time + T
        while w.time < tend - 1e-9:
            for a in [a for a in pending if a['t'] <= w.time - self.t0 + 1e-9]: self._instant(a, sham); pending.remove(a)
            amps = self._amps(cont, w.time - self.t0 + 0.5 * CHUNK); w.run(CHUNK, ctl_extra=amps)
            if observe and abs((w.time - self.t0) / OBS_EVERY - round((w.time - self.t0) / OBS_EVERY)) < 1e-6: self._observe()
    def _nearest(self, pos):
        d = np.linalg.norm(self.w.X - np.asarray(pos), axis=1); d[~self.w.alive] = 1e9; return int(d.argmin())
    def _instant(self, a, sham):
        w = self.w
        if sham: self.log.append(dict(t=float(w.time), kind='sham_' + a['type'])); return
        if a['type'] == 'tweezers': w.extrude(self._nearest(a['pos']), a['vec'])
        elif a['op'] == 'remove': w.remove(self._nearest(a['pos']))
        elif a['op'] == 'insert': w.insert(a['pos'])
        elif a['op'] == 'replace': w.replace(self._nearest(a['pos']))
        elif a['op'] == 'cut':
            n_ = np.array(a['normal']); side = (w.X @ n_ > a['d']) & w.alive; w.cut(side, np.array(a['vec']))
    def _observe(self):
        w = self.w; self.obs.append(dict(t=float(w.time - self.t0), X=w.X.copy(), C=w.C.copy(), D=w.D.copy(), alive=w.alive.copy(), cell_id=w.cell_id.copy(), MU=w.MU.copy(), L=w.L.copy()))
    def hidden(self):
        w = self.w; return dict(events=w.events + self.log, pose=self.hidden_pose, dose=self.dose, private=self.private, kind=self.kind)

def level_noise(rng, C): return C * (1 + LEVEL_NOISE * rng.standard_normal(C.shape))
def lig(f): return np.concatenate([f['C'], f['D']], axis=1)          # (n,6): 4 morphological + 2 memory ligands, all just "secreted levels"
def render_O1(frames, rng, channel_perm):
    out = []
    for f in frames:
        a = f['alive']; X = f['X'][a] + POS_NOISE * rng.standard_normal((a.sum(), 2)); Cn = level_noise(rng, lig(f)[a])[:, channel_perm]
        out.append(dict(t=f['t'], id=f['cell_id'][a], xy=X, level=Cn))
    return out
def render_O2(frames, rng, channel_perm):
    out = []
    for f in frames:
        a = f['alive']; X = f['X'][a] + POS_NOISE * rng.standard_normal((a.sum(), 2)); Cn = level_noise(rng, lig(f)[a])[:, channel_perm]; p = rng.permutation(len(X))
        out.append(dict(t=f['t'], xy=X[p], level=Cn[p]))
    return out
def render_O3(frames, rng, channel_perm, reporters=(0, 1)):
    """reporters index the PERMUTED ligand vector; variants: without memory ligands = reporters among the 4 morphological; including one memory ligand = add that ligand's permuted index"""
    g = np.linspace(-FOV, FOV, IMG_PX); GX, GY = np.meshgrid(g, g); P = np.stack([GX.ravel(), GY.ravel()], 1); px = 2 * FOV / IMG_PX; out = []
    for f in frames:
        a = f['alive']; X = f['X'][a]; C = lig(f)[a][:, channel_perm]; d = np.exp(-np.linalg.norm(P[:, None, :] - X[None], axis=-1))
        img = np.stack([(d @ C[:, r]).reshape(IMG_PX, IMG_PX) for r in reporters]); img = np.stack([gaussian_filter(im, PSF_SIGMA / px) for im in img]); pk = np.maximum(img.max(axis=(1, 2), keepdims=True), 1e-6)
        img = np.clip(img + rng.standard_normal(img.shape) * pk / SNR, 0, None); out.append(dict(t=f['t'], img=img.astype(np.float32)))
    return out
