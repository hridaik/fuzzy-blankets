import sys; sys.path.insert(0,'.')
from asm import *
for k in ('A','B','chiral'):
    tm=make_body(k); f=np.vstack([tm.Lam[0],tm.Cs[0]]); n=24
    D=np.linalg.norm(f[:,:,None]-f[:,None,:],axis=0); D[D<1e-6]=np.inf; np.fill_diagonal(D,np.inf)
    print(k,'nearest non-twin fingerprint distance per slot:',np.round(np.sort(D.min(1))[:10],2))
