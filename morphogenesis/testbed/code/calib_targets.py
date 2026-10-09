"""oracle targets for time calibration (T1.3): merging time constant and belief-differentiation timing."""
import sys; sys.path.insert(0,'.')
from common import *
from scipy.special import softmax

def merge_curve(posA, secA, t_idx):
    """posA list of (2,n,T) arrays, secA list of (4,n,T); max pairwise d_pair over individuals at times t_idx."""
    m = len(posA); out = []
    for t in t_idx:
        ds = [d_pair(posA[i][:, :, t], secA[i][:, :, t], posA[j][:, :, t], secA[j][:, :, t]) for i in range(m) for j in range(i + 1, m)]
        out.append(np.max(ds))
    return np.array(out)

def fit_tau(t, D, lo=40, hi=120):
    m = (t >= lo) & (t <= hi) & (D > 1e-12)
    s = np.polyfit(t[m], np.log(D[m]), 1)[0]
    return -1.0 / s

def belief_curve(v):  # v (slots,cells,T)
    return softmax(v, axis=0).max(0).mean(0)

def t_cross(t, y, thr):
    i = np.argmax(y >= thr); return float(t[i]) if (y >= thr).any() else np.nan

if __name__ == "__main__":
    names = [f'primary_{k:04d}' for k in range(12)]
    runs = [oracle_run(n) for n in names]
    t = np.arange(runs[0]['T'])
    D = merge_curve([r['pos'] for r in runs], [r['sec'] for r in runs], t)
    B = np.mean([belief_curve(r['v']) for r in runs], axis=0)
    out = dict(tau_merge=fit_tau(t, D), t_belief_05=t_cross(t, B, 0.5), t_belief_07=t_cross(t, B, 0.7), final_belief=float(B[-1]),
               D_at=[float(D[k]) for k in (0, 20, 40, 60, 80, 120, 160)],
               first_below_017=int(np.argmax(D < 0.17)), B_at=[float(B[k]) for k in (0, 5, 10, 20, 40, 80)])
    print(out); json.dump(out, open(os.path.join(TB, 'data', 'oracle_targets.json'), 'w'), indent=1)
    np.save(os.path.join(TB, 'data', 'oracle_curves.npy'), np.stack([t, D, B]))
