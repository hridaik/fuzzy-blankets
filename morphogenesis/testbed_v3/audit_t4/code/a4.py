"""A4: states. Confusion of the analyst's labels vs true state (sign of mean rho x structural completeness); the rare organisation; the 'mirror image' test."""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
def truth(run): return pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb'))
def true_label(g):
    st = 'a' if g['mean_rho'] > 0.5 else 'b'
    if 0.1 < g['frac_a'] < 0.9: st = 'mixed'
    comp = bool(g.get('orbit_ok', False) and g['ncomp'] == 1 and g['n'] == 24 and g.get('shape', 'L') == 'L')
    return f"{st}/{'complete' if comp else 'incomplete'}"
def main():
    nat = [r['run'] for r in CAT if META[r['run']]['family'] == 'natural']; conf = {lv: collections.defaultdict(collections.Counter) for lv in ('O1', 'O2', 'O3a', 'O3b')}; dish = {lv: {} for lv in conf}
    for run in nat:
        tr = truth(run); G = {round(t, 3): g for t, g in zip(tr['t'], tr['groups']['all'])}; o = t4out(run)
        for lv in conf:
            labs = []
            for f in o['levels'][lv]['frames']:
                g = G.get(round(f['t'], 3))
                if g is None or not f['organisms']: continue
                x = max(f['organisms'], key=lambda x: x['n'] if x['n'] else x['n_pixels']); lab = x['C3']['label']; conf[lv][lab][true_label(g)] += 1; labs.append(lab)
            dish[lv][run] = collections.Counter(labs).most_common(1)[0][0] if labs else None
    out = {lv: {str(k): dict(v) for k, v in conf[lv].items()} for lv in conf}; json.dump(out, open(os.path.join(AUD, 'data', 'a4_confusion.json'), 'w'), indent=1)
    for lv in conf:
        print('\n==', lv, '(rows: analyst label; columns: true state/completeness; natural dishes, frames)')
        cols = sorted({c for v in conf[lv].values() for c in v}); print('label', cols)
        for lab in sorted(conf[lv]): print(lab, [conf[lv][lab].get(c, 0) for c in cols])
    # rare organisation at O1 : identify the label with the fewest dishes
    lv = 'O1'; cnt = collections.Counter(dish[lv].values()); print('\nO1 modal label counts', cnt)
    rare = 1; runs_rare = [r for r, l in dish[lv].items() if l == rare]; runs_com = [r for r, l in dish[lv].items() if l != rare and l is not None]
    def stats(runs):
        rows = []
        for run in runs:
            tr = truth(run); g = tr['groups']['all']; X = np.array(tr['per_cell'][-1]['X']); D = np.linalg.norm(X[:, None] - X[None], axis=-1) + 9 * np.eye(len(X))
            rows.append(dict(mean_rho=np.mean([x['mean_rho'] for x in g]), orbit_ok=np.mean([x['orbit_ok'] for x in g]), ncomp=np.mean([x['ncomp'] for x in g]), mst=np.mean([x['mst_max'] for x in g]), dL=np.nanmean([x.get('dL', np.nan) for x in g]), nn_med=float(np.median(D.min(1))), n=g[0]['n'], state=META[run]['state'], frac_cells_place_changed=float(np.mean([np.mean(np.array(x['place']) != np.array(g[0]['place'])) for x in g[1:]])), body=META[run]['seed']))
        return rows
    rr = stats(runs_rare); rc = stats(runs_com)
    keys = ['mean_rho', 'orbit_ok', 'ncomp', 'mst', 'dL', 'nn_med', 'frac_cells_place_changed']
    print('\nrare label', rare, 'dishes', len(runs_rare), 'true states', collections.Counter(r['state'] for r in rr), 'body ids', [r['body'] for r in rr])
    for k in keys: print(k, 'rare', round(float(np.mean([r[k] for r in rr])), 4), 'common', round(float(np.mean([r[k] for r in rc])), 4))
    json.dump(dict(rare_label=rare, rare=rr, common_mean={k: float(np.mean([r[k] for r in rc])) for k in keys}), open(os.path.join(AUD, 'data', 'a4_rare.json'), 'w'), indent=1, default=float)
if __name__ == "__main__": main()
