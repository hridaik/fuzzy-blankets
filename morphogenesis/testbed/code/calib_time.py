"""T1.3: fit (k_mu,k_a) so engine time ~ SPM bins. Targets measured on 12 oracle individuals with the same operational definitions."""
import sys, time; sys.path.insert(0,'.')
from common import *
from calib_targets import merge_curve, fit_tau, belief_curve, t_cross
from scipy.special import softmax

def engine_curves(eng, names, T=200, dt0=0.05, save_dt=1.0):
    key = jax.random.PRNGKey(0)
    kmax = max(eng.P.k_mu, eng.P.k_a); dt = min(dt0 / kmax, 0.05); per = int(round(save_dt / dt)); dt = save_dt / per
    P_, S_, V_ = [], [], []
    for nm in names:
        o = oracle_run(nm); st = eng.init_from_mu(o['v0'].T)
        fin, tr = eng.run(st, 0.0, dt, per * T, key, None, 0, save_every=per)
        X, C, MU, _ = [np.array(a) for a in tr]
        P_.append(np.concatenate([np.array(st[0])[None], X]).transpose(2, 1, 0)); S_.append(np.concatenate([np.array(st[1])[None], C]).transpose(2, 1, 0))
        V_.append(np.concatenate([np.array(st[2])[None], MU]).transpose(2, 1, 0))
    return P_, S_, V_

def metrics(eng, names):
    P_, S_, V_ = engine_curves(eng, names)
    t = np.arange(P_[0].shape[2])
    D = merge_curve(P_, S_, t)
    B = np.mean([belief_curve(v) for v in V_], axis=0)
    return dict(tau_merge=fit_tau(t, D, 40, 120), t05=t_cross(t, B, 0.5), t07=t_cross(t, B, 0.7), D=D, B=B)

if __name__ == "__main__":
    tg = json.load(open(os.path.join(TB, 'data', 'oracle_targets.json')))
    t = vanilla8(); names = [f'primary_{k:04d}' for k in range(6)]
    rows = []
    for kmu in (0.1, 0.2, 0.4, 0.8, 1.6):
        for ka in (0.03, 0.06, 0.12, 0.25, 0.5):
            eng = make_engine(t, Params(k_mu=kmu, k_a=ka))
            m = metrics(eng, names)
            err = np.array([np.log(m['tau_merge'] / tg['tau_merge']), np.log(m['t05'] / tg['t_belief_05']), np.log(m['t07'] / tg['t_belief_07'])])
            rows.append((kmu, ka, m['tau_merge'], m['t05'], m['t07'], float(np.sqrt((err ** 2).mean()))))
            print(rows[-1], flush=True)
    json.dump(rows, open(os.path.join(TB, 'data', 'calib_grid.json'), 'w'))
