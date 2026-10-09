import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A'); n=24; ty=type_vector(tm); key=jax.random.PRNGKey(0)
def mkP(ls,lp,**kw):
    return Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pi_x=float(np.exp(ls)),pi_c=float(np.exp(ls)),pi_l=float(np.exp(ls)),pi_ref=float(np.exp(ls)),pi_act=1.5*float(np.exp(ls-1)),**kw)
for ls in (3,4):
  for lp in (-6,-8,-10):
    P=mkP(ls,lp,pos_on=True,pos_mode='abs'); dt=0.02*np.exp(-(ls-3)); t0=time.time()
    eng,o=run_draws(tm,P,3,T=600,dt=dt)
    print('abs from-scratch ls',ls,'lp',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],'orbok',[x['orbit_complete'] for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:3],round(time.time()-t0),flush=True)
