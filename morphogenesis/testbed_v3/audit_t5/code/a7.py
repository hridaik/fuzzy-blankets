"""A7: response slowing - T5's recovery-time measurements vs the mean-field prediction (dl/dt = -2r sinh l + g tanh(l/2) with ligand lag k_d)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truth import *
from scipy.stats import spearmanr
r_, g_, kd, eps = 0.05, 0.6, 0.4, 1e-3
sg = lambda x: 1 / (1 + np.exp(-x))
# ---- mean-field linear rates
lstar = 2 * np.arccosh(np.sqrt(g_ / (4 * r_)))
F1 = lambda l: -2 * r_ * np.sinh(l) + g_ * np.tanh(l / 2)
dF = lambda l: -2 * r_ * np.cosh(l) + g_ / 2 / np.cosh(l / 2) ** 2
def jac3(l, dA, dB):
    A, B = dA + eps / 2, dA + dB + eps; f = (dA + eps / 2) / (dA + dB + eps)
    dfdA = (dB + eps / 2) / (dA + dB + eps) ** 2; dfdB = -(dA + eps / 2) / (dA + dB + eps) ** 2; s = sg(l) * (1 - sg(l))
    return np.array([[-2 * r_ * np.cosh(l), 2 * g_ * dfdA, 2 * g_ * dfdB], [kd * s, -kd, 0], [-kd * s, 0, -kd]])
lam_star = np.linalg.eigvals(jac3(lstar, sg(lstar), 1 - sg(lstar))); lam_0 = np.linalg.eigvals(jac3(1e-9, .5, .5))
def integrate(l, dA, dB, T=400, dt=0.05):
    out = []
    for k in range(int(T / dt)):
        f = (dA + eps / 2) / (dA + dB + eps); dl = -2 * r_ * np.sinh(l) + g_ * (2 * f - 1)
        l, dA, dB = l + dt * dl, dA + dt * kd * (sg(l) - dA), dB + dt * kd * (1 - sg(l) - dB)
        if k % int(1 / dt) == 0: out.append((l, dA, dB))
    return np.array(out)
# predicted half-recovery time vs peak excursion (dev = start_dd - dd, in units of dA-dB; start state a: dd0 = tanh(lstar/2))
dd0 = np.tanh(lstar / 2); pred = []
for pk in np.linspace(0.05, 1.55, 61):                                  # excursion of dA-dB away from its starting value (full separation 2*dd0 = 1.63)
    ddp = dd0 - pk; l0 = 2 * np.arctanh(np.clip(ddp, -.9999, .9999)); tr = integrate(l0, sg(l0), 1 - sg(l0))
    dd = tr[:, 1] - tr[:, 2]; dev = dd0 - dd
    if dev[-1] > dev[0] + 0.5: pred.append((float(pk), None, 'flips', float(dev[-1]))); continue
    idx = np.where(dev <= pk / 2)[0]; pred.append((float(pk), float(idx[0]) if len(idx) else None, 'recovers', float(dev[-1])))
# ---- hidden measurements and T5's measurements on the same sub-threshold B2/stage-2 trials
R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'b1_results.jsonl'))]
rows = []
for r in R:
    if r.get('stage') not in ('2a', '2b'): continue
    L = load_ep(r['episode'], 'dev'); F = L['frames']; ft = np.array([f['t'] for f in F]); u = np.array([f['u'][0] for f in F]); s0 = np.sign(u[0]); dev = -(u - u[0]) * s0
    h, _ = load_hidden(r['episode']); t = h['t']; dd = (h['D'][:, :, 0] - h['D'][:, :, 1]).mean(1); ddn = dd * (1 if dd[20] > 0 else -1); devh = ddn[20] - ddn
    t_end = r['t_act'] + r['dur']
    def half(tt, dv):
        k = np.argmax(dv); pk = dv[k]; tk = tt[k]; after = np.where((tt > tk) & (dv <= pk / 2))[0]; return pk, tk, (tt[after[0]] - tk if len(after) else np.nan)
    if r['flipped']: continue
    pk5, tk5, th5 = half(ft, dev); pkh, tkh, thh = half(t, devh)
    if pk5 < 0.15 or pkh < 0.1: continue
    rows.append(dict(episode=r['episode'], seed=r['seed'], peak_T5=float(pk5), thalf_T5=float(th5), peak_hidden=float(pkh), thalf_hidden=float(thh), peak_lag_T5=float(tk5 - t_end), peak_lag_hidden=float(tkh - t_end)))
a = np.array([[x['peak_T5'], x['thalf_T5'], x['peak_hidden'], x['thalf_hidden']] for x in rows])
tab = []
for lo, hi in [(0.15, 0.3), (0.3, 0.45), (0.45, 0.6), (0.6, 0.75), (0.75, 1.0)]:
    m = (a[:, 0] >= lo) & (a[:, 0] < hi)
    if m.sum():
        pm = float(np.nanmedian(a[m, 0])); pr = [p for p in pred if abs(p[0] - pm) < 0.02]
        tab.append(dict(bin=[lo, hi], n=int(m.sum()), T5_peak_median=pm, T5_thalf_median=float(np.nanmedian(a[m, 1])), hidden_peak_median=float(np.nanmedian(a[m, 2])), hidden_thalf_median=float(np.nanmedian(a[m, 3])), meanfield_thalf_at_peak=(pr[0][1] if pr else None)))
res = dict(lstar=float(lstar), eig_at_lstar=[complex(x).real for x in lam_star], eig_at_unstable=[complex(x).real for x in lam_0], dF_lstar=float(dF(lstar)), dF_zero=float(dF(0.0)), table=tab, spearman_T5=float(spearmanr(a[:, 0], a[:, 1], nan_policy='omit')[0]),
    spearman_hidden=float(spearmanr(a[:, 2], a[:, 3], nan_policy='omit')[0]), n=len(rows), meanfield_curve=pred, rows=rows)
json.dump(res, open('../data/a7_slowing.json', 'w'), indent=1, default=float)
print('l*', lstar, 'eig at l*', lam_star, 'eig at 0', lam_0, 'dF', dF(lstar), dF(0.0))
for t_ in tab: print(t_)
print('spearman', res['spearman_T5'], res['spearman_hidden'])
print([ (round(p[0],2),p[1],p[2]) for p in pred][::5])
