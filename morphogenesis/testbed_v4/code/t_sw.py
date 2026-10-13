import sys,time; sys.path.insert(0,'.')
from lib4 import *
d=median_dish(); print(d, ref_angles(d,'phi04'), ref_angles(d,'phi0'), lstar_for(d,'phi04'), lstar_for(d,'phi0'))
for c in CENTRES: print(c, lit_cells(settled(d,'phi04','a')[1], c).sum())
t=time.time(); S=switch_trial(d,'phi04','a','middle',16/d['g'],1.0); print(time.time()-t)
r=score_switch(S,'a',ref_angles(d,'phi04')['b']); print({k:v for k,v in r.items() if k!='cell_cross'})
print(S['angle'][::40].round(1), S['mean_rho'][::40].round(2), S['jac'][::40].round(3))
