# v8 confirmatory system-level run on fresh fields (offset 50), pre-registered in docs/theory_v8.md.
cd /workspace/11111
while pgrep -f "scripts/run_v7.sh" >/dev/null; do sleep 60; done
python3 -c "import sys; sys.path.insert(0, 'experiments'); import ceplus; print('ceplus ok', ceplus.GATE)"
JOBS=20 bash scripts/run_v8.sh > results/logs/run_v8.log 2>&1
python3 scripts/merge_shards.py
echo "V8 DONE $(date -u)"
