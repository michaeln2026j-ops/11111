#!/usr/bin/env bash
# Run the full experiment suite on a multi-core server (e.g. an AutoDL instance).
#
#   bash scripts/run_all.sh            # uses all CPU cores
#   JOBS=32 bash scripts/run_all.sh    # or set the number of parallel processes
#
# Each experiment is split into field shards so that JOBS processes run at once.
# Results go to results/, logs to results/logs/. Merge shards and build tables and
# figures afterwards with:  python3 scripts/merge_shards.py && python3 experiments/make_tables.py
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS="${JOBS:-$(nproc)}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1  # one core per process
mkdir -p results/logs
cd experiments

run_sharded() {  # run_sharded <name> <nshards> <command...>
  local name="$1" n="$2"; shift 2
  for ((i = 0; i < n; i++)); do
    echo "$*" --shard "$i" --nshards "$n" ">" "../results/logs/${name}_${i}.log"
  done
}

{
  # E2 main comparison (corrected simulator), 60 + 60 real fields
  run_sharded main_paddy 12 python3 exp_main.py --kind paddy --fields 60 --tag _v4
  run_sharded main_wheat 12 python3 exp_main.py --kind wheat --fields 60 --tag _v4
  # E10 fixed-overlap response curves (oracle per-field lambda*, regret metric)
  run_sharded sweep_paddy 8 python3 exp_sweep.py --kind paddy --fields 60
  run_sharded sweep_wheat 8 python3 exp_sweep.py --kind wheat --fields 60
  # E9 ablations: default and hard regime
  run_sharded ablation 6 python3 exp_ablation.py --fields 30
  run_sharded ablation_hard 4 python3 exp_ablation.py --fields 20 --w 1.5 --rtk-scale 3 --kinds paddy --tag _hard
  # E1 validity, E3 cross-field, E4/E5 sensitivity, E6 drift, E8 real robot (unsharded)
  echo "python3 exp_validity.py --kind paddy --fields 12 --trials 4 > ../results/logs/validity.log"
  echo "python3 exp_cross.py --repeats 10 --n-test-runs 40 > ../results/logs/cross.log"
  echo "python3 exp_cross.py --reverse --repeats 8 --n-test-runs 40 > ../results/logs/cross_rev.log"
  echo "python3 exp_cross2.py --kind paddy --repeats 10 > ../results/logs/cross2_paddy.log"
  echo "python3 exp_cross2.py --kind wheat --repeats 10 > ../results/logs/cross2_wheat.log"
  echo "python3 exp_sens.py --part sweep --fields 10 --n-test 200 > ../results/logs/sens.log"
  echo "python3 exp_sens.py --part aci --aci-fields 6 --aci-T 400 > ../results/logs/aci.log"
  echo "python3 exp_real.py > ../results/logs/real.log"
  # E2b system-level comparison against published algorithms (added when ready)
  if [ -f exp_system.py ]; then
    run_sharded system 24 python3 exp_system.py
  fi
} > ../results/logs/jobs.txt

echo "$(wc -l < ../results/logs/jobs.txt) jobs, running $JOBS at a time"
xargs -P "$JOBS" -I{} bash -c "{} 2>&1" < ../results/logs/jobs.txt
echo "all jobs finished"
