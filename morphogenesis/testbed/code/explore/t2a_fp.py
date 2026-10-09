import sys; sys.path.insert(0,'.')
from asm import *
from scipy.optimize import root
t8=vanilla8(); n=8
for lp in (-2,-4):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)))
    eng=make_engine(t8,P)
    st0=(jnp.array(t8.Xs[0].T),jnp.array(t8.Cs[0].T),jnp.array(np.eye(n)*5.0),jnp.zeros((n,1)))
    flat0,unf=flatten_state(st0)
    f=jax.jit(lambda v: flatten_state(eng.drift(unf(v),1e9,jnp.zeros((n,4))))[0])
    jf=jax.jit(jax.jacfwd(lambda v: flatten_state(eng.drift(unf(v),1e9,jnp.zeros((n,4))))[0]))
    sol=root(lambda v: np.array(f(v)), np.array(flat0), jac=lambda v: np.array(jf(v)), method='lm')
    v=sol.x; st=unf(jnp.array(v)); print('lp',lp,'success',sol.success,'resid',np.abs(np.array(f(v))).max())
    X,C,MU,_=[np.array(a) for a in st]; p=np.array(jax.nn.softmax(MU,axis=1))
    print(' d_tmpl',d_rigid(X.T,cell_types(C.T),t8.Xs[0],type_vector(t8) if t8.types is not None else cell_types(t8.Cs[0])),'minmaxbel',p.max(1).min())
    J=np.array(jf(v))[:-n,:-n]; w=np.linalg.eigvals(J); print(' unstable',(w.real>1e-6).sum(),'max re',w.real.max(),' zero',(abs(w.real)<1e-6).sum())
