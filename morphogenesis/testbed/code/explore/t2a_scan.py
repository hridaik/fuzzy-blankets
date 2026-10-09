import sys,time,dataclasses; sys.path.insert(0,'.')
from common import *
from shape import *
t=vanilla8(); key=jax.random.PRNGKey(0)
ref=json.load(open(M2A+'/sealed/reference_phenotype_v2.json')); rp=np.array(ref['pos']); rs=np.array(ref['sec']); tr_=cell_types(rs)
for std in (1/8, 1.0, 3.0):
  for lp in (-2,-4,-6):
    for ls in (3,):
        P=Params(k_mu=1.4,k_a=1.2,pos_on=False,pi_a_x=0.0,pi_prior=float(np.exp(lp)),pi_c=float(np.exp(ls)),pi_l=float(np.exp(ls)),pi_x=float(np.exp(ls)),pi_ref=float(np.exp(ls)),pi_act=1.5*float(np.exp(ls-1)))
        eng=make_engine(t,P); out=[]
        for k in range(4):
            MU0=np.random.default_rng(k).standard_normal((8,8))*std
            st=eng.init_from_mu(MU0)
            fin=eng.run_final(st,0.0,0.02,int(800/0.02),key,None,0)
            X,C,MU,_=[np.array(a) for a in fin]
            mb=np.array(jax.nn.softmax(MU,axis=1)).max(1)
            out.append((round(float(mb.min()),2), round(d_rigid(X.T,cell_types(C.T),rp,tr_),2)))
        print('std',std,'log prior',lp,'log sens',ls,out,flush=True)
