"""Audit library: sealed access to hidden truth (raw run pickles, hidden npz/json, mapping) and READ-ONLY access to the T4 outputs/cache. Never writes into t4_blind_identity/ or any blind package."""
import os, sys, json, gzip, pickle, csv, glob, hashlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); AUD = os.path.dirname(HERE); V3 = os.path.dirname(AUD); MORPH = os.path.dirname(V3)
T4 = os.path.join(MORPH, 't4_blind_identity'); PKG = os.path.join(MORPH, 'testbed_blind_v2'); HID = os.path.join(V3, 'data', 'blind_v2_hidden'); RAW = os.path.join(V3, 'data', 'raw_v3')
sys.path.insert(0, os.path.join(V3, 'code')); sys.dont_write_bytecode = True
CFG = json.load(open(os.path.join(AUD, 'FROZEN_AUDIT_CONFIG.json')))
MAP = json.load(open(os.path.join(HID, 'mapping.json'))); META = MAP['runs']; COLP = MAP['col_perm']
CAT = list(csv.DictReader(open(os.path.join(PKG, 'catalog.csv')))); CATD = {r['run']: r for r in CAT}
HNAME = ['c0', 'c1', 'c2', 'c3', 'dA', 'dB', 'e']                    # hidden quantities in hidden order
PKGCOL = {f'c{j}': HNAME[COLP[j]] for j in range(7)}                  # package column name -> hidden quantity
INV = {v: k for k, v in PKGCOL.items()}
def raw_path(run):
    m = META[run]; fam = m['family']
    if fam == 'natural': return f"{RAW}/natural/{m['state']}_{m['tag']}_{m['seed']:03d}.pkl"
    if fam == 'stress': return f"{RAW}/stress/{m['scn'].replace('|', '_').replace(',', 'x')}_{m['state']}_{m['seed']:03d}.pkl"
    if fam == 'switch': return f"{RAW}/switch/{m['state']}_c{m['centre']}_d{m['dur']:.1f}_l{m['level']}_{m['kind']}_{int(CATD[run]['body_id'])}.pkl"
    if fam == 'decoy': return f"{RAW}/decoy/{m['state']}_{m['kind']}_{int(CATD[run]['body_id'])}.pkl"
_rawc = {}
def raw(run):
    """hidden truth frames: list of dict(t, X, C, D, E, alive, cell_id, MU, L) (arena coordinates, true), + hidden dict"""
    p = raw_path(run)
    if p not in _rawc:
        if len(_rawc) > 6: _rawc.clear()
        _rawc[p] = pickle.load(open(p, 'rb'))
    d = _rawc[p]; m = META[run]
    if m['family'] == 'stress': a = d['arms'][m['arm']]; return a['frames'], a['hidden']
    return d['frames'], d['hidden']
def hid(run): return dict(np.load(f"{HID}/{run}_hid.npz"))
def t4out(run): return json.load(gzip.open(f"{T4}/outputs/{run}.json.gz"))
def t4cache(run, lv):
    sp = 'dev' if CATD[run]['split'] == 'development' else 'held'
    return pickle.load(open(f"{T4}/cache/{sp}/{run}_{lv}.pkl", 'rb'))
def pkg(run, lv): return dict(np.load(f"{PKG}/runs/{run}_{lv}.npz"))
def rho(L): return 1 / (1 + np.exp(-L))
def onset_abs(run):
    """time (relative to observation start) of the hidden operation / light onset, or None"""
    m = META[run]
    if m['family'] in ('switch',): return m['t_on']
    if m['family'] == 'decoy': return 10.0
    if m['family'] == 'stress':
        ev = [e for e in raw(run)[1]['events'] if e['kind'] in ('remove', 'insert', 'extrude', 'cut', 'fuse', 'replace')]
        return min(e['t'] for e in ev) - 1e4 - 100.0 if ev else None
    return None
