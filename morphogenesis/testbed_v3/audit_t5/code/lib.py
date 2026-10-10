"""Shared helpers of the T5 audit (white-box). Offline regeneration of live dishes with the offline engine (live == offline, bit-identical).
SEALED: contains hidden information; never give to a blind session."""
import sys, os, json, copy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); V3 = os.path.abspath(os.path.join(HERE, '..', '..')); MORPH = os.path.abspath(os.path.join(V3, '..'))
sys.path.insert(0, os.path.join(V3, 'code')); sys.dont_write_bytecode = True
import world4, build_blind3 as B3
from world4 import Experiment4, CH4
from world3 import Mask
T5 = os.path.join(MORPH, 't5_blind_control'); SEALED = os.path.join(V3, 'live_sealed_t5')
LIGHTS = {v: k for k, v in B3.LIGHT_LABELS.items()}                 # 'L3' -> 'MA'
PRIV = {'MA': ('mem', 0), 'MB': ('mem', 1), 'SEC': ('sec', 0), 'RG': ('rg', 0), 'MIG': ('mig', 0)}
def state_of(seed): return 'a' if np.random.default_rng(seed + 17).random() < 0.5 else 'b'
def make_dish(seed, noise_key=None, state=None):
    """dish exactly as Episode.__init__ of the live server (state, burn-in 100 tu); returns Experiment4 at t=0. noise_key overrides the CRN key (for other noise realisations)."""
    ex = Experiment4(state or state_of(seed), seed=(seed if noise_key is None else noise_key), noise=0.02, sig_h=0.4, private=dict(PRIV), form_seed=seed)
    ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []
    if noise_key is not None:                       # same pose as the true dish
        pass
    return ex
def snap(ex): w = ex.w; return dict(arr=[a.copy() for a in (w.X, w.C, w.MU, w.L, w.D, w.E)], time=w.time, sc=w.step_count)
def restore(ex, s):
    w = ex.w; w.set_state([a.copy() for a in s['arr']]); w.time = s['time']; w.step_count = s['sc']
def rel_t(ex): return round(ex.w.time - ex.t0, 6)
def mk_action(label, mask_dict, amp, t_on, dur, ramp):
    k = mask_dict['type']
    if k == 'disc': sh = [('disc', float(mask_dict['xy'][0]), float(mask_dict['xy'][1]), float(mask_dict['radius']), 1.0)]
    else: sh = [('halfplane', 0.0, 0.0, -1.0, 1.0)]
    return dict(type='light', channel=LIGHTS[label], mask=Mask(sh), amp=float(amp), t_on=float(t_on), t_off=float(t_on + dur), ramp=float(ramp))
def advance(ex, T, actions):
    """advance by T tu in 1-tu server steps (identical chunking), return list of per-step hidden records (t, L, X, D, E)"""
    out = []
    n = int(round(T)); 
    for _ in range(n):
        ex.run_sched(1.0, actions, sham=False, obs_times=[])
        w = ex.w; out.append(dict(t=rel_t(ex), L=w.L.copy(), X=w.X.copy(), D=w.D.copy(), E=w.E.copy()))
    return out
