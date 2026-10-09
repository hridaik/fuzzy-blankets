import sys; sys.path.insert(0,'.')
from asm import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
col={1:'#d62728',2:'#1f77b4',3:'#2ca02c',4:'#e6a800'}
tm=make_body('A'); ms=multiscale(tm,(1.0,0.25)); n=24; key=jax.random.PRNGKey(0)
fig,ax=plt.subplots(1,4,figsize=(18,4.5))
tt=type_vector(tm); ax[0].scatter(*tm.Xs[0],c=[col[x] for x in tt],s=150); ax[0].set_aspect('equal')
for a,(lp,seed) in zip(ax[1:],[(-2,0),(-2,1),(-6,0)]):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)))
    eng=make_engine(ms,P); MU0=np.random.default_rng(seed).standard_normal((n,n))/8
    fin,tr=eng.run(eng.init_from_mu(MU0),0.0,0.01,int(500/0.01),key,None,0,save_every=500)
    X,C,MU,_=[np.array(v) for v in fin]; ty=cell_types(C.T)
    Xt=np.array(tr[0]); print(lp,seed,'centroid speed last',np.linalg.norm(Xt[-1].mean(0)-Xt[-2].mean(0))/5,'shape speed',np.abs((Xt[-1]-Xt[-1].mean(0))-(Xt[-2]-Xt[-2].mean(0))).max()/5)
    a.scatter(X[:,0],X[:,1],c=[col[x] for x in ty],s=150); a.set_aspect('equal'); a.set_title(f'ms lp{lp} seed{seed}')
plt.savefig('/tmp/t2a_view2.png',dpi=60)
