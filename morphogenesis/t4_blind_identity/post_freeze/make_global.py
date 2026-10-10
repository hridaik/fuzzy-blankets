"""Reporting only: assemble outputs/GLOBAL_SUMMARY.json from the analysis result files (no recomputation)."""
import json
L = lambda p: json.load(open(p))
sel = L('calibration/states_selection.json'); rep = L('calibration/states_report.json')
fams = {f: L(f'calibration/states_{f}.json') for f in ('pattern', 'inv', 'sens', 'noC45', 'means')}
states = {}
for lv in ('O1', 'O2', 'O3a', 'O3b'):
    states[lv] = dict(chosen_family=sel[lv]['chosen'], k_star=sel[lv]['k'], half_split_ARI=sel[lv]['stability'],
                      family_table=sel[lv]['table'], dish_label_counts_dev=rep[lv]['dish_label_counts'],
                      evidence_1_vs_k={f: dict(k_star=fams[f][lv]['k_star'], cv_loglik=fams[f][lv]['cv_ll'], cv_gain_vs_1_ci=fams[f][lv]['cv_gain_vs_1'],
                                               stability_ari=fams[f][lv]['stability_ari'], bic=fams[f][lv]['bic_cal'], val_loglik=fams[f][lv]['val_ll']) for f in fams},
                      online_estimator_dev_validation=dict(frac_frames_equal_modal=rep[lv]['val_frac_frames_equal_modal_label'], mean_posterior=rep[lv]['val_mean_posterior'],
                                                           ood_fraction=rep[lv]['val_ood_fraction'], false_changes_per_dish=rep[lv]['val_false_changes_per_dish'],
                                                           splice_detect_rate=rep[lv]['splice_detect_rate'], splice_latency_frames_median=rep[lv]['splice_latency_frames_median']))
def leak(p):
    d = L(p); t = []
    for n, r in d['partitions'].items():
        a = r['one_frame_per_dish']; b = r['all_frames']
        t.append(dict(partition=n, sizes=r['sizes'], L_one_frame=a['L'], null_median=a['null_median'], null_q05=a['null_q05'], percentile_in_null=a['percentile_in_null'],
                      L_all_frames=b['L'], null_median_all=b['null_median'], percentile_all=b['percentile_in_null'], n=a['n']))
    return dict(sampling=d['sampling'], louvain=d['louvain'], table=sorted(t, key=lambda x: x['percentile_in_null']))
def directed(p):
    d = L(p); t = []
    for n, r in d['partitions'].items():
        for k, v in r['directed'].items():
            t.append(dict(partition=n, direction=k, rel_gain=v['rel_gain'], ci=v['ci'], ci_excludes_zero_positive=bool(v['ci'][0] > 0), flagged_exceeds_permutation_null=v['exceeds_null']))
    return t
def antic(p):
    d = L(p); out = {}
    for lv, v in d.items():
        out[lv] = dict(n_change_runs=v['n_change_runs'], features={k: dict(skill=x['skill'], hit_rate=x['hit_rate'], null_hit_rate=x['null_hit_rate'], median_lead_time=x['median_lead_time']) for k, x in v['features'].items()})
    return out
g = dict(states=states, leakage=dict(development=leak('calibration/info_dev.json'), heldout=leak('results_heldout/info_heldout.json')),
         directed_influence=dict(development=directed('calibration/info_dev.json'), heldout=directed('results_heldout/info_heldout.json'),
                                 note='flagged_exceeds_permutation_null is uninformative (null centred below zero); use ci_excludes_zero_positive. See INFOTHEORY.md "known issue".'),
         anticipation=dict(development=antic('calibration/anticipation_dev.json'), heldout=antic('results_heldout/anticipation_heldout.json')),
         natural_validity=L('results_heldout/natural_validity.json'), tracking_consistency=dict(development=L('calibration/consistency_dev.json')['aggregate'], heldout=L('results_heldout/consistency_heldout.json')['aggregate']),
         frozen_code_sha256=open('FROZEN_HASH.txt').read().strip())
json.dump(g, open('outputs/GLOBAL_SUMMARY.json', 'w'), indent=1)
pos = [x for x in g['directed_influence']['development'] + g['directed_influence']['heldout'] if x['ci_excludes_zero_positive']]
print('directed with positive gain CI excluding 0:', len(pos), pos[:3])
