import sys; sys.path.insert(0,'.')
from asm import *
def show(tag,tm,P,nd=6,**kw):
    t0=time.time(); eng,o=run_draws(tm,P,nd,**kw)
    print(tag,'succ',sum(x['success'] for x in o),'/',nd,'d',[round(x['d_tmpl'],2) for x in o],'minbel',[round(x['min_maxbel'],2) for x in o],'nslots',[x['n_slots'] for x in o],round(time.time()-t0),flush=True)
base=dict(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0)
t8=vanilla8()
R8=3.0
show('v8 F1 disperse',t8,Params(**base),x0_radius=R8)
show('v8 F1+F2 ms',multiscale(t8,(1.0,0.25)),Params(**base),x0_radius=R8,dt=0.01)
tA=make_body('A'); R=5.0
show('A24 F1 disperse',tA,Params(**base),nd=4,x0_radius=R)
show('A24 F1+F2 ms',multiscale(tA,(1.0,0.25)),Params(**base),nd=4,x0_radius=R,dt=0.01)
