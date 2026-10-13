"""V4: gamma_0 bisection (median dish, middle disc, 16/g: u_d = 2.5 x switch threshold) + safe-window map. Damage onset exact: 10 CRN seeds, fail fraction >= 0.5 (sequential early stop)."""
import sys, json, time
from lib4 import *
from v4 import job_damage
MED = median_dish()
def frac_fail(variant, kg, state, centre, dur, amp, gamma, tau, nseeds=10):
    """sequential: stop as soon as >= nseeds/2 failures (True) or > nseeds/2 survivors (False)"""
    fails = 0; surv = 0; modes = []
    for s in range(nseeds):
        r = job_damage(variant, kg, state, centre, dur, amp, s, gamma, tau)
        if r['fail']: fails += 1; modes.append(r['mode'])
        else: surv += 1
        if fails >= nseeds / 2: return True, fails, s + 1, modes
        if surv > nseeds / 2: return False, fails, s + 1, modes
    return fails >= nseeds / 2, fails, nseeds, modes
def onset(variant, kg, state, centre, dur, gamma, tau, guess, tol=0.06, fac=1.4, log=False):
    """smallest amplitude with majority failure. returns (u_d, history, modes at/above onset)"""
    hist = []; modes = []
    def f(a):
        r = frac_fail(variant, kg, state, centre, dur, a, gamma, tau); hist.append((float(a), bool(r[0]), r[1], r[2])); modes.extend(r[3])
        if log: print('   amp', round(a, 3), r[:3], flush=True)
        return r[0]
    lo = hi = guess
    if f(guess):
        hi = guess
        while True:
            lo = hi / fac
            if not f(lo): break
            hi = lo
            if lo < 1e-3: return None, hist, modes
    else:
        lo = guess
        while True:
            hi = lo * fac
            if f(hi): break
            lo = hi
            if hi > 1e4: return None, hist, modes
    while hi / lo > 1 + tol:
        mid = np.sqrt(lo * hi)
        if f(mid): hi = mid
        else: lo = mid
    return float(hi), hist, modes
def job_onset(variant, kg, gf, state, centre, dm, gamma, tau, guess, g_ref=None):
    """dm in units of 1/g_ref (g_ref = population median g unless given); gamma = gamma_0 (the dish factor gf applied here)"""
    g_ref = g_ref or 4 * R_ * KG_MED; dur = dm / g_ref; d = dict(seed=-1, kappa_g=kg, g=4 * R_ * kg, gamma_factor=gf); g_eff = gamma * gf
    e = get_engine(dict(d, gamma_factor=1.0), variant, noise=True, gamma_on=False, gamma=g_eff)       # engine gamma = gamma_0*gf already (gamma_factor=1 here)
    ud, hist, modes = onset_dish(variant, d, state, centre, dur, g_eff, tau, guess)
    return dict(kg=kg, gf=gf, centre=centre, dm=dm, dur=dur, u_d=ud, hist=hist, modes=modes, chi=(None if ud is None else ud * g_eff))
def onset_dish(variant, d, state, centre, dur, g_eff, tau, guess):
    # job_damage builds its own dish with gamma_factor=1 and absolute gamma -> pass g_eff
    return onset(variant, d['kappa_g'], state, centre, dur, g_eff, tau, guess)
