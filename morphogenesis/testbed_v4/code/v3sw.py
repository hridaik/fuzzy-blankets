"""V3 switch with shape change (gamma = 0). modes: prelim | final | noise. Conditions: 5 patterns x durations {4/g,16/g} x directions x 3 variants x 3 dishes."""
import sys, json, time
from lib4 import *
KGS = [1.5, KG_MED, 4.0]; PATTERNS = list(CENTRES); DMULT = [4, 16]
def dish_kg(kg): return dict(seed=-1, kappa_g=kg, g=4 * R_ * kg, gamma_factor=1.0)
def job_bis(variant, kg, state, centre, dm, tag=''):
    d = dish_kg(kg); dur = dm / d['g']; r = bisect_switch(d, variant, state, centre, dur)
    r.update(variant=variant, kg=kg, g=d['g'], dm=dm)
    if r['thr'] is not None:       # extra clean trial at 2x threshold: min Jaccard, per-cell crossings for the record
        S = switch_trial(d, variant, state, centre, dur, 2 * r['thr']); r2 = score_switch(S, state, ref_angles(d, variant)['b' if state == 'a' else 'a']); r['min_jac_2x'] = r2['min_jac']; r['switch_2x'] = r2['switch']
        r['jac_trace_thr'] = None
    return r
def job_noise(variant, kg, state, centre, dm, thr, seed):
    d = dish_kg(kg); dur = dm / d['g']; ref = ref_angles(d, variant)['b' if state == 'a' else 'a']
    S = switch_trial(d, variant, state, centre, dur, 1.2 * thr, noise=True, seed=seed); r = score_switch(S, state, ref); r0 = None
    if seed < 2: S0 = switch_trial(d, variant, state, centre, dur, 0.0, noise=True, seed=seed, sham=True); r0 = score_switch(S0, state, ref)
    return dict(variant=variant, kg=kg, state=state, centre=centre, dm=dm, seed=seed, switch=r['switch'], state_ok=r['state_ok'], shape_ok=r['shape_ok'], intact=r['intact'], min_jac=r['min_jac'], sham_switch=(r0['switch'] if r0 else None), sham_min_jac=(r0['min_jac'] if r0 else None), sham_intact=(r0['intact'] if r0 else None))
if __name__ == "__main__":
    from par4 import run_jobs; mode = sys.argv[1]; t0 = time.time(); out = sys.argv[2] if len(sys.argv) > 2 else mode
    if mode in ('prelim', 'final'):
        args = [(v, kg, s, c, dm) for v in VARIANTS for kg in KGS for s in 'ab' for c in PATTERNS for dm in DMULT]
        res = run_jobs(job_bis, args, label='V3' + mode); json.dump(res, open(f'../data/v3_{out}.json', 'w'))
    elif mode == 'noise':
        det = json.load(open('../data/v3_final.json')); args = [(r['variant'], r['kg'], r['state'], r['centre'], r['dm'], r['thr'], s) for r in det if r['thr'] for s in range(6)]
        res = run_jobs(job_noise, args, label='V3n'); json.dump(res, open('../data/v3_noise.json', 'w'))
    print('wall', time.time() - t0)
