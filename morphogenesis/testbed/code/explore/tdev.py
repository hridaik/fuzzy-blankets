import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A'); n=24
for Td in (32.0,150.0,600.0):
  for std in (1/8,2.0):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(-6)),pos_on=True,pos_mode='abs',pi_a_x=0.0,pi_a_c=0.0,T_dev=Td); t0=time.time()
    eng,o=run_draws(tm,P,4,T=max(500,5*Td),std=std,dt=0.02)
    print('Tdev',Td,'std',round(std,2),'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],round(time.time()-t0),flush=True)
