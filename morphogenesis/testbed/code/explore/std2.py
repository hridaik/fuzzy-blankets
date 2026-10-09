import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A')
for std in (2.0,4.0,8.0):
  for lp in (-6,-10):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pos_on=True,pos_mode='abs',pi_a_x=0.0,pi_a_c=0.0); t0=time.time()
    eng,o=run_draws(tm,P,6,std=std,T=500,dt=0.02)
    print('std',std,'lp',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:3],round(time.time()-t0),flush=True)
