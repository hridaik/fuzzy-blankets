import sys; sys.path.insert(0,'.')
from pairsearch import *
import pairsearch as ps
def tmpl2(X,t,amp,kap=1.0):
    lo=X[0].min(); hi=X[0].max(); C=codes_from_types(t); C[0]=0.3+amp*(X[0]-lo)/(hi-lo); return make_template(X,C,kap,t[None])
XA,tA,XB,tB=build_pair([1,3,4],[4,4],[3,3,2],[3,3,2])
for amp in (1.0,2.0,3.0):
    for tag,(X,ty) in (('A',(XA,tA)),('B',(XB,tB))):
        res=stab(tmpl2(X,ty,amp),T=250); print('amp',amp,tag,'d',round(res['d_tmpl'],3),'orbbel',round(res['min_orbit_maxbel'],2),'orbok',res['orbit_complete'],'shp %.0e'%res['shape_speed'],flush=True)
