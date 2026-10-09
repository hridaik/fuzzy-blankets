import sys; sys.path.insert(0,'.')
from asm import *
n=24; key=jax.random.PRNGKey(0)
for kind in ('B',):
  tm=make_body(kind); ty=type_vector(tm)
  for lp in (-6,-10):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pi_a_x=0.0,pi_a_c=0.0,pos_on=False); eng=make_engine(tm,P)
    rng=np.random.default_rng(0)
    for jit in (0.0,0.3):
        st=(jnp.array(tm.Xs[0].T+jit*rng.standard_normal((n,2))),jnp.array(tm.Cs[0].T),jnp.array(np.eye(n)*8.0+jit*rng.standard_normal((n,n))),jnp.zeros((n,1)))
        fin=eng.run_final(st,1e4,0.02,int(400/0.02),key,None,0); r=analyse(eng,tm,fin,0,ty)
        print(kind,'off lp',lp,'jit',jit,'d',round(r['d_tmpl'],3),'orbbel',round(r['min_orbit_maxbel'],2),'orbok',r['orbit_complete'],'shp %.0e'%r['shape_speed'],'cs',round(r['centroid_speed'],3),'rot',round(r['rot_rate'],2),flush=True)
