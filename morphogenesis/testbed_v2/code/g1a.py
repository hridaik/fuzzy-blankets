"""G1 (a),(b): seeded-start completeness + Jacobian rates, handedness fixed rho=1, memory off, body L."""
import sys, json; sys.path.insert(0,'.')
from an2 import *
DT = 0.0125
def eigs_nonneutral(eng, fin, tol=1e-6):
    J = np.array(eng.jac_flat(fin)); ev = np.linalg.eigvals(J)
    zero = int((np.abs(ev) < tol).sum()); nz = ev[np.abs(ev) >= tol]
    return ev, zero, nz

def run(beta, kmu, pc, pl, nseed=16, T=600.0):
    P = Params2(fix_rho=1.0, beta_E=beta, k_mu=kmu, pi_c=pc, pi_lam=pl); eng = make_engine2(make_template2(), P); eng.dt = DT
    pis = (pc, pl); out = []
    for k in range(nseed):
        st, perm = seeded_start2(eng.tm, k, 'L'); fin = run_plain(eng, st, 0, T, jax.random.PRNGKey(0))
        s = summarize(eng, fin, pis=pis); s['ok'] = bool(s['label'] == 'L' and s['orbit_complete'] and s['min_orbit_bel'] >= 0.9); out.append(s)
    ev, zero, nz = eigs_nonneutral(eng, fin)
    rates = -nz.real
    return dict(beta=beta, kmu=kmu, pi_c=pc, pi_lam=pl, n_ok=sum(o['ok'] for o in out), min_orbit_bel=min(o['min_orbit_bel'] for o in out),
                max_dL=max(o['dL'] for o in out), max_re=float(ev.real.max()), n_zero=zero, slowest_nonneutral=float(np.sort(np.abs(nz.real))[0]), n_unstable=int((ev.real > 1e-6).sum()), rho_J=float(np.abs(ev).max()))
if __name__ == "__main__":
    e2 = float(np.exp(2))
    for (b, km, pc, pl) in [(4, 0.2, e2, e2), (4, 0.5, e2, e2), (3, 0.2, e2, e2), (4, 0.2, np.exp(1), np.exp(3)), (3, 0.2, np.exp(1), np.exp(3)), (2,0.2,np.exp(0), np.exp(4))]:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in run(b, km, pc, pl).items()}, flush=True)
