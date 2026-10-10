import sys,json,os,numpy as np; sys.path.insert(0,'code')
from rig import *
RES='logs/b1_results.jsonl'
HORIZON_POST=90.0
def probe(d,seed,label,p,q,r,amp,dur,ramp=None,whole=False,tag='probe',post=HORIZON_POST,sham_of=None,pool='development'):
    ep=Ep(d,pool=pool,seed=seed,tag=tag,sham_of=sham_of); t0=ep.t
    ep.act(label,p,q,r,amp,dur,ramp,reason=tag,whole=whole)
    ep.run_until(t0+dur+post)
    F=ep.log['frames']; u=np.array([f['u'][0] for f in F]); t=np.array([f['t'] for f in F]); st=[f['state'] for f in F]
    a=ep.log['actions'][0]
    res=dict(episode=ep.id,seed=seed,label=label,p=p,q=q,r=r,amp=amp,dur=dur,whole=whole,start=ep.base_state,t_act=t0,dose=a['dose'],cells=a['cells'],
        end_state=st[-1],end_sure=F[-1]['state_sure'],u_end=float(u[-1]),u_start=float(u[0]),
        flipped=bool(st[-1]!=ep.base_state and F[-1]['state_sure']),
        t_flip=next((float(tt) for tt,s,f in zip(t,st,F) if tt>t0 and s!=ep.base_state and s!='TRANS' and f['state_sure']),None),
        umax_dev=float(np.max(np.abs(u-u[0]))),
        pat_dz_max=float(max(f['pat_dz'] for f in F)),geo_warn=bool(any(f['geometry_warn'] for f in F)),
        mst_max=float(max(f['mst_max'] for f in F)),s_rel=float(max(max(f['s1_rel'],f['s2_rel']) for f in F)),
        V_body=bool(F[-1]['V_body']),Vc=bool(F[-1]['V_body_conservative']),events=sorted({e for f in F for e in f['events']}),
        time_used=ep.t)
    ep.end(); return res
def save(res,path=RES):
    with open(path,'a') as f: f.write(json.dumps(res,default=lambda o:o.item() if hasattr(o,'item') else str(o))+'\n')
def twin(d,seed,T,tag='twin'):
    ep=Ep(d,seed=seed,tag=tag); ep.run_until(T); 
    F=ep.log['frames']; r=dict(episode=ep.id,seed=seed,tag=tag,start=ep.base_state,u=[f['u'][0] for f in F],t=[f['t'] for f in F]); ep.end(); return r
