# stop the first autorun (old error model); its results would be superseded anyway
for p in $(ps -eo pid,args | awk '/scripts\/autorun\.sh|scripts\/run_all\.sh|python3 exp_/ && !/awk/ {print $1}'); do kill "$p" 2>/dev/null && echo "killed $p"; done
sleep 3; ps -eo pid,args | grep -E "autorun|run_all|python3 exp_" | grep -v grep || echo "none left"
