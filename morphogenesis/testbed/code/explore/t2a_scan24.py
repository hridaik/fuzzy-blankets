import sys,time,dataclasses; sys.path.insert(0,'.')
from common import *
from shape import *
from templates import *
t=make_body('A'); key=jax.random.PRNGKey(0); n=24
tt=type_vector(t)
for std in (1/8, 1.0):
  for lp in (-2,-4,-6):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)))
    eng=make_engine(t,P); out=[]
    t0=time.time()
    for k in range(4):
        MU0=np.random.default_rng(k).standard_normal((n,n))*std
        st=eng.init_from_mu(MU0)
        fin=eng.run_final(st,0.0,0.02,int(600/0.02),key,None,0)
        X,C,MU,_=[np.array(a) for a in fin]
        mb=np.array(jax.nn.softmax(MU,axis=1)).max(1)
        sp=max(float(jnp.abs(a).max()) for a in eng.drift(fin,1e9,jnp.zeros((n,4))))
        out.append((round(float(mb.min()),2), round(d_rigid(X.T,cell_types(C.T),t.Xs[0],tt),2), '%.0e'%sp))
    print('std',std,'log prior',lp,out,round(time.time()-t0),flush=True)
