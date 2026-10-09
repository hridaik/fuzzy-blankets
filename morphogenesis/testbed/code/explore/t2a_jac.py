import sys,time,dataclasses; sys.path.insert(0,'.')
from common import *
from shape import *
from templates import *
t=make_body('A'); n=24
for lp in (-2,-4,-8):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)))
    eng=make_engine(t,P)
    MU=np.eye(n)*(6.0 if lp>-6 else 12.0)
    st=(jnp.array(t.Xs[0].T),jnp.array(t.Cs[0].T),jnp.array(MU),jnp.zeros((n,1)))
    d=eng.drift(st,1e9,jnp.zeros((n,4))); print('lp',lp,'drift max',[float(jnp.abs(a).max()) for a in d])
    J=np.array(eng.jac_flat(st,1e9))[:-n,:]; J=J[:, :-n]
    w=np.linalg.eigvals(J); print(' n unstable',(w.real>1e-6).sum(),'max re',w.real.max(),'n near zero',(np.abs(w.real)<1e-6).sum())
