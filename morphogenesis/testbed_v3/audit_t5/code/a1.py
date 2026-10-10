"""A1: truth of the claims for every held-out episode. Output data/a1_episodes.json, data/a1_tables.json"""
import sys, os, json, numpy as np, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truth import *
R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'heldout_summary.jsonl'))]
by = collections.defaultdict(dict)
for r in R: by[r['seed']][r['arm']] = r
HOLD, TAIL, MARG = 120.0, 40.0, CFG['true_switch']['tail_margin_rho']
rows = []; geomdump = {}
for seed, arms in sorted(by.items()):
    c = arms['ctrl']
    if c['reason'] == 'quota_skip': continue
    twin = arms.get('twin', {}).get('episode')
    for arm, r in arms.items():
        S = summarise(r['episode'], twin if (arm != 'twin' and twin) else None)
        L = load_ep(r['episode']); F = L['frames']; ft = np.array([f['t'] for f in F]); t = S['t']; rho = S['rho']
        start = 'a' if rho[0] > 0.5 else 'b'; start20 = 'a' if rho[min(20, len(rho) - 1)] > 0.5 else 'b'; end = 'a' if rho[-1] > 0.5 else 'b'
        tgt_a = (start == 'b'); on_t = (rho > 0.5) if tgt_a else (rho < 0.5)
        # first crossing that persists to the end
        persist_t = None
        for k in range(len(t)):
            if on_t[k:].all(): persist_t = float(t[k]); break
        tail = t > t[-1] - TAIL - 1e-9; margin_ok = bool(np.all(np.abs(rho[tail] - 0.5) >= MARG) and on_t[tail].all())
        t_last_end = r.get('t_last_end'); hold_ok = (t_last_end is None) or (t[-1] >= t_last_end + HOLD - 1e-9)
        # monitor side
        mon_state = [f['state'] for f in F]; mon_sure = [f['state_sure'] for f in F]
        tgt_lab = 'S+' if tgt_a else 'S-'
        mon_t = None
        for k in range(len(F)):
            if all(mon_state[j] == tgt_lab and mon_sure[j] for j in range(k, len(F))): mon_t = float(ft[k]); break
        # body truth
        g_ok = S['geom_ok_inst']; intact_members = S['members_ok']; ev_empty = (len(S['hidden_events']) == 0)
        dX = S.get('dX_twin'); same_as_twin = (dX is None) or (dX <= 1e-6)
        intact = bool(intact_members and ev_empty and same_as_twin and g_ok.all())
        intact_core = bool(intact_members and ev_empty and same_as_twin)             # no operation, positions identical to twin
        true_success = bool(persist_t is not None and margin_ok and hold_ok and intact and start20 != end)
        # monitor flags first violation
        v_now = [f['V_body_now'] for f in F]; first_viol = next((float(ft[k]) for k in range(len(F)) if not v_now[k]), None)
        rows.append(dict(seed=seed, arm=arm, eid=r['episode'], start_true=start, start_true_t20=start20, end_true=end, target_side=('a' if tgt_a else 'b'),
            start_mon=r.get('start'), end_mon=r.get('end_state'), end_sure=r.get('end_sure'), t_end=float(t[-1]), t_last_end=t_last_end, persisted_switch=persist_t is not None and start20 != end,
            t_cross_true=persist_t, margin_ok=margin_ok, hold_ok=hold_ok, true_intact=intact, true_intact_core=intact_core, true_geom_ok_all=bool(g_ok.all()), true_geom_ok_frac=float(g_ok.mean()), dX_twin=dX,
            members_ok=intact_members, hidden_events=len(S['hidden_events']), true_success=true_success, rho_end=float(rho[-1]), rho_t20=float(rho[min(20, len(rho) - 1)]), max_mst_true=float(S['geom']['mst'].max()), max_s1rel_true=float(S['r1'].max()), max_s2rel_true=float(S['r2'].max()),
            mon_success=bool(r['success']), mon_V=bool(r['V_body']), mon_Vc=bool(r['V_body_conservative']), mon_abort=(r.get('reason') == 'abort_identity'), mon_reason=r.get('reason'), mon_t_target_sustained=mon_t,
            mon_first_viol_t=first_viol, dose=r['dose']))
        if (arm == 'twin' and seed in (6040,)) or (arm == 'ctrl' and seed in (6001, 6039, 6040)):
            geomdump[f'{seed}_{arm}'] = dict(t=t.tolist(), mst=S['geom']['mst'].tolist(), r1=S['r1'].tolist(), r2=S['r2'].tolist(), ncomp=S['geom']['ncomp'].tolist(), n=S['geom']['n'].tolist(),
                mon_mst=[f['mst_max'] for f in F], mon_s1rel=[f['s1_rel'] for f in F], mon_s2rel=[f['s2_rel'] for f in F], mon_ncomp=[f['ncomp'] for f in F], mon_n=[f['n'] for f in F], mon_t=ft.tolist(), mon_vnow=v_now)
json.dump(rows, open('../data/a1_episodes.json', 'w'), default=float); json.dump(geomdump, open('../data/a1_geomdump.json', 'w'), default=float)
# ---------------------------------------------------------------- tables
def conf(rows, mon, tru):
    tp = sum(1 for r in rows if r[mon] and r[tru]); fp = sum(1 for r in rows if r[mon] and not r[tru]); fn = sum(1 for r in rows if not r[mon] and r[tru]); tn = sum(1 for r in rows if not r[mon] and not r[tru]); return dict(TP=tp, FP=fp, FN=fn, TN=tn)
ev = [r for r in rows if r['mon_reason'] != 'baseline_not_clean']             # 60 evaluated dishes x 7 arms = 420 episodes
bn = [r for r in rows if r['mon_reason'] == 'baseline_not_clean']
T = dict(n_eval_episodes=len(ev), n_baseline_not_clean_episodes=len(bn))
T['success'] = {arm: conf([r for r in ev if r['arm'] == arm], 'mon_success', 'true_success') for arm in ['ctrl', 'twin', 'sham', 'random', 'fixed', 'whole', 'whole_dm']}
T['success_all'] = conf(ev, 'mon_success', 'true_success')
T['V_body_vs_intact'] = {arm: conf([r for r in ev if r['arm'] == arm], 'mon_V', 'true_intact') for arm in ['ctrl', 'twin', 'sham', 'random', 'fixed', 'whole', 'whole_dm']}
T['V_body_all'] = conf(ev, 'mon_V', 'true_intact'); T['Vc_all'] = conf(ev, 'mon_Vc', 'true_intact')
T['V_body_vs_intact_core_all'] = conf(ev, 'mon_V', 'true_intact_core')
T['abort_vs_intact'] = dict(abort_n=sum(r['mon_abort'] for r in ev), abort_with_true_loss=sum(1 for r in ev if r['mon_abort'] and not r['true_intact_core']))
T['baseline_not_clean'] = [dict(seed=r['seed'], mon_V=r['mon_V'], true_intact=r['true_intact'], true_geom_frac=r['true_geom_ok_frac'], max_mst=r['max_mst_true'], max_s1=r['max_s1rel_true'], max_s2=r['max_s2rel_true']) for r in bn]
# state truth: start/end
T['start_end'] = {arm: collections.Counter((r['start_true_t20'], r['end_true']) for r in ev if r['arm'] == arm) for arm in ['ctrl', 'twin', 'fixed', 'whole', 'whole_dm', 'random']}
T['start_end'] = {a: {f'{k[0]}->{k[1]}': v for k, v in c.items()} for a, c in T['start_end'].items()}
T['persisted_switch'] = {arm: sum(r['persisted_switch'] for r in ev if r['arm'] == arm) for arm in ['ctrl', 'twin', 'sham', 'random', 'fixed', 'whole', 'whole_dm']}
T['mon_target_state_at_end_vs_true'] = {arm: dict(mon_end_is_target=sum(1 for r in ev if r['arm'] == arm and r['mon_success']), true_end_on_target=sum(1 for r in ev if r['arm'] == arm and r['persisted_switch'])) for arm in ['ctrl', 'fixed', 'whole', 'random', 'whole_dm']}
# disagreements
dis = []
for r in ev:
    for mon, tru, name in [('mon_success', 'true_success', 'SUCCESS'), ('mon_V', 'true_intact', 'V_body'), ('mon_Vc', 'true_intact', 'V_body_conservative')]:
        if r[mon] != r[tru]: dis.append(dict(seed=r['seed'], arm=r['arm'], eid=r['eid'], verdict=name, monitor=r[mon], truth=r[tru], reason=r['mon_reason'], persisted_switch=r['persisted_switch'], true_geom_ok_frac=r['true_geom_ok_frac'], rho_end=r['rho_end'], t_cross_true=r['t_cross_true'], mon_first_viol_t=r['mon_first_viol_t']))
T['disagreements'] = dis
# latency monitor vs truth (ctrl, fixed, whole successes both)
lat = [r['mon_t_target_sustained'] - r['t_cross_true'] for r in ev if r['persisted_switch'] and r['mon_t_target_sustained'] is not None and r['t_cross_true'] is not None and r['arm'] in ('ctrl', 'fixed', 'whole')]
T['monitor_target_label_lag_after_true_crossing_tu'] = dict(n=len(lat), median=float(np.median(lat)), q10=float(np.quantile(lat, .1)), q90=float(np.quantile(lat, .9)), min=float(min(lat)), max=float(max(lat)))
# twin: body truth in natural dishes
tw = [r for r in ev if r['arm'] == 'twin']; T['twin_true_geometry'] = dict(n=len(tw), max_mst_median=float(np.median([r['max_mst_true'] for r in tw])), max_mst_max=float(max(r['max_mst_true'] for r in tw)), n_geom_exceed_true=sum(not r['true_geom_ok_all'] for r in tw))
T['all_arms_positions_identical_to_twin'] = dict(max_dX=float(max(r['dX_twin'] for r in ev if r['dX_twin'] is not None)), n_checked=sum(r['dX_twin'] is not None for r in ev))
T['true_success_rates'] = {arm: float(np.mean([r['true_success'] for r in ev if r['arm'] == arm])) for arm in ['ctrl', 'twin', 'sham', 'random', 'fixed', 'whole', 'whole_dm']}
T['mon_success_rates'] = {arm: float(np.mean([r['mon_success'] for r in ev if r['arm'] == arm])) for arm in ['ctrl', 'twin', 'sham', 'random', 'fixed', 'whole', 'whole_dm']}
json.dump(T, open('../data/a1_tables.json', 'w'), indent=1, default=float)
print(json.dumps({k: T[k] for k in ['n_eval_episodes', 'success_all', 'V_body_all', 'Vc_all', 'V_body_vs_intact_core_all', 'abort_vs_intact', 'baseline_not_clean', 'persisted_switch', 'monitor_target_label_lag_after_true_crossing_tu', 'twin_true_geometry', 'all_arms_positions_identical_to_twin', 'true_success_rates', 'mon_success_rates']}, indent=1, default=float))
print(len(dis)); [print(d) for d in dis[:40]]
