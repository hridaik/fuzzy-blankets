import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A'); n=24; ty=type_vector(tm); key=jax.random.PRNGKey(0)
for mode,kw in (('abs',dict(pos_on=True,pos_mode='abs')),('bodyframe',dict(pos_on=True,pos_mode='bodyframe',pi_a_x=0.0)),('off',dict(pos_on=False,pi_a_x=0.0))):
  for lp in (-2,-4):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),T_dev=1.0,**kw); eng=make_engine(tm,P)
    for jit in (0.0,0.2):
        rng=np.random.default_rng(0); MU=np.eye(n)*6.0+jit*rng.standard_normal((n,n))
        st=(jnp.array(tm.Xs[0].T+jit*rng.standard_normal((n,2))),jnp.array(tm.Cs[0].T),jnp.array(MU),jnp.zeros((n,1)))
        fin=eng.run_final(st,100.0,0.02,int(600/0.02),key,None,0)
        r=analyse(eng,tm,fin,0,ty)
        print(mode,'lp',lp,'jit',jit,'d_tmpl',round(r['d_tmpl'],3),'orbbel',round(r['min_orbit_maxbel'],2),'orbok',r['orbit_complete'],'shp %.0e'%r['shape_speed'],'type_ok',r['type_ok'],flush=True)
