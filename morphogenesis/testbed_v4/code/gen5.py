"""Package-v4 raw run generators (pickles in ../data/raw_v5/<family>/). Families: natural (population dishes), stress (identity events, CRN triplets event/twin/sham),
damage (all five lights above damage onset, matched twin + sham), switch (below / at / above threshold, wrong location, sham)."""
import sys, os, json, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface4 import *
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw_v5'); G_MED = 4 * R_ * KG_MED
NAT_T = 3000.0
def _save(fam, name, obj):
    os.makedirs(os.path.join(RAW, fam), exist_ok=True); p = os.path.join(RAW, fam, name + '.pkl'); pickle.dump(obj, open(p, 'wb'), protocol=4); return p
def _ex(dish, state, seed, private=None, form_seed=0, noise=True): return Experiment4(state, seed=seed, noise=noise, dish=dish, variant='phi04', private=private or {}, form_seed=form_seed)
def job_natural(dseed, state, tag):
    d = sample_dish(dseed); ex = _ex(d, state, dseed, form_seed=dseed % 7); ex.run(300.0, observe=False); ex.t0 = ex.w.time; ex.obs = []; ex.base_nbr = nbr_matrix(ex.w.X)
    ex.run_sched(NAT_T, obs_times=obs_schedule(NAT_T)); return _save('natural', f'{state}_{tag}_{dseed:05d}', dict(frames=ex.obs, hidden=ex.hidden(), state=state, seed=dseed, tag=tag, dish=d))
def _axis(X):
    c = X.mean(0); u, s, vt = np.linalg.svd(X - c); return c, vt[0], vt[1]
def job_stress(scn, state, dseed, T=600.0, t_ev=50.0):
    d = sample_dish(dseed); out = {}
    for arm in ('event', 'twin', 'sham'):
        ex = _ex(d, state, dseed, form_seed=dseed % 7); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []; ex.base_nbr = nbr_matrix(ex.w.X); X0 = ex.w.X.copy(); acts = []
        if scn.startswith('fuse'):
            kind, st2, offs = scn.split('|'); off = [float(v) for v in offs.split(',')]; ex2 = _ex(d, st2, dseed + 500, form_seed=(dseed + 3) % 7); ex2.run(100.0, observe=False)
            w = fuse_worlds(ex.w, ex2.w, off if arm == 'event' else [14.0, 14.0]); w.key = jax.random.PRNGKey(9000 + dseed); ex.w = w; ex.t0 = w.time; ex.obs = []
            if arm == 'sham': ex.log.append(dict(t=float(w.time), kind='sham_fuse'))
            dense = (0.0, 100.0)
        else:
            c, u1, u2 = _axis(X0); i = int(np.argsort(np.linalg.norm(X0 - c, axis=1))[3 + dseed % 5])
            if scn == 'replace3':
                idxs = [int(np.argsort(np.linalg.norm(X0 - c, axis=1))[k]) for k in (2 + dseed % 4, 9, 17)]; acts = [dict(type='surgery', op='replace', pos=X0[j].tolist(), t=t_ev + 100 * q) for q, j in enumerate(idxs)]; dense = (t_ev - 20, t_ev + 300)
            elif scn == 'extrude':
                v = X0[i] - c; v = 8.0 * v / np.linalg.norm(v); acts = [dict(type='tweezers', pos=X0[i].tolist(), vec=v.tolist(), t=t_ev)]; dense = (t_ev - 20, t_ev + 100)
            else:
                n = u1 if scn == 'cutx' else u2; acts = [dict(type='surgery', op='cut', normal=n.tolist(), d=float(c @ n), vec=(7.0 * n).tolist(), t=t_ev)]; dense = (t_ev - 20, t_ev + 100)
        ex.run_sched(T, acts if arm != 'twin' else [], sham=(arm == 'sham'), obs_times=obs_schedule(T, dense)); out[arm] = dict(frames=ex.obs, hidden=ex.hidden(), n=ex.w.N, dense=dense)
    return _save('stress', f'{scn.replace("|", "_").replace(",", "x")}_{state}_{dseed:05d}', dict(arms=out, scn=scn, state=state, seed=dseed, dish=d))
def _thr(dish, state, centre, dur):
    from lib4 import bisect_switch
    return bisect_switch(dish, 'phi04', state, centre, dur)
def _centre_place(centre):
    """place index nearest the named centre in the undeformed template"""
    c = CENTRES[centre]; return int(np.argmin(np.linalg.norm(TM.Xs.T - c[None], axis=1)))
def job_switch(dseed, state, centre, dm, kinds=('below', 'at', 'above', 'wrong', 'sham'), t_on=40.0, T_after=100.0):
    d = sample_dish(dseed); dur = dm / G_MED; thr = _thr(d, state, centre, dur)['thr']; far = {'middle': 'tail_end', 'limb_side': 'head_end', 'tail_end': 'middle', 'head_end': 'limb_side', 'whole': 'tail_end'}[centre]
    ch = 'MB' if state == 'a' else 'MA'; out = []
    for kind in kinds:
        ex = _ex(d, state, dseed * 10 + len(out), private={ch: CH[ch]}, form_seed=dseed % 7); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []; ex.base_nbr = nbr_matrix(ex.w.X)
        perm = ex.w.perm0; lit = lit_cells(perm, centre if kind != 'wrong' else far); amp = thr * dict(below=0.7, at=1.0, above=1.4, wrong=1.4, sham=1.4)[kind]; ramp = min(5.0, dur / 4)
        cen = CENTRES[centre if kind != 'wrong' else far]; c0 = ex.place_in_arena(_centre_place(centre if kind != 'wrong' else far)) if cen is not None else ex.w.X.mean(0)
        # light mask = disc around the arena image of the named centre point (r = 1.5); whole body: all
        mask = Mask([('all', 1.0)]) if centre == 'whole' and kind != 'wrong' else Mask([('disc', c0[0], c0[1], 1.5, 1.0)])
        act = [dict(type='light', channel=ch, mask=mask, amp=amp, t_on=t_on, t_off=t_on + dur, ramp=ramp)]; T = t_on + dur + T_after
        ex.run_sched(T, act, sham=(kind == 'sham'), obs_times=obs_schedule(T, (t_on - 20.0, t_on + dur + T_after)))
        meta = dict(state=state, centre=centre, dm=dm, dur=dur, kind=kind, amp=amp, thr=thr, disc_xy0=[float(x) for x in c0], radius=1.5, t_on=t_on, t_off=t_on + dur, ramp=ramp, channel=ch, dseed=dseed, n_lit=int(lit.sum()))
        out.append(_save('switch', f'{state}_s{dseed}_{centre}_{dm}_{kind}', dict(frames=ex.obs, hidden=ex.hidden(), meta=meta, dish=d)))
    return out
def job_damage(dseed, light, centre, dm, state='a', onset=None, mult=1.5, T_post=300.0, t_on=40.0):
    """light in MA/MB/SEC/RG/MIG at mult x the dish's damage onset amplitude (from the chi table); arms event / twin / sham"""
    from v5 import chi_table
    d = sample_dish(dseed) if dseed >= 0 else median_dish(); dur = dm / G_MED
    if onset is None:
        chi = chi_table(json.load(open(os.path.join(DATA, 'v5_chi_L0.json')))); onset = chi(d['kappa_g'], centre, dm) / (gamma0() * d['gamma_factor'])
    amp = mult * onset; ch = light if light in CH else None; out = {}
    for arm in ('event', 'twin', 'sham'):
        ex = _ex(d, state, abs(dseed) * 10 + 1, private={light: CH[light]}, form_seed=abs(dseed) % 7); ex.run(100.0, observe=False); ex.t0 = ex.w.time; ex.obs = []; ex.base_nbr = nbr_matrix(ex.w.X)
        cen = CENTRES[centre]; c0 = ex.place_in_arena(_centre_place(centre)); mask = Mask([('disc', c0[0], c0[1], 1.5, 1.0)]); ramp = min(5.0, dur / 4)
        act = [dict(type='light', channel=light, mask=mask, amp=amp, t_on=t_on, t_off=t_on + dur, ramp=ramp)]; T = t_on + dur + T_post
        ex.run_sched(T, act if arm != 'twin' else [], sham=(arm == 'sham'), obs_times=obs_schedule(T, (t_on - 20.0, t_on + dur + 100.0))); out[arm] = dict(frames=ex.obs, hidden=ex.hidden(), n=ex.w.N)
    meta = dict(state=state, centre=centre, dm=dm, dur=dur, light=light, amp=amp, onset=onset, mult=mult, disc_xy0=[float(x) for x in c0], radius=1.5, t_on=t_on, t_off=t_on + dur, ramp=ramp, dseed=dseed)
    return _save('damage', f'{light}_s{dseed}_{centre}_{dm}', dict(arms=out, meta=meta, dish=d))
