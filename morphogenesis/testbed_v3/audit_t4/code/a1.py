"""A1: tracking and body frame vs truth."""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
from scipy.spatial.distance import cdist
def truth(run): return pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb'))
def link_accuracy(run):
    """O2 tracker-id continuity vs the true permanent ids (O1 ids are the true ids; O2 rows are matched to O1 rows by position)."""
    c1 = t4cache(run, 'O1')['frames']; c2 = t4cache(run, 'O2')['frames']; tr = truth(run); prev = None; res = []
    on = tr['onset']; dt = float(CATD[run]['frame_interval'])
    for f1, f2 in zip(c1, c2):
        P1 = np.array(f1['cells']['xy']); I1 = np.array(f1['cells']['ids']); P2 = np.array(f2['cells']['xy']); I2 = np.array(f2['cells']['ids'])
        if len(P1) == 0 or len(P2) == 0: prev = None; continue
        D = cdist(P2, P1); j = D.argmin(1); ok = D.min(1) < 2e-3; tru = np.where(ok, I1[j], -1); cur = dict(zip(tru.tolist(), I2.tolist()))
        if prev is not None:
            common = [i for i in cur if i in prev and i >= 0]; correct = sum(cur[i] == prev[i] for i in common)
            near = on is not None and abs(f1['t'] - on) <= CFG['event_match_window_frame_intervals'] * dt + 1e-9
            res.append((len(common), correct, int(near)))
        prev = cur
    return res
def e1_agreement(run, lv):
    """analyst e1 / centroid / count vs truth, per frame (single true component frames for e1)"""
    cf = t4cache(run, lv)['frames']; tr = truth(run); tt = {round(t, 3): g for t, g in zip(tr['t'], tr['groups']['all'])}; out = []
    for f in cf:
        g = tt.get(round(f['t'], 3))
        if g is None: continue
        orgs = f['orgs']; rec = dict(t=f['t'], n_true_comp=g['ncomp'], n_org=len(orgs))
        if orgs and g['ncomp'] == 1 and 'e1' in g:
            o = max(orgs, key=lambda o: o.get('n', 0)); e1 = np.array(o['e1']); et = np.array(g['e1']); e2t = np.array(g['e2']); rec.update(cos=float(e1 @ et), cos_e2=float(e1 @ e2t), cerr=float(np.linalg.norm(np.array(o['centroid']) - np.array(g['centroid']))), sign_src=o.get('sign_src'), sign_conf=o.get('sign_conf'), n_est=o.get('n'), n_true=g['n'])
        out.append(rec)
    return out
def main():
    LA = {'natural': [], 'ops': [], 'light': []}; near_tot = [0, 0]
    for r in CAT:
        run = r['run']; fam = META[run]['family']; grp = 'natural' if fam == 'natural' else ('ops' if fam == 'stress' else 'light')
        for n, c, near in link_accuracy(run): LA[grp].append((n, c, near))
    A = {}
    for g, v in LA.items():
        v = np.array(v); A[g] = dict(links=int(v[:, 0].sum()), correct=int(v[:, 1].sum()), accuracy=float(v[:, 1].sum() / max(v[:, 0].sum(), 1)))
        if g == 'ops': nr = v[v[:, 2] == 1]; ot = v[v[:, 2] == 0]; A[g].update(near_op=dict(links=int(nr[:, 0].sum()), accuracy=float(nr[:, 1].sum() / max(nr[:, 0].sum(), 1))), far_op=dict(links=int(ot[:, 0].sum()), accuracy=float(ot[:, 1].sum() / max(ot[:, 0].sum(), 1))))
    json.dump(A, open(os.path.join(AUD, 'data', 'a1_links.json'), 'w'), indent=1); print(json.dumps(A, indent=1))
    # body frame / O3
    R = collections.defaultdict(list)
    for r in CAT:
        run = r['run']; fam = META[run]['family']; st = META[run].get('state')
        for lv in ('O1', 'O2', 'O3a', 'O3b'):
            for rec in e1_agreement(run, lv): R[(lv, fam, st)].append(rec)
    S = {}
    for (lv, fam, st), recs in R.items():
        c = np.array([x['cos'] for x in recs if 'cos' in x]); ce = np.array([x['cerr'] for x in recs if 'cerr' in x]); cnt = np.mean([x['n_org'] == x['n_true_comp'] for x in recs]); cx = np.array([x['cos_e2'] for x in recs if 'cos_e2' in x])
        S[f'{lv}|{fam}|{st}'] = dict(frames=len(recs), frames_1comp=int(len(c)), count_agree=float(cnt), e1_sign_correct=float((c > 0).mean()) if len(c) else None, abs_cos_median=float(np.median(np.abs(c))) if len(c) else None, cos_median_signed=float(np.median(c)) if len(c) else None,
                                  centroid_err_median=float(np.median(ce)) if len(ce) else None, e1_dot_e2true_median=float(np.median(cx)) if len(c) else None)
    json.dump(S, open(os.path.join(AUD, 'data', 'a1_frame.json'), 'w'), indent=1)
    for k, v in sorted(S.items()): print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()})
if __name__ == "__main__": main()
