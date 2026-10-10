"""Online closed-loop controller for collective-state change (T5). Uses the frozen monitor via rig.Ep; every decision at time t
uses only observations up to t. Policy: escalating short pulses at the body centre with commit detection."""
import sys,json,numpy as np; sys.path.insert(0,'code')
from rig import *
def dev_of(m,u0,s0): return -s0*(m['u'][0]-u0)
class Controller:
    def __init__(self,cfg): self.c=cfg if isinstance(cfg,dict) else json.load(open(cfg))
    def run(self,d,seed,pool='development',tag='ctrl',logdir='episodes',skip_if=None):
        c=self.c; ep=Ep(d,pool=pool,seed=seed,tag=tag,logdir=logdir,baseline_tu=c['baseline_tu'],dt=c['dt_obs'])
        S=dict(episode=ep.id,seed=ep.seed,pool=pool,tag=tag,start=ep.base_state,success=False,reason=None,n_pulses=0,dose=0.0,t_first_action=None,t_last_end=None,t_success=None,probes=0)
        F=ep.log['frames']; base=F[-1]
        if base['state']=='TRANS' or not base['state_sure'] or not base['V_body']:
            S['reason']='baseline_not_clean'; ep.decide(action='none',reason='baseline state not sure or body not valid'); return self._finish(ep,S)
        if skip_if and skip_if(base['state']):
            S['reason']='quota_skip'; ep.decide(action='none',reason='direction quota already filled (decided before any action)'); return self._finish(ep,S)
        s0=1.0 if base['state']=='S+' else -1.0; target='S-' if s0>0 else 'S+'; lab=c['actuator'][base['state']]
        u0=float(np.median([f['u'][0] for f in F[-10:]])); S['target']=target; S['label']=lab; S['u0']=u0
        ep.decide(action='plan',reason=f"start {base['state']} (u0={u0:.2f}); target {target}; actuator {lab}; location body-centre r={c['radius']}")
        k=0; amp=c['amp0']; committed=False; peak_prev=0.0; prod_hist=[]
        t_hard=c['max_time']; bad=0
        while ep.t<t_hard:
            m=ep.last; bad=0 if m['V_body_now'] else bad+1
            if m['events'] or bad>=c['abort_persist']:
                S['reason']='abort_identity'; ep.decide(action='abort',reason=f"body-identity axis left envelope (events={m['events']}, geo_ok={m['geometry_ok']}, material_ok={m['material_ok']})"); break
            if not committed and k<c['max_pulses'] and S['dose']<c['max_dose'] and (ep.t < c['t_act_end']):
                amp=float(min(amp,c['amp_max']))
                r=ep.act(lab,c['p'],c['q'],c['radius'],amp,c['dur'],c['ramp'],reason=f"pulse {k+1}: amp {amp:.2f} dur {c['dur']}")
                S['dose']+=r['dose']; k+=1; S['n_pulses']=k; S['t_first_action']=S['t_first_action'] or ep.t
                ep.decide(action='act',amp=amp,reason=f"pulse {k}: escalation step, last peak dev {peak_prev:.2f}")
                t_rel=ep.t+c['dur']; ep.run_until(t_rel); t_end=ep.t; S['t_last_end']=t_end
                ep.run_until(t_rel+c['wait'])
                def trace():
                    Fr=ep.log['frames']; tt=np.array([f['t'] for f in Fr]); dv=np.array([-s0*(f['u'][0]-u0) for f in Fr]); return Fr,tt,dv
                Fr,tt,dv=trace()
                # while the response is still rising and below the commit level, keep watching (bounded): near threshold the peak lags the release
                while ep.t<t_rel+c['wait_max'] and dv[-1]<c['commit_dev'] and dv[-1]>dv[-4]+0.01 and dv[-1]>c['rising_min']:
                    ep.advance(c['dt_obs']); Fr,tt,dv=trace()
                seg=(tt>=t_rel-c['dur']); pk=float(dv[seg].max()); now=float(dv[-1]); rel=float(dv[tt<=t_rel][-1])
                peak_prev=pk; S['probes']+=1
                if now>=c['commit_dev']:
                    committed=True; ep.decide(action='commit',reason=f"dev now {now:.2f} (release {rel:.2f}, peak {pk:.2f}): past the barrier -> stop acting, wait for the state to settle")
                else:
                    g=max(pk,0.05)/max(amp*c['dur'],1e-9)          # observed gain (dev per unit product)
                    need=c['target_dev']/g if not c.get('use_cue') else self._cue_need(c,Fr,t_rel,pk,amp)
                    nxt=float(np.clip(need/c['dur'],amp*c['esc_min'],amp*c['esc_max'])) if not c.get('chain') else amp*c['chain_growth']
                    ep.decide(action='escalate',reason=f"sub-threshold: peak dev {pk:.2f}, now {now:.2f}; gain {g:.4f}/unit -> next amp {nxt:.2f}")
                    amp=nxt
                continue
            if committed and ep.t>S['t_last_end']+c['uncommit_after'] and -s0*(m['u'][0]-u0)<c['uncommit_dev']:
                committed=False; amp=amp*c['esc_min']; ep.decide(action='uncommit',reason=f"response fell back to dev {-s0*(m['u'][0]-u0):.2f} without settling in target: resume pulses")
                continue
            # waiting / checking success
            ok=self._success(ep,S,target)
            if ok: S['success']=True; S['t_success']=ep.t; S['reason']='success'; break
            ep.advance(c['dt_obs'])
        else:
            S['reason']=S['reason'] or 'time_limit'
        if S['reason'] is None: S['reason']='unknown'
        return self._finish(ep,S)
    def _cue_need(self,c,Fr,t_rel,pk,amp):
        # response-slowing cue: half-recovery time after the pulse -> estimated fraction of the way to threshold
        tt=np.array([f['t'] for f in Fr]); dv=np.array([-f['u'][0] for f in Fr])
        return c['target_dev']/max(pk,0.05)*amp*c['dur']
    def _success(self,ep,S,target):
        c=self.c
        if S['t_last_end'] is None: return False
        if ep.t<S['t_last_end']+c['hold']: return False
        F=ep.log['frames']; w=[f for f in F if f['t']>ep.t-c['hold_tail']-1e-9]
        return all(f['state']==target and f['state_sure'] for f in w) and F[-1]['V_body_conservative']
    def _finish(self,ep,S):
        F=ep.log['frames']; S.update(V_body=bool(F[-1]['V_body']),V_body_conservative=bool(F[-1]['V_body_conservative']),events=sorted({e for f in F for e in f['events']}),end_state=F[-1]['state'],end_sure=bool(F[-1]['state_sure']),t_end=ep.t,
            time_to_success=(S['t_success']-S['t_first_action']) if S['t_success'] and S['t_first_action'] else None)
        ep.log['summary']=S; ep.end(); return S

# ---------------------------------------------------------------- replay arms (twin / sham / fixed / random / whole)
def success_rule(ep,cfg,target,t_last_end):
    """Same SUCCESS rule as the controller; t_last_end None => no action (twin)."""
    F=ep.log['frames']; w=[f for f in F if f['t']>ep.t-cfg['hold_tail']-1e-9]
    ok_state=all(f['state']==target and f['state_sure'] for f in w)
    ok_hold=(t_last_end is None) or (ep.t>=t_last_end+cfg['hold']-1e-9)
    return bool(ok_state and ok_hold and F[-1]['V_body_conservative'])
def replay(d,seed,cfg,plan,t_end,start_state,pool='development',sham_of=None,tag='arm',logdir='episodes',rng=None):
    """plan: list of dict(t, mode in {'body','whole','random_dose'}, label, p,q,radius,amp,dur,ramp,dose_target).
    Pulse times are absolute episode times (baseline_tu is observed first)."""
    ep=Ep(d,pool=pool,seed=seed,sham_of=sham_of,tag=tag,logdir=logdir,baseline_tu=cfg['baseline_tu'],dt=cfg['dt_obs'])
    target='S-' if ep.base_state=='S+' else 'S+'
    last_end=None; dose=0.0; ncell=[]
    for a in sorted(plan,key=lambda a:a['t']):
        ep.run_until(a['t'])
        if a['mode']=='whole':
            r=ep.act(a['label'],0,0,0,a['amp'],a['dur'],a['ramp'],reason=tag,whole=True)
        else:
            p,q,rad,amp=a['p'],a['q'],a['radius'],a['amp']
            if a['mode']=='random_dose':
                c,e1,e2=ep.frame(); X=(ep.xy-c); P=X@e1; Q=X@e2
                j=int(rng.integers(len(P))); p,q=float(P[j]),float(Q[j])           # random body-frame location: centred on a random cell
                n=int(((P-p)**2+(Q-q)**2<=rad**2).sum()); amp=a['dose_target']/(a['dur']*max(n,1))
            r=ep.act(a['label'],p,q,rad,amp,a['dur'],a['ramp'],reason=tag)
        dose+=r['dose']; ncell.append(r['cells_in_mask']); last_end=ep.t+a['dur']
    ep.run_until(t_end)
    F=ep.log['frames']
    S=dict(episode=ep.id,seed=seed,pool=pool,tag=tag,start=ep.base_state,target=target,dose=dose,cells=ncell,t_last_end=last_end,t_end=ep.t,
           success=success_rule(ep,cfg,target,last_end),V_body=bool(F[-1]['V_body']),V_body_conservative=bool(F[-1]['V_body_conservative']),
           events=sorted({e for f in F for e in f['events']}),end_state=F[-1]['state'],end_sure=bool(F[-1]['state_sure']),
           u_end=F[-1]['u'][0],actions=ep.log['actions'])
    ep.log['summary']=S; ep.end(); return S
