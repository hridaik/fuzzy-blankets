import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A')
for lp in (-2,-4):
    P=Params(k_mu=1.4,k_a=1.2,pos_on=True,pos_mode='abs',pi_prior=float(np.exp(lp)))
    t0=time.time(); eng,o=run_draws(tm,P,4,T=600,dt=0.02)
    print('A24 abs lp',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'minbel',[round(x['min_orbit_maxbel'],2) for x in o],'orbok',[x['orbit_complete'] for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:3],round(time.time()-t0),flush=True)
