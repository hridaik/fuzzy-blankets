import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A'); base=dict(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0)
for tag,t_ in (('A24',tm),('A24 ms',multiscale(tm,(1.0,0.25)))):
  for dt in (0.02,0.01,0.005):
    t0=time.time(); eng,o=run_draws(t_,Params(**base),3,T=600,dt=dt)
    print(tag,dt,[round(x['d_tmpl'],2) for x in o],['%.0e'%x['resid'] for x in o],[round(x['min_maxbel'],2) for x in o],round(time.time()-t0),flush=True)
