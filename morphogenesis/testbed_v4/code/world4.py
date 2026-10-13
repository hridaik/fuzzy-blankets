"""v4 identity-event world (adapted from testbed_v3/code/world3.py for the 7-tuple state incl. ubar)."""
from lib4 import *
class World4:
    def __init__(self, eng, state, alive=None, cell_id=None, key=0, perm=None):
        self.eng = eng; self.X, self.C, self.MU, self.L, self.D, self.E, self.U = [np.array(a) for a in state]; self.N = len(self.X)
        self.alive = np.ones(self.N, bool) if alive is None else np.array(alive, bool); self.cell_id = np.arange(self.N) if cell_id is None else np.array(cell_id)
        self.next_id = int(self.cell_id.max() + 1); self.events = []; self.time = 1e4; self.step_count = 0; self.key = jax.random.PRNGKey(key); self.perm0 = perm
    def state(self): return tuple(jnp.array(a) for a in (self.X, self.C, self.MU, self.L, self.D, self.E, self.U))
    def set_state(self, s): self.X, self.C, self.MU, self.L, self.D, self.E, self.U = [np.array(a) for a in s]
    def run(self, T, ctl_extra=None):
        ctl = list(zero_ctl(self.eng)); ctl[4] = jnp.array(self.alive.astype(float)); ctl = tuple(ctl) if ctl_extra is None else ctl_extra; nst = int(round(T / self.eng.dt))
        fin = self.eng.run_ctl(self.state(), self.time, self.eng.dt, nst, self.key, ctl, -1e30, 1e30, 1.0, step0=self.step_count); self.set_state(fin); self.time += nst * self.eng.dt; self.step_count += nst
    def log(self, kind, **kw): self.events.append(dict(t=float(self.time), kind=kind, **kw))
    def remove(self, i): self.log('remove', index=int(i), cell_id=int(self.cell_id[i])); self.alive[i] = False
    def insert(self, pos, j=None, seed=0):
        j = int(np.where(~self.alive)[0][0]) if j is None else j; rng = np.random.default_rng(10_000 + self.next_id + seed)
        self.X[j] = pos; self.C[j] = 0.0; self.D[j] = 0.0; self.E[j] = 0.0; self.U[j] = 0.0; self.MU[j] = rng.standard_normal(self.MU.shape[1]) / 8; self.L[j] = 0.0
        self.cell_id[j] = self.next_id; self.alive[j] = True; self.log('insert', index=int(j), cell_id=int(self.next_id)); self.next_id += 1; return j
    def replace(self, i, seed=0): pos = self.X[i].copy(); self.remove(i); return self.insert(pos, j=i, seed=seed)
    def extrude(self, i, vec): self.X[i] = self.X[i] + np.asarray(vec); self.log('extrude', index=int(i), vec=[float(v) for v in vec])
    def cut(self, mask, vec): idx = np.where(mask & self.alive)[0]; self.X[idx] += np.asarray(vec); self.log('cut', cells=[int(self.cell_id[i]) for i in idx])
    def rho(self): return 1 / (1 + np.exp(-self.L))

def new_world(state='a', noise=False, key=0, N=None, dish=None, variant='phi04'):
    dish = dish or median_dish(); e = get_engine(dish, variant, noise=noise, gamma_on=False, N=N); arr, perm = settled(dish, variant, state)
    if N is None or N == 24: return World4(e, arr, key=key, perm=perm)
    raise ValueError

def describe4(w, group=None, base=None):
    """truth for a group of cells (indices). group=None -> all alive. returns n, components, isolated, fill_ok (full bodies only), tail angle (if computable), mean rho, state"""
    g = np.where(w.alive)[0] if group is None else np.asarray(group); X = w.X[g]; MU = w.MU[g]; q = np.exp(MU - MU.max(1, keepdims=True)); q /= q.sum(1, keepdims=True); pl = q.argmax(1)
    A = nbr_matrix(X); nc, lab = connected_components(csr_matrix(A), directed=False); sizes = np.bincount(lab); rho = w.rho()[g]
    d = dict(n=int(len(g)), n_components=int(nc), n_isolated=int((sizes == 1).sum()) if len(g) > 1 else 0, mean_rho=float(rho.mean()), frac_a=float((rho > 0.5).mean()), state=('a' if rho.mean() > 0.5 else 'b'))
    nb = int(np.isin(pl, TM.body).sum()); nt = int(np.isin(pl, TM.tail).sum()); d['angle'] = float(tail_angle(TM, X, pl)) if (nb >= 4 and nt >= 1) else None
    if len(g) == 24: ok, mb = place_fill(TM, q); d['fill_ok'] = bool(ok); d['min_bel'] = float(mb)
    if base is not None and len(g) == 24:
        inter = (A & base).sum(1); uni = (A | base).sum(1); d['jac'] = float(np.where(uni > 0, inter / np.maximum(uni, 1), 1.0).mean())
    tau = tauJ()
    if len(g) == 24:
        d['intact_structure'] = bool(d['n_components'] == 1 and d['fill_ok'] and (d.get('jac', 1.0) >= tau))   # (ii)-(iv); (i) material is violated by definition in replacement events
    return d
