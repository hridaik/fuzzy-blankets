"""Part D extras on development natural dishes: state descriptions, online estimator quality, splice latency test."""
import sys, json, pickle; sys.path.insert(0, '.')
import numpy as np
from t4 import io, states, outputs
cal_ = outputs.Calib(); cat = io.catalog()
nat = [r for r in cat if r['condition'] == 'N0' and r['split'] == 'development']
val = [r for r in nat if r['body_id'] % 2 == 1]
rng = np.random.default_rng(5)
report = {}
for lv in ['O1', 'O2', 'O3a', 'O3b']:
    M = cal_.models[lv]; est = cal_.est[lv]
    allnames = None
    recs = {r['run']: pickle.load(open(f"cache/dev/{r['run']}_{lv}.pkl", 'rb')) for r in nat}
    def seqdesc(rec):
        frames = rec['frames']; o = [max(f['orgs'], key=lambda o: o['n']) for f in frames]
        return o, [f['t'] for f in frames]
    # descriptions: modal label per dish (calibration + validation)
    rows = []
    for r in nat:
        o, t = seqdesc(recs[r['run']]); X = np.array([[x['desc'][n] for n in M['names']] for x in o]); res = est.run(X, t)
        rows.append((r['run'], r['body_id'], res, o))
    lab_mode = {}
    for run, b, res, o in rows:
        v = res['label'][res['label'] >= 0]; lab_mode[run] = int(np.bincount(v).argmax()) if len(v) else -1
    desc = {}
    keyf = ['c4_mean', 'c5_mean', 'c1_dq_sens', 'c2_dq_sens', 'c0_dq_sens', 'c3_dq_sens', 'mst_max', 's2', 'q3_sens', 'ppq_sens']
    for s in sorted(set(lab_mode.values())):
        sel = [x for x in rows if lab_mode[x[0]] == s]
        d = {'n_dishes_dev': len(sel)}
        for f_ in keyf:
            vals = [x[3][i]['desc'].get(f_) for x in sel for i in range(len(x[3]))]
            if vals and vals[0] is not None: d[f_] = [float(np.mean(vals)), float(np.std(vals))]
        desc[str(s)] = d
    # consistency of online labels on validation dishes
    cons = []; post = []; nchg = []; ood = []
    for run, b, res, o in rows:
        if b % 2 == 0: continue
        m = lab_mode[run]; cons.append(np.mean(res['label'] == m)); post.append(res['post'].mean()); ood.append(res['ood'].mean())
        nchg.append(len(states.change_times(res['label'], res['post'])))
    # splice latency test: switch from a validation dish with modal label a to one with label b != a at frame 4
    byl = {}
    for run, b, res, o in rows:
        if b % 2 == 1: byl.setdefault(lab_mode[run], []).append((run, o))
    lat = []; det = 0; trials = 0
    labs = [l for l in byl if l >= 0]
    for _ in range(200):
        if len(labs) < 2: break
        a, c = rng.choice(labs, 2, replace=False)
        ra = byl[a][rng.integers(len(byl[a]))]; rc = byl[c][rng.integers(len(byl[c]))]
        X = np.array([[x['desc'][n] for n in M['names']] for x in ra[1][:4] + rc[1][4:]]); res = est.run(X, [100.0 * (i + 1) for i in range(8)])
        ch = [t for t in states.change_times(res['label'], res['post']) if t[0] >= 4]
        trials += 1
        if ch: det += 1; lat.append(ch[0][0] - 4)
    report[lv] = dict(family=M['family'], k=M['k'], state_descriptions=desc, dish_label_counts={str(s): int(sum(1 for v in lab_mode.values() if v == s)) for s in set(lab_mode.values())},
                      val_frac_frames_equal_modal_label=[float(np.mean(cons)), float(np.std(cons))], val_mean_posterior=float(np.mean(post)),
                      val_ood_fraction=float(np.mean(ood)), val_false_changes_per_dish=float(np.mean(nchg)),
                      splice_trials=trials, splice_detect_rate=det / max(trials, 1), splice_latency_frames_median=(float(np.median(lat)) if lat else None),
                      splice_latency_frames_q90=(float(np.quantile(lat, .9)) if lat else None), declared_latency_note='frames after the true switch; one frame = 100 time units at natural sampling')
    print(lv, json.dumps({k: v for k, v in report[lv].items() if k != 'state_descriptions'}))
json.dump(report, open('calibration/states_report.json', 'w'), indent=1)
