"""Summarise v7 system results: (1) same-stack layer comparison on BCD + LQR-I, (2) all systems.
Metric conventions as make_tables.py: meet = one-sided binomial test not significantly below 0.9 on
the field's n_test runs; infeasible counts as not meeting; regret = overlap - oracle overlap (pp)."""
import glob
import sys

import numpy as np
import pandas as pd
from scipy.stats import binomtest

d = pd.concat([pd.read_csv(f) for f in glob.glob(sys.argv[1] + '/system_v7*.csv')], ignore_index=True)
n_test = 200


def meets(p):
    return bool(np.isfinite(p)) and binomtest(int(round(p * n_test)), n_test, 0.9, alternative='less').pvalue >= 0.05


d['meet'] = d.p_nomiss.apply(meets)
pd.set_option('display.width', 250, 'display.max_rows', 400, 'display.max_colwidth', 64)
for r, g in d.groupby('regime'):
    nf = g.field.nunique()
    t = g.groupby('system').agg(P=('p_nomiss', 'mean'), meet=('meet', 'mean'),
                                ov=('overlap', lambda x: 100 * x.mean()), regret=('regret_pp', 'mean'),
                                infeas=('infeasible', lambda x: int(x.fillna(False).astype(bool).sum())),
                                n=('field', 'count'))
    print(f'\n=== {r}: {nf} fields; oracle meets {np.mean([meets(p) for p in g.drop_duplicates("field").oracle_p]):.2f}')
    same = t[t.index.str.contains('BCD \\+ LQR-I') | ~t.index.str.contains(' \\+ ')
             | t.index.str.contains('Conformal|Scenario|Gaussian|Wasserstein|GP cautious|Model-based|Tube')]
    print('-- layers on the BCD + LQR-I stack (meet >= 0.5)')
    print(same[same.meet >= 0.5].sort_values('regret').round(3).to_string())
    print('-- all systems with meet >= 0.9, by regret')
    print(t[t.meet >= 0.9].sort_values('regret').round(3).to_string())
