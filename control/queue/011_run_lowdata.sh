# E-low (docs/prereg_lowdata.md), after the v8 confirmatory run (queue 010) so they never share the cores.
cd /workspace/11111
sleep 180
while pgrep -f "scripts/run_v8.sh" >/dev/null || pgrep -f "010_run_v8.sh" >/dev/null; do sleep 60; done
echo "starting E-low $(date -u)"
python3 -c "import sys; sys.path.insert(0, 'experiments'); import evt_theory, exp_lowdata; print('modules ok')"
JOBS=20 bash scripts/run_lowdata.sh > results/logs/run_lowdata.log 2>&1
echo "LOWDATA DONE $(date -u)"
