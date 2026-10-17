# install dependencies (try default index, then a domestic mirror)
pip install -q numpy scipy pandas shapely scikit-learn matplotlib 2>&1 | tail -2 || true
python3 -c "import numpy, scipy, pandas, shapely, sklearn, matplotlib" 2>/dev/null \
  || pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple numpy scipy pandas shapely scikit-learn matplotlib 2>&1 | tail -2
python3 -c "import numpy, scipy, pandas, shapely, sklearn, matplotlib; print('deps OK')"
