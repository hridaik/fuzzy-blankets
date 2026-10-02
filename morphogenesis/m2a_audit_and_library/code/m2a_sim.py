"""Python driver for oracle/m2a_run.m (unmodified spm_ADEM + M2A process/model functions)."""
import os, sys, time, uuid
import numpy as np, scipy.io as sio
sys.path.insert(0, os.path.dirname(__file__))
from m2a_common import *

CFG_DIR = os.path.join(DATA, "cfg"); os.makedirs(CFG_DIR, exist_ok=True)

def make_events(evs):
    """evs: list of dict. Superset schema (all fields present; unused ones empty). Cells are 0-based here, 1-based in Octave.
    type: 'pos'|'sec'|'gain' (raised-cosine pulse: ch, amp, onset, w) | 'kuch' (sign, onset, off, w) | 'sham' (freqs, phx, phy, amp, onset, off, w)"""
    if not evs: return np.zeros((0,), dtype=object)
    names = ["type", "cells", "ch", "amp", "onset", "w", "off", "sign", "freqs", "phx", "phy", "amp0"]
    dt = np.dtype([(k, object) for k in names])
    arr = np.zeros((len(evs),), dtype=dt)
    E = np.zeros((0, 0))
    for i, e in enumerate(evs):
        off = e.get("off"); 
        arr[i] = (e["type"], np.asarray(e["cells"], float).reshape(-1) + 1, float(e.get("ch", 0)), float(e.get("amp", 0)),
                  float(e["onset"]), float(e["w"]), (np.inf if off is None else float(off)), float(e.get("sign", 1)),
                  np.asarray(e.get("freqs", E), float), np.asarray(e.get("phx", E), float).reshape(-1), np.asarray(e.get("phy", E), float).reshape(-1), float(e.get("amp0", 0.0)))
    return arr

def simulate(out, N, seed=0, L=2, v0=None, ax0=None, as0=None, ramp_mode="N", ramp_const=0.6,
             ramp_ref=512, t_off=0, events=None, V1=None, quiet=True, engine="spm", cont_file=None,
             GV1=None, noise_seed=None, noise_horizon=None, ablate=None, kick=None, prec=None, dt=None):
    cfg = dict(L=L, N=N, seed=seed, ramp_mode=ramp_mode, ramp_const=ramp_const, ramp_ref=float(ramp_ref),
               t_off=float(t_off), out=out)
    cfg["v0"] = np.zeros((0, 0)) if v0 is None else v0
    if ax0 is not None: cfg["ax0"] = ax0
    if as0 is not None: cfg["as0"] = as0
    if events: cfg["events"] = make_events(events)
    if V1 is not None: cfg["V1"] = V1
    cfg["engine"] = engine
    if ablate: cfg["ablate"] = ablate
    if kick: cfg["kick"] = kick
    if prec: cfg["prec"] = {k: (np.inf if v is None else float(v)) for k, v in prec.items()}
    if dt is not None: cfg["dt"] = float(dt)
    if cont_file: cfg["cont_file"] = cont_file
    if GV1 is not None: cfg["GV1"] = float(GV1)
    if noise_seed is not None: cfg["noise_seed"] = float(noise_seed)
    if noise_horizon: cfg["noise_horizon"] = float(noise_horizon)
    cf = os.path.join(CFG_DIR, uuid.uuid4().hex + ".mat")
    sio.savemat(cf, {"cfg": cfg})
    try:
        _, el = octave(f"m2a_run('{cf}');")
    finally:
        if os.path.exists(cf): os.remove(cf)
    return el

def load(path):
    m = sio.loadmat(path)
    return {k: m[k] for k in m if not k.startswith("__")}

def unpack(m, b=-1, n=None):
    n = n or int(np.asarray(m["n"]).item())
    pos = m["positions"][:, b].reshape(n, 2).T
    sec = m["secretion"][:, b].reshape(4, n, order="F")
    v = m["v_expect"][:, b].reshape(n, n, order="F")
    return pos, sec, v

def jacobian(out, cont_file, T_dev=32.0, steps=(1e-4, 1e-6), events=None, prec=None, L=2, seed=0):
    """One-bin-map Jacobian around the state stored in cont_file (see oracle/m2a_jac.m)."""
    cfg = dict(L=L, N=1, seed=seed, ramp_mode="abs", ramp_const=0.6, ramp_ref=float(T_dev), t_off=0.0, out=out, engine="m2a",
               cont_file=cont_file, steps=np.asarray(steps, float), v0=np.zeros((0, 0)))
    if events: cfg["events"] = make_events(events)
    if prec: cfg["prec"] = {k: (np.inf if v is None else float(v)) for k, v in prec.items()}
    cf = os.path.join(CFG_DIR, uuid.uuid4().hex + ".mat"); sio.savemat(cf, {"cfg": cfg})
    try: _, el = octave(f"m2a_jac('{cf}');")
    finally:
        if os.path.exists(cf): os.remove(cf)
    return el
