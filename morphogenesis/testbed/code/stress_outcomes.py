import pickle, glob, os, json, sys, numpy as np; sys.path.insert(0, '.')
from asm import make_body
import chiral as CH
from exports import component_labels
t = make_body('chiral'); res = {}
for pk in sorted(glob.glob('../data/stress_raw/*.pkl')):
    b = os.path.basename(pk)[:-4].split('_'); scn = '_'.join(b[:-2]); kind = b[-2]
    d = pickle.load(open(pk, 'rb'))
    for arm in ('event', 'twin'):
        f = d[arm]['frames'][-1]; al = f['alive']; X = f['X'][al]; C = f['C'][al]; MU = f['MU'][al]
        comp = int(component_labels(X, 1.6).max() + 1); slots = MU.argmax(1); cnt = np.bincount(slots, minlength=24)
        if len(X) == 24:
            lab, dL, dR = CH.classify(t, X, C); lab = lab if (cnt == 1).all() and comp == 1 else 'DEFECT'
        else: lab = 'two-body' if comp >= 2 else 'merged'
        res.setdefault((scn, kind, arm), []).append(lab.upper() if lab in ('L', 'R') else lab)
out = {}
for (scn, kind, arm), v in sorted(res.items()):
    from collections import Counter; out[f'{scn}|{kind}|{arm}'] = dict(Counter(v)); print(scn, kind, arm, dict(Counter(v)))
json.dump(out, open('../data/stress_outcomes.json', 'w'), indent=1)
