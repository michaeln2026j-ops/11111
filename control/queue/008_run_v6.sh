# v6: rerun of every calibrating experiment with the exact run score and the selection-free two-stage
# calibration (v5 audit). v5 outputs are archived (nothing is deleted); sweeps and real-robot results are kept.
cd /workspace/11111
mkdir -p results/v5 results/logs/v5
for f in results/*_shard*of*.csv; do
  case "$f" in results/sweep_*) ;; *) [ -f "$f" ] && mv "$f" results/v5/ ;; esac
done
for f in results/*.csv results/tables.md; do
  case "$f" in results/real.csv|results/real_aci.csv|results/sweep_paddy.csv|results/sweep_wheat.csv) ;;
    *) [ -f "$f" ] && mv "$f" results/v5/ ;; esac
done
mv results/logs/*.log results/logs/v5/ 2>/dev/null
mkdir -p "$HOME/server-out/v5/results" "$HOME/server-out/v5/logs"
for f in "$HOME"/server-out/results/*; do
  case "$f" in */sweep_*|*/real.csv|*/real_aci.csv) ;; *) [ -f "$f" ] && mv "$f" "$HOME/server-out/v5/results/" ;; esac
done
mv "$HOME"/server-out/logs/* "$HOME/server-out/v5/logs/" 2>/dev/null
python3 -c "import sys; sys.path.insert(0, 'experiments'); import core; print('exact_scores' in dir(core))"
JOBS=20 bash scripts/run_v6.sh > results/logs/run_v6.log 2>&1
python3 scripts/merge_shards.py
python3 experiments/make_tables.py > /dev/null 2>&1 || true
echo "V6 DONE $(date -u)"
