import sys; sys.path.insert(0,'.')
from asm import *
for tag,tm in (('v8',vanilla8()),('A24',make_body('A'))):
  n=tm.n; ty=type_vector(tm) if tm.types is not None else cell_types(tm.Cs[0]); key=jax.random.PRNGKey(0)
  for lp in (-2,-4,-6,-8):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)),T_dev=1.0)
    eng=make_engine(tm,P)
    for jit,mu_amp in ((0.0,12.0),(0.3,12.0),(0.3,8.0)):
        rng=np.random.default_rng(0); perm=rng.permutation(n)
        MU=np.zeros((n,n)); MU[np.arange(n),perm]=mu_amp
        X0=tm.Xs[0][:,perm].T+jit*rng.standard_normal((n,2)); C0=tm.Cs[0][:,perm].T
        st=(jnp.array(X0),jnp.array(C0),jnp.array(MU),jnp.zeros((n,1)))
        fin=eng.run_final(st,100.0,0.02,int(600/0.02),key,None,0)
        r=analyse(eng,tm,fin,0,ty,t_eval=1e9)
        print(tag,'lp',lp,'jit',jit,'MU',mu_amp,'d_tmpl',round(r['d_tmpl'],3),'minbel',round(r['min_maxbel'],2),'res %.0e'%r['resid'],'slots',r['n_slots'],flush=True)
