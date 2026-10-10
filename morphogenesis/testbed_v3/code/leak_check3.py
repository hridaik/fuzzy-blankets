"""Leak checker for testbed_blind_v2: forbidden vocabulary in names/text/keys, allowed array keys, opaque-label and structural checks. Writes LEAK_CHECK.md into the package."""
import os, re, json, glob, csv, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.join(os.path.dirname(os.path.dirname(HERE)), 'testbed_blind_v2')
FORBID = [r'memory', r'handed', r'chiral', r'situs', r'lateral', r'reporter', r'slot', r'belief', r'\bplans?\b', r'\bfate', r'template', r'mirror', r'state[ _-]?[ab]\b', r'\bstates?\b',
          r'mechanism', r'enantio', r'latent', r'hidden', r'posterior', r'softmax', r'logit', r'zeta', r'orbit', r'\brole', r'\bmu\b', r'receptor', r'\bgain\b', r'migration', r'\bbias', r'precision', r'free.?energy',
          r'attractor', r'ground.?truth', r'jacobian', r'ratiometric', r'paracrine', r'quorum', r'toggle', r'\bL-form', r'\bR-form']
ALLOWED = {'O1': {'t', 'frame_ptr', 'cell_id', 'xy', 'level'}, 'O2': {'t', 'frame_ptr', 'xy', 'level'}, 'O3a': {'t', 'image'}, 'O3b': {'t', 'image'}}
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
            checked['npz'] += 1; lvl = f.split('_')[-1][:-4]; d = np.load(p)
            for k in d.files:
                scan_text('NPZKEY ' + rel, k)
                if k not in ALLOWED[lvl]: findings.append((rel, 'unexpected array key', k))
            if lvl in ('O2',) and 'cell_id' in d.files: findings.append((rel, 'O2 carries ids', ''))
rows = list(csv.DictReader(open(os.path.join(PKG, 'catalog.csv'))))
bad = [r for r in rows if not (re.fullmatch(r'N0|P\d\d|T\d[ab]|X[a-z_]+|C\d+', r['condition']) and r['arm'] in ('untreated', 'treated', 'untreated_control', 'sham_treated'))]
if bad: findings.append(('catalog.csv', 'non-opaque label', str(bad[:2])))
# O2 shuffled relative to O1; pose randomised
r0 = rows[0]['run']; o1 = np.load(os.path.join(PKG, 'runs', r0 + '_O1.npz')); o2 = np.load(os.path.join(PKG, 'runs', r0 + '_O2.npz')); n0 = o1['frame_ptr'][1] - o1['frame_ptr'][0]
if np.allclose(o1['xy'][:n0], o2['xy'][:n0], atol=0.2): findings.append((r0, 'O2 rows not shuffled relative to O1', ''))
cent = np.array([np.load(os.path.join(PKG, 'runs', r['run'] + '_O1.npz'))['xy'][:np.load(os.path.join(PKG, 'runs', r['run'] + '_O1.npz'))['frame_ptr'][1]].mean(0) for r in rows[:80]])
if cent.std(0).min() <= 0.5: findings.append(('runs', 'cluster pose not randomised', str(cent.std(0))))
lines = ['# LEAK_CHECK.md — automated scan of testbed_blind_v2', '', f'Scanned {checked["files"]} files ({checked["text_files"]} text, {checked["npz"]} npz) with `code/leak_check3.py`.', '', '**Forbidden vocabulary (regex, case-insensitive):** ' + ', '.join('`%s`' % p for p in FORBID), '',
         '**Allowed array keys:** ' + json.dumps({k: sorted(v) for k, v in ALLOWED.items()}), '', '**Structural checks:** opaque condition/arm labels only; O2 rows shuffled relative to O1 and carrying no ids; cluster pose randomised across runs (centroid sd per axis %.2f units).' % cent.std(0).min(), '',
         f'**Result: {"PASS — 0 findings" if not findings else "FAIL — %d findings" % len(findings)}**', '']
for f in findings[:60]: lines.append('- ' + ' | '.join(str(x) for x in f))
lines += ['', 'Not checkable automatically: whether the numerical data themselves allow the observer to infer withheld facts (the later blind analyses test that).']
open(os.path.join(PKG, 'LEAK_CHECK.md'), 'w').write('\n'.join(lines)); print('\n'.join(lines[:14]))
