import sys; sys.path.insert(0,'.')
from asm import *
tag=sys.argv[1]; tm={'v8':vanilla8,'A24':lambda: make_body('A')}[tag]()
dt=float(sys.argv[2]) if len(sys.argv)>2 else 0.01
for ls in (3,4,5):
  for lp in (-2,-4,-6):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=True,pos_mode='bodyframe',pi_a_x=0.0,pi_prior=float(np.exp(lp)),pi_x=float(np.exp(ls)),pi_c=float(np.exp(ls)),pi_l=float(np.exp(ls)),pi_ref=float(np.exp(ls)),pi_act=1.5*float(np.exp(ls-1)))
    t0=time.time(); eng,o=run_draws(tm,P,4,T=600,dt=dt)
    print(tag,'logsens',ls,'logprior',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'minbel',[round(x['min_maxbel'],2) for x in o],'nslots',[x['n_slots'] for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:2],'cs',[round(x['centroid_speed'],2) for x in o][:2],round(time.time()-t0),flush=True)
