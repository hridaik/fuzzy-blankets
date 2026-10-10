"""Unsupervised state discovery (own GMM-EM) and the online state estimator."""
import numpy as np


def logsumexp(a, axis=-1):
    m = a.max(axis, keepdims=True)
    return (m + np.log(np.exp(a - m).sum(axis, keepdims=True))).squeeze(axis)


class GMM:
    def __init__(self, k, ridge=1e-3, n_init=8, iters=200, seed=0):
        self.k, self.ridge, self.n_init, self.iters, self.seed = k, ridge, n_init, iters, seed

    def _logp(self, X):
        n, d = X.shape
        out = np.zeros((n, self.k))
        for j in range(self.k):
            L = np.linalg.cholesky(self.cov[j])
            z = np.linalg.solve(L, (X - self.mu[j]).T)
            out[:, j] = np.log(self.pi[j] + 1e-300) - 0.5 * (z ** 2).sum(0) - np.log(np.diag(L)).sum() - 0.5 * d * np.log(2 * np.pi)
        return out

    def fit(self, X):
        n, d = X.shape
        best = None
        for s in range(self.n_init):
            rng = np.random.default_rng(self.seed * 1000 + s)
            # k-means++ init
            cen = [X[rng.integers(n)]]
            for _ in range(self.k - 1):
                dd = np.min(((X[:, None] - np.array(cen)[None]) ** 2).sum(-1), 1)
                cen.append(X[rng.choice(n, p=dd / dd.sum())] if dd.sum() > 0 else X[rng.integers(n)])
            self.mu = np.array(cen); self.pi = np.full(self.k, 1 / self.k); self.cov = np.array([np.eye(d)] * self.k)
            lab = np.argmin(((X[:, None] - self.mu[None]) ** 2).sum(-1), 1)
            R = np.eye(self.k)[lab]
            prev = -np.inf
            for it in range(self.iters):
                Nk = R.sum(0) + 1e-9
                self.pi = Nk / n
                self.mu = (R.T @ X) / Nk[:, None]
                for j in range(self.k):
                    Xc = X - self.mu[j]
                    self.cov[j] = (R[:, j, None] * Xc).T @ Xc / Nk[j] + self.ridge * np.eye(d)
                lp = self._logp(X)
                ll = logsumexp(lp, 1).sum()
                R = np.exp(lp - logsumexp(lp, 1)[:, None])
                if ll - prev < 1e-7 * abs(ll):
                    break
                prev = ll
            if best is None or ll > best[0]:
                best = (ll, self.mu.copy(), self.cov.copy(), self.pi.copy())
        _, self.mu, self.cov, self.pi = best
        self.train_ll = best[0]
        return self

    def loglik(self, X):
        return logsumexp(self._logp(X), 1)

    def posterior(self, X):
        lp = self._logp(X)
        return np.exp(lp - logsumexp(lp, 1)[:, None])

    def n_params(self, d):
        return self.k * (d + d * (d + 1) / 2) + self.k - 1


def ari(a, b):
    a = np.asarray(a); b = np.asarray(b)
    ua, ia = np.unique(a, return_inverse=True); ub, ib = np.unique(b, return_inverse=True)
    C = np.zeros((len(ua), len(ub)))
    np.add.at(C, (ia, ib), 1)
    comb = lambda x: x * (x - 1) / 2
    s = comb(C).sum(); sa = comb(C.sum(1)).sum(); sb = comb(C.sum(0)).sum(); n = comb(len(a))
    exp = sa * sb / n if n > 0 else 0
    mx = (sa + sb) / 2
    return 1.0 if mx == exp else float((s - exp) / (mx - exp))


class Preproc:
    """standardise + PCA (fit on calibration only)."""
    def fit(self, X, var=0.95, max_dim=8):
        self.m = X.mean(0); self.s = np.maximum(X.std(0), 1e-9)
        Z = (X - self.m) / self.s
        U, S, Vt = np.linalg.svd(Z, full_matrices=False)
        ev = S ** 2 / (S ** 2).sum()
        self.d = int(min(max_dim, np.searchsorted(np.cumsum(ev), var) + 1))
        self.W = Vt[:self.d].T / (S[:self.d] / np.sqrt(len(X)))      # whitened
        return self

    def transform(self, X):
        return ((X - self.m) / self.s) @ self.W


class OnlineState:
    """Frozen GMM + sticky HMM filter. label=-1 when the frame is out-of-distribution (loglik below cal quantile)."""
    def __init__(self, pre, gmm, ood_thr, stay=0.95):
        self.pre, self.gmm, self.ood, self.stay = pre, gmm, ood_thr, stay
        self.k = gmm.k
        self.rate = -np.log(stay) / 100.0     # switching hazard per time unit; `stay` is the per-natural-interval (100) persistence

    def _A(self, dt):
        k = self.k; st = float(np.exp(-self.rate * dt)) if k > 1 else 1.0
        A = np.full((k, k), (1 - st) / max(k - 1, 1)); np.fill_diagonal(A, st)
        return A

    def run(self, X_seq, t_seq=None):
        """X_seq: (T,D) raw descriptors of one lineage, in time order. Returns dict of per-frame arrays."""
        Z = self.pre.transform(X_seq)
        lp = self.gmm._logp(Z)
        ll = logsumexp(lp, 1)
        post_raw = np.exp(lp - ll[:, None])
        alpha = None; labels = []; post = []
        for t in range(len(Z)):
            lik = np.exp(lp[t] - lp[t].max())
            dt = 100.0 if (t_seq is None or t == 0) else float(t_seq[t] - t_seq[t - 1])
            a = (self.gmm.pi if alpha is None else alpha @ self._A(dt)) * lik
            alpha = a / a.sum()
            labels.append(int(np.argmax(alpha))); post.append(float(alpha.max()))
        labels = np.array(labels)
        ood = ll < self.ood
        return dict(label=np.where(ood, -1, labels), post=np.array(post), post_raw=post_raw, ll=ll, ood=ood)


def change_times(labels, post, conf=0.9, ood_is_change=True):
    """Online change detection: a change is declared at the first frame where the filtered label differs from the
    last confirmed label with posterior >= conf. OOD label (-1) counts as a change away from every state."""
    out = []; cur = None
    for t, (l, p) in enumerate(zip(labels, post)):
        if cur is None:
            if l >= 0 and p >= conf:
                cur = l
            continue
        if l != cur and (p >= conf or l == -1):
            out.append((t, int(cur), int(l)))
            cur = l if l >= 0 else cur
    return out
