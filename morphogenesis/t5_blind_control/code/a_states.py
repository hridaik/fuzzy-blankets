import sys,numpy as np; sys.path.insert(0,'code')
from t5mon import io
z=np.load('logs/nat_feats.npz'); names=list(z['names'])
dev=io.natural('development')
j0=names.index('c0_dq_sens')
rows=[]
for r in dev:
    X=z[r['run']]; rows.append((r['run'],int(r['body_id']),np.sign(X[:,j0].mean()),X.mean(0),X.std(0)))
sg=np.array([r[2] for r in rows]); M=np.array([r[3] for r in rows]); S=np.array([r[4] for r in rows])
print('dishes +/-:',(sg>0).sum(),(sg<0).sum(), 'bodies',[ (r[1],int(r[2])) for r in rows])
# per-feature separation d' between + and - groups (dish means), and within-dish sd
res=[]
for k,n in enumerate(names):
    a=M[sg>0,k]; b=M[sg<0,k]; sp=np.sqrt((a.var()+b.var())/2+1e-18)
    res.append((abs(a.mean()-b.mean())/sp,n,a.mean(),b.mean(),sp,S[:,k].mean()))
res.sort(reverse=True)
for d,n,a,b,sp,w in res[:25]: print(f'{n:16s} dprime={d:7.1f} plus={a:8.3f} minus={b:8.3f} betweenSD={sp:.3f} withinSD={w:.3f}')
print('--- invariant (not _sens) top:')
for d,n,a,b,sp,w in [x for x in res if 'sens' not in x[1]][:8]: print(f'{n:16s} dprime={d:7.1f} plus={a:8.3f} minus={b:8.3f} within={w:.3f}')
print('sign_conf mean',M[:,names.index('sign_conf')], 'n',M[:,names.index('n')])
