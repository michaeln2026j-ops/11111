# environment report
echo "== host"; hostname; nproc; free -g | head -2; df -h /workspace | tail -1
echo "== python"; which python3; python3 --version
python3 -c "import numpy, scipy, pandas, shapely, sklearn, matplotlib; print('deps OK', numpy.__version__, scipy.__version__, pandas.__version__, shapely.__version__)" 2>&1
echo "== pip config"; pip config list 2>/dev/null; echo "== processes"; ps -eo pid,etimes,args | grep -E "autorun|run_all|python3|pip" | grep -v grep | head -30
echo "== autorun.log"; tail -5 /workspace/11111/autorun.log 2>/dev/null
