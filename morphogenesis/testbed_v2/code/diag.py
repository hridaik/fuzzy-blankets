import sys, json; sys.path.insert(0, '.')
from an2 import *; from g2cfg import *; from g3 import setup, disc_cells, RAMP
# (1) dt convergence (deterministic, from a perturbed seeded start, 200 tu, full model)
tm = make_template2(); st, perm = seeded_start2(tm, 0, 'L', jit_x=0.3); res = {}
ref = None
for dt in (0.025, 0.0125, 0.00625, 0.003125):
    eng = make_engine2(tm, Params2(**FULL)); eng.dt = dt; fin = run_plain(eng, st, 0, 200.0, jax.random.PRNGKey(0), dt=dt); res[dt] = fin
ref = res[0.003125]
dtc = {dt: max(float(jnp.abs(a - b).max()) for a, b in zip(f, ref)) for dt, f in res.items()}; print('dt convergence (max abs error vs dt=0.003125):', dtc)
# (2) Kramers table per place: U(l) = 2r cosh l - 2G ln cosh(l/2), G = G_mem + G_morph_k
mf = mean_field(tm, FULL); r = FULL['r']; sig = 1.0; rows = []
for k in range(24):
    G = mf['G_mem'] + mf['Gmorph_per_place'][k]
    if G <= 4 * r: rows.append((k, G, None, None)); continue
    l = float(mf['lstar_per_place'][k]); U = lambda x: 2 * r * np.cosh(x) - 2 * G * np.log(np.cosh(x / 2)); dU = U(0) - U(l)
    U2s = 2 * r * np.cosh(l) - G / (2 * np.cosh(l / 2) ** 2) * 1.0; U20 = 2 * r - G / 2    # U'' at l*, at 0
    rate = np.sqrt(abs(U2s * U20)) / (2 * np.pi) * np.exp(-2 * dU / sig ** 2); rows.append((k, G, dU, rate))
print('Kramers (sigma_h=1) per place: (place, G, dU, rate/tu)'); [print(x) for x in rows]
json.dump(dict(dt=dtc, kramers=rows), open('../data/diag.json', 'w'), default=float)
# (3) G3 mechanism: whole-body, amp 8, 160 tu (no tearing): per-cell min rho
eng, st0, perm, tm = setup('L'); n = 24
ext = np.zeros((n, NL)); ext[:, 5] = 8.0; amps = (jnp.array(ext), jnp.zeros((n, NL)), jnp.zeros(n), jnp.zeros((n, 24)), jnp.ones(n))
fin, tr = eng.run_ctl(st0, 0.0, DT, int(round(260 / DT / 160)) * 160, jax.random.PRNGKey(0), amps, 0.0, 160.0, RAMP, save_every=160)
rho = 1 / (1 + np.exp(-np.array(tr[4]))); rho0 = 1 / (1 + np.exp(-np.array(st0[4])))
gm = np.array(mf['Gmorph_per_place'])[perm]
print('whole-body mR amp 8 for 160 tu: per-cell min rho during forcing vs start (cells sorted by G_morph):')
for c in np.argsort(gm): print(f'place {perm[c]:2d} G_morph {gm[c]:6.2f} rho0 {rho0[c]:.2f} min rho {rho[:, c].min():.2f}')
print('max disp vs start', float(np.linalg.norm(np.array(tr[0]) - np.array(st0[0]), axis=2).max()))
