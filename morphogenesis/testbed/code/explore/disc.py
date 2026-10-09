import sys; sys.path.insert(0,'.')
from asm import *
d=json.load(open(os.path.join(M2A,'sealed','template_numbers.json')))['L4']
t16=make_template(np.array(d['P']),np.array(d['S']),1.0)
for tag,tm in (('v8',vanilla8()),('v16',t16),('A24',make_body('A')),('B24',make_body('B'))):
    L=tm.Lam[0]; C=tm.Cs[0]; X=tm.Xs[0]; n=tm.n
    def mind(M):
        D=np.linalg.norm(M[:,:,None]-M[:,None,:],axis=0)+1e9*np.eye(n); return D.min(1)
    f=np.vstack([L,C]); 
    print(tag,'min field+code dist (per slot, sorted):',np.round(np.sort(mind(f))[:8],3),'| pos nn',np.round(np.sort(mind(X))[:3],2),'| #slots with field-twin<0.05:',(mind(f)<0.05).sum())
