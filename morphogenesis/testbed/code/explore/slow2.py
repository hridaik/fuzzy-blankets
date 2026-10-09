import sys; sys.path.insert(0,'.')
from slow import *
from par import run_jobs
def job(kappa_m,mem_amp,pim,pi_zeta,bias):
    from slow import g_of_s,np
    return dict(args=(kappa_m,mem_amp,pim,pi_zeta,bias),res=g_of_s(kappa_m,mem_amp,pim,pi_zeta,bias,list(np.linspace(-1,7,17)),T_relax=50))
if __name__=="__main__":
    args=[(2.0,1.0,20.0,0,0),(2.0,2.0,20.0,0,0),(2.0,4.0,20.0,0,0),(3.0,2.0,20.0,0,0),(3.0,4.0,20.0,0,0),(1.0,4.0,20.0,0,0),(2.0,2.0,100.0,0,0),(3.0,2.0,100.0,0,0)]
    res=run_jobs(job,args,workers=8,label='slow2')
    for r in res:
        print(r['args']); print('  s:',[round(float(x['s']),1) for x in r['res']]); print('  g:',[round(x['g'],4) for x in r['res']])
