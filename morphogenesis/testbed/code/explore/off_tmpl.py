import sys; sys.path.insert(0,'.')
from asm import *
n=24; key=jax.random.PRNGKey(0)
for kind in ('A','B'):
  tm=make_body(kind); ty=type_vector(tm)
  for tag,P0 in (('off',dict(pos_on=False)),('off+ms',dict(pos_on=False))):
    t_=tm if tag=='off' else multiscale(tm,(1.0,0.3))
    dt=0.02 if tag=='off' else 0.01
    for lp in (-6,-10):
        P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pi_a_x=0.0,pi_a_c=0.0,**P0); eng=make_engine(t_,P)
        rng=np.random.default_rng(0)
        for jit in (0.0,0.2):
            nc=t_.nc
            st=(jnp.array(t_.Xs[0].T+jit*rng.standard_normal((n,2))),jnp.array(t_.Cs[0].T),jnp.array(np.eye(n)*8.0+jit*rng.standard_normal((n,n))),jnp.zeros((n,1)))
            fin=eng.run_final(st,1e4,dt,int(400/dt),key,None,0); r=analyse(eng,t_,fin,0,ty)
            print(kind,tag,'lp',lp,'jit',jit,'d',round(r['d_tmpl'],3),'orbbel',round(r['min_orbit_maxbel'],2),'orbok',r['orbit_complete'],'shp %.0e'%r['shape_speed'],'cs',round(r['centroid_speed'],3),'rot',round(r['rot_rate'],2),flush=True)
