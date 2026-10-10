"""Viewer exemplars for testbed v2 (declared exemplar rule: FIXED seeds / fixed doses, no outcome-based selection; stated in each title).
Reuses morphogenesis/viz/build_viewer_testbed.py (unmodified) with its strings patched in memory for the v2 ring/heatmap semantics. Output: ../viewer/*.html"""
import sys, os, json; sys.path.insert(0, '.'); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'viz'))
from world2 import *
from g2cfg import FULL, G1, DT, mean_field
import build_viewer_testbed as V
V.TEMPLATE = V.TEMPLATE.replace('plan-B ring', 'handedness ring (red = P(L) high, blue = P(R) high)').replace('target overlay', 'template overlay').replace('memory-ligand heatmap', 'memory-ligand heatmap (mL for L-panels, as given in the panel title)')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'viewer'); os.makedirs(OUT, exist_ok=True)

def frames_to_roll(label, frames, t0, lig_idx=None, events=None, series=None, tm=None):
    t = np.array([f['t'] - t0 for f in frames]); X = np.stack([f['X'] for f in frames]); C = np.stack([f['C'] for f in frames]); D = np.stack([f['D'] for f in frames]); L = np.stack([f['L'] for f in frames]); al = np.stack([f['alive'] for f in frames])
    types = np.stack([cell_types(c.T) * a for c, a in zip(C, al)]); rho = 1 / (1 + np.exp(-L)); MU = np.stack([f['MU'] for f in frames])
    r = dict(label=label, t=t, X=np.where(al[:, :, None], X, 0.0), types=types, planB=rho * al, role=MU.argmax(2))
    if lig_idx is not None: r['ligand'] = dict(kappa=1.0, C=D[:, :, lig_idx] * al)
    if events: r['events'] = events
    ser = dict(mean_rho_L=(rho * al).sum(1) / al.sum(1))
    if series: ser.update(series)
    r['series'] = ser
    r['audit_series'] = dict(mean_maxbel=(np.stack([np.exp(m - m.max(1, keepdims=True)) / np.exp(m - m.max(1, keepdims=True)).sum(1, keepdims=True) for m in MU]).max(2) * al).sum(1) / al.sum(1))
    return r

def roll_world(w, label, T, every, lig_idx=0, events_fn=None, ev_cells=None, t_rel=True, series_fn=None):
    t0 = w.time; w.frames = []; w.snapshot(); w.run(T, save_every=every); fr = w.frames
    r = frames_to_roll(label, fr, t0, lig_idx)
    if series_fn: r['series'].update(series_fn(fr))
    return r

def emit(name, title, rolls, sub=''):
    p = V.build_html(rolls, os.path.join(OUT, name + '.html'), title, audit=True, sub=sub); print(p); return p

def dL_series(tm):
    def f(fr): return dict(typed_dist_to_L=np.array([classify_shape(tm, x['X'][x['alive']], x['C'][x['alive']])[1] for x in fr]))
    return f

def main():
    tm = make_template2()
    # ---------------- G1: durability (rho fixed 1, memory off), noise, 3000 tu, fixed seed 0
    from g1b import OP, DT as DT1
    P = Params2(fix_rho=1.0, sig_x=0.02, sig_c=0.02, sig_mu=0.02, **OP); eng = make_engine2(tm, P); eng.dt = DT1
    st, perm = seeded_start2(tm, 0, 'L'); w = World2(tm, eng, st, perm, key=1000); w.time = 0.0
    r = roll_world(w, 'G1 categorical body L, noise sigma_x=sigma_c=sigma_mu=0.02, seed 0 (3000 tu; 20000 tu x 10 seeds: 0 dissolutions)', 3000.0, 25.0, lig_idx=None, series_fn=dL_series(tm))
    emit('g1_durability', 'v2 G1 - categorical identity, durable under noise', [r], sub='fixed seed 0; hidden tier overlays ON')
    # ---------------- G2: forget vs remember
    rolls = []
    for form in 'LR':
        w = new_adult2(form, k=0, noise=0.02, sig_h=1.0, key=11); w.time = 0.0
        rolls.append(roll_world(w, f'G2 body {form} (noise incl. sigma_h = 1; fixed seed 11); ring = P(L); heatmap = mL' if form == 'L' else 'G2 body R (same noise, seed 11); heatmap = mL (low)', 1500.0, 15.0, lig_idx=0 if form == "L" else 1, series_fn=dL_series(tm)))
    # isolated cell from l = +3 (single cell, place 8 (w_max), body-row type), N=1
    e1 = make_engine2(tm, Params2(**FULL), N=1); e1.dt = DT; pl = 8
    st = (jnp.array([[0.0, 0.0]]), jnp.array(tm.CL[:, [pl]].T), jnp.array([[1.0, 0.0]]), jnp.array(np.eye(24)[[pl]] * 8.0), jnp.array([3.0]))
    w1 = World2(tm, e1, st, None); w1.time = 0.0; rolls.append(roll_world(w1, 'G2 isolated cell, l(0) = +3: forgets (rho -> 0.5)', 600.0, 6.0, lig_idx=0))
    emit('g2_forget_vs_remember', 'v2 G2 - the body remembers, a cell forgets', rolls, sub='bodies L and R (noise) vs isolated cell; ring colour = P(L)')
    # ---------------- G3: attempted switch vs wrong location vs sham (synced)
    rolls = []
    perm_ = None
    def g3_roll(label, centre, amp, dur=40.0, sham=False, T=400.0):
        w = new_adult2('L', k=0, noise=0, key=0); w.time = 0.0; lit = np.zeros(24, bool)
        from g3 import disc_cells; lit = disc_cells(tm, w.perm0, centre)
        ext = np.zeros((24, NL)); ext[lit, 5] = 0.0 if sham else amp; amps = (jnp.array(ext), jnp.zeros((24, NL)), jnp.zeros(24), jnp.zeros((24, 24)), jnp.ones(24))
        t0 = w.time; fr = []; w.frames = []; w.snapshot()
        eng = w.eng; per = int(round(4.0 / DT)); n1 = int(round(T / DT / per)) * per
        fin, tr = eng.run_ctl(w.state(), 0.0, DT, n1, w.key, amps, 0.0, dur, 5.0, save_every=per)
        fr = [dict(t=0.0, X=w.X, C=w.C, D=w.D, MU=w.MU, L=w.L, alive=w.alive)] + [dict(t=(k + 1) * per * DT, X=np.array(tr[0][k]), C=np.array(tr[1][k]), D=np.array(tr[2][k]), MU=np.array(tr[3][k]), L=np.array(tr[4][k]), alive=w.alive) for k in range(len(tr[0]))]
        r = frames_to_roll(label, fr, 0.0, 1, events=[dict(t0=0.0, t1=dur, cells=[int(i) for i in np.where(lit)[0]], label='lit')] if not sham else None, series=None)
        r['series']['typed_dist_to_L'] = np.array([classify_shape(tm, f['X'], f['C'])[1] for f in fr]); return r
    rolls = [g3_roll('G3 light on place 12 (limb row), amp 2 on mR, 40 tu, ramp 5', 12, 2.0), g3_roll('G3 wrong location: place 22 (tail corner), same dose', 22, 2.0),
             g3_roll('G3 place 12, amp 8 (above movement limit 0.3)', 12, 8.0), g3_roll('G3 sham (same code path, amp 0)', 12, 0.0, sham=True)]
    emit('g3_switch_attempt', 'v2 G3 - memory-light attempt vs wrong location vs sham (NO switch found)', rolls, sub='L -> R attempt; heatmap = mR (the opposing memory ligand); fixed doses stated in titles')
    # ---------------- G4: events
    rolls = []
    w = new_adult2('L', capacity=24, noise=0, key=3); w.time = 0.0; w.replace(12, seed=12); rolls.append(roll_world(w, 'G4 single replacement of cell at place %d (cell 12)' % w.perm0[12], 400.0, 8.0, series_fn=dL_series(tm)))
    w = new_adult2('L', capacity=24, noise=0, key=3); w.time = 0.0; c = w.X.mean(0); u = w.X[5] - c; w.extrude(5, 8.0 * u / np.linalg.norm(u)); rolls.append(roll_world(w, 'G4 extrusion of cell 5 by 8 units', 300.0, 6.0, series_fn=dL_series(tm)))
    def cut_roll(kind, T=60.0):
        w = new_adult2('L', capacity=24, noise=0, key=0); w.time = 0.0; Tb = w.tm.Xs[:, w.perm0].T; mask = (Tb[:, 1] > 0) if kind == 'y' else (Tb[:, 0] > 0)
        a_ = Tb - Tb.mean(0); b_ = w.X - w.X.mean(0); U, S, Vt = np.linalg.svd(a_.T @ b_); R = Vt.T @ U.T
        if np.linalg.det(R) < 0: Vt[-1] *= -1; R = Vt.T @ U.T
        w.cut(mask, R @ np.array([0.0, 7.0] if kind == 'y' else [7.0, 0.0])); return roll_world(w, f'G4 cut along the {kind} axis, separation 7: fragments drift apart ({T:.0f} tu)', T, 1.0)
    emit('g4_cut', 'v2 G4 - cut: the fragments keep their handedness but drift apart', [cut_roll('y'), cut_roll('x')], sub='deterministic; ring = P(L)')
    a = new_adult2('L', capacity=24, noise=0, key=1); b = new_adult2('R', k=1, capacity=24, noise=0, key=2); wf = fuse2(a, b, [8.0, 0.0]); wf.time = 0.0; rolls.append(roll_world(wf, 'G4 fusion L + R, offset (8, 0)', 800.0, 10.0))
    a = new_adult2('L', capacity=24, noise=0, key=1); b = new_adult2('L', k=1, capacity=24, noise=0, key=2); wf = fuse2(a, b, [8.0, 0.0]); wf.time = 0.0; rolls.append(roll_world(wf, 'G4 fusion L + L, offset (8, 0)', 800.0, 10.0))
    emit('g4_identity_events', 'v2 G4 - identity events (replacement, extrusion, cut, L+R fusion)', rolls, sub='deterministic; ring = P(L); series: mean P(L)')
if __name__ == "__main__": main()
