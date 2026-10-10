import sys,numpy as np; sys.path.insert(0,'code')
from t5mon import io
z=np.load('logs/nat_feats.npz'); names=list(z['names'])
dev=io.natural('development'); cal=[r['run'] for r in dev if int(r['body_id'])<=2105]; val=[r['run'] for r in dev if int(r['body_id'])>=2106]
print(len(cal),len(val))
def acf(x,L=300):
    x=x-x.mean(); v=(x*x).mean(); return np.array([(x[:len(x)-k]*x[k:]).mean()/v for k in range(L)])
for f in ['c0_dq_sens','c4_mean','c6_mean','c0_mean','s1','s2','n','mst_max','c4_slope_p','pq_cov_sens','c0_dabsq_inv','c6_dq_sens']:
    j=names.index(f)
    A=np.mean([acf(z[r][:,j]) for r in cal],0)  # lag unit = 2 tu
    tau=next((2*k for k in range(len(A)) if A[k]<np.exp(-1)),None)
    z0=next((2*k for k in range(len(A)) if A[k]<0.05),None)
    print(f, 'e-fold tu',tau,'acf<0.05 tu',z0, 'between-dish var share', round(np.var([z[r][:,j].mean() for r in cal])/np.var(np.concatenate([z[r][:,j] for r in cal])),2))
# per-dish: sign structure of c0_dq_sens
j=names.index('c0_dq_sens')
for r in cal[:12]:
    x=z[r][:,j]; print(r, round(x.mean(),3), round(x.std(),3), 'frac>0',round((x>0).mean(),2), 'sign flips',int((np.diff(np.sign(x))!=0).sum()))
