import sys; sys.path.insert(0,'.')
from mem import *
tm=make_body('AB'); key=jax.random.PRNGKey(0)
for pim in (0.0,1.0,float(np.exp(2)),float(np.exp(3))):
    P,d=mem_params(pi_m=pim); eng=make_engine(tm,P); eng.dt,eng.rho=auto_dt(eng,tm)
    for plan in (0,1):
        st,perm=mem_start(tm,plan)
        fin=eng.run_final(st,1e4,eng.dt,int(300/eng.dt),key,None,0)
        r=plan_state(eng,tm,fin); print('pi_m',round(pim,2),'start',plan,'dt',round(eng.dt,4),{k:(round(v,3) if isinstance(v,float) else v) for k,v in r.items()},flush=True)
