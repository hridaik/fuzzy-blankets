"""Baseline-relative envelopes (dish compared with itself, first 20 tu baseline), natural cal -> val."""
import sys,json,numpy as np; sys.path.insert(0,'code')
from t5mon import io
exec(open('code/a_calib.py').read().split("Wfast=5")[0])   # reuse loaders
Wfast=5
PATF=PAT+[]
ixp=[ix(f) for f in PATF]
sd_within=np.mean([z[r][:,ixp].std(0) for r in cal],0)
def med(x,w):
    return np.array([np.median(x[max(0,i-w+1):i+1],0) for i in range(len(x))])
def stats(r,L=300,stride=100,nb=10):
    X=z[r]; F=med(X[:,ixp],Wfast); S=X[:,[ix('s1'),ix('s2'),ix('mst_max'),ix('n'),ix('ncomp_coh')]]
    out=[]
    for s in range(0,len(X)-L,stride):
        base=np.median(F[s+Wfast:s+nb+Wfast],0); sb=np.median(S[s:s+nb],0)
        pz=np.abs((F[s+nb+Wfast:s+L]-base)/sd_within).max()
        ds=np.abs(S[s+nb:s+L,0]-sb[0]).max(); d2=np.abs(S[s+nb:s+L,1]-sb[1]).max()
        # shape relative change
        rs1=(np.abs(S[s+nb:s+L,0]/sb[0]-1)).max(); rs2=(np.abs(S[s+nb:s+L,1]/sb[1]-1)).max()
        out.append([pz,rs1,rs2,S[s+nb:s+L,2].max(),S[s+nb:s+L,3].min(),S[s+nb:s+L,3].max(),S[s+nb:s+L,4].max()])
    return np.array(out)
C=np.concatenate([stats(r) for r in cal]); V=[stats(r) for r in val]
print('windows cal',len(C))
b={}
for k,(j,nm) in enumerate([(0,'pat_dz'),(1,'s1_rel'),(2,'s2_rel'),(3,'mst_max')]):
    b[nm]=float(np.quantile(C[:,j],0.99))*1.15
bc={nm:float(np.quantile(C[:,j],0.95)) for j,nm in [(0,'pat_dz'),(1,'s1_rel'),(2,'s2_rel'),(3,'mst_max')]}
print(b,bc)
def rate(W,B):
    v=np.c_[W[:,0]>B['pat_dz'],W[:,1]>B['s1_rel'],W[:,2]>B['s2_rel'],W[:,3]>B['mst_max'],(W[:,4]<24)|(W[:,5]>24),W[:,6]>1]
    return v.mean(0).round(3), v.any(1).mean().round(3)
print('cal',rate(C,b),rate(C,bc)); 
Vall=np.concatenate(V); print('val',rate(Vall,b),rate(Vall,bc))
print('val per-dish any-viol (V_body bounds):',[float(rate(v,b)[1]) for v in V])
cfg=json.load(open('MONITOR_CONFIG_draft.json')); cfg.pop('bounds');cfg.pop('bounds_conservative')
cfg['baseline']={'n_frames':10,'note':'median of first 10 frames (20 tu) before any action'}
cfg['pat_sd_within']=sd_within.tolist(); cfg['bounds']=b; cfg['bounds_conservative']=bc
cfg['bound_def']={'pat_dz':'max_k |median5(x_k)-baseline_k|/sd_within_k','s1_rel/s2_rel':'|s/s_base-1|','mst_max':'absolute'}
json.dump(cfg,open('MONITOR_CONFIG_draft.json','w'),indent=1)
