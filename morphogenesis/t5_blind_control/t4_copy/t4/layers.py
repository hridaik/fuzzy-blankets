"""Identity layers (C1 material, C2 structural) per organism lineage, and the validity envelope.
Pure functions of stage-1 records; causal (value at frame k uses frames <= k of the lineage)."""
import numpy as np
from .describe import pattern_names
from .geom import procrustes

AXES = ['material', 'count', 'cohesion', 'shape', 'pattern']


def lineages(rec):
    """org id -> list of (frame_index, org_record). Also event lookup by (org, k)."""
    L = {}
    for f in rec['frames']:
        for o in f['orgs']:
            L.setdefault(o['org'], []).append((f['k'], o))
    ev = {}
    for f in rec['frames']:
        for e in f['events']:
            ev.setdefault((e['org'], f['k']), []).append(e)
    return L, ev


def _jac(a, b):
    a, b = set(a), set(b)
    u = len(a | b)
    return len(a & b) / u if u else 1.0


def _dice(a, b):
    a, b = set(a), set(b)
    return 2 * len(a & b) / (len(a) + len(b)) if (len(a) + len(b)) else 1.0


def layer_series(rec, org, seq, pat_sd, cell_lookup=None):
    """Per-frame C1/C2 descriptors for one lineage. seq = [(k, orgrec)]."""
    ch = rec['ch']
    pn = pattern_names(ch)
    ref = seq[0][1]
    ref_pat = np.array([ref['desc'][n] for n in pn])
    ref_members = ref['members'] if rec['level'] != 'O3a' and rec['level'] != 'O3b' else ref['_pix']
    out = []
    prev_members = None
    for k, o in seq:
        mem = o['members'] if rec['level'] in ('O1', 'O2') else o['_pix']
        d = o['desc']
        pat = np.array([d[n] for n in pn])
        z = (pat - ref_pat) / pat_sd if pat_sd is not None else pat - ref_pat
        row = dict(k=k, t=rec['frames'][k]['t'],
                   J_init=_jac(ref_members, mem), D_init=_dice(ref_members, mem),
                   J_prev=_jac(prev_members, mem) if prev_members is not None else 1.0,
                   n=d['n'], n_dev=abs(d['n'] / max(ref['desc']['n'], 1e-9) - 1.0),
                   mst_max=d['mst_max'], ncomp=d['ncomp_coh'],
                   shape_dev=float(np.hypot(np.log(d['s1'] / ref['desc']['s1']), np.log(d['s2'] / ref['desc']['s2']))),
                   pattern_dev=float(np.sqrt(np.mean(z ** 2))),
                   sign_conf=o['sign_conf'], unresolved=o['unresolved'])
        if cell_lookup is not None and rec['level'] in ('O1', 'O2'):
            fr = rec['frames'][k]['cells']; r0 = rec['frames'][seq[0][0]]['cells']
            ids_k = dict(zip(fr['ids'], fr['xy'])); ids_0 = dict(zip(r0['ids'], r0['xy']))
            common = [c for c in mem if c in ids_k and c in ids_0]
            if len(common) >= 4:
                A = np.array([ids_0[c] for c in common]); B = np.array([ids_k[c] for c in common])
                row['procr_rot'] = procrustes(A, B, False); row['procr_refl'] = procrustes(A, B, True)
        prev_members = mem
        out.append(row)
    return out


def axis_values(series):
    """Map layer series to the 5 envelope axes (higher = further from the reference)."""
    return np.array([[1 - r['J_init'], r['n_dev'], r['mst_max'],
                      r['shape_dev'], r['pattern_dev']] for r in series])


def verdicts(vals, bounds):
    return vals <= (np.asarray(bounds)[None, :] + 1e-9)


WINDOW = 100.0     # declared causal smoothing window = the natural-dish sampling interval (time units)


def smooth_seq(rec, seq, window=WINDOW):
    """Causal median of every descriptor over the lineage's frames with t' in (t-window, t]. At the natural
    sampling interval (100) this is the raw value, so thresholds calibrated on natural dishes stay time-scale matched."""
    ts = np.array([rec['frames'][k]['t'] for k, _ in seq])
    keys = list(seq[0][1]['desc'].keys())
    M = np.array([[o['desc'][n] for n in keys] for _, o in seq], float)
    out = []
    for i, (k, o) in enumerate(seq):
        lo = np.searchsorted(ts, ts[i] - window + 1e-9, side='right') if window > 0 else i
        lo = min(lo, i)
        med = np.nanmedian(M[lo:i + 1], axis=0)
        o2 = dict(o); o2['desc'] = dict(zip(keys, med.tolist()))
        out.append((k, o2))
    return out
