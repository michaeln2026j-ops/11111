"""Merge results/<name>_shardIofN.csv files into results/<name>.csv."""
import glob
import os
import re
from collections import defaultdict

import pandas as pd

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")

groups = defaultdict(list)
for f in glob.glob(os.path.join(RES, "*_shard*of*.csv")):
    base = re.sub(r"_shard\d+of\d+\.csv$", ".csv", os.path.basename(f))
    groups[base].append(f)
for base, files in sorted(groups.items()):
    df = pd.concat([pd.read_csv(f) for f in sorted(files)], ignore_index=True)
    df.to_csv(os.path.join(RES, base), index=False)
    n_expected = int(re.search(r"of(\d+)\.csv$", files[0]).group(1))
    note = "" if len(files) == n_expected else f"  WARNING: {len(files)}/{n_expected} shards present"
    print(f"{base}: {len(files)} shards, {len(df)} rows{note}")
