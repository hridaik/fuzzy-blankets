"""Chapter 3.4: T4's blind descriptors (O1, natural dishes, 8 frames each) with T4's blind labels and the true state (hidden tier)."""
import sys; sys.path.insert(0, '.')
from common import *
import csv, gzip, ast
cat = list(csv.DictReader(open(f'{MORPH}/testbed_blind_v2/catalog.csv'))); nat = [r for r in cat if r['condition'] == 'N0']; H = f'{V3}/data/blind_v2_hidden'
x = []; y = []; lab = []; tru = []; body = []; split = []
for r in nat:
    run = r['run']; o = json.load(gzip.open(f'{MORPH}/t4_blind_identity/outputs/{run}.json.gz')); hm = json.load(open(f'{H}/{run}.json')); st = hm['meta']['state']
    for fr in o['levels']['O1']['frames']:
        if not fr['organisms']: continue
        org = fr['organisms'][0]; d = org['desc'] if isinstance(org['desc'], dict) else ast.literal_eval(org['desc']); c3 = org['C3'] if isinstance(org['C3'], dict) else ast.literal_eval(org['C3'])
        x.append(round(d['c0_dq_sens'], 4)); y.append(round(d['c4_mean'] - d['c5_mean'], 4)); lab.append(c3['label']); tru.append(1 if st == 'a' else 0); body.append(int(r['body_id'])); split.append(1 if r['split'] != 'development' else 0)
lab = np.array(lab); tru = np.array(tru)
agree = {}
for L in sorted(set(lab.tolist())): m = lab == L; agree[str(L)] = dict(n=int(m.sum()), frac_true_a=float(tru[m].mean()))
common = np.isin(lab, [0, 2]); acc = float(((lab[common] == 2) == (tru[common] == 1)).mean())
write_js('c34', dict(x=x, y=y, lab=lab.tolist(), truth=tru.tolist(), body=body, split=split, n_dishes=len(nat), agree=agree, common_label_accuracy=acc, source='t4_blind_identity/outputs (O1 descriptors c0_dq_sens, c4_mean - c5_mean; C3 label) + testbed_v3/data/blind_v2_hidden (true state)'))
print(agree, acc)
