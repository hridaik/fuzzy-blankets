"""Hidden-tier fix: for dish-merge runs (48 cells) the ORGANISM INTACT flag is defined per original organism (cells 0-23 and 24-47 separately: one component, orbit-complete fill, Jaccard vs the first frame >= tau_J).
'intact' = both organisms intact; 'intact_org1' / 'intact_org2' stored separately. Single-cluster runs are unchanged."""
import sys, os, pickle, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_blind5 as B5
from lib4 import *
specs = B5.index_runs(); n = 0; tau = tauJ()
for s in specs:
    if s['fam'] != 'stress': continue
    d = pickle.load(open(s['path'], 'rb'))
    if not d['scn'].startswith('fuse'): continue
    fr = d['arms'][s['arm']]['frames']; base = [nbr_matrix(fr[0]['X'][:24]), nbr_matrix(fr[0]['X'][24:48])]; flags = [[], []]
    for f in fr:
        for h, sl in enumerate((slice(0, 24), slice(24, 48))):
            fs = frame_stats(f['X'][sl], f['MU'][sl], f['L'][sl], base[h]); flags[h].append(bool(fs['ncomp'] == 1 and fs['fill_ok'] and fs['jac'] >= tau))
    p = f"{B5.HID}/{s['name']}_hid.npz"; z = dict(np.load(p)); z['intact_org1'] = np.array(flags[0]); z['intact_org2'] = np.array(flags[1]); z['intact'] = z['intact_org1'] & z['intact_org2']; np.savez_compressed(p, **z); n += 1
    print(s['arm'], d['scn'], 'org1', np.mean(flags[0]).round(3), 'org2', np.mean(flags[1]).round(3))
print('patched', n)
