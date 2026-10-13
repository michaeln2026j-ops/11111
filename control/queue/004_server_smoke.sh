# check that the experiment stack runs on this server (small, 1 field per regime)
cd experiments
python3 -c "import numpy, scipy, pandas, shapely, sklearn, matplotlib; print('deps', numpy.__version__, scipy.__version__, pandas.__version__, shapely.__version__, sklearn.__version__)"
export OMP_NUM_THREADS=1
time python3 exp_system.py --fields 1 --n-cal 30 --n-test 30 --regimes R1 --tag _srvsmoke 2>&1 | grep -vE "warn" | tail -5
python3 -c "import pandas as pd; d=pd.read_csv('../results/system_srvsmoke.csv'); print(d[['system','p_nomiss','overlap']].round(3).to_string())"
