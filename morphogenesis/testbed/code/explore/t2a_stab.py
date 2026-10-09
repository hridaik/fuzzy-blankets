import sys,time,dataclasses; sys.path.insert(0,'.')
from common import *
from shape import *
from templates import *
t=make_body('A'); key=jax.random.PRNGKey(0); n=24; tt=type_vector(t)
for lp in (-2,-4):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)),T_dev=1.0)
    eng=make_engine(t,P)
    rng=np.random.default_rng(0)
    perm=rng.permutation(n)
    for noise in (0.0,0.3,1.0):
        MU=np.zeros((n,n)); MU[np.arange(n),perm]=6.0
        # positions: template positions of the believed slot + jitter
        X0=t.Xs[0][:,perm].T+noise*rng.standard_normal((n,2))*0.5
        C0=t.Cs[0][:,perm].T
        st=(jnp.array(X0),jnp.array(C0),jnp.array(MU+noise*rng.standard_normal((n,n))),jnp.zeros((n,1)))
        fin=eng.run_final(st,100.0,0.02,int(400/0.02),key,None,0)
        X,C,MU2,_=[np.array(a) for a in fin]; mb=np.array(jax.nn.softmax(MU2,axis=1)).max(1)
        print('logprior',lp,'jitter',noise,'d_rigid',round(d_rigid(X.T,cell_types(C.T),t.Xs[0],tt),3),'min maxbel',round(float(mb.min()),2),flush=True)
