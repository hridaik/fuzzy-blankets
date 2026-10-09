"""Part I: identity-event support. A World holds up to N_cap cell positions (alive or dead) over S template slots.
Permanent unique cell_id (never reused), alive mask, event log, frames with per-frame alive/cell_id.
Events: remove, insert (naive cell), replace, extrude (tweezers), cut (body-frame line), fuse (two bodies in one arena)."""
import sys, os, json; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from asm import *
import chiral as CH

class World:
    def __init__(self, tmpl, eng, state, perm_slots, alive=None, cell_id=None, key=0, sig=0.0):
        self.t, self.eng = tmpl, eng; X, C, MU, ZE = [np.array(a) for a in state]
        self.X, self.C, self.MU, self.ZE = X, C, MU, ZE; self.N = len(X)
        self.alive = np.ones(self.N, bool) if alive is None else np.array(alive, bool)
        self.cell_id = np.arange(self.N) if cell_id is None else np.array(cell_id)
        self.next_id = int(self.cell_id.max() + 1); self.events = []; self.time = 1e4; self.step_count = 0
        self.key = jax.random.PRNGKey(key); self.frames = []; self.perm0 = perm_slots

    # ---- dynamics
    def state(self): return (jnp.array(self.X), jnp.array(self.C), jnp.array(self.MU), jnp.array(self.ZE))
    def set_state(self, s): self.X, self.C, self.MU, self.ZE = [np.array(a) for a in s]
    def run(self, T, save_every=None, ctl_extra=None):
        eng = self.eng; dt = eng.dt; per = int(round((save_every or T) / dt)); nst = per * int(round(T / (per * dt))) if save_every else int(round(T / dt))
        n, nc, S = eng.n, eng.nc, eng.S
        ctl = (jnp.zeros((n, nc)), jnp.zeros((n, nc)), jnp.zeros(n), jnp.zeros((n, S)), jnp.array(self.alive.astype(float))) if ctl_extra is None else ctl_extra
        if save_every:
            fin = self._run_save(dt, per, nst, ctl)
        else:
            fin = self._run_plain(dt, nst, ctl)
        self.set_state(fin); self.time += nst * dt; self.step_count += nst
    def _run_plain(self, dt, nst, ctl):
        return self.eng.run_ctl(self.state(), self.time, dt, nst, self.key, ctl, -1e30, 1e30, 1.0, step0=self.step_count)
    def _run_save(self, dt, per, nst, ctl):
        fin, tr = self.eng.run_ctl(self.state(), self.time, dt, nst, self.key, ctl, -1e30, 1e30, 1.0, step0=self.step_count, save_every=per)
        for k in range(len(tr[0])):
            self.frames.append(dict(t=self.time + (k + 1) * per * dt, X=np.array(tr[0][k]), C=np.array(tr[1][k]), MU=np.array(tr[2][k]), alive=self.alive.copy(), cell_id=self.cell_id.copy()))
        return fin
    def snapshot(self): self.frames.append(dict(t=self.time, X=self.X.copy(), C=self.C.copy(), MU=self.MU.copy(), alive=self.alive.copy(), cell_id=self.cell_id.copy()))

    # ---- events (all logged)
    def log(self, kind, **kw): self.events.append(dict(t=float(self.time), kind=kind, **kw))
    def remove(self, i):
        self.log('remove', index=int(i), cell_id=int(self.cell_id[i])); self.alive[i] = False
    def insert(self, pos, j=None, seed=0):
        """naive cell: near-uniform logits N(0,0.125), secretion reset to 0, at `pos`; uses a dead array slot j"""
        j = int(np.where(~self.alive)[0][0]) if j is None else j
        rng = np.random.default_rng(10_000 + self.next_id + seed)
        self.X[j] = pos; self.C[j] = 0.0; self.MU[j] = rng.standard_normal(self.MU.shape[1]) / 8; self.ZE[j] = 0.0
        self.cell_id[j] = self.next_id; self.alive[j] = True
        self.log('insert', index=int(j), cell_id=int(self.next_id), pos=[float(x) for x in pos]); self.next_id += 1; return j
    def replace(self, i, seed=0):
        pos = self.X[i].copy(); old = int(self.cell_id[i]); self.remove(i); j = self.insert(pos, j=i, seed=seed)
        self.events[-1]['replaces'] = old; self.log('replace', index=int(i), old_id=old, new_id=int(self.cell_id[i])); return j
    def extrude(self, i, vec):
        """tweezers: instantaneous displacement of one cell by vec (arena coordinates)"""
        self.X[i] = self.X[i] + np.asarray(vec); self.log('extrude', index=int(i), cell_id=int(self.cell_id[i]), vec=[float(v) for v in vec])
    def cut(self, side_mask, vec):
        """CUT: the cells in side_mask are moved apart (arena displacement vec) as a separate fragment"""
        idxs = np.where(side_mask & self.alive)[0]; self.X[idxs] += np.asarray(vec)
        self.log('cut', cells=[int(self.cell_id[i]) for i in idxs], vec=[float(v) for v in vec])
    def body_frame(self, ref_perm=None):
        """body-frame template coordinates of the slot each cell holds (ground truth; hidden tier only)"""
        p = np.array(jax.nn.softmax(jnp.array(self.MU), axis=1)); slot = p.argmax(1); return self.t.Xs[0][:, slot].T, slot

def fuse(w1, w2, offset, angle=0.0, eng=None):
    """FUSION: two bodies placed in one arena; each cell keeps its logits over the S slots. returns a new World with engine for N1+N2."""
    c, s = np.cos(angle), np.sin(angle); R = np.array([[c, -s], [s, c]])
    X2 = (w2.X - w2.X[w2.alive].mean(0)) @ R.T + w2.X[w2.alive].mean(0) + np.asarray(offset)
    X = np.concatenate([w1.X, X2]); C = np.concatenate([w1.C, w2.C]); MU = np.concatenate([w1.MU, w2.MU]); ZE = np.concatenate([w1.ZE, w2.ZE])
    alive = np.concatenate([w1.alive, w2.alive]); ids = np.concatenate([w1.cell_id, w2.cell_id + w1.next_id])
    eng2 = make_engine(w1.t, w1.eng.P, N=len(X)); eng2.dt = w1.eng.dt
    w = World(w1.t, eng2, (X, C, MU, ZE), None, alive=alive, cell_id=ids); w.next_id = int(ids.max() + 1)
    w.log('fuse', n1=int(len(w1.X)), n2=int(len(w2.X)), offset=[float(o) for o in offset], angle=float(angle)); return w

def new_adult(kind='L', k=0, capacity=24, sig=0.0, key=0):
    """adult chiral body (L or R), operating point of SITUS_CALIBRATION.md; capacity > 24 adds dead spare positions for insertions"""
    from s3common import setup, adult
    t, eng = setup(sig=sig)
    fin, perm = adult(t, eng, k, mirror=(kind == 'R'))
    if capacity > 24:
        eng = make_engine(t, eng.P, N=capacity); eng.dt = 0.02
        X, C, MU, ZE = [np.array(a) for a in fin]; pad = capacity - 24
        X = np.concatenate([X, np.full((pad, 2), 1e3)]); C = np.concatenate([C, np.zeros((pad, C.shape[1]))]); MU = np.concatenate([MU, np.zeros((pad, MU.shape[1]))]); ZE = np.concatenate([ZE, np.zeros((pad, ZE.shape[1]))])
        alive = np.r_[np.ones(24, bool), np.zeros(pad, bool)]; w = World(t, eng, (X, C, MU, ZE), perm, alive=alive, cell_id=np.arange(capacity), key=key)
        w.next_id = 24; w.cell_id[24:] = -1
    else:
        w = World(t, eng, fin, perm, key=key)
    return w
