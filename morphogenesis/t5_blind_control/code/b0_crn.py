import sys; sys.path.insert(0,'code')
import numpy as np
from rig import *
d=connect()
A=Ep(d,seed=5001,tag='crn_twin',baseline_tu=20); 
B=Ep(d,seed=5001,tag='crn_probe',baseline_tu=20)
print('same pre-action frame xy:',np.allclose(A.xy,B.xy),'state',A.base_state,B.base_state)
B.act('L3',0,0,1.5,5.0,7,reason='crn test')
A.run_until(60); B.run_until(60)
print('post-action diff max',np.abs(A.xy-B.xy).max(),'u twin',A.last['u'],'u probe',B.last['u'], 'dose',B.log['actions'][0]['dose'],B.log['actions'][0]['cells'])
S=Ep(d,seed=5001,sham_of=B.id,tag='sham',baseline_tu=20); S.act('L3',0,0,1.5,5.0,7); S.run_until(60)
print('sham vs twin diff',np.abs(S.xy-A.xy).max(),'sham dose',S.log['actions'][0]['dose'])
for e in (A,B,S): e.end()
print(d.status()['budget'] if 'budget' in d.status() else d.status())
