# v5 part 2: system-level comparison with the frozen baselines + DGPS ablation (6 m)
cd /workspace/11111
JOBS=20 bash scripts/run_v5_system.sh > results/logs/run_v5_system.log 2>&1
python3 scripts/merge_shards.py
python3 experiments/make_tables.py > /dev/null 2>&1 || true
echo "V5 SYSTEM DONE $(date -u)"
