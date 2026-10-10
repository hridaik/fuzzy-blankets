"""A5: change detection vs true switch times (mean rho crossing 1/2; reporter flip)."""
import sys, json, pickle, collections; sys.path.insert(0, '.')
from lib import *
LAB = {}   # level -> {'a': label, 'b': label} from natural dishes (modal)
def build_labels():
    conf = json.load(open(os.path.join(AUD, 'data', 'a4_confusion.json')))
    for lv, d in conf.items():
        m = {}
        for st in ('a', 'b'):
            best = max(((lab, v.get(f'{st}/complete', 0)) for lab, v in d.items() if lab not in ('-1', '-2')), key=lambda x: x[1]); m[st] = int(best[0])
        LAB[lv] = m
def truth_switch(run):
    tr = pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb')); G = tr['groups']['all']; t = np.array(tr['t']); mr = np.array([g['mean_rho'] for g in G]); rc = np.array([g['rep_contrast'] for g in G]); st0 = 'a' if mr[0] > 0.5 else 'b'
    other = (mr < 0.5) if st0 == 'a' else (mr > 0.5); n = len(t); tail = other[int(0.8 * n):]; switched = bool(tail.all() and other.any())
    tc = float(t[np.argmax(other)]) if switched else None; rother = (rc < 0) if st0 == 'a' else (rc > 0); tr_ = float(t[np.argmax(rother)]) if rother.any() and rother[int(0.8 * n):].all() else None
    return dict(start=st0, switched=switched, t_cross=tc, t_rep=tr_, mr0=float(mr[0]), mr_end=float(mr[-1]), t=t)
def analyst_changes(run, lv):
    o = t4out(run)['levels'][lv]; org = [x for x in o['organisms'].values() if x['origin'] == 'founder']
    if not org: return None
    labs = []; ts = []
    for f in o['frames']:
        c = [x for x in f['organisms'] if str(x['id']) == str(list(o['organisms'].keys())[list(o['organisms'].values()).index(org[0])])]
        if c: labs.append(c[0]['C3']['label']); ts.append(f['t'])
    labs = np.array(labs); ts = np.array(ts)
    frozen = [c['t'] for x in org for c in x['state_changes']]                                       # frozen list (repeats OOD changes every frame)
    keep = labs != -2; L2 = labs[keep]; T2 = ts[keep]; trans = [(float(T2[i]), int(L2[i - 1]), int(L2[i])) for i in range(1, len(L2)) if L2[i] != L2[i - 1]]
    return dict(frozen_first=(min(frozen) if frozen else None), n_frozen=len(frozen), transitions=trans, t=ts.tolist(), labels=labs.tolist())
def main():
    build_labels(); print('label maps', LAB); res = []
    for r in CAT:
        run = r['run']; m = META[run]
        if m['family'] not in ('switch', 'decoy') and not (m['family'] == 'stress' and not m['scn'].startswith('fuse')) and m['family'] != 'natural': continue
        ts = truth_switch(run); row = dict(run=run, fam=m['family'], kind=m.get('kind'), level=m.get('level'), arm=r['arm'], cond=r['condition'], start=ts['start'], switched=ts['switched'], t_cross=ts['t_cross'], t_rep=ts['t_rep'], onset=onset_abs(run), dt=float(r['frame_interval']))
        for lv in ('O1', 'O2', 'O3a', 'O3b'):
            ac = analyst_changes(run, lv)
            if ac is None: row[lv] = None; continue
            tgt = LAB[lv]['b' if ts['start'] == 'a' else 'a']; src = LAB[lv][ts['start']]
            to_tgt = [tt for tt, a, b in ac['transitions'] if b == tgt]; to_any = [tt for tt, a, b in ac['transitions']]; to_real = [tt for tt, a, b in ac['transitions'] if b >= 0]
            row[lv] = dict(frozen_first=ac['frozen_first'], n_trans=len(ac['transitions']), first_trans=(to_any[0] if to_any else None), first_to_target=(to_tgt[0] if to_tgt else None), first_to_real=(to_real[0] if to_real else None))
        res.append(row)
    json.dump(res, open(os.path.join(AUD, 'data', 'a5_changes.json'), 'w'))
    sw = [x for x in res if x['fam'] == 'switch']
    print('\ntrue switches among switch runs by kind/level:'); c = collections.Counter((x['kind'], x['level'], x['switched']) for x in sw)
    for k, v in sorted(c.items(), key=str): print(k, v)
    for lv in ('O1', 'O2', 'O3a', 'O3b'):
        S = [x for x in sw if x['switched'] and x[lv]]; lat_t = [x[lv]['first_to_target'] - x['t_cross'] for x in S if x[lv]['first_to_target'] is not None]; lat_rep = [x[lv]['first_to_target'] - x['t_rep'] for x in S if x[lv]['first_to_target'] is not None and x['t_rep'] is not None]
        miss = sum(1 for x in S if x[lv]['first_to_target'] is None); anyc = sum(1 for x in S if x[lv]['first_trans'] is not None)
        N = [x for x in sw if not x['switched'] and x[lv]]; fc_corr = sum(1 for x in N if x[lv]['n_trans'] > 0); fc_frozen = sum(1 for x in N if x[lv]['frozen_first'] is not None)
        nat = [x for x in res if x['fam'] == 'natural' and x[lv]]; nfc = sum(1 for x in nat if x[lv]['n_trans'] > 0); nfz = sum(1 for x in nat if x[lv]['frozen_first'] is not None)
        q = lambda v, p: float(np.quantile(v, p)) if v else None
        print(f'{lv}: true switches {len(S)}; detected to the correct target label {len(S)-miss}; missed {miss}; (any transition {anyc}); latency vs mean-rho crossing: median {q(lat_t,.5)} q10 {q(lat_t,.1)} q90 {q(lat_t,.9)}; vs reporter flip median {q(lat_rep,.5)} | non-switching switch-family runs {len(N)}: corrected false-change runs {fc_corr}, frozen-list runs {fc_frozen} | natural dishes {len(nat)}: corrected {nfc}, frozen {nfz}')
if __name__ == "__main__": main()
