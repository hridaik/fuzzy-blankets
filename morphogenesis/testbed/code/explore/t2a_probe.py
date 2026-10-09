import sys,time,dataclasses; sys.path.insert(0,'.')
from common import *
from shape import *
t=vanilla8(); key=jax.random.PRNGKey(0)
P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0)
eng=make_engine(t,P)
ref=json.load(open(M2A+'/sealed/reference_phenotype_v2.json')); rp=np.array(ref['pos']); rs=np.array(ref['sec'])
tr_=cell_types(rs)
res=[]
t0=time.time()
for k in range(6):
    o=oracle_run(f'primary_{k:04d}'); st=eng.init_from_mu(o['v0'].T)
    fin=eng.run_final(st,0.0,0.02,int(600/0.02),key,None,0)
    X,C,MU,_=[np.array(a) for a in fin]
    dr=d_rigid(X.T,cell_types(C.T),rp,tr_)
    sp=max(float(jnp.abs(a).max()) for a in eng.drift(fin,1e9,jnp.zeros((8,4))))
    res.append((round(dr,4),'%.0e'%sp, np.round(X.mean(0),2)))
print(res, time.time()-t0)
Xs=[];Ts=[]
for k in range(6):
    o=oracle_run(f'primary_{k:04d}'); st=eng.init_from_mu(o['v0'].T)
    fin=eng.run_final(st,0.0,0.02,int(600/0.02),key,None,0)
    X,C,MU,_=[np.array(a) for a in fin]; Xs.append(X.T); Ts.append(cell_types(C.T))
    print(k,'maxbel',np.round(np.array(jax.nn.softmax(MU,axis=1)).max(1),2),'types',Ts[-1])
M=np.array([[d_rigid(Xs[i],Ts[i],Xs[j],Ts[j]) for j in range(6)] for i in range(6)]); print(np.round(M,3))
M2=np.array([[d_rigid(Xs[i],Ts[i],Xs[j],Ts[j],reflection=True) for j in range(6)] for i in range(6)]); print(np.round(M2,3))
print('to template',[round(d_rigid(x,tt,t.Xs[0],cell_types(t.Cs[0]),reflection=True),3) for x,tt in zip(Xs,Ts)])
