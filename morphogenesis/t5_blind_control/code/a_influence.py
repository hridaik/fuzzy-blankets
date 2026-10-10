import sys,numpy as np; sys.path.insert(0,'code')
from t5mon import io
z=np.load('logs/nat_feats.npz'); names=list(z['names']); ix=lambda n:names.index(n)
dev=io.natural('development'); cal=[r['run'] for r in dev if int(r['body_id'])<=2105]; val=[r['run'] for r in dev if int(r['body_id'])>=2106]
G={'A(c4,c5 dish-level)':['c4_slope_p','c5_slope_p','c4_tailhead','c5_tailhead','c4_dabsq_inv','c5_dabsq_inv'],
   'B(type c0-c3)':['c0_mean','c1_mean','c2_mean','c3_mean','c0_slope_p','c1_tailhead','c2_tailhead'],
   'C(graded c6)':['c6_mean','c6_slope_p','c6_tailhead','c6_dabsq_inv'],
   'D(shape)':['s1','s2','rg','mst_max']}
def XY(runs,src,dst,lag):
    X=[];Y=[]
    for r in runs:
        a=z[r][:,[ix(n) for n in G[src]]]; b=z[r][:,[ix(n) for n in G[dst]]]
        a=(a-a.mean(0))/a.std(0); b=(b-b.mean(0))/b.std(0)       # within-dish standardised
        X.append(np.c_[b[:-lag],a[:-lag]] if False else (b[:-lag],a[:-lag])); Y.append(b[lag:])
    return X,Y
def gain(src,dst,lag,lam=1.0):
    # held-out dish-clustered: fit on cal, test on val; loss reduction when adding src_t to dst_t as predictors of dst_{t+lag}
    def stack(runs,with_src):
        Xs=[];Ys=[]
        for r in runs:
            a=z[r][:,[ix(n) for n in G[src]]]; b=z[r][:,[ix(n) for n in G[dst]]]
            a=(a-a.mean(0))/(a.std(0)+1e-12); b=(b-b.mean(0))/(b.std(0)+1e-12)
            x=np.c_[b[:-lag],a[:-lag]] if with_src else b[:-lag]; Xs.append(x); Ys.append(b[lag:])
        return np.vstack(Xs),np.vstack(Ys)
    out=[]
    for ws in (False,True):
        X,Y=stack(cal,ws); W=np.linalg.solve(X.T@X+lam*np.eye(X.shape[1]),X.T@Y)
        Xv,Yv=stack(val,ws); out.append(((Yv-Xv@W)**2).mean())
    return 1-out[1]/out[0]
for lag in (1,5,25):
    print(f'lag {2*lag} tu: relative held-out loss reduction from adding source group (rows src -> cols dst)')
    ks=list(G)
    for s in ks: print('  ',s[:12].ljust(12),[f"{gain(s,dd,lag):+.3f}" if s!=dd else '  -  ' for dd in ks])
