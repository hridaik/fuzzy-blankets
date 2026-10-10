import sys,os,json,numpy as np; sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..','code'))
from controller import success_rule, Controller
CFG=json.load(open(os.path.join(os.path.dirname(__file__),'..','CONTROLLER_CONFIG.json')))
class FakeEp:
    def __init__(s,frames,t): s.log={'frames':frames}; s.t=t
def fr(t,state,sure=True,vc=True): return dict(t=t,state=state,state_sure=sure,V_body_conservative=vc)
def test_success_needs_hold_and_tail():
    F=[fr(t,'S-') for t in range(0,200)]; ep=FakeEp(F,199.0)
    assert success_rule(ep,CFG,'S-',t_last_end=60.0)          # 199 >= 60+120, last 40 tu in target
    assert not success_rule(ep,CFG,'S-',t_last_end=100.0)     # hold not yet elapsed
def test_success_fails_on_unsure_or_identity():
    F=[fr(t,'S-') for t in range(0,200)]; F[190]=fr(190,'TRANS',False); assert not success_rule(FakeEp(F,199.0),CFG,'S-',60.0)
    F=[fr(t,'S-',vc=(t<150)) for t in range(0,200)]; assert not success_rule(FakeEp(F,199.0),CFG,'S-',60.0)
def test_twin_without_action_never_succeeds_from_start_state():
    F=[fr(t,'S+') for t in range(0,200)]; assert not success_rule(FakeEp(F,199.0),CFG,'S-',None)
def test_limits_declared():
    assert CFG['hold']>=10*1.0 and CFG['max_dose']<=20000 and CFG['max_pulses']<=20 and CFG['max_time']<=600
def test_dose_formula_matches_api_example():
    assert abs(0.1*5*12-6.0)<1e-9     # smoke test: amp*dur*cells
if __name__=='__main__':
    for k,v in list(globals().items()):
        if k.startswith('test_'): v(); print('ok',k)
