"""Same-stack (BCD + LQR-I) Pareto check: is every baseline layer dominated by one of our variants
(regret <= and meet >=, one strictly)? Also overall-system check over all systems."""
import glob
import sys

import numpy as np
import pandas as pd
from scipy.stats import binomtest

d = pd.concat([pd.read_csv(f) for f in glob.glob(sys.argv[1] + '/system_v7*.csv')], ignore_index=True)


def meets(p):
    return bool(np.isfinite(p)) and binomtest(int(round(p * 200)), 200, 0.9, alternative='less').pvalue >= 0.05


d['meet'] = d.p_nomiss.apply(meets)
ours = d.family.eq('ours')
same_ours = d.system.str.startswith('BCD + LQR-I + CE')
same_base = (~ours) & ~d.system.str.contains('Lenain|offset-free|ESO|vendor|Fields2Cover|Hameed|Follow-previous')
for scope, mask_o, mask_b in (('SAME STACK (BCD + LQR-I)', same_ours, same_base), ('ALL SYSTEMS', ours, ~ours)):
    print(f'\n######## {scope}')
    for r, g in d.groupby('regime'):
        t = g.groupby('system').agg(meet=('meet', 'mean'), regret=('regret_pp', 'mean'), fam=('family', 'first'))
        o = t.loc[t.index.isin(g[mask_o.loc[g.index]].system)]
        b = t.loc[t.index.isin(g[mask_b.loc[g.index]].system)]
        orc = np.mean([meets(p) for p in g.drop_duplicates('field').oracle_p])
        print(f'\n== {r} ({g.field.nunique()} fields, oracle meet {orc:.2f})')
        for nm, row in b.sort_values('regret').iterrows():
            if not np.isfinite(row.regret):
                continue
            dom = o[(o.regret <= row.regret) & (o.meet >= row.meet) & ((o.regret < row.regret) | (o.meet > row.meet))]
            tag = 'dominated by ' + dom.sort_values('regret').index[0] if len(dom) else 'NOT DOMINATED'
            print(f'  {row.regret:+7.2f} pp  meet {row.meet:.2f}  {nm[:58]:58s} -> {tag}')
