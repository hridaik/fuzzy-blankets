import sys; sys.path.insert(0,'.')
from mem import *
from par import run_jobs
def job(pi_zeta,pim,plan,kappa_m,mem_amp,bias=1.0,T=200):
    from mem import make_body,mem_params,make_engine,auto_dt,mem_start,plan_state,jax,np,wB
    tm=make_body('AB',kappa_m=kappa_m,mem_amp=mem_amp); P,d=mem_params(pi_m=pim,pi_zeta=pi_zeta,kappa_m=kappa_m,bias=bias,mem_amp=mem_amp); eng=make_engine(tm,P); eng.dt,eng.rho=auto_dt(eng,tm)
    st,perm=mem_start(tm,plan); per=int(round(20/eng.dt)); nst=per*int(T/20)
    fin,tr=eng.run(st,1e4,eng.dt,nst,jax.random.PRNGKey(0),None,0,save_every=per)
    ser=[float(np.array(jax.nn.softmax(tr[3][k],axis=1))[:,1].mean()) for k in range(len(tr[3]))]
    r=plan_state(eng,tm,fin); r.update(dt=eng.dt,pi_zeta=pi_zeta,pi_m=pim,start=plan,kappa_m=kappa_m,mem_amp=mem_amp,wB_series=[round(x,3) for x in ser]); return r
if __name__=="__main__":
    args=[(0.001,pm,pl,km,ma) for (pm,km,ma) in ((20.0,0.35,0.25),(20.0,1.0,0.5),(100.0,1.0,0.5),(20.0,2.0,1.0)) for pl in (0,1)]
    res=run_jobs(job,args,workers=8,label='mem3')
    for r in res: print({k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items()})
