"""Calibrate monitor v2 thresholds on NATURAL calibration dishes (bodies 2100-2105), check on validation (2106-2111)."""
import sys,json,numpy as np; sys.path.insert(0,'code')
from t5mon import io
z=np.load('logs/nat_feats.npz'); names=list(z['names']); ix=lambda n:names.index(n)
dev=io.natural('development')
cal=[r['run'] for r in dev if int(r['body_id'])<=2105]; val=[r['run'] for r in dev if int(r['body_id'])>=2106]
PAT=['c0_mean','c1_mean','c2_mean','c3_mean','c6_mean','c6_slope_p','c1_tailhead','c2_tailhead','c6_tailhead','c6_dabsq_inv','c6_dq_sens','c1_dq_sens','c2_dq_sens','c3_dq_sens']
GEO_SLOW=['s1','s2']
DT=2.0
def med(x,w):  # causal running median over w frames
    out=np.empty_like(x)
    for i in range(len(x)): out[i]=np.median(x[max(0,i-w+1):i+1],0)
    return out
Wfast=5   # 10 tu: acf of fast features < 0.05 by 12-18 tu
cfg={'dt_frame':DT,'window_fast_tu':Wfast*DT,'pattern_features':PAT}
P=np.concatenate([z[r][:,[ix(f) for f in PAT]] for r in cal]); mu=P.mean(0); sd=P.std(0)
cfg['pat_mu']=mu.tolist(); cfg['pat_sd']=sd.tolist()
def pat_stat(r):
    X=z[r][:,[ix(f) for f in PAT]]; return np.abs((med(X,Wfast)-mu)/sd).max(1)
def geo(r):
    X=z[r]; return dict(mst=X[:,ix('mst_max')],ncomp=X[:,ix('ncomp_coh')],n=X[:,ix('n')],s1=X[:,ix('s1')],s2=X[:,ix('s2')],rg=X[:,ix('rg')])
def window_max(a,L=300): # 600-tu windows (episode scale), stride 50 frames
    return np.array([a[i:i+L].max() for i in range(0,len(a)-L,50)])
def window_min(a,L=300): return np.array([a[i:i+L].min() for i in range(0,len(a)-L,50)])
stat={}
stat['pat']=np.concatenate([window_max(pat_stat(r)) for r in cal])
stat['mst']=np.concatenate([window_max(geo(r)['mst']) for r in cal])
sh=lambda r:geo(r)
stat['s1_hi']=np.concatenate([window_max(geo(r)['s1']) for r in cal]); stat['s1_lo']=np.concatenate([window_min(geo(r)['s1']) for r in cal])
stat['s2_hi']=np.concatenate([window_max(geo(r)['s2']) for r in cal]); stat['s2_lo']=np.concatenate([window_min(geo(r)['s2']) for r in cal])
margin=0.15
q=0.99
b={}
b['pat_z']=float(np.quantile(stat['pat'],q))*(1+margin)
b['mst_max']=float(np.quantile(stat['mst'],q))*(1+margin)
for k in ['s1','s2']:
    b[k+'_hi']=float(np.quantile(stat[k+'_hi'],q))*(1+margin); b[k+'_lo']=float(np.quantile(stat[k+'_lo'],1-q))/(1+margin)
b['n']=24
# conservative = tighter margin-free bounds at q=0.95
bc={'pat_z':float(np.quantile(stat['pat'],0.95)),'mst_max':float(np.quantile(stat['mst'],0.95)),
    **{k+'_hi':float(np.quantile(stat[k+'_hi'],0.95)) for k in['s1','s2']},**{k+'_lo':float(np.quantile(stat[k+'_lo'],0.05)) for k in['s1','s2']}}
cfg['bounds']=b; cfg['bounds_conservative']=bc
cfg['r_link']=1.6; cfg['r_hold']=2.08; cfg['r_coh']=1.42
# state model
def u(r):
    X=z[r]; return np.c_[X[:,ix('c4_mean')]-X[:,ix('c5_mean')],X[:,ix('c0_dq_sens')]]
U={'p':np.concatenate([u(r)[:] for r in cal if u(r)[:,1].mean()>0]),'m':np.concatenate([u(r) for r in cal if u(r)[:,1].mean()<0])}
mp,mm=U['p'].mean(0),U['m'].mean(0)
Sw=(np.cov(U['p'].T)+np.cov(U['m'].T))/2
cfg['state']={'mean_plus':mp.tolist(),'mean_minus':mm.tolist(),'cov':Sw.tolist(),'names':['S+ (c4-high, c0 dipole +)','S- (c4-low, c0 dipole -)']}
Si=np.linalg.inv(Sw)
def maha(x,m): d=x-m; return np.einsum('ij,jk,ik->i',d,Si,d)
alld=np.concatenate([np.minimum(maha(u(r),mp),maha(u(r),mm)) for r in cal])
cfg['state']['trans_maha2']=float(np.quantile(alld,0.999))*2   # frames beyond this to both classes = TRANS
cfg['state']['p_conf']=0.99
json.dump(cfg,open('MONITOR_CONFIG_draft.json','w'),indent=1)
print(json.dumps({k:cfg[k] for k in['bounds','bounds_conservative']},indent=1)); print('trans',cfg['state']['trans_maha2'],'class sep maha2',float(((mp-mm)@Si@(mp-mm))))
# validation: false-violation per 600-tu window
def viol(r,B):
    g=geo(r); ps=pat_stat(r)
    v=dict(pat=window_max(ps)>B['pat_z'],mst=window_max(g['mst'])>B['mst_max'],n=(window_min(g['n'])<24)|(window_max(g['n'])>24),comp=window_max(g['ncomp'])>1)
    for k in['s1','s2']: v[k]=(window_max(g[k])>B[k+'_hi'])|(window_min(g[k])<B[k+'_lo'])
    v['any']=np.any([v[k] for k in v],0); return v
for nm,rs in [('cal',cal),('val',val)]:
    for lab,B in[('V_body bounds',b),('conservative',bc)]:
        V=[viol(r,B) for r in rs]; keys=V[0].keys()
        print(nm,lab,{k:round(float(np.mean(np.concatenate([v[k] for v in V]))),3) for k in keys}, 'dishes with any viol:',sum(v['any'].any() for v in V),'/',len(rs))
