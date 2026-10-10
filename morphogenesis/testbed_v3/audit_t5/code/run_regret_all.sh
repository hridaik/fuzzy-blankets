#!/bin/bash
# launches 4 resumable worker slices of regret.py (A3)
cd "$(dirname "$0")"
SEEDS=$(python3 -c "
import regret
by=regret.load_heldout(); print(' '.join(str(s) for s in sorted(s for s,v in by.items() if v['ctrl']['reason'] not in ('quota_skip','baseline_not_clean'))))")
i=0; declare -a SL; for s in $SEEDS; do SL[$((i%4))]="${SL[$((i%4))]} $s"; i=$((i+1)); done
for k in 0 1 2 3; do
  OMP_NUM_THREADS=2 XLA_FLAGS="--xla_cpu_multi_thread_eigen=false intra_op_parallelism_threads=2" nohup python3 regret.py ${SL[$k]} > ../data/regret_worker$k.log 2>&1 &
done
wait
