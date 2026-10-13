import json, numpy as np
from scipy.stats import spearmanr
from lib4 import *
from theory4 import phi_cells, W_of
r = json.load(open('../data/v3_final.json')); out = {}
print('found threshold in', sum(x['thr'] is not None for x in r), '/', len(r))
print('max transient neighbour loss over all thresholds:', max(x['max_nbr_loss'] for x in r), ' min Jaccard', min(x['min_jac'] for x in r), ' at 2x thr min jac', min(x['min_jac_2x'] for x in r))
Wm = W_of(TM)
for v in VARIANTS:
    rows = []
    for x in r:
        if x['variant'] != v or x['kg'] > 2.5 or x['kg'] < 2.4: continue
        d = dict(seed=-1, kappa_g=x['kg'], g=x['g'], gamma_factor=1.0); perm = settled(d, v, x['state'])[1]; ph = phi_cells(TM, x['g'], alpha_for(VARIANTS[v]))[perm]
        cc = np.array([np.nan if c is None else c for c in x['cell_cross']]); ok = ~np.isnan(cc)
        rho_s = spearmanr(ph[ok], cc[ok])[0] if ok.sum() > 4 and ph.std() > 0 else None
        lit = np.zeros(24, bool)
        rows.append(dict(centre=x['centre'], dm=x['dm'], state=x['state'], rho_phi_cross=rho_s, W_cross=spearmanr(Wm[perm][ok], cc[ok])[0], lag=x['lag'], thr=x['thr'], dose=x['dose'], first_places=[int(perm[i]) for i in np.argsort(np.where(ok, cc, 1e9))[:4]]))
    out[v] = rows
    print(v)
    for c in CENTRES:
        for dm in (4, 16):
            q = [q for q in rows if q['centre'] == c and q['dm'] == dm and q['state'] == 'a'][0]
            print('  ', c, dm, 'dose', round(q['dose']), 'lag', None if q['lag'] is None else round(q['lag'], 2), 'rho(phi,cross)', None if q['rho_phi_cross'] is None else round(q['rho_phi_cross'], 2), 'rho(W,cross)', round(q['W_cross'], 2), 'first places', q['first_places'])
    lags = [q['lag'] for q in rows if q['lag'] is not None]; print('   lag median', np.median(lags), 'range', min(lags), max(lags))
json.dump(out, open('../data/v3_analysis.json', 'w'), default=float)
# dose by dish and variant (middle, whole)
for kg in (1.5, 4.0):
    print('kg', kg, {v: [round(x['dose']) for x in r if x['variant'] == v and x['kg'] == kg and x['state'] == 'a' and x['centre'] == 'middle'] for v in VARIANTS})
# phi effect on dose at median dish middle
for dm in (4, 16):
    print('dm', dm, {v: round(np.mean([x['thr'] for x in r if x['variant'] == v and abs(x['kg'] - 2.4495) < 1e-3 and x['centre'] == 'middle' and x['dm'] == dm])/np.mean([x['thr'] for x in r if x['variant'] == 'phi0' and abs(x['kg'] - 2.4495) < 1e-3 and x['centre'] == 'middle' and x['dm'] == dm]), 3) for v in VARIANTS})
