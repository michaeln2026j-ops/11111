# v5: stop this project's v4 experiment jobs (single i2Nav GNSS record; exp_system vendor bug) and run
# E1-E10 with the real multi-station NOAA CORS GNSS error bank. The system-level comparison follows as 007.
# Nothing is deleted: v4 outputs are archived under results/v4 and server-out/v4.
cd /workspace/11111
for p in $(ps -eo pid,args | awk '/control\/queue\/005_run_v4\.sh|scripts\/run_all\.sh|xargs -P|python3 exp_/ && !/awk/ {print $1}'); do
  kill "$p" 2>/dev/null && echo "stopped $p"
done
sleep 5
ps -eo pid,args | grep -E "run_all|python3 exp_" | grep -v grep || echo "no v4 jobs left"
mkdir -p results/v4 results/logs/v4
mv results/*_shard*of*.csv results/v4/ 2>/dev/null
for f in results/*.csv results/tables.md; do
  case "$f" in results/real.csv|results/real_aci.csv) ;; *) [ -f "$f" ] && mv "$f" results/v4/ ;; esac
done
mv results/logs/*.log results/logs/v4/ 2>/dev/null
# archive the v4 copies on the output branch as well, so only v5 files sit in server-out/results
mkdir -p "$HOME/server-out/v4/results" "$HOME/server-out/v4/logs"
mv "$HOME"/server-out/results/* "$HOME/server-out/v4/results/" 2>/dev/null
mv "$HOME"/server-out/logs/* "$HOME/server-out/v4/logs/" 2>/dev/null
python3 -c "import sys; sys.path.insert(0, 'experiments'); import core; [core.gnss_bank(g) for g in core.GNSS_GRADES]; print('gnss bank ok')"
SUITE=core JOBS=20 bash scripts/run_v5.sh > results/logs/run_v5_core.log 2>&1
python3 scripts/merge_shards.py
python3 experiments/make_tables.py > /dev/null 2>&1 || true
echo "V5 CORE DONE $(date -u)"
