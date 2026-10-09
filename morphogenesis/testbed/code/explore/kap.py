import sys; sys.path.insert(0,'.')
from asm import *
for kap in (2.0,3.0):
  tm=make_body('A',kappa=kap)
  for lp in (-2,-6):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pos_on=True,pos_mode='abs'); t0=time.time()
    eng,o=run_draws(tm,P,4,T=500,dt=0.01)
    print('A24 abs kappa',kap,'lp',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],'orbok',[x['orbit_complete'] for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:3],round(time.time()-t0),flush=True)
