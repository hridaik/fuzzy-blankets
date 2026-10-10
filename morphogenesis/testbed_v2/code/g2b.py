"""G2(d) hysteresis continuation on pi_psi multiplier; G2(e) sigma_h pilot."""
import sys, json; sys.path.insert(0,'.')
from an2 import *
from g2cfg import *
def hyst(form='L', scales=(0, 0.5, 1, 1.5, 2, 3, 4, 6), T=1500.0):
    tm = make_template2(); mf = mean_field(tm, FULL); far = np.where(np.array(mf['Gmorph_per_place']) < 0.5)[0]; near = np.where(np.array(mf['Gmorph_per_place']) >= 0.5)[0]
    st, perm = seeded_start2(tm, 0, form); rows = []; seq = [(s, 'up') for s in scales[scales.index(1) if False else 0:]]
    seq = [(1.0, 'start')] + [(s, 'up') for s in scales if s > 1] + [(s, 'down') for s in scales[::-1] if s <= 6] + [(1.0, 'back')]
    t = 0.0
    for s, ph in seq:
        eng = make_engine2(tm, Params2(psi_scale=s, **FULL), None); eng.dt = DT
        st = run_plain(eng, st, t, T, jax.random.PRNGKey(0)); t += T
        sm = summarize(eng, st, mirror_orbits=True); L = np.array(st[4]); rho = 1 / (1 + np.exp(-L)); cellplace = perm
        farc = np.isin(perm, far); nearc = np.isin(perm, near)
        rows.append(dict(scale=s, phase=ph, label=sm['label'], mean_rho_far=float(rho[farc].mean()), mean_rho_near=float(rho[nearc].mean()), absl_far=float(np.abs(L[farc]).mean()), mean_rho=sm['mean_rho'], dL=sm['dL'], dR=sm['dR'], orbit_complete=sm['orbit_complete']))
        print(rows[-1], flush=True)
    return rows
def sig_pilot(sh, form='L'):
    P = Params2(sig_x=0.02, sig_c=0.02, sig_d=0.02, sig_mu=0.02, sig_h=sh, **FULL); tm = make_template2(); eng = make_engine2(tm, P); eng.dt = DT
    st, perm = seeded_start2(tm, 0, form); key = jax.random.PRNGKey(5); mf = mean_field(tm, FULL); lstar = np.array(mf['lstar_per_place'])[perm]
    st = run_plain(eng, st, 0, 1500, key); Ls = []; t = 1500.0; k0 = int(1500 / DT)
    for i in range(600):
        st = run_plain(eng, st, t, 5.0, key, step0=k0 + i * 400); t += 5.0; Ls.append(np.array(st[4]))
    Ls = np.array(Ls); sm = summarize(eng, st, mirror_orbits=True)
    return dict(sig_h=sh, std_l=Ls.std(0).tolist(), mean_l=Ls.mean(0).tolist(), lstar=lstar.tolist(), median_std_bistable=float(np.median(Ls.std(0)[lstar > 1.0])), label=sm['label'], min_l=float(Ls.min()), max_l=float(Ls.max()))
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == 'hyst': json.dump(hyst(), open('../data/g2_hysteresis.json', 'w'), indent=1)
    else:
        from par import run_jobs
        res = run_jobs(sig_pilot, [(0.5,), (1.0,), (2.0,)], workers=3, label='sig'); json.dump(res, open('../data/g2_sigh_pilot.json', 'w'))
        for r in res: print(r['sig_h'], 'median std (bistable cells)', round(r['median_std_bistable'], 3), r['label'], 'l range', round(r['min_l'], 1), round(r['max_l'], 1))
