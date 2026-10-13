import sys; sys.path.insert(0,'.')
from an4 import *
tm=make_template4(30); eng=make_engine4(tm,Params4(g=0.6,alpha=0.0))
key=jax.random.PRNGKey(0)
for rho in (1.0,0.0,0.5,0.9):
    for k in range(3):
        st,perm=seeded_start4(tm,k,'a'); ctl=list(zero_ctl(eng)); ctl[12]=jnp.full(24,rho)
        fin=run_plain(eng,st,0,600,key,ctl=tuple(ctl)); s=summarize4(eng,fin); print(rho,k,{a:(round(b,3) if isinstance(b,float) else b) for a,b in s.items()})
