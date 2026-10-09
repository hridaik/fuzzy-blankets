"""T2e: operating noise, CRN verification, natural ensembles (relational compact bodies, K=1 plans A, B and chiral)."""
import sys, json, os; sys.path.insert(0, '.')
from par import run_jobs

KMU, KA = 1.4, 0.4
def setup(kind, sig=0.0, sig_mu=0.0):
    from asm import Params, np, make_engine, make_body, auto_dt, tb_params
    t = make_body(kind)
    P = tb_params(sig_x=sig, sig_c=sig, sig_mu=sig_mu)
    eng = make_engine(t, P); eng.dt, eng.rho = auto_dt(make_engine(t, tb_params()), t)
    return t, eng

def fluct_job(kind, sig, k, T=400.0, burn=100.0):
    from asm import np, jax, seeded_start, analyse, d_rigid, cell_types, type_vector
    t, eng = setup(kind, sig, sig_mu=0.0); dt = eng.dt; per = int(round(5.0 / dt)); dt = 5.0 / per
    st = seeded_start(t, k, jit_x=0.0, jit_mu=0.0)
    fin, tr = eng.run(st, 0.0, dt, per * int(T / 5), jax.random.PRNGKey(1000 + k), None, 0, save_every=per)
    X = np.array(tr[0]); C = np.array(tr[1]); nb = int(burn / 5)
    ref = X[nb:].mean(0)                                   # mean shape (aligned frame by frame to the first post-burn frame)
    def align(A, B):
        a = A - A.mean(0); b = B - B.mean(0); U, S, Vt = np.linalg.svd(a.T @ b); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        return (R @ a.T).T
    ref0 = X[nb] - X[nb].mean(0); al = np.stack([align(X[j], ref0) for j in range(nb, len(X))])
    rms = float(np.sqrt(al.var(0).sum(1).mean() / 2))        # RMS over cells and coordinates of the time-std in the body frame
    ds = [d_rigid(X[j].T, cell_types(C[j].T), t.Xs[0], type_vector(t)) for j in range(nb, len(X), 4)]
    return dict(kind=kind, sig=sig, k=k, rms=rms, rms_over_nn=rms / 0.9, dmax=float(max(ds)), dmean=float(np.mean(ds)))

def crn_job():
    """paired twins: same key & dt; twin 2 receives a disc pulse at t_on. Checks: identical before t_on; diverge after; sham (amp 0) identical throughout."""
    from asm import np, jax, jnp, seeded_start
    t, eng = setup('A', 0.02, 0.0); dt = eng.dt; key = jax.random.PRNGKey(7); st = seeded_start(t, 0, jit_x=0.0, jit_mu=0.0)
    n, nc = t.n, t.nc; amp = np.zeros((n, nc)); amp[:6, 2] = 5.0; ton, toff = 50.0, 60.0
    ns1 = int(ton / dt) ; ns2 = int(100 / dt)
    f0 = eng.run_final(st, 0.0, dt, ns1, key, None, 0)                                   # no-intervention reference to t_on
    # twin runs over [0,100] with window box [ton,toff)
    a = eng.run_final(st, 0.0, dt, ns2, key, (jnp.zeros((n, nc)), ton, toff), 0)         # sham: amp 0
    b = eng.run_final(st, 0.0, dt, ns2, key, (jnp.array(amp), ton, toff), 0)             # pulse
    c = eng.run_final(st, 0.0, dt, ns2, key, None, 0)                                    # no window at all
    pre_b = eng.run_final(st, 0.0, dt, ns1, key, (jnp.array(amp), ton, toff), 0)         # state just before t_on in the pulsed twin
    cat = lambda s: np.concatenate([np.array(x).ravel() for x in s])
    return dict(pre_onset_max_abs_diff=float(np.abs(cat(pre_b) - cat(f0)).max()), sham_vs_none_max_abs_diff=float(np.abs(cat(a) - cat(c)).max()),
                pulse_vs_none_max_abs_diff=float(np.abs(cat(b) - cat(c)).max()), dt=dt)

def ensemble_job(kind, sig, k, T=400.0, burn=100.0, tag='train'):
    from asm import np, jax, seeded_start, make_engine
    from exports import export_run
    t, eng = setup(kind, sig); dt = eng.dt; per = int(round(5.0 / dt)); dt = 5.0 / per
    seed_off = 0 if tag == 'train' else 5000
    st = seeded_start(t, seed_off + k, jit_x=0.3)
    fin, tr = eng.run(st, 0.0, dt, per * int(T / 5), jax.random.PRNGKey(seed_off + 100 + k), None, 0, save_every=per)
    nb = int(burn / 5); frames = tuple(np.array(a)[nb:] for a in tr); tt = 5.0 * (np.arange(len(tr[0]))[nb:] + 1)
    os.makedirs('../data/natural', exist_ok=True)
    p = f'../data/natural/{kind}_{tag}_{k:02d}'; export_run(p, eng, t, frames, tt)
    return p

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == 'fluct':
        args = [('A', s, k) for s in (0.005, 0.01, 0.02, 0.04, 0.08) for k in range(3)]
        res = run_jobs(fluct_job, args, workers=8, label='fluct'); json.dump(res, open('../data/noise_fluct.json', 'w'))
        import numpy as np
        for s in (0.005, 0.01, 0.02, 0.04, 0.08):
            r = [x for x in res if x['sig'] == s]; print('sigma', s, 'rms/NN', round(float(np.mean([x['rms_over_nn'] for x in r])), 4), 'max d_tmpl over time', round(max(x['dmax'] for x in r), 3))
    elif mode == 'crn':
        print(json.dumps(crn_job(), indent=1)); json.dump(crn_job(), open('../data/crn.json', 'w'))
    elif mode == 'ens':
        sig = float(sys.argv[2]); args = [(kd, sig, k, 400.0, 100.0, tag) for kd in ('A', 'B', 'chiral') for tag, N in (('train', 12), ('val', 6)) for k in range(N)]
        res = run_jobs(ensemble_job, args, workers=8, label='ens'); json.dump(dict(sigma=sig, files=res), open('../data/natural/manifest.json', 'w'))
