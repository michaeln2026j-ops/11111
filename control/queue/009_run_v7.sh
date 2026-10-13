# v7: system-level comparison with CE+ (ceplus.py). Waits for the v6 suite (008) so the two never share
# the 20 cores; then runs scripts/run_v7.sh and merges the shards.
cd /workspace/11111
while pgrep -f "scripts/run_v6.sh" >/dev/null || pgrep -f "008_run_v6.sh" >/dev/null; do sleep 60; done
echo "v6 finished, starting v7 $(date -u)"
python3 -c "import sys; sys.path.insert(0, 'experiments'); import ceplus; print('ceplus ok')"
JOBS=20 bash scripts/run_v7.sh > results/logs/run_v7.log 2>&1
python3 scripts/merge_shards.py
echo "V7 DONE $(date -u)"
