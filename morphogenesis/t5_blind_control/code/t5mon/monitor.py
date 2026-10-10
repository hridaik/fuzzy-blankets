"""Online identity monitor v2 for O1 frames (causal; each update uses only frames up to now).
Layers: MATERIAL (cell ids), GEOMETRY (n, cohesion, shape), PATTERN (channel pattern excl. state-carrying features), STATE (2-state posterior).
BODY IDENTITY = MATERIAL + GEOMETRY. State changes are NOT identity failures."""
import json, numpy as np
from . import geom, describe
CH7=['c0','c1','c2','c3','c4','c5','c6']
PAT=['c0_mean','c1_mean','c2_mean','c3_mean','c6_mean','c6_slope_p','c1_tailhead','c2_tailhead','c6_tailhead','c6_dabsq_inv','c6_dq_sens','c1_dq_sens','c2_dq_sens','c3_dq_sens']
class OnlineMonitor:
    def __init__(self, cfg):
        if isinstance(cfg,str): cfg=json.load(open(cfg))
        self.c=cfg; self.W=int(round(cfg['window_fast_tu']/cfg['dt_frame'])); self.nb=cfg['baseline']['n_frames']
        s=cfg['state']; self.mp=np.array(s['mean_plus']); self.mm=np.array(s['mean_minus']); self.Si=np.linalg.inv(np.array(s['cov']))
        self.reset()
    def reset(self):
        self.hist_u=[]; self.hist_pat=[]; self.hist_s=[]; self.prev_e1=None; self.base=None; self.t=[]; self.ids0=None; self.events=[]; self.raw=[]
        self.prev_ids=None; self.s_base=None; self.state_hist=[]
        self.vb_ok=True; self.vc_ok=True; self.viol_log=[]; self.event_flag=False
    def _maha(self,u,m): d=u-m; return float(d@self.Si@d)
    def update(self, t, xy, lev, ids):
        """frame at time t. lock_baseline: True while no action has been delivered (pre-action baseline accumulates)."""
        c=self.c; bf=geom.body_frame(xy,lev,CH7,self.prev_e1); self.prev_e1=bf['e1']
        d=describe.describe(xy,lev,CH7,bf,c['r_coh'])
        pat=np.array([d[k] for k in c['pattern_features']]); u=np.array([d['c4_mean']-d['c5_mean'],d['c0_dq_sens']])
        self.hist_u.append(u); self.hist_pat.append(pat); self.t.append(t)
        us=np.median(self.hist_u[-self.W:],0); ps=np.median(self.hist_pat[-self.W:],0)
        # events (O1 ids)
        ev=[]; idset=set(ids.tolist())
        if self.ids0 is None: self.ids0=set(idset); self.prev_ids=set(idset)
        lost=self.prev_ids-idset; arr=idset-self.prev_ids
        if lost: ev.append('LOSS')
        if arr: ev.append('ARRIVAL')
        lab=geom.components(xy,c['r_link']); ncomp=int(lab.max()+1); sizes=np.bincount(lab)
        if (sizes>=3).sum()>=2: ev.append('SPLIT')
        elif ncomp>1 and len(lost)==0: ev.append('EXTRUSION')   # isolated single cells leave the linked body
        self.prev_ids=idset
        self.hist_s.append([d['s1'],d['s2']])
        if self.base is None and len(self.t)>=self.nb:      # baseline = median of first nb frames (caller observes before acting)
            self.base=np.median(self.hist_pat[:self.nb],0); self.s_base=np.median(self.hist_s[:self.nb],0)
        # state posterior
        m2p=self._maha(us,self.mp); m2m=self._maha(us,self.mm)
        lp=np.array([-0.5*m2p,-0.5*m2m]); lp-=lp.max(); post=np.exp(lp)/np.exp(lp).sum()
        trans=min(m2p,m2m)>c['state']['trans_maha2']
        lab_s='TRANS' if trans else ('S+' if post[0]>=post[1] else 'S-')
        out=dict(t=t,state=lab_s,p_plus=float(post[0]),p_conf=float(post.max()),u=[float(us[0]),float(us[1])],state_sure=(not trans) and post.max()>=c['state']['p_conf'],
                 n=int(len(xy)),mst_max=float(d['mst_max']),s1=float(d['s1']),s2=float(d['s2']),ncomp=ncomp,events=ev,centroid=bf['centroid'].tolist(),e1=bf['e1'].tolist(),sign_conf=float(bf['sign_conf']))
        # layers
        B=c['bounds']; Bc=c['bounds_conservative']
        mat_ok=(len(lost)==0 and len(arr)==0 and self.ids0==idset)
        out['material_J']=len(self.ids0&idset)/max(len(self.ids0|idset),1)
        if self.base is not None:
            dz=float(np.max(np.abs((ps-self.base)/np.array(c['pat_sd_within'])))); r1=abs(d['s1']/self.s_base[0]-1); r2=abs(d['s2']/self.s_base[1]-1)
        else: dz=r1=r2=0.0
        out.update(pat_dz=dz,s1_rel=r1,s2_rel=r2)
        geo_ok=(len(xy)==24 and ncomp==1 and d['mst_max']<=B['mst_max'] and r1<=B['s1_rel'] and r2<=B['s2_rel'])
        geo_warn=bool(d['mst_max']>Bc['mst_max'] or r1>Bc['s1_rel'] or r2>Bc['s2_rel'])   # inside V_body, beyond the 95% natural level
        pat_ok=dz<=B['pat_dz']
        if ev: self.event_flag=True
        out.update(material_ok=mat_ok,geometry_ok=geo_ok,pattern_ok=pat_ok,geometry_warn=geo_warn)
        self.vb_ok=self.vb_ok and mat_ok and geo_ok            # V_body: cumulative since start
        self.vc_ok=self.vb_ok and not self.event_flag      # conservative = V_body and no SPLIT/MERGE/EXTRUSION/LOSS/ARRIVAL flag ever
        out.update(V_body=self.vb_ok,V_body_conservative=self.vc_ok,V_body_now=bool(mat_ok and geo_ok))
        self.last=out; self.state_hist.append((t,lab_s,float(post.max()),bool(out['state_sure'])))
        return out
    def _shape(self,xy):
        x=xy-xy.mean(0); w=np.linalg.eigvalsh(x.T@x/len(x)); return np.sqrt(w[::-1])
    def sustained(self, target, hold_tu, t_now):
        """True if state==target (sure) in every frame of the last hold_tu."""
        h=[s for s in self.state_hist if s[0]>t_now-hold_tu-1e-9]
        return len(h)>0 and (self.state_hist[0][0]<=t_now-hold_tu) and all(s[1]==target and s[3] for s in h)
