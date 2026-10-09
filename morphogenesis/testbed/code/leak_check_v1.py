"""Leak checker for testbed_blind_v1: forbidden vocabulary in names/text/keys, allowed array keys, structural checks. Writes LEAK_CHECK.md into the package."""
import os, re, json, glob, csv, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'testbed_blind_v1')
FORBID = [r'slot', r'belief', r'\bplans?\b', r'template', r'mechanism', r'chiral', r'situs', r'fate', r'mirror', r'enantio', r'handed', r'latent', r'hidden', r'posterior', r'softmax', r'logit', r'zeta', r'orbit',
          r'\brole', r'\bmu\b', r'receptor', r'\bgain\b', r'migration', r'tweezer', r'pipette', r'surgery', r'\bbias', r'precision', r'free.?energy', r'attractor', r'\bL-form', r'\bR-form', r'ground.?truth', r'perm(uted)? channel', r'jacobian']
ALLOWED = {'O1': {'t', 'frame_ptr', 'cell_id', 'xy', 'level'}, 'O2': {'t', 'frame_ptr', 'xy', 'level'}, 'O3': {'t', 'image'}}
findings = []; checked = dict(files=0, text_files=0, npz=0)
def scan_text(name, text):
    for pat in FORBID:
        for m in re.finditer(pat, text, flags=re.I): findings.append((name, pat, text[max(0, m.start() - 20):m.end() + 20].replace('\n', ' ')))
for root, _, fs in os.walk(PKG):
    for f in fs:
        p = os.path.join(root, f); rel = os.path.relpath(p, PKG); checked['files'] += 1; scan_text('FILENAME ' + rel, rel)
        if f == 'LEAK_CHECK.md': continue
        if f.endswith(('.md', '.json', '.csv', '.txt')): checked['text_files'] += 1; scan_text(rel, open(p).read())
        if f.endswith('.npz'):
            checked['npz'] += 1; lvl = f.split('_')[-1][:2]; d = np.load(p)
            for k in d.files:
                scan_text('NPZKEY ' + rel, k)
                if k not in ALLOWED[lvl]: findings.append((rel, 'unexpected array key', k))
            if lvl == 'O2' and 'cell_id' in d.files: findings.append((rel, 'O2 carries ids', ''))
# opaque-label sanity
rows = list(csv.DictReader(open(os.path.join(PKG, 'catalog.csv')))); bad = [r for r in rows if r['strain_code'] not in ('S1', 'S2') or not re.fullmatch(r'N0|P[1-6]', r['condition'])]
if bad: findings.append(('catalog.csv', 'non-opaque label', str(bad[:2])))
# O2 frame shuffling check: two frames of a natural run must not have the same row order of levels as O1 (i.e. O2 rows are permuted)
o1 = np.load(os.path.join(PKG, 'runs', rows[0]['run'] + '_O1.npz')); o2 = np.load(os.path.join(PKG, 'runs', rows[0]['run'] + '_O2.npz'))
n0 = o1['frame_ptr'][1] - o1['frame_ptr'][0]; same_order = np.allclose(np.sort(o1['xy'][:n0, 0]), np.sort(o2['xy'][:n0, 0]), atol=0.2) and np.allclose(o1['xy'][:n0], o2['xy'][:n0], atol=0.2)
if same_order: findings.append((rows[0]['run'], 'O2 rows not shuffled relative to O1', ''))
# body-frame check: no run has its cluster centroid at the origin with zero rotation (pose randomised): centroid spread across runs
cent = []
for r in rows[:60]:
    d = np.load(os.path.join(PKG, 'runs', r['run'] + '_O1.npz')); cent.append(d['xy'][:d['frame_ptr'][1]].mean(0))
cent = np.array(cent); pose_ok = cent.std(0).min() > 0.5
if not pose_ok: findings.append(('runs', 'cluster pose not randomised', str(cent.std(0))))
lines = ['# LEAK_CHECK.md — automated scan of testbed_blind_v1', '', f'Scanned {checked["files"]} files ({checked["text_files"]} text, {checked["npz"]} npz) with `code/leak_check_v1.py`.', '',
         '**Forbidden vocabulary (regex, case-insensitive):** ' + ', '.join('`%s`' % p for p in FORBID), '', '**Allowed array keys:** ' + json.dumps({k: sorted(v) for k, v in ALLOWED.items()}), '',
         '**Structural checks:** opaque labels only (`S1/S2`, `N0`, `P1–P6`); O2 files carry no ids and rows are shuffled relative to O1; cluster pose randomised across runs (centroid sd per axis %.2f units).' % cent.std(0).min(), '',
         f'**Result: {"PASS — 0 findings" if not findings else "FAIL — %d findings" % len(findings)}**', '']
for f in findings[:50]: lines.append('- ' + ' | '.join(str(x) for x in f))
lines += ['', 'Not checkable automatically: whether the numerical data themselves allow the observer to infer withheld facts (that is what the later blind analyses test); the package-wide level order and the identity of the two reporter channels are withheld.']
open(os.path.join(PKG, 'LEAK_CHECK.md'), 'w').write('\n'.join(lines)); print('\n'.join(lines[:12]))
