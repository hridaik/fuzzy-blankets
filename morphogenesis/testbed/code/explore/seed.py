import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A'); n=24
for a in (0.5,1.0,2.0,3.0):
  for lp in (-6,):
    MU0s=[]
    for k in range(6):
        rng=np.random.default_rng(k); perm=rng.permutation(n); M=rng.standard_normal((n,n))/8; M[np.arange(n),perm]+=a; MU0s.append(M)
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pos_on=True,pos_mode='abs',pi_a_x=0.0,pi_a_c=0.0); t0=time.time()
    eng,o=run_draws(tm,P,6,MU0s=MU0s,T=500,dt=0.02)
    print('seed a',a,'lp',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:3],round(time.time()-t0),flush=True)
