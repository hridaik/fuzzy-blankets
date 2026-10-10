"""v2 identity-event world: cells with (x, c, d, mu, l); alive mask; permanent unique ids; event log.  Adapted from testbed/code/world.py."""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from an2 import *
from g2cfg import FULL, DT
from shape import cell_types
HERE = os.path.dirname(os.path.abspath(__file__)); ADULTS = os.path.join(HERE, '..', 'data', 'adults')

def component_labels(X, radius=1.6):
    n = len(X); D = np.linalg.norm(X[:, None] - X[None], axis=-1) < radius; lab = -np.ones(n, int); k = 0
    for s in range(n):
        if lab[s] >= 0: continue
        st = [s]; lab[s] = k
        while st:
            u = st.pop()
            for v in np.where(D[u] & (lab < 0))[0]: lab[v] = k; st.append(v)
        k += 1
    return lab

def noise_params(noise=0.02, sig_h=0.0):
    return dict(sig_x=noise, sig_c=noise, sig_d=noise, sig_mu=noise, sig_h=sig_h)

def settled_adult(form, k=0, T=1500.0, cfg=None):
    """deterministic settled adult (cached): (state tuple of numpy arrays, perm)"""
    cfg = cfg or FULL; os.makedirs(ADULTS, exist_ok=True); import hashlib; tag = f"{form}_{k}_{hashlib.md5(json.dumps(sorted(cfg.items())).encode()).hexdigest()[:8]}"; p = os.path.join(ADULTS, tag + '.npz')
    tm = make_template2()
    if os.path.exists(p):
        z = np.load(p); return tuple(z[f'a{i}'] for i in range(5)), z['perm']
    eng = make_engine2(tm, Params2(**cfg)); eng.dt = DT
    st, perm = seeded_start2(tm, k, form); fin = run_plain(eng, st, 0, T, jax.random.PRNGKey(0))
    arr = tuple(np.array(a) for a in fin); np.savez(p, perm=perm, **{f'a{i}': a for i, a in enumerate(arr)}); return arr, perm

class World2:
    def __init__(self, tm, eng, state, perm, alive=None, cell_id=None, key=0):
        self.tm, self.eng = tm, eng; self.X, self.C, self.D, self.MU, self.L = [np.array(a) for a in state]; self.N = len(self.X)
        self.alive = np.ones(self.N, bool) if alive is None else np.array(alive, bool)
        self.cell_id = np.arange(self.N) if cell_id is None else np.array(cell_id)
        self.next_id = int(self.cell_id.max() + 1); self.events = []; self.time = 1e4; self.step_count = 0
        self.key = jax.random.PRNGKey(key); self.frames = []; self.perm0 = perm
    def state(self): return tuple(jnp.array(a) for a in (self.X, self.C, self.D, self.MU, self.L))
    def set_state(self, s): self.X, self.C, self.D, self.MU, self.L = [np.array(a) for a in s]
    def default_ctl(self):
        n, S = self.eng.n, self.eng.S
        return (jnp.zeros((n, NL)), jnp.zeros((n, NL)), jnp.zeros(n), jnp.zeros((n, S)), jnp.array(self.alive.astype(float)))
    def run(self, T, save_every=None, ctl_extra=None):
        dt = self.eng.dt; ctl = self.default_ctl() if ctl_extra is None else ctl_extra
        if save_every:
            per = int(round(save_every / dt)); nst = per * int(round(T / (per * dt)))
            fin, tr = self.eng.run_ctl(self.state(), self.time, dt, nst, self.key, ctl, -1e30, 1e30, 1.0, step0=self.step_count, save_every=per)
            for k in range(len(tr[0])):
                self.frames.append(dict(t=self.time + (k + 1) * per * dt, X=np.array(tr[0][k]), C=np.array(tr[1][k]), D=np.array(tr[2][k]), MU=np.array(tr[3][k]), L=np.array(tr[4][k]), alive=self.alive.copy(), cell_id=self.cell_id.copy()))
        else:
            nst = int(round(T / dt)); fin = self.eng.run_ctl(self.state(), self.time, dt, nst, self.key, ctl, -1e30, 1e30, 1.0, step0=self.step_count)
        self.set_state(fin); self.time += nst * dt; self.step_count += nst
    def snapshot(self): self.frames.append(dict(t=self.time, X=self.X.copy(), C=self.C.copy(), D=self.D.copy(), MU=self.MU.copy(), L=self.L.copy(), alive=self.alive.copy(), cell_id=self.cell_id.copy()))
    # ---- events
    def log(self, kind, **kw): self.events.append(dict(t=float(self.time), kind=kind, **kw))
    def remove(self, i): self.log('remove', index=int(i), cell_id=int(self.cell_id[i])); self.alive[i] = False
    def insert(self, pos, j=None, seed=0):
        """naive cell: near-uniform place logits N(0,1/8), secretions 0, l = 0 (rho = 0.5), new id"""
        j = int(np.where(~self.alive)[0][0]) if j is None else j
        rng = np.random.default_rng(10_000 + self.next_id + seed)
        self.X[j] = pos; self.C[j] = 0.0; self.D[j] = 0.0; self.MU[j] = rng.standard_normal(self.MU.shape[1]) / 8; self.L[j] = 0.0
        self.cell_id[j] = self.next_id; self.alive[j] = True
        self.log('insert', index=int(j), cell_id=int(self.next_id), pos=[float(x) for x in pos]); self.next_id += 1; return j
    def replace(self, i, seed=0):
        pos = self.X[i].copy(); old = int(self.cell_id[i]); self.remove(i); j = self.insert(pos, j=i, seed=seed)
        self.events[-1]['replaces'] = old; self.log('replace', index=int(i), old_id=old, new_id=int(self.cell_id[i])); return j
    def extrude(self, i, vec): self.X[i] = self.X[i] + np.asarray(vec); self.log('extrude', index=int(i), cell_id=int(self.cell_id[i]), vec=[float(v) for v in vec])
    def cut(self, side_mask, vec):
        idxs = np.where(side_mask & self.alive)[0]; self.X[idxs] += np.asarray(vec); self.log('cut', cells=[int(self.cell_id[i]) for i in idxs], vec=[float(v) for v in vec])
    def rho(self): return 1 / (1 + np.exp(-self.L))

def fuse2(w1, w2, offset, angle=0.0):
    c, s = np.cos(angle), np.sin(angle); R = np.array([[c, -s], [s, c]]); m2 = w2.X[w2.alive].mean(0)
    X2 = (w2.X - m2) @ R.T + m2 + np.asarray(offset)
    cat = lambda a, b: np.concatenate([a, b])
    st = (cat(w1.X, X2), cat(w1.C, w2.C), cat(w1.D, w2.D), cat(w1.MU, w2.MU), cat(w1.L, w2.L))
    ids = cat(w1.cell_id, w2.cell_id + w1.next_id); eng2 = make_engine2(w1.tm, w1.eng.P, N=len(st[0])); eng2.dt = w1.eng.dt
    w = World2(w1.tm, eng2, st, None, alive=cat(w1.alive, w2.alive), cell_id=ids); w.next_id = int(ids.max() + 1)
    w.log('fuse', n1=int(len(w1.X)), n2=int(len(w2.X)), offset=[float(o) for o in offset], angle=float(angle)); return w

def new_adult2(form='L', k=0, capacity=24, noise=0.02, sig_h=0.0, key=0, cfg=None, burn=0.0):
    cfg = dict(cfg or FULL); (arr, perm) = settled_adult(form, k, cfg=cfg); tm = make_template2()
    P = Params2(**cfg, **noise_params(noise, sig_h)) if noise else Params2(**cfg)
    eng = make_engine2(tm, P, N=capacity if capacity > 24 else None); eng.dt = DT
    X, C, D, MU, L = [a.copy() for a in arr]
    if capacity > 24:
        pad = capacity - 24; X = np.concatenate([X, np.full((pad, 2), 1e3)]); C = np.concatenate([C, np.zeros((pad, 4))]); D = np.concatenate([D, np.zeros((pad, 2))])
        MU = np.concatenate([MU, np.zeros((pad, 24))]); L = np.concatenate([L, np.zeros(pad)])
        alive = np.r_[np.ones(24, bool), np.zeros(pad, bool)]; w = World2(tm, eng, (X, C, D, MU, L), perm, alive=alive, cell_id=np.arange(capacity), key=key); w.next_id = 24; w.cell_id[24:] = -1
    else: w = World2(tm, eng, (X, C, D, MU, L), perm, key=key)
    if burn: w.run(burn)
    return w

def describe2(w, group=None):
    g = np.where(w.alive)[0] if group is None else np.array(group); tm = w.tm; S = tm.S
    X = w.X[g]; q = np.array(jax.nn.softmax(jnp.array(w.MU[g]), axis=1)); slot = q.argmax(1); orb = orbits_mirror(tm); no = orb.max() + 1
    cnt = np.bincount(slot, minlength=S); ocnt = np.bincount(orb[slot], minlength=no); oexp = np.bincount(orb, minlength=no)
    comp = component_labels(X, 1.6); D = np.linalg.norm(X[:, None] - X[None], axis=-1) + 9 * np.eye(len(g))
    rho = w.rho()[g]
    d = dict(n=int(len(g)), n_components=int(comp.max() + 1), n_isolated=int((D.min(1) > 1.6).sum()), slots_once=int((cnt == 1).sum()), orbit_ok=bool((ocnt == oexp).all()), slots_vacant=int((cnt == 0).sum()),
             slots_dup=int((cnt > 1).sum()), min_maxbel=float(q.max(1).min()), mean_rho=float(rho.mean()), frac_rho_L=float((rho > 0.5).mean()))
    if len(g) == S:
        lab, dL, dR = classify_shape(tm, X, w.C[g]); d.update(shape=lab, dL=float(dL), dR=float(dR))
        if lab in ('L', 'R') and not d['orbit_ok']: d['shape'] = 'DEFECT'; d['reason'] = 'incomplete'
        if d['n_components'] > 1 or d['n_isolated']: d['shape'] = 'DEFECT'; d['reason'] = 'split/extrusion'
    else: d['shape'] = 'fragment'
    return d
