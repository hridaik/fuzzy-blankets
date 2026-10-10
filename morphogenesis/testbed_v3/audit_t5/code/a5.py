"""A5: true mechanism of L1-L5 and one-directionality of L3/L4 (hidden effects of the B1 stage-1 screening episodes vs offline CRN twin)."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truth import *
from lib import *
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
LAB = {v: k for k, v in B3.LIGHT_LABELS.items()}
MECH = {'MA': 'memory-ligand A secretion (u_A on lit cells; enters only neighbours\' paracrine sensing)', 'MB': 'memory-ligand B secretion (u_B on lit cells)', 'SEC': 'structural-signal secretion (adds to the cell\'s emitted type code c)', 'RG': 'receptor gain (scales the sensed field lambda)', 'MIG': 'migration gain (scales the movement rate k_a)'}
R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'b1_results.jsonl'))]
S1 = [r for r in R if r['stage'] in (1, '1')]
twins = {}
for seed in sorted({r['seed'] for r in S1}):
    ex = make_dish(seed); ex.run_sched(20.0, [], sham=False, obs_times=[]); rec = [dict(t=rel_t(ex), X=ex.w.X.copy(), C=ex.w.C.copy(), MU=ex.w.MU.copy(), L=ex.w.L.copy())]
    for _ in range(130):
        ex.run_sched(1.0, [], sham=False, obs_times=[]); rec.append(dict(t=rel_t(ex), X=ex.w.X.copy(), C=ex.w.C.copy(), MU=ex.w.MU.copy(), L=ex.w.L.copy()))
    twins[seed] = rec
rows = []
for r in S1:
    h, e = load_hidden(r['episode']); tw = twins[r['seed']]; t = h['t']
    # twin rows aligned by time (twin starts at t=20): hidden t index k -> time k
    idx = [k for k in range(len(t)) if t[k] >= 20 and (k - 20) < len(tw)]
    dX = np.array([np.abs(h['X'][k] - tw[k - 20]['X']).max() for k in idx]); dC = np.array([np.abs(h['C'][k] - tw[k - 20]['C']).max() for k in idx])
    dMU = np.array([np.abs(h['MU'][k] - tw[k - 20]['MU']).max() for k in idx]); sm = lambda L: (1 / (1 + np.exp(-L))).mean(1)
    rho = sm(h['L']); rho_tw = np.array([1 / (1 + np.exp(-tw[k - 20]['L'])).mean() if False else (1 / (1 + np.exp(-tw[k - 20]['L']))).mean() for k in idx])
    rho_h = np.array([rho[k] for k in idx])
    g = geom_series(h['X'], h['alive']); a_tw = np.array([np.argmax(tw[k - 20]['MU'], 1) for k in idx]); a_h = np.array([np.argmax(h['MU'][k], 1) for k in idx])
    rows.append(dict(episode=r['episode'], seed=r['seed'], label=r['label'], channel=LAB[r['label']], amp=r['amp'], start_true=('a' if rho_h[0] > .5 else 'b'), max_dX=float(dX.max()), max_dC=float(dC.max()), max_dMU=float(dMU.max()),
        d_rho_end=float(rho_h[-1] - rho_tw[-1]), max_abs_d_rho=float(np.abs(rho_h - rho_tw).max()), rho_end=float(rho_h[-1]), n_place_changes=int((a_tw[-1] != a_h[-1]).sum()), max_ncomp=int(g['ncomp'].max()), max_mst=float(g['mst'].max()),
        mon_flipped=r['flipped'], mon_damage=r.get('events'), mon_pat_dz=r['pat_dz_max'], dose=r['dose']))
json.dump(dict(mechanism=MECH, label_to_channel=LAB, rows=rows), open('../data/a5_actuators.json', 'w'), indent=1, default=float)
import collections
print({k: v for k, v in LAB.items()})
for x in sorted(rows, key=lambda x: (x['label'], x['seed'], x['amp'])): print(x['label'], x['channel'], x['seed'], x['start_true'], x['amp'], 'dX %.3f dC %.3f dMU %.2f drho_end %+.3f ncomp %d nplace %d mon_flip %s' % (x['max_dX'], x['max_dC'], x['max_dMU'], x['d_rho_end'], x['max_ncomp'], x['n_place_changes'], x['mon_flipped']))
