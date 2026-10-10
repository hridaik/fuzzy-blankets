import sys,json,numpy as np; sys.path.insert(0,'code')
from t5mon import io
from t5mon.monitor import OnlineMonitor
T=json.load(open('data_v3/treatments.json'))
cfg=json.load(open('MONITOR_CONFIG_draft.json'))
def run_mon(run,stride=1):
    m=OnlineMonitor(cfg); out=[]
    for f in io.o1_frames(run,stride): out.append(m.update(f['t'],f['xy'],f['lev'],f['ids']))
    return out
def summarize(run,out,tr):
    t=np.array([o['t'] for o in out]); u=np.array([o['u'][0] for o in out]); st=[o['state'] for o in out]
    ev=[(o['t'],e) for o in out for e in o['events']]
    return t,u,st,ev
rows=[r for r in io.catalog() if r['condition'][:2] in('T3','T4') and r['split']=='development' and r['arm']!='sham_treated']
res=[]
for r in rows:
    out=run_mon(r['run']); t,u,st,ev=summarize(r['run'],out,T[r['run']])
    onset=40.0; pre=u[t<onset]
    s0=np.sign(np.median(pre))
    # raw crossing: first t after onset where u*s0<0 ; monitor change: first frame label is pure opposite
    raw=next((tt for tt,uu in zip(t,u) if tt>onset and uu*s0<0),None)  # u here is 5-frame median; use raw below
    lab0='S+' if s0>0 else 'S-'; opp='S-' if s0>0 else 'S+'
    ch=next((o['t'] for o in out if o['t']>onset and o['state']==opp and o['state_sure']),None)
    # settle time: first time after which label stays opp to end
    stay=None
    for i in range(len(out)):
        if all(o['state']==opp and o['state_sure'] for o in out[i:]): stay=out[i]['t']; break
    res.append(dict(run=r['run'],cond=r['condition'],V_body=out[-1]['V_body'],Vc=out[-1]['V_body_conservative'],events=sorted(set(e for _,e in ev)),t_cross=raw,t_det=ch,t_stay=stay,end=out[-1]['state'],start=lab0,t_off=T[r['run']][0]['t_off']))
for x in res: print(x)
