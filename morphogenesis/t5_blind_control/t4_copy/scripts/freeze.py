"""Write FROZEN_CONFIG.json (all parameters) + code hash. Run ONCE, before any held-out output exists."""
import sys, os, json, hashlib, glob, datetime; sys.path.insert(0, '.')
import t4.celltrack as ct, t4.outputs as op, t4.layers as ly
files = sorted(glob.glob('t4/*.py') + ['t4/viewer_template.html'] + glob.glob('scripts/*.py') + glob.glob('tests/*.py') +
               glob.glob('calibration/*.json') + glob.glob('calibration/state_models.pkl'))
files = [f for f in files if not os.path.basename(f).startswith('log_')]
h = hashlib.sha256()
for f in files:
    h.update(f.encode()); h.update(open(f, 'rb').read())
digest = h.hexdigest()
cfg = dict(
    created=datetime.datetime.now().isoformat(timespec='seconds'), code_sha256=digest, files_hashed=files,
    geometry=json.load(open('calibration/geometry.json')),
    cell_tracker=dict(sigma_d=0.3, gate=20.0, fingerprint='type channels raw/0.15 + log(c6)/0.08', block_vote_grid=0.4, block_vote_min=3),
    organism_tracker=dict(min_cells_declared='geometry.m_min', margin='geometry.margin', hysteresis_r_hold='geometry.r_hold'),
    o3=dict(window='[-fov,fov]^2, pixel centres', kernel_sd='geometry.s_eff', fg='smoothed(0.5px) c6 > far-field mean + 4*sd', min_pixels='ceil(m_min/px^2)',
            count='mass/mass_per_cell', pseudo_cells='Richardson-Lucy(10 it) + weighted k-means', sign='c6-centroid minus c2-centroid along e1, S0=geometry.o3_sign_S0'),
    envelope={lv: {k: v for k, v in e.items() if k != 'pat_sd'} for lv, e in json.load(open('calibration/envelope.json')).items()},
    envelope_pattern_sd_file='calibration/envelope.json',
    smoothing_window=ly.WINDOW, min_state_n=op.MIN_STATE_N, state_stay_per_100=0.95, change_posterior=0.9, ood_quantile=0.005,
    states=json.load(open('calibration/states_selection.json')),
    state_selection_rule='family: highest half-split ARI at its k* among {pattern,inv,sens} with k*>=2, ARI>=0.8, median validation loglik gain>0; k*: see scripts/discover_states.py',
    anticipation=dict(file='calibration/antic_thresholds.json', FA=0.05, BASE=3, NSHIFT=200),
    info_theory=dict(shrinkage=0.2, ridge=1.0, n_perm_leak=1000, n_perm_g3=200, folds=5, variables='7 channels x 3 body-frame terciles', seed=11),
    exemplar_seed=20260101,
    splits=dict(calibration='natural development dishes with body_id even', validation='natural development dishes with body_id odd',
                heldout='all runs whose manifest split != development'))
json.dump(cfg, open('FROZEN_CONFIG.json', 'w'), indent=1)
open('FROZEN_HASH.txt', 'w').write(digest)
print(digest, len(files))
