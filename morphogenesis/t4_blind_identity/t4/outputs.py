"""Stage 2: apply frozen calibration (envelope bounds, state models) to stage-1 records -> per-run auditor output."""
import gzip, json, os, pickle
import numpy as np
from . import io, layers, states
from .describe import pattern_names

MIN_STATE_N = 12      # organisms smaller than this (cells) are not assigned a state (label -2)


class Calib:
    def __init__(self, root=None):
        root = root or io.ROOT
        self.env = json.load(open(os.path.join(root, 'calibration', 'envelope.json')))
        self.models = pickle.load(open(os.path.join(root, 'calibration', 'state_models.pkl'), 'rb'))
        self.geo = json.load(open(os.path.join(root, 'calibration', 'geometry.json')))
        self.est = {lv: states.OnlineState(m['pre'], m['gmm'], m['ood'], stay=0.95) for lv, m in self.models.items()}


def _r(x, nd=4):
    return None if x is None else (round(float(x), nd) if np.isfinite(x) else None)


def level_output(rec, calib, cell_lookup=True):
    lv = rec['level']
    env = calib.env[lv]
    pat_sd = np.array([env['pat_sd'][n] for n in pattern_names(rec['ch'])])
    bounds = np.array([env['bounds'][a] for a in layers.AXES])
    L, ev = layers.lineages(rec)
    nfr = len(rec['frames'])
    org_info = {}; per = {}
    names = calib.models[lv]['names']
    for oid, seq in L.items():
        seq_s = layers.smooth_seq(rec, seq)
        ser = layers.layer_series(rec, oid, seq_s, pat_sd, cell_lookup=cell_lookup)
        vals = layers.axis_values(ser)
        ok = layers.verdicts(vals, bounds)            # (T, 5); frame 0 of lineage is the reference -> passes trivially
        ok[0, :] = True
        running = np.cumprod(ok.all(1)).astype(bool)
        X = np.array([[o['desc'][n] for n in names] for _, o in seq_s])
        tl = [rec['frames'][k]['t'] for k, _ in seq]
        st = calib.est[lv].run(X, tl)
        small = np.array([o['n'] < MIN_STATE_N for _, o in seq])
        label = np.where(small, -2, st['label'])
        changes = states.change_times(label, st['post']) if not small.all() else []
        first = seq[0][0]
        parent = seq[0][1]['parent']
        flags = {}
        for k, _ in seq:
            for e in ev.get((oid, k), []):
                flags[e['type']] = flags.get(e['type'], 0) + 1
        unres = any(o['unresolved'] for _, o in seq)
        alive_end = seq[-1][0] == nfr - 1
        V = bool(alive_end and running[-1])
        blockers = flags.get('SPLIT', 0) + flags.get('MERGE', 0) + int(unres)
        fail_first = {a: (int(seq[int(np.argmax(~ok[:, j]))][0]) if (~ok[:, j]).any() else None) for j, a in enumerate(layers.AXES)}
        org_info[oid] = dict(origin='founder' if first == 0 else ('split_child' if parent is not None else 'birth'), parent=parent,
                             born_k=first, last_k=seq[-1][0], alive_at_end=alive_end, V=V, V_conservative=bool(V and blockers == 0),
                             flags=flags, unresolved_any=bool(unres), axis_first_fail_k=fail_first,
                             axis_fail_any={a: bool((~ok[:, j]).any()) for j, a in enumerate(layers.AXES)},
                             state_changes=[dict(k=int(seq[t][0]), t=_r(rec['frames'][seq[t][0]]['t'], 3), frm=a, to=b) for t, a, b in changes],
                             state_first=int(label[0]), state_last=int(label[-1]))
        per[oid] = dict(ser=ser, ok=ok, running=running, label=label, post=st['post'], ood=st['ood'], seq=seq)
    # per-frame output
    frames = []
    for f in rec['frames']:
        orgs = []
        for o in f['orgs']:
            p = per[o['org']]; i = [k for k, _ in p['seq']].index(f['k'])
            s = p['ser'][i]
            inf = org_info[o['org']]
            blocked = inf['flags'].get('SPLIT', 0) + inf['flags'].get('MERGE', 0)
            e1 = np.array(o['e1']); e2 = [-e1[1], e1[0]]
            orgs.append(dict(
                id=o['org'], members=o['members'], n=o['n'], n_pixels=o.get('n_pixels'),
                centroid=[_r(v) for v in o['centroid']], e1=[_r(v) for v in e1], e2=[_r(v) for v in e2],
                axis_conf=_r(o['axis_conf']), sign_conf=_r(o['sign_conf']), sign_src=o['sign_src'], unresolved=o['unresolved'],
                C1={k: _r(s[k]) for k in ('J_init', 'D_init', 'J_prev')},
                C2={**{k: _r(s[k]) for k in ('n', 'n_dev', 'mst_max', 'ncomp', 'shape_dev', 'pattern_dev')},
                    **{k: _r(s[k]) for k in ('procr_rot', 'procr_refl') if k in s}},
                axis_pass=dict(zip(layers.AXES, [bool(v) for v in p['ok'][i]])),
                V_running=bool(p['running'][i]),
                V_conservative_running=bool(p['running'][i] and not o['unresolved']
                                            and not any(e['type'] in ('SPLIT', 'MERGE') and e['k'] <= f['k'] for kk in range(f['k'] + 1) for e in ev.get((o['org'], kk), []))),
                C3=dict(label=int(p['label'][i]), posterior=_r(p['post'][i]), ood=bool(p['ood'][i])),
                desc={k: _r(v) for k, v in o['desc'].items()}))
        frames.append(dict(k=f['k'], t=_r(f['t'], 3), n_free=f['n_free'], organisms=orgs,
                           events=[{k: (v if not isinstance(v, (np.floating, np.integer)) else float(v)) for k, v in e.items()} for e in f['events']]))
    evs = {}
    for f in frames:
        for e in f['events']:
            d = evs.setdefault(e['type'], dict(n=0, first_t=f['t'])); d['n'] += 1
    fo = [v for v in org_info.values() if v['origin'] == 'founder']
    summary = dict(n_frames=nfr, n_organisms_total=len(org_info), n_founders=len(fo),
                   frac_founders_V=_r(np.mean([v['V'] for v in fo])) if fo else None,
                   frac_founders_V_conservative=_r(np.mean([v['V_conservative'] for v in fo])) if fo else None,
                   events=evs, state_change_times=sorted({c['t'] for v in org_info.values() for c in v['state_changes']}),
                   first_state_change_t=min([c['t'] for v in org_info.values() for c in v['state_changes']], default=None))
    return dict(level=lv, channels=rec['ch'], summary=summary, frames=frames, organisms={str(k): v for k, v in org_info.items()})


def write_run(row, recs, calib, outdir, cfg_hash):
    out = dict(run=row['run'], condition=row['condition'], arm=row['arm'], split=row['split'], group=row['group'],
               body_id=row['body_id'], onset=row['onset'], frame_interval=row['frame_interval'], config_hash=cfg_hash,
               levels={lv: level_output(rec, calib) for lv, rec in recs.items()})
    with gzip.open(os.path.join(outdir, row['run'] + '.json.gz'), 'wt') as fh:
        json.dump(out, fh, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    return out
