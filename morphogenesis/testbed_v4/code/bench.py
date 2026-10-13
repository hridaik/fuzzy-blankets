import time, sys; sys.path.insert(0,'.')
from engine4 import *
tm=make_template4(30); P=Params4(g=0.6,alpha=0.00196)
eng=make_engine4(tm,P)
st,perm=seeded_start4(tm,0,'a'); key=jax.random.PRNGKey(0)
t=time.time(); f=run_plain(eng,st,0,10,key); jax.block_until_ready(f); print('compile+10tu',time.time()-t)
t=time.time(); f=run_plain(eng,st,0,100,key); jax.block_until_ready(f); print('100tu',time.time()-t, 'steps/s', 8000/(time.time()-t))
