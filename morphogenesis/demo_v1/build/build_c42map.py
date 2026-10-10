"""Chapter 4.2 map data from the audit (a4_location.json, a4b_duration.json)."""
import sys; sys.path.insert(0, '.')
from common import *
a4 = json.load(open(f'{AUD5}/data/a4_location.json')); out = dict(template=a4['template'])
BM = a4['T5_blind_map']; out['blind_dose'] = {k: v['dose_gm'] for k, v in BM.items()}; out['blind_rel'] = a4['T5_relative_dose_vs_centre']; out['blind_rel_same_dish'] = {k: v['gm'] for k, v in a4['T5_relative_dose_same_dish'].items()}
out['blind_centres'] = {k: v['mean_centre_template_xy'] for k, v in a4['T5_discs_in_true_frame'].items()}; out['blind_types'] = {k: v['types_lit'][0] for k, v in a4['T5_discs_in_true_frame'].items()}
t = a4['true_switch_v3']; out['true'] = {k: [dict(centre=r['centre'], dose=r['dose'], thr_amp=r['thr_amp'], n_lit=r['n_lit'], conn=r['conn'], xy=r['xy'], type=r['type']) for r in t[k]['rows']] for k in ('4g', '16g')}
out['true_spearman'] = {k: dict(conn_amp=t[k]['spearman_conn_amp'], conn_dose=t[k]['spearman_conn_dose']) for k in t}
out['relative_true'] = a4['relative_dose_true_nearest_place']
import os
p = f'{AUD5}/data/a4b_duration.json'
if os.path.exists(p): out['duration_true'] = json.load(open(p))
write_js('c42map', out)
