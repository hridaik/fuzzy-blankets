import sys,json,os,numpy as np; sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','code'))
from t5mon import io
from t5mon.monitor import OnlineMonitor
CFG=os.path.join(os.path.dirname(__file__),'..','MONITOR_CONFIG.json')
def frames(run,n): return io.o1_frames(run)[:n]
def test_causal():
    run=io.natural('development')[0]['run']; fr=frames(run,80)
    a=OnlineMonitor(CFG); oa=[a.update(f['t'],f['xy'],f['lev'],f['ids']) for f in fr[:60]]
    b=OnlineMonitor(CFG); ob=[b.update(f['t'],f['xy'],f['lev'],f['ids']) for f in fr[:80]]
    assert all(x['state']==y['state'] and x['pat_dz']==y['pat_dz'] and x['V_body']==y['V_body'] for x,y in zip(oa,ob[:60]))
def test_natural_pure_and_ok():
    for r in io.natural('development')[:4]:
        m=OnlineMonitor(CFG); o=[m.update(f['t'],f['xy'],f['lev'],f['ids']) for f in io.o1_frames(r['run'],20)[:100]]
        assert all(x['state_sure'] for x in o[5:]) and o[-1]['V_body_conservative'] and not any(x['events'] for x in o)
def test_state_change_is_not_identity_loss():
    # mirror-reflect the body (state flip is a mirror partner): geometry/material verdicts unchanged
    run=io.natural('development')[0]['run']; fr=frames(run,40)
    m=OnlineMonitor(CFG); o=[m.update(f['t'],f['xy']*np.array([1,-1]),f['lev'],f['ids']) for f in fr]
    assert o[-1]['V_body']
def test_loss_event_detected():
    run=io.natural('development')[0]['run']; fr=frames(run,40)
    m=OnlineMonitor(CFG)
    for f in fr[:20]: m.update(f['t'],f['xy'],f['lev'],f['ids'])
    f=fr[20]; o=m.update(f['t'],f['xy'][1:],f['lev'][1:],f['ids'][1:])
    assert 'LOSS' in o['events'] and not o['V_body'] and not o['V_body_conservative']
def test_extrusion_detected():
    run=io.natural('development')[0]['run']; fr=frames(run,40); m=OnlineMonitor(CFG)
    for f in fr[:20]: m.update(f['t'],f['xy'],f['lev'],f['ids'])
    f=fr[20]; xy=f['xy'].copy(); xy[0]+=np.array([12.,0]); o=m.update(f['t'],xy,f['lev'],f['ids'])
    assert 'EXTRUSION' in o['events'] and not o['geometry_ok']
if __name__=='__main__':
    for k,v in list(globals().items()):
        if k.startswith('test_'): v(); print('ok',k)
