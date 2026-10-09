"""Viewer exemplars for Testbed v1 (S1, S2, S3/S4, I2 events, natural ensemble O1/O3). Declared exemplar rule: fixed seeds, no outcome-based selection."""
import sys, os, json; sys.path.insert(0, '.'); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'viz'))
from interface import *
import build_viewer_testbed as V
import s4
from s3common import setup, adult, T_ON
OUT = os.path.join(MORPH, 'viz', 'output', 'testbed'); entries = json.load(open(os.path.join(OUT, 'entries.json')))
def emit(name, title, rolls, sub='', audit_too=True):
    for aud in ((True, False) if audit_too else (False,)):
        p = V.build_html(rolls, f'{OUT}/{"audit" if aud else "observable"}/{name}.html', title, audit=aud, sub=sub)
        entries.append(dict(name=name, tier='audit' if aud else 'observable', title=title, path=os.path.relpath(p, os.path.join(MORPH, 'viz'))))

def types_of(C, alive): 
    ty = cell_types(C.T).copy(); ty[~alive] = 0; return ty

def roll_from_frames(label, frames, t, t0=0.0, events=None, role=True, extra_series=None):
    X = np.stack([f['X'] for f in frames]); ty = np.stack([types_of(f['C'], f['alive']) for f in frames])
    r = dict(label=label, t=np.asarray(t) - t0, X=np.where(ty[..., None] > 0, X, 0.0), types=ty)
    sp = np.r_[0, [np.linalg.norm((X[k] - X[k - 1])[ty[k] > 0], axis=1).mean() if (ty[k] > 0).any() else 0 for k in range(1, len(X))]]; r['series'] = dict(mean_step=sp, n_cells=ty.astype(bool).sum(1).astype(float))
    if events: r['events'] = events
    if role and 'MU' in frames[0]: r['role'] = np.stack([f['MU'].argmax(1) for f in frames])
    return r

def world_run(w, T, save=5.0):
    w.frames = []; w.snapshot(); w.run(T, save_every=save); return roll_from_frames('', w.frames, [f['t'] for f in w.frames], t0=w.frames[0]['t'])

def main():
    # S1 operating point: L and R adults under operating noise
    rolls = []
    for kind in ('L', 'R'):
        w = new_adult(kind, sig=0.02, key=1); r = world_run(w, 300.0, 5.0); r['label'] = f'adult form {kind} (operating point lp -8, sigma 0.02), seed 0'; rolls.append(r)
    emit('v1_s1_operating_point', 'S1 operating point: both forms under operating noise', rolls, sub='log pi_prior -8, log pi_s 2, sigma_x = sigma_c = 0.02, sigma_mu = 0. Plasticity target NOT met (SITUS_CALIBRATION.md).')
    # S2 correspondence
    w1 = new_adult('L'); r1 = world_run(w1, 60.0, 5.0); r1['label'] = 'form L'; w2 = new_adult('R'); r2 = world_run(w2, 60.0, 5.0); r2['label'] = 'form R (= mirror image)'
    emit('v1_s2_correspondence', 'S2: the two forms have the same position set and differ by an exchange of the types of 8 cells', [r1, r2], sub='Position-only rigid distance 0.0; type-free correspondence: 8 cells change type, 0 move; type-preserving correspondence: 8 cells move (mean 0.67, max 3.0).')
    # S3/S4: switch vs matched-dose wrong location vs sham (fate-bias fallback; the physical families gave no switch)
    t, eng = setup(); n, nc = t.n, t.nc; fin, perm = adult(t, eng, 0); key = jax.random.PRNGKey(0)
    def run_amps(label, amps, dur, T=400.0, save=10.0):
        per = int(round(save / eng.dt)); ns = per * int(T / save)
        out, tr = eng.run_ctl(fin, T_ON, eng.dt, ns, key, amps, T_ON, T_ON + dur, 5.0, save_every=per)
        X = np.concatenate([np.array(fin[0])[None], np.array(tr[0])]); C = np.concatenate([np.array(fin[1])[None], np.array(tr[1])]); MU = np.concatenate([np.array(fin[2])[None], np.array(tr[2])])
        fr = [dict(X=X[k], C=C[k], MU=MU[k], alive=np.ones(n, bool)) for k in range(len(X))]
        return roll_from_frames(label, fr, save * np.arange(len(X)))
    fb, lit = s4.make_fb(t, fin, 'both', 0.3, 'LR'); z = (jnp.zeros((n, nc)), jnp.zeros((n, nc)), jnp.zeros(n))
    ev = [dict(t0=0.0, t1=40.0, cells=[int(i) for i in np.where(lit > 0)[0]], label='light')]
    treated = run_amps('fate-bias light on the 8 body-row cells, b 0.3, 40 tu (treated)', z + (jnp.array(fb),), 40.0); treated['events'] = ev
    # wrong location, matched dose: same bias applied to the 8 tail-type cells (type 4), toward type-2/3 slots
    from asm import cell_types as ct_, type_vector as tv_
    ct = ct_(np.array(fin[1]).T); ty = tv_(t); fbw = np.zeros((n, n)); idx4 = np.where(ct == 4)[0]; half = idx4[:4]; other = idx4[4:]
    fbw[np.ix_(half, np.where(ty == 2)[0])] = 0.3; fbw[np.ix_(other, np.where(ty == 3)[0])] = 0.3
    wrong = run_amps('same dose, wrong location (8 tail cells) ', z + (jnp.array(fbw),), 40.0); wrong['events'] = [dict(t0=0.0, t1=40.0, cells=[int(i) for i in idx4], label='light')]
    sham = run_amps('sham (identical code path, amplitude 0)', z + (jnp.zeros((n, n)),), 40.0)
    emit('v1_s4_switch_vs_wrong_location_vs_sham', 'S4 fate-bias light: treated vs matched-dose wrong location vs sham (synced)', [treated, wrong, sham], sub='NO identity-preserving switch was obtained: treated body fragments/defects. Seed 0, deterministic.')
    # S3 physical actuator representative: secretion pulse at a head disc
    from s3common import masks
    M = masks(t, perm)['disc_head']; ext = np.zeros((n, nc)); ext[:, 2] = 1.0 * M; amps = (jnp.array(ext), jnp.zeros((n, nc)), jnp.zeros(n), jnp.zeros((n, n)))
    ph = run_amps('secretion of signal 3, head disc, amp 1, 20 tu (treated)', amps, 20.0); ph['events'] = [dict(t0=0.0, t1=20.0, cells=[int(i) for i in np.where(M > 0)[0]], label='pulse')]
    ph_s = run_amps('sham', (jnp.zeros((n, nc)), jnp.zeros((n, nc)), jnp.zeros(n), jnp.zeros((n, n))), 20.0)
    emit('v1_s3_physical_vs_sham', 'S3 physical actuator (secretion) vs sham', [ph, ph_s], sub='1728 forward runs of nine actuator families x eight spatial patterns: none gave the other form.')
    # I2 events: each with its matched no-event twin
    def pair(name, title, build_event, T=300.0, sub=''):
        a = new_adult('L', capacity=24, key=3); b = new_adult('L', capacity=24, key=3)
        build_event(a); ra = world_run(a, T, 5.0); rb = world_run(b, T, 5.0); ra['label'] = 'event'; rb['label'] = 'matched no-event twin (same seed, noise stream)'
        emit(name, title, [ra, rb], sub=sub)
    pair('v1_i2a_replacement', 'I2(a) single replacement (cell 3 -> naive cell, new id)', lambda w: w.replace(3))
    pair('v1_i2b_serial_replacement', 'I2(b) serial replacement (one cell every 100 tu until all 24 are new)', lambda w: None)   # placeholder replaced below
    entries.pop(); entries.pop()
    a = new_adult('L', capacity=24, key=3); b = new_adult('L', capacity=24, key=3); order = np.random.default_rng(0).permutation(24)
    a.frames = []; a.snapshot()
    for i in order[:24]: a.replace(int(i), seed=1); a.run(100.0, save_every=5.0)
    ra = roll_from_frames('serial replacement (24 events, interval 100 tu)', a.frames, [f['t'] for f in a.frames], t0=a.frames[0]['t']); rb = world_run(b, 100.0 * 24, 5.0); rb['label'] = 'matched no-event twin'
    T_ = min(len(ra['t']), len(rb['t'])); 
    for r in (ra, rb):
        for k in ('t', 'X', 'types', 'role'):
            if k in r: r[k] = r[k][:T_]
        r['series'] = {k: v[:T_] for k, v in r['series'].items()}
    emit('v1_i2b_serial_replacement', 'I2(b) Ship of Theseus: all 24 cells replaced serially', [ra, rb], sub='Outcome: body does not persist (DEFECT in 4/4 seeds, interval 100 and 400 tu).')
    def ex(w):
        i = 5; c = w.X[w.alive].mean(0); u = w.X[i] - c; u /= np.linalg.norm(u); w.extrude(i, 8.0 * u)
    pair('v1_i2c_extrusion', 'I2(c) extrusion of one cell (8 units outward)', ex)
    def cut(w):
        Tb = w.t.Xs[0][:, w.perm0].T; X = w.X; a_ = Tb - Tb.mean(0); b_ = X - X.mean(0); U, S, Vt = np.linalg.svd(a_.T @ b_); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        w.cut(Tb[:, 1] > 0, R @ np.array([0.0, 7.0]))
    pair('v1_i2d_cut', 'I2(d) cut: the two body halves moved 7 units apart', cut)
    for kinds, nm in ((('L', 'L'), 'LL'), (('L', 'R'), 'LR')):
        a1 = new_adult(kinds[0], key=1); b1 = new_adult(kinds[1], key=2); w = fuse(a1, b1, [9.0, 0.0]); r = world_run(w, 300.0, 5.0); r['label'] = f'fusion {nm}: two bodies placed 9 units apart'
        a2 = new_adult(kinds[0], key=1); b2 = new_adult(kinds[1], key=2); w2 = fuse(a2, b2, [40.0, 0.0]); r2 = world_run(w2, 300.0, 5.0); r2['label'] = 'twin: same bodies 40 units apart'
        emit(f'v1_i2e_fusion_{nm}', f'I2(e) fusion {nm}', [r, r2], sub='Bodies interpenetrate and both end defective.')
    # natural ensemble O1 vs O3
    ex_ = Experiment('L', seed=0, noise=0.02); ex_.w.run(100.0); ex_.t0 = ex_.w.time; ex_._observe(); ex_.run(150.0)
    rng = np.random.default_rng(0); perm4 = rng.permutation(4); fr = ex_.obs; O3 = render_O3(fr, rng, perm4)
    imgs = np.stack([o['img'][0] for o in O3]); lo, hi = np.percentile(imgs, 1), np.percentile(imgs, 99.5); u8 = (255 * np.clip((imgs - lo) / (hi - lo), 0, 1)).astype(np.uint8)[:, ::-1, :]
    rO1 = roll_from_frames('O1: tracked cells (arena coordinates, ids)', [dict(X=f['X'], C=f['C'], alive=f['alive']) for f in fr], [f['t'] for f in fr], role=False)
    rO3 = dict(label='O3: image of reporter 1 (96x96, PSF 0.5, SNR 20)', t=rO1['t'], X=rO1['X'], types=rO1['types'], img=u8, fov=12.0)
    emit('v1_natural_O1_vs_O3', 'Natural member: O1 tracked cells vs O3 image', [rO1, rO3], sub='Body placed at a hidden random rigid pose in the arena; the observer must locate it.')
    json.dump(entries, open(os.path.join(OUT, 'entries.json'), 'w'), indent=1); print(len(entries), 'entries')

if __name__ == '__main__': main()
