import sys; sys.path.insert(0,'.')
from pairsearch import *
specs={'t0':([1,3,4],[4,4],[3,3,2],[2,3,3]),
       't1':([1,3,4],[4,4],[3,3,2],[3,3,2]),
       't2':([1,3,4],[4,4],[4,3,1],[1,3,4]),
       't3':([1,3,4],[4,4],[2,2,2,2],[1,3,4])}
for nm,(h,b,t,r) in specs.items():
    try: XA,tA,XB,tB=build_pair(h,b,t,r)
    except AssertionError: print(nm,'bad counts'); continue
    for tag,(X,ty) in (('A',(XA,tA)),('B',(XB,tB))):
        res=stab(tmpl(X,ty),T=250); print(nm,tag,'d',round(res['d_tmpl'],3),'orbbel',round(res['min_orbit_maxbel'],2),'orbok',res['orbit_complete'],'shp %.0e'%res['shape_speed'],flush=True)
