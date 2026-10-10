#!/bin/bash
# starts (or restarts) the sealed live server; state persists in this directory
cd /home/hkhurana/work/code/fuzzy-blankets/morphogenesis/testbed_v3/live
exec python live_server.py --ready /home/hkhurana/work/code/fuzzy-blankets/morphogenesis/t5_blind_control/rig/ready.json --sealed /home/hkhurana/work/code/fuzzy-blankets/morphogenesis/testbed_v3/live_sealed_t5 --budget '{"total_episodes": 1500, "total_time": 500000.0, "total_dose": 3500000.0}' >> /home/hkhurana/work/code/fuzzy-blankets/morphogenesis/testbed_v3/live_sealed_t5/server.out 2>> /home/hkhurana/work/code/fuzzy-blankets/morphogenesis/testbed_v3/live_sealed_t5/server.err
