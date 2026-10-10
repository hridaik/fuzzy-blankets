"""Live episode harness: logs every request/action/monitor output; body-frame <-> arena mapping."""
import sys,json,time,os,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','live')); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from live_client import Dish, DishError
from t5mon.monitor import OnlineMonitor
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG=os.environ.get('T5_MONITOR_CFG',os.path.join(ROOT,'MONITOR_CONFIG.json'))
def connect(): return Dish(os.path.join(ROOT,'rig','ready.json'))
class Ep:
    """One live episode with an attached online monitor. All time advances through advance()."""
    def __init__(self,dish,pool='development',seed=None,sham_of=None,tag='',logdir='episodes',baseline_tu=20.0,dt=1.0):
        self.d=dish; r=dish.reset(pool,seed,sham_of); self.id=r['episode']; self.seed=r['seed']; self.sham=r['sham']; self.pool=pool; self.tag=tag
        self.mon=OnlineMonitor(CFG); self.t=0.0; self.log=dict(episode=self.id,seed=self.seed,pool=pool,sham=self.sham,sham_of=sham_of,tag=tag,requests=[],actions=[],frames=[],decisions=[],budget=None)
        self.dt=dt; self.logdir=logdir; self.last=None; self.budget=r['budget']
        self._observe()
        n=int(round(baseline_tu/dt))
        for _ in range(n): self.advance(dt)
        self.base_state=self.last['state']; self.base_c=np.array(self.last['centroid']); 
    def _observe(self):
        o=self.d.observe(self.id,'O1'); self.log['requests'].append(dict(t=o['t'],level='O1'))
        m=self.mon.update(o['t'],o['xy'],o['lev'] if 'lev' in o else o['level_values'],o['id']); m['xy']=np.round(o['xy'],2).tolist(); m['lev']=np.round(o['level_values'][:,[0,4,5,6]],2).tolist(); m['ids']=o['id'].tolist()
        self.log['frames'].append(m); self.last=m; self.t=o['t']; self.budget=o['budget']; self.xy=o['xy']; return m
    def advance(self,dt):
        r=self.d.step(self.id,dt); self.budget=r['budget']; return self._observe()
    def frame(self):
        e1=np.array(self.last['e1']); return np.array(self.last['centroid']),e1,np.array([-e1[1],e1[0]])
    def to_arena(self,p,q):
        c,e1,e2=self.frame(); return (c+p*e1+q*e2).tolist()
    def act(self,label,p,q,radius,amp,dur,ramp=None,reason='',whole=False):
        ramp=min(ramp if ramp is not None else min(5.0,dur/4),dur/2)
        mask={'type':'all'} if whole else {'type':'disc','xy':self.to_arena(p,q),'radius':radius}
        r=self.d.act(self.id,label,mask,amp,dur,ramp); self.budget=r['budget']
        self.log['actions'].append(dict(t=self.t,label=label,mask=mask,body_frame=[p,q],radius=radius,amp=amp,dur=dur,ramp=ramp,accepted=r['accepted'],dose=r['dose'],cells=r['cells_in_mask'],reason=reason))
        return r
    def decide(self,**kw): self.log['decisions'].append(dict(t=self.t,**kw))
    def run_until(self,t_end,dt=None,stop=None):
        dt=dt or self.dt
        while self.t<t_end-1e-9:
            m=self.advance(min(dt,t_end-self.t))
            if stop and stop(m): return m
        return self.last
    def end(self,save=True):
        r=self.d.end_episode(self.id); self.log['budget']=r['budget']
        if save:
            os.makedirs(os.path.join(ROOT,self.logdir),exist_ok=True)
            json.dump(self.log,open(os.path.join(ROOT,self.logdir,f'ep_{self.id:05d}.json'),'w'),default=lambda o:o.item() if hasattr(o,'item') else str(o))
        return r
