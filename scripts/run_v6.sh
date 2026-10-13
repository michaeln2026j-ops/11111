#!/usr/bin/env bash
# v6 suite = v5 (real NOAA CORS GNSS bank) + the validity fixes of the v5 audit: exact run score
# (core.exact_scores) and selection-free two-stage calibration. Everything that calibrates is rerun;
# the fixed-overlap sweeps (exp_sweep, no calibration) and the real-robot replay (exp_real) are unchanged.
#   JOBS=20 bash scripts/run_v6.sh
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs
cd experiments
JOBFILE="../results/logs/jobs_v6.txt"

run_sharded() {  # run_sharded <name> <nshards> <command...>
  local name="$1" n="$2"; shift 2
  for ((i = 0; i < n; i++)); do
    echo "$*" --shard "$i" --nshards "$n" ">" "../results/logs/v6_${name}_${i}.log"
  done
}

{
  # longest jobs first (system-level comparison), then the rest
  run_sharded system 30 python3 exp_system.py --fields 30 --tag _v6
  run_sharded main_paddy 12 python3 exp_main.py --kind paddy --fields 60 --tag _v6
  run_sharded main_wheat 12 python3 exp_main.py --kind wheat --fields 60 --tag _v6
  run_sharded validity 12 python3 exp_validity.py --kind paddy --fields 12 --trials 4
  run_sharded ablation 6 python3 exp_ablation.py --fields 30
  run_sharded ablation_hard 4 python3 exp_ablation.py --fields 20 --w 1.5 --wet --kinds paddy --tag _hard
  run_sharded ablation_dgps 4 python3 exp_ablation.py --fields 20 --w 6 --gnss dgps --kinds paddy --tag _dgps
  run_sharded cross 10 python3 exp_cross.py --repeats 10 --n-test-runs 40
  run_sharded cross_rev 8 python3 exp_cross.py --reverse --repeats 8 --n-test-runs 40
  run_sharded cross2_paddy 10 python3 exp_cross2.py --kind paddy --repeats 10
  run_sharded cross2_wheat 10 python3 exp_cross2.py --kind wheat --repeats 10
  run_sharded sens 10 python3 exp_sens.py --part sweep --fields 10 --n-test 200
  run_sharded aci 6 python3 exp_sens.py --part aci --aci-fields 6 --aci-T 400
  run_sharded diag 6 python3 diag_validity.py --fields 6 --reps 40
} > "$JOBFILE"

echo "$(wc -l < "$JOBFILE") v6 jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
echo "all v6 jobs finished"
