import sys,time,dataclasses; sys.path.insert(0,'.')
from common import *
from shape import *
from templates import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
t=make_body('A'); key=jax.random.PRNGKey(0); n=24
col={1:'#d62728',2:'#1f77b4',3:'#2ca02c',4:'#e6a800'}
fig,ax=plt.subplots(1,4,figsize=(18,4.5))
tt=type_vector(t); ax[0].scatter(*t.Xs[0],c=[col[x] for x in tt],s=200); ax[0].set_title('template A'); ax[0].set_aspect('equal')
for a,(lp,std,seed) in zip(ax[1:],[(-2,1.0,2),(-4,0.125,0),(-6,1.0,1)]):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)))
    eng=make_engine(t,P); MU0=np.random.default_rng(seed).standard_normal((n,n))*std
    fin=eng.run_final(eng.init_from_mu(MU0),0.0,0.02,int(600/0.02),key,None,0)
    X,C,MU,_=[np.array(v) for v in fin]; ty=cell_types(C.T)
    a.scatter(X[:,0],X[:,1],c=[col[x] for x in ty],s=200); a.set_aspect('equal'); a.set_title(f'logprior {lp}')
plt.savefig('/tmp/t2a_view.png',dpi=60)
