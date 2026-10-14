"""EXPLORATORY (same fields as the pre-registered run): leave-one-field-out lambda of candidate pivots,
compared with the per-field oracle; overlap is a deterministic function of the plan."""
import sys, glob, pickle, math, numpy as np
sys.path.insert(0, '/home/user/11111/experiments')
import ceplus as CP, exp_lowdata as X, exp_system as E, exp_lib as L, core
key = sys.argv[1]
rname, reg = X.regime(key); w = reg['w']
fields = core.load_fields(reg['kind'], w=w, seed=0)
recs = sorted([pickle.load(open(f, 'rb')) for f in glob.glob(f'/home/user/11111/results/lowdata/A_{key}_*.pkl')], key=lambda r: r['fi'])
recs = [r for r in recs if not np.isnan(r['Fhat']).any()]
n = len(recs)
S = np.array([r['S_hist'] for r in recs]); orc = np.array([r['oracle_lam'] for r in recs])
q9 = np.array([X.inv_cdf(r['tgrid'], r['Fhat'], 0.9) for r in recs])
V = np.array([np.interp(r['S_hist'], r['tgrid'], np.maximum.accumulate(r['Fhat'])) for r in recs])
lg = np.array([math.sqrt(2 * math.log(max(r['N_len'], 2))) for r in recs])
print(f"{key}: n={n}  oracle CV {orc.std()/orc.mean():.3f}  theory/oracle mean {np.mean(q9/orc):.3f} sd {np.std(q9/orc):.3f}  corr {np.corrcoef(q9, orc)[0,1]:.2f}")
rng = np.random.default_rng(0)
ovc = {}
def ov(i, lam):
    k = (i, round(lam, 4))
    if k not in ovc:
        try: ovc[k] = L.overlap_ratio(fields[recs[i]['fi']], core.plan(fields[recs[i]['fi']], w, lam, E.UNIT), w)
        except ValueError: ovc[k] = np.nan
    return ovc[k]
res = {}
for g in range(n):
    cal = rng.choice([i for i in range(n) if i != g], size=min(30, n - 1), replace=False)
    for tag, dl in (("marg", None), ("PAC", 0.1)):
        res.setdefault(f"raw {tag}", []).append(CP.quantile(S[cal], 0.1, dl))
        res.setdefault(f"PIT {tag}", []).append(X.inv_cdf(recs[g]['tgrid'], recs[g]['Fhat'], CP.quantile(V[cal], 0.1, dl)))
        res.setdefault(f"ratio-q0.9 {tag}", []).append(q9[g] * CP.quantile(S[cal] / q9[cal], 0.1, dl))
        res.setdefault(f"scale-law {tag}", []).append(lg[g] * CP.quantile(S[cal] / lg[cal], 0.1, dl))
        res.setdefault(f"ratio-oracle(ideal) {tag}", []).append(orc[g] * CP.quantile(S[cal] / orc[cal], 0.1, dl))
oo = np.array([ov(i, orc[i]) for i in range(n)])
for m, lam in res.items():
    lam = np.array(lam)
    ex = np.array([100 * (ov(i, lam[i]) - oo[i]) for i in range(n)])
    print(f"  {m:26s} lam/oracle mean {np.mean(lam/orc):.3f} sd {np.std(lam/orc):.3f}  frac below oracle {np.mean(lam < orc):.2f}  excess {np.nanmean(ex):+.2f} pp")
