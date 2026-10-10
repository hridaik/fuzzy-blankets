"""A7: true lead of memory variables over the reporter vs the package frame intervals."""
import sys, json, pickle; sys.path.insert(0, '.')
from lib import *
res = json.load(open(os.path.join(AUD, 'data', 'a5_changes.json'))); rows = []
for x in res:
    if x['fam'] != 'switch' or not x['switched']: continue
    tr = pickle.load(open(os.path.join(AUD, 'data', 'truth', x['run'] + '.pkl'), 'rb')); G = tr['groups']['all']; t = np.array(tr['t']); mr = np.array([g['mean_rho'] for g in G]); dA = np.array([g['dA'] for g in G]); dB = np.array([g['dB'] for g in G]); rc = np.array([g['rep_contrast'] for g in G]); a0 = mr[0] > 0.5
    first = lambda m: float(t[np.argmax(m)]) if m.any() else None
    t_rho = first(mr < 0.5 if a0 else mr > 0.5); t_lig = first((dA < dB) if a0 else (dA > dB)); t_rep = first((rc < 0) if a0 else (rc > 0))
    rows.append(dict(run=x['run'], t_rho=t_rho, t_lig=t_lig, t_rep=t_rep))
d1 = np.array([r['t_lig'] - r['t_rho'] for r in rows]); d2 = np.array([r['t_rep'] - r['t_rho'] for r in rows]); d3 = np.array([r['t_rep'] - r['t_lig'] for r in rows])
q = lambda a: [float(np.quantile(a, p)) for p in (.1, .5, .9)]
print('n switched runs', len(rows), '\nligand crossing minus rho crossing [q10,q50,q90]', q(d1), '\nreporter flip minus rho crossing', q(d2), '\nreporter flip minus ligand crossing (= lead of the memory ligands over the reporter)', q(d3))
print('fraction of runs with reporter flip strictly later than ligand crossing:', float((d3 > 0).mean()), 'frame interval in these runs: 2 tu')
json.dump(dict(rows=rows, lig_minus_rho=q(d1), rep_minus_rho=q(d2), rep_minus_lig=q(d3), frac_rep_later=float((d3 > 0).mean())), open(os.path.join(AUD, 'data', 'a7_lead.json'), 'w'), indent=1)
