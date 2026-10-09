import sys; sys.path.insert(0,'.')
from mem import *
from par import run_jobs
def job(pi_zeta,pim,plan,kappa_m=0.35,mem_amp=0.25,bias=1.0,T=250):
    from mem import make_body,mem_params,make_engine,auto_dt,mem_start,plan_state,jax,np
    tm=make_body('AB',kappa_m=kappa_m,mem_amp=mem_amp); P,d=mem_params(pi_m=pim,pi_zeta=pi_zeta,kappa_m=kappa_m,bias=bias); eng=make_engine(tm,P); eng.dt,eng.rho=auto_dt(eng,tm)
    st,perm=mem_start(tm,plan); fin=eng.run_final(st,1e4,eng.dt,int(T/eng.dt),jax.random.PRNGKey(0),None,0)
    r=plan_state(eng,tm,fin); r.update(dt=eng.dt,pi_zeta=pi_zeta,pi_m=pim,start=plan); return r
if __name__=="__main__":
    args=[(pz,pm,pl) for pz in (0.02,0.2) for pm in (float(np.exp(1)),float(np.exp(3))) for pl in (0,1)]
    res=run_jobs(job,args,workers=8,label='mem2')
    for r in res: print({k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items()})
