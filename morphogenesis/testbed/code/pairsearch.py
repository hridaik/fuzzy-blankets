import sys; sys.path.insert(0,'.')
from asm import *
def build_pair(head, body, tail, rear, dx=0.9):
    """rows lists. A = head|body|tail ; B = head|body|rear (rear re-codes the tail slots as a second head). returns tmplA,tmplB (K=1 each)"""
    def rows(sizes,x0):
        out=[]
        for r,k in enumerate(sizes):
            for j in range(k): out.append((x0+r*dx,(j-(k-1)/2.0)))
        return out
    H=rows(head,0.0); xb=len(head)*dx; Bd=rows(body,xb); xt=xb+len(body)*dx; T=rows(tail,xt); R=rows(rear,xt)
    assert len(H)+len(Bd)+len(T)==24 and len(T)==len(R)
    # body types: cells with |y| < 1.0 -> trunk(T2) else limb(T3), (rows with <=2 cells all trunk)
    bt=[2 if abs(p[1])<1.0 else 3 for p in Bd]
    XA=np.array(H+Bd+T,float).T; tA=np.array([1]*len(H)+bt+[4]*len(T))
    XB=np.array(H+Bd+R,float).T; tB=np.array([1]*len(H)+bt+[1]*len(R))
    c=XA[0].mean(); XA[0]-=c; XB[0]-=c
    return XA,tA,XB,tB
def tmpl(X,t,kap=1.0,lo=None,hi=None):
    lo=X[0].min() if lo is None else lo; hi=X[0].max() if hi is None else hi
    C=codes_from_types(t); C[0]=0.5+1.0*(X[0]-lo)/(hi-lo)
    return make_template(X,C,kap,t[None])
def stab(tm,lp=-10,jit=0.3,T=300,seed=0):
    n=tm.n; ty=type_vector(tm); key=jax.random.PRNGKey(0)
    P=Params(k_mu=1.4,k_a=1.2,pi_prior=float(np.exp(lp)),pi_a_x=0.0,pi_a_c=0.0,pos_on=False); eng=make_engine(tm,P)
    rng=np.random.default_rng(seed)
    st=(jnp.array(tm.Xs[0].T+jit*rng.standard_normal((n,2))),jnp.array(tm.Cs[0].T),jnp.array(np.eye(n)*8.0+jit*rng.standard_normal((n,n))),jnp.zeros((n,1)))
    w=np.linalg.eigvals(np.array(eng.jac_flat(st,1e9))); dt=min(0.02,0.8/np.abs(w).max())
    fin=eng.run_final(st,1e4,dt,int(T/dt),key,None,0); r=analyse(eng,tm,fin,0,ty); r['dt']=dt; r['rho']=float(np.abs(w).max()); return r
if __name__=="__main__":
    specs={'s0':([1,3,4],[4,4],[2,2,2,2],[3,3,2]),
           's1':([1,3,3],[4,4,2],[2,2,2,1],[3,3,1]),
           's2':([1,3,4],[4,4,4],[3,3,2],[3,3,2]) ,
           's3':([1,3,4],[4,4,4,4],[2,2],[2,2]) }
    for nm,(h,b,t,r) in specs.items():
        try: XA,tA,XB,tB=build_pair(h,b,t,r)
        except AssertionError: print(nm,'bad counts'); continue
        for tag,(X,ty) in (('A',(XA,tA)),('B',(XB,tB))):
            res=stab(tmpl(X,ty)); print(nm,tag,'d',round(res['d_tmpl'],3),'orbbel',round(res['min_orbit_maxbel'],2),'orbok',res['orbit_complete'],'shp %.0e'%res['shape_speed'],flush=True)
