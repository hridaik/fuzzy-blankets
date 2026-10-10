import sys, json; sys.path.insert(0,'.')
from an2 import *
from g2cfg import *
tm = make_template2(); mf = mean_field(tm, FULL); json.dump(mf, open('../data/g2_meanfield.json','w'), indent=1)
print({k: (round(v,4) if isinstance(v,float) else v) for k,v in mf.items() if k not in ('Gmorph_per_place','lstar_per_place')})
print('G_morph per place', np.round(mf['Gmorph_per_place'],2)); print('l* per place', np.round(mf['lstar_per_place'],2))
P = Params2(**FULL); eng = make_engine2(tm, P); eng.dt = DT
res = {}
for form in 'LR':
    st, perm = seeded_start2(tm, 0, form); fin = run_plain(eng, st, 0, 2000, jax.random.PRNGKey(0)); s = summarize(eng, fin, pis=(FULL['pi_c'], FULL['pi_lam']))
    L = np.array(fin[4]); D = np.array(fin[2]); res[form] = dict(s, l_mean=float(L.mean()), l_min=float(L.min()), l_max=float(L.max()), d_mean=D.mean(0).tolist(), l_cells=L.tolist())
    print(form, {k: (round(v,3) if isinstance(v,float) else v) for k,v in s.items()}, 'l mean/min/max', L.mean().round(2), L.min().round(2), L.max().round(2), 'd', D.mean(0).round(3))
json.dump(res, open('../data/g2_fixedpoints.json','w'))
# (b) isolated cell and far-apart cells, from l=+-3 ; N=1 and N=2 (distance 40)
def relax(N, l0, T=600.0, dist=40.0, place=18):
    e = make_engine2(tm, P, N=N); e.dt = DT
    X = np.zeros((N, 2)); X[1:, 0] = dist * np.arange(1, N); C = np.tile(tm.CL[:, place], (N, 1)) if l0 > 0 else np.tile(tm.CR[:, place], (N, 1)); D = np.tile([1.0, 0.0] if l0 > 0 else [0.0, 1.0], (N, 1))
    MU = np.zeros((N, 24)); MU[:, place] = 8.0; L = np.full(N, l0)
    st = (jnp.array(X), jnp.array(C), jnp.array(D), jnp.array(MU), jnp.array(L)); ts = []; ls = []
    for k in range(int(T / 5)):
        st = run_plain(e, st, k * 5.0, 5.0, jax.random.PRNGKey(0), step0=k * 400); ls.append(np.array(st[4])[0])
    ls = np.array(ls); t = 5.0 * (1 + np.arange(len(ls)))
    # fit decay rate on |l| between 0.3 and 2.5
    m = (np.abs(ls) > 0.05) & (np.abs(ls) < 2.5); rate = -np.polyfit(t[:10], np.log(np.abs(ls[:10])), 1)[0]
    return dict(N=N, l0=l0, l_final=float(ls[-1]), rate=float(rate), q_max=float(np.array(jax.nn.softmax(st[3],1)).max()), l_series=ls[::8].tolist())
pw = int(np.argmax(tm.w)); pm = int(np.argmin(tm.w)); print('place w_max',pw,tm.w[pw],'w_min',pm,tm.w[pm])
b = [dict(relax(1, 3.0, place=pw), place=pw, w=float(tm.w[pw])), dict(relax(1, 3.0, place=pm), place=pm, w=float(tm.w[pm])), dict(relax(1, -3.0, place=pw), place=pw), relax(2, 3.0, place=pw), relax(2, -3.0, place=pw)]
for x in b: print({k: v for k, v in x.items() if k != 'l_series'})
print('pred rate (spec, w=1) 2r-G1/2 =', mf['relax_rate_isolated_pred']); print('pred (amplified) 2r-Giso/2: w_max', 2*FULL['r']-mf['G_iso_per_place'][pw]/2, 'w_min', 2*FULL['r']-mf['G_iso_per_place'][pm]/2)
json.dump(b, open('../data/g2_forget.json','w'))
