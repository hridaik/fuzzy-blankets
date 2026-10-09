import os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from interface import *

def _end(ex): return ex.w.X.copy(), ex.w.C.copy()

def test_pipette_bath_light_act_and_sham_is_null():
    base = Experiment('L', seed=0, noise=0.02, private={'L1': ('sec', 2)}); base.t0 = base.w.time; base.run(20.0, [])
    cen = base.w.X[base.w.alive].mean(0)
    for acts in ([dict(type='pipette', pos=cen.tolist(), ligand_index=2, amp=2.0, t_on=0.0, t_off=15.0, ramp=3.0)],
                 [dict(type='bath', ligand_index=2, amp=1.0, t_on=0.0, t_off=15.0, ramp=3.0)],
                 [dict(type='light', channel='L1', mask=Mask([('disc', float(cen[0]), float(cen[1]), 3.0, 1.0)]), amp=1.0, t_on=0.0, t_off=15.0, ramp=3.0)]):
        e1 = Experiment('L', seed=0, noise=0.02, private={'L1': ('sec', 2)}); e1.t0 = e1.w.time; e1.run(20.0, acts)
        e2 = Experiment('L', seed=0, noise=0.02, private={'L1': ('sec', 2)}); e2.t0 = e2.w.time; e2.run(20.0, acts, sham=True)
        assert np.abs(e1.w.C - base.w.C).max() > 1e-4           # the actuator acts
        assert np.abs(e2.w.C - base.w.C).max() < 1e-9 and np.abs(e2.w.X - base.w.X).max() < 1e-9   # sham = no treatment, same RNG consumption

def test_events_have_unique_permanent_ids():
    from world import new_adult
    w = new_adult('L', capacity=24); ids0 = set(w.cell_id.tolist())
    for i in (3, 3, 3): w.replace(i)
    assert len(set(w.cell_id.tolist())) == 24 and w.cell_id[3] == 26 and not ({24, 25} & set(w.cell_id.tolist())) and len([e for e in w.events if e['kind'] == 'replace']) == 3

def test_observable_renderers_have_no_ids_in_O2():
    rng = np.random.default_rng(0); fr = [dict(t=0.0, X=np.random.rand(24, 2), C=np.random.rand(24, 4), alive=np.ones(24, bool), cell_id=np.arange(24))]
    assert 'id' not in render_O2(fr, rng, np.arange(4))[0] and render_O3(fr, rng, np.arange(4))[0]['img'].shape == (2, IMG_PX, IMG_PX)
