import sys,json; sys.path.insert(0,'code')
from controller import *
d=connect(); C=Controller(sys.argv[1])
for s in [int(x) for x in sys.argv[2:]]:
    S=C.run(d,s,tag='b3_dev'); print({k:S[k] for k in('seed','start','success','reason','n_pulses','dose','t_first_action','t_last_end','time_to_success','V_body_conservative','events','end_state')},flush=True)
