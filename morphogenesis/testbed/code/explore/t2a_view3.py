import sys; sys.path.insert(0,'.')
from asm import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
col={1:'#d62728',2:'#1f77b4',3:'#2ca02c',4:'#e6a800'}
tm=make_body('A'); n=24; key=jax.random.PRNGKey(0); tt=type_vector(tm)
fig,ax=plt.subplots(1,3,figsize=(18,4.5))
ax[0].scatter(*tm.Xs[0],c=[col[x] for x in tt],s=150); ax[0].set_aspect('equal')
P=Params(k_mu=1.4,k_a=1.2,pos_on=True,pos_mode='abs',pi_prior=float(np.exp(-2)))
eng=make_engine(tm,P); MU0=np.random.default_rng(0).standard_normal((n,n))/8
fin=eng.run_final(eng.init_from_mu(MU0),0.0,0.02,int(600/0.02),key,None,0)
X,C,MU,_=[np.array(v) for v in fin]; ty=cell_types(C.T); p=np.array(jax.nn.softmax(MU,axis=1))
ax[1].scatter(X[:,0],X[:,1],c=[col[x] for x in ty],s=150); ax[1].set_aspect('equal')
ax[2].imshow(p,aspect='auto'); 
plt.savefig('/tmp/t2a_view3.png',dpi=60)
print(np.bincount(ty), p.max(1).round(2))
