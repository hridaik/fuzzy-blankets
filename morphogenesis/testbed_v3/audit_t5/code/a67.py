"""A6 (history-dependent threshold vs hidden state) and A7 (response slowing vs mean-field). Data: development sysid stages 2a/2b (288 L3/L4 trials, 6 dishes), hidden logs matched by episode id."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truth import *
R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'b1_results.jsonl'))]
B2 = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'b2_results.jsonl'))]
TR = []
for cf in B2:
    for t_ in cf['trials']:
        if t_['damage']: continue
        La = load_ep(t_['episode'], 'dev')['actions'][0]
        TR.append(dict(episode=t_['episode'], seed=cf['seed'], label=cf['label'], flipped=t_['flipped'], t_act=La['t'], dur=La['dur'], amp=t_['amp'], umax_dev=t_['umax'], loc=cf['loc']))
print('B2 non-damaging trials (the set of T5 b2_commit.py):', len(TR))
sg = lambda x: 1 / (1 + np.exp(-x))
def best_thr(x, y):
    xs = np.sort(np.unique(x)); c = np.r_[xs[0] - 1, (xs[1:] + xs[:-1]) / 2, xs[-1] + 1]; best = (0, None, 1)
    for s in (1, -1):
        for t in c:
            a = np.mean(((s * (x - t)) > 0) == y)
            if a > best[0]: best = (a, t, s)
    return best
def loo_dish(x, y, g):
    acc = []
    for d in np.unique(g):
        m = g == d; a, t, s = best_thr(x[~m], y[~m]); acc.append(((s * (x[m] - t) > 0) == y[m]))
    return float(np.mean(np.concatenate(acc)))
def logit_fit(X, y, it=60, lam=1e-3):
    Xb = np.c_[np.ones(len(X)), X]; w = np.zeros(Xb.shape[1])
    for _ in range(it):
        p = sg(Xb @ w); W = p * (1 - p) + 1e-6; H = Xb.T @ (Xb * W[:, None]) + lam * np.eye(len(w)); g_ = Xb.T @ (p - y) + lam * w; w -= np.linalg.solve(H, g_)
    return w
def loo_logit(X, y, g):
    mu, sd = X.mean(0), X.std(0) + 1e-9; Z = (X - mu) / sd; acc = []
    for d in np.unique(g):
        m = g == d; w = logit_fit(Z[~m], y[~m]); p = sg(np.c_[np.ones(m.sum()), Z[m]] @ w); acc.append((p > .5) == y[m])
    return float(np.mean(np.concatenate(acc)))
rows = []
for r in TR:
    h, e = load_hidden(r['episode']); L = load_ep(r['episode'], 'dev'); F = L['frames']; ft = np.array([f['t'] for f in F]); u = np.array([f['u'][0] for f in F])
    t = h['t']; start_pos = h['L'][20].mean() > 0; st = -1.0 if start_pos else 1.0              # st: sign of the direction of travel in l
    t_rel = r['t_act'] + r['dur']
    k_end = int(round(t_rel)); k8 = k_end + 8
    if k8 >= len(t): continue
    ml = h['L'].mean(1); frac = ((h['L'] * st) > 0).mean(1); rho = sg(h['L']).mean(1); dd = (h['D'][:, :, 0] - h['D'][:, :, 1]).mean(1)
    flip_true = bool((rho[-1] < 0.5) if start_pos else (rho[-1] > 0.5))
    u0 = float(np.median(u[(ft >= 10) & (ft < 20)])); s0 = np.sign(u0); dev = -s0 * (u - u0); dev8 = float(dev[np.argmin(np.abs(ft - (t_rel + 8)))]); devpk = float(dev[(ft >= r['t_act']) & (ft <= t_rel + 8)].max())
    rows.append(dict(episode=r['episode'], seed=r['seed'], label=r['label'], flipped_T5=bool(r['flipped']), flip_true=flip_true, dev8=dev8, devpk=devpk, dev_end=float(dev[np.argmin(np.abs(ft - t_rel))]),
        x_l_end=float(st * ml[k_end]), x_l_8=float(st * ml[k8]), frac_end=float(frac[k_end]), frac_8=float(frac[k8]), rho_end=float(st * (rho[k_end] - .5)), rho_8=float(st * (rho[k8] - .5)), dd_end=float(st * dd[k_end]), dd_8=float(st * dd[k8]),
        x_l_pk=float(max(st * ml[20:k8 + 1])), amp=r['amp'], dur=r['dur'], umax_dev=r['umax_dev']))
y = np.array([x['flip_true'] for x in rows]); yT5 = np.array([x['flipped_T5'] for x in rows]); g = np.array([x['seed'] for x in rows])
res = dict(n=len(rows), n_flip_true=int(y.sum()), T5_flag_agrees_with_true=float((y == yT5).mean()))
for nm in ['dev8', 'devpk', 'dev_end', 'x_l_end', 'x_l_8', 'frac_end', 'frac_8', 'rho_end', 'rho_8', 'dd_end', 'dd_8', 'x_l_pk']:
    x = np.array([r_[nm] for r_ in rows]); a, t_, s_ = best_thr(x, y); res[nm] = dict(in_sample_acc=float(a), thr=float(t_), loo_dish_acc=loo_dish(x, y, g))
for nm, cols in [('2D x_l_8+dd_8', ['x_l_8', 'dd_8']), ('2D x_l_end+dd_end', ['x_l_end', 'dd_end']), ('2D x_l_8+frac_8', ['x_l_8', 'frac_8']), ('T5 dev8 + dev_end', ['dev8', 'dev_end'])]:
    X = np.array([[r_[c] for c in cols] for r_ in rows]); res[nm] = dict(loo_dish_acc=loo_logit(X, y, g))
res['class_balance_baseline'] = float(max(y.mean(), 1 - y.mean()))
# errors of the T5 rule: which trials
a, t_, s_ = best_thr(np.array([r_['dev8'] for r_ in rows]), y)
res['T5_rule_errors'] = [dict(episode=r_['episode'], seed=r_['seed'], dev8=r_['dev8'], flip=r_['flip_true'], x_l_8=r_['x_l_8'], dd_8=r_['dd_8']) for r_ in rows if ((s_ * (r_['dev8'] - t_) > 0) != r_['flip_true'])]
json.dump(dict(rows=rows, summary=res), open('../data/a6_threshold.json', 'w'), indent=1, default=float)
print(json.dumps(res, indent=1, default=float)[:3500])
