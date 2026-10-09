import sys; sys.path.insert(0,'.')
from asm import *
def show(tag,tm,P,nd=4,**kw):
    t0=time.time(); eng,o=run_draws(tm,P,nd,**kw)
    print(tag,'succ',sum(x['success'] for x in o),'/',nd,'d',[round(x['d_tmpl'],2) for x in o],'minbel',[round(x['min_maxbel'],2) for x in o],'res',['%.0e'%x['resid'] for x in o][:3],round(time.time()-t0),flush=True)
base=dict(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0)
for tag,tm in (('v8',vanilla8()),('A24',make_body('A'))):
    ms=multiscale(tm,(1.0,0.25))
    for lp in (-2,-6):
        show(f'{tag} F1 only lp{lp}',ms,Params(**base,pi_prior=float(np.exp(lp))) ,)
