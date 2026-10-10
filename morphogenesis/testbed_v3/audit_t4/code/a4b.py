"""A4: is 'mirror image' accurate?  Hidden-channel left-right dipoles by true state, and a direct a-vs-b structure comparison for clone bodies."""
import sys, json, pickle; sys.path.insert(0, '.')
from lib import *
from truth2 import pattern_vec, CH
def tr(run): return pickle.load(open(os.path.join(AUD, 'data', 'truth', run + '.pkl'), 'rb'))
byid = {}
for r in CAT:
    m = META[r['run']]
    if m['family'] == 'natural': byid.setdefault(m['seed'], {})[m['state']] = r['run']
D = {'a': [], 'b': []}
for seed, d in byid.items():
    for st, run in d.items():
        frs, _ = raw(run); t = tr(run)['groups']['all']; fr = frs[0]; idx = np.where(fr['alive'])[0]; g = t[0]; pv = pattern_vec(fr, idx, np.array(g['e1']), np.array(g['e2'])); D[st].append(np.array([pv[c] for c in CH]))
A = np.mean(D['a'], 0); B = np.mean(D['b'], 0); sd = np.std(D['a'], 0)
names = ['mean', 'slope along e1 (head->tail)', 'dipole along e2 (left-right = +y limb side)', 'tail-head contrast']
print('hidden channel | package column | quantity | state a | state b | sd across dishes (a)')
out = {}
for i, ch in enumerate(CH):
    for j in range(4):
        out[f'{ch}|{names[j]}'] = dict(package_column=INV[ch], a=float(A[i, j]), b=float(B[i, j]), sd_a=float(sd[i, j]))
        if j in (0, 2): print(f'{ch:3s} {INV[ch]:3s} {names[j][:12]:12s} a {A[i,j]:+.4f} b {B[i,j]:+.4f} sd {sd[i,j]:.4f}  {"FLIPS" if A[i,j]*B[i,j]<0 and abs(A[i,j]-B[i,j])>3*sd[i,j] else ("exchanged/different" if abs(A[i,j]-B[i,j])>3*sd[i,j] else "same")}')
# direct clone comparison: same body id in both states
diffs = []
for seed, d in byid.items():
    if 'a' in d and 'b' in d:
        fa, _ = raw(d['a']); fb, _ = raw(d['b'])
        diffs.append((max(float(np.abs(x['X'] - y['X']).max()) for x, y in zip(fa, fb)), max(float(np.abs(x['C'] - y['C']).max()) for x, y in zip(fa, fb)), max(float(np.abs(x['MU'] - y['MU']).max()) for x, y in zip(fa, fb))))
diffs = np.array(diffs); print('\nclone bodies (same id in both states):', len(diffs), 'max |X_a - X_b|', diffs[:, 0].max(), 'max |C_a - C_b|', diffs[:, 1].max(), 'max |mu_a - mu_b|', diffs[:, 2].max())
json.dump(dict(channels=out, clone_max_diff=dict(X=float(diffs[:, 0].max()), C=float(diffs[:, 1].max()), MU=float(diffs[:, 2].max()), n=len(diffs))), open(os.path.join(AUD, 'data', 'a4_mirror.json'), 'w'), indent=1)
