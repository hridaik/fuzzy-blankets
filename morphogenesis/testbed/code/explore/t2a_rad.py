import sys; sys.path.insert(0,'.')
from asm import *
def show(tag,tm,P,nd=6,**kw):
    t0=time.time(); eng,o=run_draws(tm,P,nd,**kw)
    print(tag,'succ',sum(x['success'] for x in o),'/',nd,'d',[round(x['d_tmpl'],2) for x in o],'minbel',[round(x['min_maxbel'],2) for x in o],'nslots',[x['n_slots'] for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:3],'cs',[round(x['centroid_speed'],3) for x in o][:3],'rot',[round(x['rot_rate'],2) for x in o][:3],round(time.time()-t0),flush=True)
base=dict(k_mu=1.4,k_a=1.2,pos_on=True,pos_mode='bodyframe',frame_grad=False,pi_a_x=0.0)
show('v8 bodyframe',vanilla8(),Params(**base))
show('A24 bodyframe',make_body('A'),Params(**base),nd=4)
