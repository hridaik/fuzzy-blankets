import sys; sys.path.insert(0,'.')
from asm import *
d=json.load(open(os.path.join(M2A,'sealed','template_numbers.json')))['L4']
t16=make_template(np.array(d['P']),np.array(d['S']),1.0); n=16
print('16-cell template types',cell_types(t16.Cs[0]))
P=Params(k_mu=1.4,k_a=1.2,pos_on=True,pos_mode='abs'); key=jax.random.PRNGKey(0)
eng=make_engine(t16,P); res=[]
for k in range(10):
    MU0=np.random.default_rng(k).standard_normal((n,n))/8
    fin=eng.run_final(eng.init_from_mu(MU0),0.0,0.02,int(500/0.02),key,None,0)
    X,C,MU,_=[np.array(a) for a in fin]; p=np.array(jax.nn.softmax(MU,axis=1))
    res.append((round(d_rigid(X.T,cell_types(C.T),t16.Xs[0],cell_types(t16.Cs[0])),2), round(float(p.max(1).min()),2), len(set(p.argmax(1)))))
print(res)
