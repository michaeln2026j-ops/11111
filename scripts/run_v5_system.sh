#!/usr/bin/env bash
# v5 part 2: E2b system-level comparison (frozen baseline modules, 3 CORS regimes x 30 fields)
# and the DGPS ablation at a 6 m implement (12 m leaves too few paddy fields after the headland).
#   JOBS=20 bash scripts/run_v5_system.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs
cd experiments
JOBFILE="../results/logs/jobs_v5_system.txt"
{
  for ((i = 0; i < 30; i++)); do
    echo "python3 exp_system.py --fields 30 --tag _v5 --shard $i --nshards 30 > ../results/logs/v5_system_${i}.log"
  done
  for ((i = 0; i < 4; i++)); do
    echo "python3 exp_ablation.py --fields 20 --w 6 --gnss dgps --kinds paddy --tag _dgps --shard $i --nshards 4 > ../results/logs/v5_ablation_dgps6_${i}.log"
  done
} > "$JOBFILE"
echo "$(wc -l < "$JOBFILE") jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
echo "all system jobs finished"
