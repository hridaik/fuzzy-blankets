"""v2 outcome taxonomy (hidden tier / audit). Reference phenotype is empirical (R1), not the template."""
import json, os, sys
import numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0, os.path.dirname(__file__))
from v2 import *

REF_PATH = os.path.join(SEALED, "reference_phenotype_v2.json")

def load_ref():
    r = json.load(open(REF_PATH)); return np.array(r["pos"]), np.array(r["sec"])

def hung(cost):
    r, c = linear_sum_assignment(cost); return r, c

def slot_assignment(pos, sec, ref=None):
    """slot[i] = index of the reference-phenotype cell matched to cell i (position + secretion distance)."""
    rp, rs = ref or load_ref()
    cost = np.linalg.norm(pos[:, :, None] - rp[:, None, :], axis=0) + np.linalg.norm(sec[:, :, None] - rs[:, None, :], axis=0)
    r, c = hung(cost); slot = np.zeros(pos.shape[1], int); slot[r] = c
    return slot, float(cost[r, c].mean())

def d_pair_pos(pa, sa, pb, sb):
    """permutation-invariant shape distance (M1's d_pair: type-preferring Hungarian mean position distance)."""
    from analysis import d_pair
    return d_pair(pa, sa, pb, sb)

def cycle_structure(slot_u, slot_p):
    """cycle type (non-trivial cycles only) of the slot permutation tau: slot_u[i] -> slot_p[i]."""
    tau = {int(a): int(b) for a, b in zip(slot_u, slot_p)}
    seen, cyc = set(), []
    for s in tau:
        if s in seen: continue
        c = [s]; seen.add(s); x = tau[s]
        while x != s: c.append(x); seen.add(x); x = tau[x]
        if len(c) > 1: cyc.append(len(c))
    return sorted(cyc, reverse=True)

def roles(pos_p, sec_p, pos_u, sec_u, target=None):
    sp, _ = slot_assignment(pos_p, sec_p); su, _ = slot_assignment(pos_u, sec_u)
    diff = int((sp != su).sum())
    out = dict(relabelled=bool(diff > 0), n_cells_changed=diff, cycles=cycle_structure(su, sp))
    if target is not None: out["target_fate_changed"] = bool(sp[target] != su[target])
    return out

def shape_outcome(P, U, S, tau, nonconv=False):
    """P, U, S = (pos, sec) end states of perturbed, unperturbed twin, sustained twin."""
    if nonconv: return dict(shape="NONCONVERGED")
    dU = d_pair_pos(*P, *U); dS = d_pair_pos(*P, *S) if S is not None else None; dUS = d_pair_pos(*U, *S) if S is not None else None
    if S is not None and dUS < tau: lab = "NO-SUSTAINED-EFFECT" if dU < tau else ("PERSISTED" if dS < tau else "NOVEL")
    elif dU < tau: lab = "REVERTED"
    elif dS is not None and dS < tau: lab = "PERSISTED"
    else: lab = "NOVEL"
    return dict(shape=lab, d_unpert=float(dU), d_sustained=None if dS is None else float(dS), d_us=None if dUS is None else float(dUS))

def window_dev(mp, mu, lo, hi, n=8):
    """RMS-over-cells index-wise position deviation series between perturbed and twin trajectories, bins lo..hi (relative to segment)."""
    a = mp["positions"].reshape(n, 2, -1); b = mu["positions"].reshape(n, 2, -1); k = min(a.shape[-1], b.shape[-1])
    dev = np.sqrt(((a[..., :k] - b[..., :k]) ** 2).sum(1).mean(0)); return dev
