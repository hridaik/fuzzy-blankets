import sys; sys.path.insert(0,'.')
from asm import *
tm=make_body('A'); n=24; ty=type_vector(tm); key=jax.random.PRNGKey(0)
P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(-10)),pos_on=True,pos_mode='abs',T_dev=1.0); eng=make_engine(tm,P)
st=(jnp.array(tm.Xs[0].T),jnp.array(tm.Cs[0].T),jnp.array(np.eye(n)*8.0),jnp.zeros((n,1)))
fin,tr=eng.run(st,100.0,0.02,int(300/0.02),key,None,0,save_every=500)
for k in range(0,30,3):
    X=np.array(tr[0][k]); MU=np.array(tr[2][k]); p=np.array(jax.nn.softmax(MU,axis=1)); C=np.array(tr[1][k])
    print('t',(k+1)*10,'d_tmpl',round(d_rigid(X.T,cell_types(C.T),tm.Xs[0],ty),3),'p max min',round(p.max(1).min(),3),'mean',round(p.max(1).mean(),3),'worst cell',p.max(1).argmin())
