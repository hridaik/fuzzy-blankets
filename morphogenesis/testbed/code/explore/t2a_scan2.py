import sys; sys.path.insert(0,'.')
from asm import *
t8=vanilla8()
def show(tag,tm,P,nd=4,**kw):
    t0=time.time(); eng,o=run_draws(tm,P,nd,**kw)
    print(tag,'succ',sum(x['success'] for x in o),'/',nd,'d',[round(x['d_tmpl'],2) for x in o],'minbel',[round(x['min_maxbel'],2) for x in o],'res',['%.0e'%x['resid'] for x in o][:2],round(time.time()-t0),flush=True)
base=dict(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0)
show('base',t8,Params(**base))
show('Tdev256',t8,Params(**base,T_dev=256.0))
show('pl e5',t8,Params(**base,pi_l=float(np.exp(5)),pi_ref=float(np.exp(3))))
show('pc e1',t8,Params(**base,pi_c=float(np.exp(1))))
show('prior -4,Tdev128',t8,Params(**base,T_dev=128.0,pi_prior=float(np.exp(-4))))
