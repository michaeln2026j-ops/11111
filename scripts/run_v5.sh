#!/usr/bin/env bash
# v5 suite: every simulated experiment with the REAL multi-station NOAA CORS GNSS error bank
# (core.gnss_bank, receiver grades rtk_fix / rtk_float / dgps) instead of the single i2Nav record.
#
#   SUITE=core   JOBS=20 bash scripts/run_v5.sh   # E1-E10 (needs only core.py / exp_lib.py)
#   SUITE=system JOBS=20 bash scripts/run_v5.sh   # E2b system-level comparison (needs frozen baselines/)
#
# Results go to results/ (main tag _v5), logs to results/logs/v5_*.log.
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
SUITE="${SUITE:-core}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p results/logs
cd experiments
JOBFILE="../results/logs/jobs_v5_${SUITE}.txt"

run_sharded() {  # run_sharded <name> <nshards> <command...>
  local name="$1" n="$2"; shift 2
  for ((i = 0; i < n; i++)); do
    echo "$*" --shard "$i" --nshards "$n" ">" "../results/logs/v5_${name}_${i}.log"
  done
}

{
  if [ "$SUITE" = system ]; then
    run_sharded system 30 python3 exp_system.py --fields 30 --tag _v5
  else
    run_sharded main_paddy 12 python3 exp_main.py --kind paddy --fields 60 --tag _v5
    run_sharded main_wheat 12 python3 exp_main.py --kind wheat --fields 60 --tag _v5
    run_sharded sweep_paddy 8 python3 exp_sweep.py --kind paddy --fields 60
    run_sharded sweep_wheat 8 python3 exp_sweep.py --kind wheat --fields 60
    run_sharded ablation 6 python3 exp_ablation.py --fields 30
    run_sharded ablation_hard 4 python3 exp_ablation.py --fields 20 --w 1.5 --wet --kinds paddy --tag _hard
    run_sharded ablation_dgps 4 python3 exp_ablation.py --fields 20 --w 12 --gnss dgps --kinds paddy --tag _dgps
    run_sharded validity 12 python3 exp_validity.py --kind paddy --fields 12 --trials 4
    run_sharded cross 10 python3 exp_cross.py --repeats 10 --n-test-runs 40
    run_sharded cross_rev 8 python3 exp_cross.py --reverse --repeats 8 --n-test-runs 40
    run_sharded cross2_paddy 10 python3 exp_cross2.py --kind paddy --repeats 10
    run_sharded cross2_wheat 10 python3 exp_cross2.py --kind wheat --repeats 10
    run_sharded sens 10 python3 exp_sens.py --part sweep --fields 10 --n-test 200
    run_sharded aci 6 python3 exp_sens.py --part aci --aci-fields 6 --aci-T 400
  fi
} > "$JOBFILE"

echo "$(wc -l < "$JOBFILE") $SUITE jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < "$JOBFILE"
echo "all $SUITE jobs finished"
