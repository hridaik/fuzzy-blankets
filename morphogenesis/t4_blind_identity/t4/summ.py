"""Run-level summaries from per-run output files (used by Parts E, F, H)."""
import gzip, json, os
import numpy as np

EVTS = ['SPLIT', 'MERGE', 'EXTRUSION', 'ARRIVAL', 'LOSS', 'BIRTH', 'SPLIT_CHILD', 'END', 'END_MERGED']


def load_out(path):
    return json.load(gzip.open(path, 'rt'))


def founders(L):
    return [k for k, v in L['organisms'].items() if v['origin'] == 'founder']


def layer_verdicts(L, oid):
    """persist / change / break per layer for one founder lineage."""
    info = L['organisms'][oid]
    fr = [(f, o) for f in L['frames'] for o in f['organisms'] if str(o['id']) == oid]
    c1 = [o['C1']['J_init'] for _, o in fr]
    mat_fail = info['axis_fail_any']['material']
    struct_fail = any(info['axis_fail_any'][a] for a in ('count', 'cohesion', 'shape', 'pattern'))
    alive = info['alive_at_end']
    labs = [o['C3']['label'] for _, o in fr]
    lab_ref = next((l for l in labs if l >= 0), None)
    state_changed = len(info['state_changes']) > 0
    ood_end = labs[-1] == -1
    small_end = labs[-1] == -2
    def cls(fail, brk):
        return 'break' if brk else ('change' if fail else 'persist')
    return dict(C1=cls(mat_fail, not alive or min(c1) < 0.5), C2=cls(struct_fail, not alive or ood_end),
                C3=cls(state_changed, not alive or ood_end or small_end))


def run_metrics(out, lv='O1'):
    L = out['levels'][lv]
    F = founders(L)
    m = dict(n_founders=len(F), V=[], Vc=[], layers=[], minJ=[], max_shape=[], max_pattern=[], max_ndev=[], n_state_changes=0)
    for oid in F:
        info = L['organisms'][oid]
        fr = [o for f in L['frames'] for o in f['organisms'] if str(o['id']) == oid]
        m['V'].append(info['V']); m['Vc'].append(info['V_conservative'])
        m['layers'].append(layer_verdicts(L, oid))
        m['minJ'].append(min(o['C1']['J_init'] for o in fr))
        m['max_shape'].append(max(o['C2']['shape_dev'] for o in fr))
        m['max_pattern'].append(max(o['C2']['pattern_dev'] for o in fr))
        m['max_ndev'].append(max(o['C2']['n_dev'] for o in fr))
        m['n_state_changes'] += len(info['state_changes'])
    ev = {}
    for f in L['frames']:
        for e in f['events']:
            ev.setdefault(e['type'], []).append(e.get('t', f['t']))
    m['events'] = {k: dict(n=len(v), first_t=min(v)) for k, v in ev.items()}
    return m
