import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A'); n=24; ty=type_vector(tm); key=jax.random.PRNGKey(0)
for pax,pac in ((0.0,0.0),(0.0,float(np.exp(-2)))):
  for lp in (-2,-6):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pos_on=True,pos_mode='abs',pi_a_x=pax,pi_a_c=pac); eng=make_engine(tm,P)
    st=(jnp.array(tm.Xs[0].T),jnp.array(tm.Cs[0].T),jnp.array(np.eye(n)*8.0),jnp.zeros((n,1)))
    fin=eng.run_final(st,1e4,0.02,int(400/0.02),key,None,0); r=analyse(eng,tm,fin,0,ty)
    t0=time.time(); eng,o=run_draws(tm,P,4,T=500,dt=0.02)
    print('pa_x',pax,'pa_c',round(pac,3),'lp',lp,'| from template: d',round(r['d_tmpl'],3),'orbbel',round(r['min_orbit_maxbel'],2),'| from scratch succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],flush=True)
