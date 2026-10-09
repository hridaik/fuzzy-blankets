"""T3: experimenter-level interface. Arena coordinates only; the body is placed by a hidden random rigid motion; internal quantities (slots, beliefs, plan, template) never appear in observable output.
Experiment.run(T, actions, sham=False) ; renderers O1 (tracked cells), O2 (unlabelled point clouds), O3 (images)."""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from world import *
from scipy.ndimage import gaussian_filter

OBS_EVERY = 5.0          # observation frame interval (time units)
CHUNK = 1.0              # actuation update interval (control re-evaluated at cell positions every CHUNK)
FOV = 12.0               # arena window [-FOV, FOV]^2
IMG_PX = 96              # image size
PSF_SIGMA = 0.5          # Gaussian PSF sigma (arena units)
SNR = 20.0               # image peak SNR
POS_NOISE = 0.02         # O1/O2 localisation noise (arena units)
LEVEL_NOISE = 0.03       # O1/O2 multiplicative noise on levels

class Mask:
    """smooth indicator in ARENA coordinates: union of discs and half-planes; edge width 0.3. shapes: ('disc', cx, cy, r, sign) ; ('halfplane', nx, ny, d, sign) = points with n.x > d"""
    def __init__(self, shapes): self.shapes = shapes
    def __call__(self, X):
        m = np.zeros(len(X))
        for s in self.shapes:
            if s[0] == 'disc': v = 1 / (1 + np.exp(-(s[3] - np.linalg.norm(X - np.array(s[1:3]), axis=1)) / 0.15))
            else: v = 1 / (1 + np.exp(-((X @ np.array(s[1:3])) - s[3]) / 0.15))
            m = m + s[-1] * v
        return m

class Experiment:
    def __init__(self, kind='L', seed=0, noise=0.02, private=None, capacity=24, arena_seed=None, T_settle=0.0):
        """private: hidden mapping of opaque light channels to internal effects, e.g. {'L1': ('fb', 2), 'L2': ('fb', 3)}"""
        self.w = new_adult(kind, capacity=capacity, sig=noise, key=seed); self.kind = kind; self.private = private or {}; self.noise = noise; self.seed = seed
        rng = np.random.default_rng(31_000 + (seed if arena_seed is None else arena_seed)); th = rng.uniform(0, 2 * np.pi); sh = rng.uniform(-3, 3, 2)
        c, s = np.cos(th), np.sin(th); R = np.array([[c, -s], [s, c]]); al = self.w.alive; cen = self.w.X[al].mean(0)
        self.w.X[al] = (self.w.X[al] - cen) @ R.T + sh
        self.hidden_pose = dict(angle=float(th), shift=[float(x) for x in sh])
        self.dose = {}; self.t0 = self.w.time; self.obs = []; self.log = []
    # ------------------------------------------------------------------ actuation
    def _amps(self, actions, t):
        w = self.w; n, nc, S = w.eng.n, w.eng.nc, w.eng.S; ext = np.zeros((n, nc)); rg = np.zeros((n, nc)); mig = np.zeros(n); fb = np.zeros((n, S))
        src_pos = np.zeros((1, 2)); src_amp = np.zeros((1, nc)); bath = np.zeros(nc); lit_total = 0.0; ty = type_vector(w.t)
        srcs = []
        for k, a in enumerate(actions):
            ph = float(w.eng.window(t, a['t_on'], a['t_off'], a['ramp'])); amp = a.get('amp', 0.0) * ph
            if a['type'] == 'light':
                m = a['mask'](w.X) * w.alive; lit_total += float((np.abs(m) > 0.5).sum()) * abs(amp) * CHUNK
                kind, par = self.private[a['channel']]
                if kind == 'fb': fb[:, ty == par] += (amp * m)[:, None]
                elif kind == 'rg': rg[:, par] += amp * m
                elif kind == 'sec': ext[:, par] += amp * m
                elif kind == 'mig': mig += amp * m
            elif a['type'] == 'pipette': srcs.append((a['pos'], np.eye(nc)[a['ligand_index']] * amp)); lit_total += abs(amp) * CHUNK
            elif a['type'] == 'bath': bath[a['ligand_index']] += amp; lit_total += abs(amp) * CHUNK * float(w.alive.sum())
            self.dose[k] = self.dose.get(k, 0.0) + (lit_total if k == len(actions) - 1 else 0.0)
        if srcs: src_pos = np.array([s[0] for s in srcs]); src_amp = np.array([s[1] for s in srcs])
        return tuple(jnp.array(x) for x in (ext, rg, mig, fb, w.alive.astype(float), src_pos, src_amp, bath))
    def run(self, T, actions=(), sham=False, label=''):
        """chunked forcing; `sham` runs the identical code path with all amplitudes 0 (identical RNG consumption). tweezers/surgery are instantaneous logged events."""
        w = self.w; dt = w.eng.dt; per = int(round(CHUNK / dt)); acts = [dict(a, amp=(0.0 if sham else a.get('amp', 0.0))) for a in actions]
        pending = sorted([a for a in acts if a['type'] in ('tweezers', 'surgery')], key=lambda a: a['t'])
        cont = [a for a in acts if a['type'] not in ('tweezers', 'surgery')]
        tend = w.time + T
        while w.time < tend - 1e-9:
            for a in [a for a in pending if a['t'] <= w.time - self.t0 + 1e-9]:
                self._instant(a, sham); pending.remove(a)
            amps = self._amps(cont, w.time - self.t0 + 0.5 * CHUNK)     # action times are relative to the experiment start
            w.run(CHUNK, ctl_extra=amps)
            if abs((w.time - self.t0) / OBS_EVERY - round((w.time - self.t0) / OBS_EVERY)) < 1e-6: self._observe()
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
        w = self.w; self.obs.append(dict(t=float(w.time - self.t0), X=w.X.copy(), C=w.C.copy(), alive=w.alive.copy(), cell_id=w.cell_id.copy(), MU=w.MU.copy()))
    def hidden(self):
        """ground truth (HIDDEN tier)"""
        w = self.w; return dict(events=w.events + self.log, pose=self.hidden_pose, dose=self.dose, private=self.private, kind=self.kind)

# -------------------------------------------------------------------------------- renderers
def level_noise(rng, C): return C * (1 + LEVEL_NOISE * rng.standard_normal(C.shape))

def render_O1(frames, rng, channel_perm):
    """tracked cells: per frame ids, positions, 4 opaque secreted levels (order shuffled by channel_perm)"""
    out = []
    for f in frames:
        a = f['alive']; ids = f['cell_id'][a]; X = f['X'][a] + POS_NOISE * rng.standard_normal((a.sum(), 2)); Cn = level_noise(rng, f['C'][a][:, :4])[:, channel_perm]
        out.append(dict(t=f['t'], id=ids, xy=X, level=Cn))
    return out

def render_O2(frames, rng, channel_perm):
    out = []
    for f in frames:
        a = f['alive']; X = f['X'][a] + POS_NOISE * rng.standard_normal((a.sum(), 2)); Cn = level_noise(rng, f['C'][a][:, :4])[:, channel_perm]; p = rng.permutation(len(X))
        out.append(dict(t=f['t'], xy=X[p], level=Cn[p]))
    return out

def render_O3(frames, rng, channel_perm, reporters=(0, 1)):
    """images (n_reporters, IMG_PX, IMG_PX): ligand concentration field of the reporter subset (kernel exp(-|r|)), Gaussian PSF, Gaussian noise at peak SNR, arena window [-FOV,FOV]^2"""
    g = np.linspace(-FOV, FOV, IMG_PX); GX, GY = np.meshgrid(g, g); P = np.stack([GX.ravel(), GY.ravel()], 1); px = 2 * FOV / IMG_PX; out = []
    for f in frames:
        a = f['alive']; X = f['X'][a]; C = f['C'][a][:, :4][:, channel_perm]
        d = np.exp(-np.linalg.norm(P[:, None, :] - X[None], axis=-1))                     # (px, cells)
        img = np.stack([(d @ C[:, r]).reshape(IMG_PX, IMG_PX) for r in reporters])
        img = np.stack([gaussian_filter(im, PSF_SIGMA / px) for im in img]); pk = np.maximum(img.max(axis=(1, 2), keepdims=True), 1e-6)
        img = np.clip(img + rng.standard_normal(img.shape) * pk / SNR, 0, None)
        out.append(dict(t=f['t'], img=img.astype(np.float32)))
    return out
