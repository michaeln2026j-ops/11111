#!/usr/bin/env bash
# Run a contiguous range of the 45 v8 shards (same commands as scripts/run_v8.sh, resumable).
#   JOBS=4 bash scripts/run_v8_range.sh FIRST LAST        e.g. 15 24
set -euo pipefail
cd "$(dirname "$0")/.."
FIRST=$1; LAST=$2
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs
cd experiments
for ((i = FIRST; i <= LAST; i++)); do
  echo python3 exp_system.py --fields 30 --tag _v8 --offset 50 --shard "$i" --nshards 45 ">>" "../results/logs/v8_system_${i}.log"
done | xargs -P "$JOBS" -I{} bash -c "{} 2>&1"
echo "v8 shards $FIRST-$LAST finished"
