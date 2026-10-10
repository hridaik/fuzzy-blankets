"""Online cell tracker for unlabelled points (O2) and segmented cells (O3).
Frame-to-frame Hungarian assignment on (registered position, signal fingerprint) cost.
Registration candidates: identity, global translation, global rigid (ICP); chosen per frame by total cost.
Causal: uses only the previous frame's track state and the current frame."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist

BIG = 1e6


def features(lev, ch, sig_scale=1.0):
    """Fingerprint: type-like channels (raw) and log of the graded channel c6."""
    cols = []
    for name in ('c0', 'c1', 'c2', 'c3'):
        if name in ch:
            cols.append(lev[:, ch.index(name)] / (0.15 * sig_scale))
    if 'c6' in ch:
        cols.append(np.log(np.clip(lev[:, ch.index('c6')], 0.05, None)) / (0.08 * sig_scale))
    return np.stack(cols, 1) if cols else np.zeros((len(lev), 0))


def kabsch(P, Q):
    pc, qc = P.mean(0), Q.mean(0)
    U, S, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    d = np.sign(np.linalg.det(U @ Vt)); D = np.diag([1, d])
    R = (U @ D @ Vt).T          # row-vector convention: Q ~ (P-pc) @ R + qc
    return R, qc - pc @ R


class CellTracker:
    def __init__(self, ch, sigma_d=0.3, gate=20.0, sig_scale=1.0):
        self.ch, self.sd, self.gate, self.ss = ch, sigma_d, gate, sig_scale
        self.xy = None; self.f = None; self.ids = None; self.next_id = 0

    def _cost(self, Pxy, Pf, Cxy, Cf):
        d2 = cdist(Pxy, Cxy, 'sqeuclidean') / self.sd ** 2
        if Pf.shape[1]:
            d2 = d2 + cdist(Pf, Cf, 'sqeuclidean')
        return d2

    def _assign(self, C):
        Cg = np.where(C > self.gate, BIG, C)
        r, c = linear_sum_assignment(Cg)
        ok = Cg[r, c] < BIG
        return r[ok], c[ok]

    def _score(self, C, r, c):
        n_un = max(C.shape) - len(r)
        return C[r, c].sum() + n_un * self.gate

    def step(self, xy, lev):
        f = features(lev, self.ch, self.ss)
        n = len(xy)
        if self.xy is None:
            ids = np.arange(n); self.next_id = n
            self.xy, self.f, self.ids = xy.copy(), f, ids
            return ids.copy(), dict(reg='init', n_match=n)
        # candidates
        cands = {}
        cands['identity'] = (self.xy, None)
        t0 = xy.mean(0) - self.xy.mean(0)
        cands['translate'] = (self.xy + t0, None)
        # ICP from translation
        Pxy = self.xy + t0
        for _ in range(8):
            C = self._cost(Pxy, self.f, xy, f)
            r, c = self._assign(C)
            if len(r) < 4:
                break
            R, tt = kabsch(self.xy[r], xy[c])
            Pxy = self.xy @ R + tt
        cands['rigid'] = (Pxy, None)
        best = None
        for name, (P, _) in cands.items():
            C = self._cost(P, self.f, xy, f)
            r, c = self._assign(C)
            s = self._score(C, r, c)
            if best is None or s < best[0] - 1e-9:
                best = (s, name, r, c)
        _, name, r, c = best
        r, c = list(r), list(c)
        # stage 2: rigidly displaced blocks (e.g. a fragment moved apart abruptly): vote for a common displacement among
        # leftover points whose fingerprints agree, then rematch the block with that shift.
        for _ in range(3):
            U = np.array(sorted(set(range(len(self.xy))) - set(r)), int); V = np.array(sorted(set(range(n)) - set(c)), int)
            if len(U) < 3 or len(V) < 3:
                break
            S = cdist(self.f[U], f[V], 'sqeuclidean') if f.shape[1] else np.zeros((len(U), len(V)))
            ui, vi = np.where(S < 8.0)
            if len(ui) < 3:
                break
            disp = xy[V[vi]] - self.xy[U[ui]]
            keyg = np.round(disp / 0.4).astype(int)
            keys, inv, cnt = np.unique(keyg, axis=0, return_inverse=True, return_counts=True)
            j = int(np.argmax(cnt))
            if cnt[j] < 3:
                break
            shift = disp[inv.ravel() == j].mean(0)
            C2 = self._cost(self.xy[U] + shift, self.f[U], xy[V], f[V])
            r2, c2 = self._assign(C2)
            if len(r2) < 3:
                break
            r += list(U[r2]); c += list(V[c2])
        r, c = np.array(r, int), np.array(c, int)
        ids = -np.ones(n, int)
        ids[c] = self.ids[r]
        new = np.where(ids < 0)[0]
        ids[new] = np.arange(self.next_id, self.next_id + len(new)); self.next_id += len(new)
        self.xy, self.f, self.ids = xy.copy(), f, ids.copy()
        return ids, dict(reg=name, n_match=len(r))
