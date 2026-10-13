import sys, json
from viewer4 import *
from viewer4 import _r
G = 4 * R_ * KG_MED; MED = median_dish(); w = json.load(open('../data/v4_window.json')); v3 = json.load(open('../data/v3_final.json'))
def thr_of(kg, centre, dm, variant='phi04', state='a'): return [x['thr'] for x in v3 if x['variant'] == variant and abs(x['kg'] - kg) < 1e-3 and x['centre'] == centre and x['dm'] == dm and x['state'] == state][0]
def clamp_roll(label, rhos, hold=100.0, every=5.0):
    tm = TM; e = make_engine4(tm, Params4(g=MED['g'])); e.dt = DT; st, perm = seeded_start4(tm, 0, 'b'); base = None; frames = []; tt = []; t = 0.0; step0 = 0; key = jax.random.PRNGKey(0)
    per = int(round(every / DT)); P = dict(label=label, note='', t=[], X=[], rho=[], ubar=[], angle=[], jac=[], intact=[], ncomp=[], head=[], hinge=[], tailc=[], lit=[0] * 24, lit_on=[0, 0], perm=perm.tolist(), types=[], place=[])
    for r in rhos:
        ctl = list(zero_ctl(e)); ctl[12] = jnp.full(24, float(r)); st, tr = e.run_ctl(st, t, DT, int(round(hold / DT)), key, tuple(ctl), -1e30, 1e30, 1.0, step0=step0, save_every=per); t += hold; step0 += int(round(hold / DT))
        if base is None: base = nbr_matrix(np.array(tr[0][-1]))
        for k in range(len(tr[0])):
            X, C, MU, L, D, E, U = [np.array(a[k]) for a in tr]; fs = frame_stats(X, MU, L, base); ax = axes_of(X, MU); P['t'].append(round(t - hold + every * (k + 1), 2)); P['X'].append(_r(X)); P['rho'].append([float(r)] * 24); P['ubar'].append([0.0] * 24)
            P['angle'].append(None if fs['angle'] != fs['angle'] else round(float(fs['angle']), 2)); P['jac'].append(round(fs['jac'], 4)); P['ncomp'].append(fs['ncomp']); P['intact'].append(True)
            P['head'].append(_r(ax[0]) if ax else None); P['hinge'].append(_r(ax[1]) if ax else None); P['tailc'].append(_r(ax[2]) if ax else None); P['place'].append([])
    return P
if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('all', 'shapes'):
        a = audit_roll('settled body, state a (rho = 0.89)', MED, 'phi04', 'a', 0.5, 0.5); b = audit_roll('settled body, state b (rho = 0.11)', MED, 'phi04', 'b', 0.5, 0.5)
        sweep = clamp_roll('rho clamped 0 -> 1 in steps of 0.1 (100 tu each; start from the b body)', [round(x, 1) for x in np.linspace(0, 1, 11)])
        emit('shapes', 'v4 - two shapes and the clamped-rho sweep', 'tail angle is the signed angle between body axis (green) and tail axis (purple); + = limb side', [a, b, sweep], info='Left, centre: the two stable bodies of the median dish. Right: the shape follows the clamped belief monotonically (SHAPES.md).')
    if which in ('all', 'switch'):
        thr = thr_of(KG_MED, 'middle', 16); dur = 16 / G; r = audit_roll('clean switch: light on the middle disc, 16/g, 1.5 x threshold; no cell lost', MED, 'phi04', 'a', dur + 20 / G, 1.0, light=dict(centre='middle', dur=dur, amp=1.5 * thr))
        emit('switch', 'v4 - a clean switch: the tail swings over', 'median dish; deterministic; dashed rings = lit cells while the light is on', [r])
    if which in ('all', 'damage'):
        ud4 = [x['u_d'] for x in w if x['centre'] == 'middle' and x['dm'] == 4][0]; thr16 = thr_of(KG_MED, 'middle', 16); dur4 = 4 / G; dur16 = 16 / G
        bright = audit_roll(f'BRIGHT & SHORT: 4/g, amplitude {1.5 * ud4:.1f} (1.5 x damage onset)', MED, 'phi04', 'a', dur4 + 150, 2.0, light=dict(centre='middle', dur=dur4, amp=1.5 * ud4), noise=True, seed=3, burn=100.0)
        gentle = audit_roll(f'GENTLE & LONG: 16/g, amplitude {1.5 * thr16:.2f} (1.5 x switch threshold)', MED, 'phi04', 'a', dur16 + 150, 2.0, light=dict(centre='middle', dur=dur16, amp=1.5 * thr16), noise=True, seed=3, burn=100.0)
        emit('damage_vs_safe', 'v4 - a damaging pulse versus a safe pulse at the same disc', 'both switch the memory; the bright pulse also drives the lit cells off their places (orange rings = light damage)', [bright, gentle], ubar_scale=25.0, info='Same dish, same disc, same noise (CRN). Compare intact flag and cell positions after the light.')
    if which in ('all', 'coupling'):
        ps = []
        for kg, nm in ((1.5, 'LOW coupling kappa_g 1.5'), (KG_MED, 'MEDIAN coupling 2.45'), (4.0, 'HIGH coupling 4.0')):
            d = dict(seed=-1, kappa_g=kg, g=4 * R_ * kg, gamma_factor=1.0); thr = thr_of(kg, 'middle', 16); dur = 16 / d['g']; ps.append(audit_roll(f'{nm}: g = {d["g"]:.2f}, thr {thr:.2f}', d, 'phi04', 'a', dur + 20 / d['g'], 1.0, light=dict(centre='middle', dur=dur, amp=1.5 * thr)))
        emit('coupling', 'v4 - one dish each at low, median and high coupling', 'same protocol (middle disc, 16/g, 1.5 x own threshold); settled angle and speed differ with g', ps)
