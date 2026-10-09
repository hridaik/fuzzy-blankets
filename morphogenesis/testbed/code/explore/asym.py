import sys; sys.path.insert(0,'.')
from asm import *
XA,tA=body24_planA(); ty=tA.copy()
# break twin symmetry: lower-side (y<-0.3) cells get a different type than their upper twin
rot={1:3,2:4,3:2,4:1}
for i in range(24):
    if XA[1,i]<-0.3: ty[i]=rot[ty[i]]
tm=make_template(XA,codes_from_types(ty,xs=XA[0]),1.0,ty[None])
print('types',np.bincount(ty),'twins',(np.sort(np.linalg.norm(np.vstack([tm.Lam[0],tm.Cs[0]])[:,:,None]-np.vstack([tm.Lam[0],tm.Cs[0]])[:,None,:],axis=0)+1e9*np.eye(24),axis=1)[:,0]<0.05).sum())
n=24
for mode,kw in (('abs',dict(pos_on=True,pos_mode='abs')),('bodyframe',dict(pos_on=True,pos_mode='bodyframe',pi_a_x=0.0)),('off',dict(pos_on=False,pi_a_x=0.0))):
  for lp in (-2,-6):
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),**kw); t0=time.time()
    eng,o=run_draws(tm,P,4,T=500,dt=0.02)
    print('asym',mode,'lp',lp,'succ',sum(x['success'] for x in o),'d',[round(x['d_tmpl'],2) for x in o],'orbbel',[round(x['min_orbit_maxbel'],2) for x in o],'orbok',[x['orbit_complete'] for x in o],'shp',['%.0e'%x['shape_speed'] for x in o][:3],round(time.time()-t0),flush=True)
