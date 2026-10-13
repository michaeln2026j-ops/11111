# v4 full suite on 20 cores: corrected simulator + earth-fixed i2Nav RTK errors (CORS model comes as v5)
cd /workspace/11111
mkdir -p results/logs
SYSTEM=1 JOBS=20 bash scripts/run_all.sh > results/logs/run_all_v4.log 2>&1
python3 scripts/merge_shards.py
python3 experiments/make_tables.py > /dev/null 2>&1 || true
echo "V4 SUITE DONE $(date -u)"
