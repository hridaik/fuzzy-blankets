import sys; sys.path.insert(0,'.')
from asm import *
XA,tA=body24_planA()
for sc in (1.5,2.0,3.0):
  X=XA*sc; tm=make_template(X,codes_from_types(tA,xs=XA[0]),1.0,tA[None])
  for lp in (-6,):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pos_on=True,pos_mode='abs',pi_a_x=0.0,pi_a_c=0.0); t0=time.time()
    eng,o=run_draws(tm,P,4,T=500,dt=0.02)
    print('scale',sc,'lp',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],round(time.time()-t0),flush=True)
