"""Merge results/<name>_shardIofN.csv files into results/<name>.csv.

Refuses (exit code 1, nothing written for that name) when the shard files of one name come from runs
with different N, or when shards are missing, so stale shards of an earlier run can never be mixed
silently into new results.
"""
import glob
import os
import re
import sys
from collections import defaultdict

import pandas as pd

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")

groups = defaultdict(lambda: defaultdict(dict))  # base -> N -> {i: path}
for f in glob.glob(os.path.join(RES, "*_shard*of*.csv")):
    m = re.match(r"(.*)_shard(\d+)of(\d+)\.csv$", os.path.basename(f))
    if m:
        groups[m.group(1) + ".csv"][int(m.group(3))][int(m.group(2))] = f
bad = False
for base, byn in sorted(groups.items()):
    if len(byn) != 1:
        print(f"{base}: REFUSED, shard sets of different runs present (N = {sorted(byn)})")
        bad = True
        continue
    (n_expected, files), = byn.items()
    missing = sorted(set(range(n_expected)) - set(files))
    df = pd.concat([pd.read_csv(files[i]) for i in sorted(files)], ignore_index=True)
    df.to_csv(os.path.join(RES, base), index=False)
    note = f"  WARNING: {len(files)}/{n_expected} shards present, missing {missing}" if missing else ""
    print(f"{base}: {len(files)} shards, {len(df)} rows{note}")
    bad |= bool(missing)
sys.exit(1 if bad else 0)
