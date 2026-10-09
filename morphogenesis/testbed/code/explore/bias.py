import sys; sys.path.insert(0,'.')
from par import run_jobs
def job(bias,plan,pi_zeta,km=2.0,ma=1.0,pim=20.0,T=300):
    from mem import make_body,mem_params,make_engine,auto_dt,mem_start,plan_state,jax,np
    tm=make_body('AB',kappa_m=km,mem_amp=ma); P,d=mem_params(pi_m=pim,pi_zeta=pi_zeta,kappa_m=km,bias=bias,mem_amp=ma); eng=make_engine(tm,P); eng.dt,eng.rho=auto_dt(eng,tm)
    st,perm=mem_start(tm,plan); fin=eng.run_final(st,1e4,eng.dt,int(T/eng.dt),jax.random.PRNGKey(0),None,0)
    r=plan_state(eng,tm,fin); r.update(bias=bias,start=plan,pi_zeta=pi_zeta); return r
if __name__=="__main__":
    args=[(b,pl,0.3) for b in (-3.0,-2.0,-1.0,0.0) for pl in (0,1)]
    for r in run_jobs(job,args,workers=8,label='bias'): print({k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items()})
