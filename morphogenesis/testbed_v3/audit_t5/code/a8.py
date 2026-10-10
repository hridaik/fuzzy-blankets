"""A8: was the collective truly past the tipping point at each controller commit? Deterministic noise-free continuation of the hidden state at the commit time (lights off).
Also the hidden quantities at commit and at the end of each pulse."""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from truth import *
from lib import *
import jax.numpy as jnp
R = [json.loads(l) for l in open(os.path.join(T5, 'logs', 'heldout_summary.jsonl'))]
ctrl = [r for r in R if r['arm'] == 'ctrl' and r['reason'] not in ('quota_skip', 'baseline_not_clean')]
exnf = {}
def nf_for(seed, start):
    return Experiment4(start, seed=seed, noise=0.0, sig_h=0.0, private=dict(PRIV), form_seed=seed)
def continue_det(h, k, start, T=250, seed=0):
    ex = nf_for(seed, start); w = ex.w
    w.set_state([h[a][k].copy() for a in ('X', 'C', 'MU', 'L', 'D', 'E')]); w.time = 1e4 + float(h['t'][k]); ex.t0 = w.time - float(h['t'][k])
    traj = []
    for _ in range(int(T)):
        ex.run_sched(1.0, [], sham=False, obs_times=[]); traj.append(float((1 / (1 + np.exp(-w.L[w.alive]))).mean()))
    return traj
out = []
for r in ctrl:
    L = load_ep(r['episode']); h, e = load_hidden(r['episode']); dec = L['decisions']; t = h['t']; start = state_of(r['seed'])
    commits = [d for d in dec if d['action'] == 'commit']; uncs = [d for d in dec if d['action'] == 'uncommit']
    rho = (1 / (1 + np.exp(-h['L']))).mean(1)
    for ci, d in enumerate(commits):
        k = int(np.argmin(np.abs(t - d['t']))); l = h['L'][k]; Dd = h['D'][k]
        tgt_sign = -1.0 if start == 'a' else 1.0
        traj = continue_det(h, k, start)
        end_target = (traj[-1] < 0.5) if start == 'a' else (traj[-1] > 0.5)
        out.append(dict(seed=r['seed'], start=start, ctrl_success=r['success'], commit_idx=ci, n_commits=len(commits), t_commit=float(d['t']), mean_rho=float(rho[k]), mean_l=float(l.mean()), frac_cells_target_side=float(((l * tgt_sign) > 0).mean()),
            dA_minus_dB=float((Dd[:, 0] - Dd[:, 1]).mean()), det_continuation_end_rho=traj[-1], det_continuation_switches=bool(end_target), t_uncommit=(uncs[ci]['t'] if ci < len(uncs) else None), reason_text=d['reason']))
json.dump(out, open('../data/a8_commits.json', 'w'), indent=1, default=float)
import collections
ok = [o for o in out if o['ctrl_success']]; bad = [o for o in out if not o['ctrl_success']]
print('commits in successful dishes', len(ok), 'truly past tipping (det. continuation switches):', sum(o['det_continuation_switches'] for o in ok))
print('commits in failed dishes', len(bad)); [print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in o.items() if k != 'reason_text'}) for o in bad]
print('mean rho at commit: success dishes median', np.median([o['mean_rho'] for o in ok]), 'min', min(o['mean_rho'] for o in ok))
