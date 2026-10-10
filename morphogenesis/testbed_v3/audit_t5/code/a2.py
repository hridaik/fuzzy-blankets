"""A2: natural false-alarm anatomy of the cohesion axis. Observed (monitor) vs true (noise-free) geometry for the 62 baseline-clean-or-not dishes (60 twin episodes + the 2 baseline_not_clean controller episodes)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truth import *
R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'heldout_summary.jsonl'))]
rows = []; MB = MB
sel = [r for r in R if r['arm'] == 'twin'] + [r for r in R if r['arm'] == 'ctrl' and r['reason'] == 'baseline_not_clean']
for r in sel:
    h, e = load_hidden(r['episode']); g = geom_series(h['X'], h['alive']); L = load_ep(r['episode']); F = L['frames']; n = min(len(F), len(g['mst']))
    obs = np.array([f['mst_max'] for f in F])[:n]; tru = g['mst'][:n]; s1o = np.array([f['s1_rel'] for f in F])[:n]; s2o = np.array([f['s2_rel'] for f in F])[:n]
    _, r1, r2 = true_geometry_ok(g)
    med3 = np.array([np.median(obs[max(0, k - 2):k + 1]) for k in range(n)]); med5 = np.array([np.median(obs[max(0, k - 4):k + 1]) for k in range(n)])
    rows.append(dict(seed=r['seed'], episode=r['episode'], n=int(n), true_max_mst=float(tru.max()), obs_max_mst=float(obs.max()), margin_true=float(MB['mst_max'] - tru.max()), obs_minus_true_median=float(np.median(obs - tru)), obs_minus_true_p95=float(np.quantile(obs - tru, .95)),
        obs_exceed_raw=bool((obs > MB['mst_max']).any()), true_exceed=bool((tru > MB['mst_max']).any()), obs_exceed_med3=bool((med3 > MB['mst_max']).any()), obs_exceed_med5=bool((med5 > MB['mst_max']).any()),
        n_obs_exceed_frames=int((obs > MB['mst_max']).sum()), s1_obs_max=float(s1o.max()), s2_obs_max=float(s2o.max()), s1_true_max=float(r1[:n].max()), s2_true_max=float(r2[:n].max())))
T = dict(n_dishes=len(rows), n_obs_exceed_raw=sum(r['obs_exceed_raw'] for r in rows), n_true_exceed=sum(r['true_exceed'] for r in rows), n_obs_exceed_med3=sum(r['obs_exceed_med3'] for r in rows), n_obs_exceed_med5=sum(r['obs_exceed_med5'] for r in rows),
    true_max_mst_quantiles={q: float(np.quantile([r['true_max_mst'] for r in rows], q)) for q in (0.5, 0.9, 0.95, 0.99, 1.0)}, obs_max_mst_quantiles={q: float(np.quantile([r['obs_max_mst'] for r in rows], q)) for q in (0.5, 0.9, 0.95, 0.99, 1.0)},
    obs_minus_true_median=float(np.median([r['obs_minus_true_median'] for r in rows])), obs_minus_true_p95_median=float(np.median([r['obs_minus_true_p95'] for r in rows])),
    dishes_with_true_margin_below_0_06=[r['seed'] for r in rows if r['margin_true'] < 0.06], bound=MB['mst_max'], s1_bound=MB['s1_rel'], s2_bound=MB['s2_rel'],
    max_s1_obs=max(r['s1_obs_max'] for r in rows), max_s2_obs=max(r['s2_obs_max'] for r in rows), frame_dt_in_live_logs=1.0)
json.dump(dict(summary=T, rows=rows), open('../data/a2_falsealarm.json', 'w'), indent=1, default=float)
print(json.dumps(T, indent=1, default=float)); print([ (r['seed'], round(r['true_max_mst'], 3), round(r['obs_max_mst'], 3), r['n_obs_exceed_frames'], r['obs_exceed_med3']) for r in rows if r['obs_exceed_raw'] or r['margin_true'] < 0.1])
F = load_ep(R[0]['episode'])['frames']; print('live frame spacing', F[1]['t'] - F[0]['t'])
