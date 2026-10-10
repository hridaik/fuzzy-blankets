"""A6: twins that the analyst marked out-of-distribution late in long runs: which hidden variables drift; real drift or calibration mismatch?"""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
from scipy.stats import ks_2samp
def tr(run): return pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb'))
def last_label(run, lv='O1'):
    o = t4out(run)['levels'][lv]; f = o['frames'][-1]
    return f['organisms'][0]['C3']['label'] if f['organisms'] else None
def varset(g, g0):
    place = np.array(g.get('place', [])); p0 = np.array(g0.get('place', []))
    e1 = np.array(g['e1']); e10 = np.array(g0['e1'])
    return dict(dL=g.get('dL', np.nan), mst=g['mst_max'], rep_dip=abs(g['rep_contrast']), place_changed=float(np.mean(place != p0)) if len(place) == len(p0) and len(place) else np.nan, rot=float(np.degrees(np.arctan2(e1[0]*e10[1]-e1[1]*e10[0], e1 @ e10))),
                dA=g['dA'] if g0['dA'] > 0.5 else g['dB'], mean_rho_dev=abs(g['mean_rho'] - g0['mean_rho']))
def main():
    twins = [r['run'] for r in CAT if r['arm'] in ('untreated_control', 'sham_treated') and META[r['run']]['family'] == 'stress' and not META[r['run']]['scn'].startswith('fuse')]
    rows = []
    for run in twins:
        t = tr(run); G = t['groups']['all']; V = [varset(g, G[0]) for g in G]; ll = last_label(run, 'O1'); on = ll == -1
        late = [v for v, tt in zip(V, t['t']) if tt >= t['t'][-1] - 100]
        rows.append(dict(run=run, ood_last=bool(on), **{k: float(np.nanmean([v[k] for v in late])) for k in V[0]}, dL_max=float(np.nanmax([v['dL'] for v in V])), age_end=float(t['t'][-1] + 100)))
    ood = [r for r in rows if r['ood_last']]; ok = [r for r in rows if not r['ood_last']]; print('twin/sham runs', len(rows), 'OOD at last frame (O1)', len(ood))
    keys = ['dL', 'dL_max', 'mst', 'rep_dip', 'place_changed', 'rot', 'dA', 'mean_rho_dev']
    for k in keys: print(f'{k:14s} OOD mean {np.nanmean([r[k] for r in ood]):8.4f}  non-OOD mean {np.nanmean([r[k] for r in ok]):8.4f}')
    # natural vs twin at comparable age (>= 250): distributions of the same variables
    nat = [r['run'] for r in CAT if META[r['run']]['family'] == 'natural']; NV = collections.defaultdict(list); TV = collections.defaultdict(list)
    for run in nat:
        t = tr(run); G = t['groups']['all']
        for g in G[1:]:
            v = varset(g, G[0]); [NV[k].append(v[k]) for k in v]
    for run in twins:
        t = tr(run); G = t['groups']['all']
        for g, tt in zip(G, t['t']):
            if tt >= 150: v = varset(g, G[0]); [TV[k].append(v[k]) for k in v]
    print('\nvariable (relative to first observed frame): natural(age 350-950) vs twins/shams (age>=250)')
    cmp = {}
    for k in ('dL', 'mst', 'rep_dip', 'place_changed', 'rot', 'dA', 'mean_rho_dev'):
        a = np.array(NV[k]); b = np.array(TV[k]); a = a[~np.isnan(a)]; b = b[~np.isnan(b)]; cmp[k] = dict(nat_mean=float(a.mean()), twin_mean=float(b.mean()), ks_p=float(ks_2samp(a, b).pvalue)); print(f'{k:14s} natural {a.mean():8.4f} (sd {a.std():.4f})  twin {b.mean():8.4f} (sd {b.std():.4f})  KS p={cmp[k]["ks_p"]:.3g}')
    # time course in twins: shape deviation vs age
    T = collections.defaultdict(list)
    for run in twins:
        t = tr(run); G = t['groups']['all']
        for g, tt in zip(G, t['t']):
            if 'dL' in g and not np.isnan(g.get('dL', np.nan)): T[int(tt // 100)].append(g['dL'])
    print('\ntypical true typed distance dL to the template vs time since observation start (bins of 100 tu; twins/shams):', {b: round(float(np.mean(v)), 3) for b, v in sorted(T.items())})
    json.dump(dict(rows=rows, cmp=cmp), open(os.path.join(AUD, 'data', 'a6_twin.json'), 'w'), indent=1)
if __name__ == "__main__": main()
