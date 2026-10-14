"""E-low analysis, exactly as pre-registered (docs/prereg_lowdata.md section 4).

    python3 scripts/analyze_lowdata.py            # reads results/lowdata/lowdata_R*.csv

Validity
  marginal class: pooled P(no miss) over test fields not significantly below 0.9
                  (one-sided test with a field-clustered standard error, level 0.05);
  PAC class:      number of fields failing the per-field meet test (successes <= 172 of 200, alpha = 0.043)
                  not significantly above Bin(F, delta + alpha) (one-sided upper binomial test, level 0.05).
Efficiency
  mean excess overlap (pp over the per-field oracle); relative improvement of CE-EVT over the strongest
  VALID comparator of the same class; one-sided paired Wilcoxon per field, Holm over regime x comparator.
  The relative difference in absolute overlap is reported as well.
"""
import glob
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "results", "lowdata")
EPS, DELTA, ALPHA_MEET, N_TEST, LEVEL = 0.1, 0.1, 0.043, 200, 0.05
MEET_MAX_FAIL = 172  # meet test fails iff successes <= 172 of 200 (theory_v8 Prop 4)

OURS = {"marginal": "CE-EVT (ours)", "PAC": "CE-EVT PAC (ours)"}
COMPARATORS = {"marginal": ["Pooled conformal, raw scores", "Farmer-tuned global overlap", "Spec overlap (2x p2p)"],
               "PAC": ["Pooled conformal, raw scores PAC", "Farmer-tuned global overlap", "Spec overlap (2x p2p)"]}


def validity(d, cls):
    p = d["p_nomiss"].fillna(0.0).to_numpy()  # a method that cannot deploy on a field fails there
    if cls == "marginal":
        m, se = p.mean(), p.std(ddof=1) / np.sqrt(len(p))
        pval = stats.norm.cdf((m - (1 - EPS)) / max(se, 1e-12))
        return dict(P=m, n_fields=len(p), p_value=pval, valid=pval >= LEVEL)
    succ = np.rint(p * N_TEST).astype(int)
    k = int((succ <= MEET_MAX_FAIL).sum())
    pval = stats.binom.sf(k - 1, len(p), DELTA + ALPHA_MEET)
    return dict(P=p.mean(), n_fields=len(p), fails=k, p_value=pval, valid=pval >= LEVEL)


def main():
    files = sorted(glob.glob(os.path.join(SRC, "lowdata_R*.csv")))
    if not files:
        sys.exit("no results")
    df = pd.concat([pd.read_csv(f) for f in files])
    out, tests = [], []
    for reg, dr in df.groupby("regime"):
        n_inf = int(dr.get("infeasible", pd.Series(dtype=float)).fillna(False).astype(bool).sum())
        out.append(f"\n== {reg}: {dr['fid'].nunique()} test fields, infeasible deployments {n_inf}")
        for meth, dm in dr.groupby("method"):
            cls = "PAC" if "PAC" in meth else "marginal"
            v = validity(dm, cls)
            out.append(f"  {meth:42s} [{cls:8s}] P={v['P']:.3f} valid={'yes' if v['valid'] else 'NO '} "
                       f"(p={v['p_value']:.3f}{', fails ' + str(v['fails']) if 'fails' in v else ''})  "
                       f"excess={dm['excess_pp'].mean():+.2f} pp  overlap={100 * dm['overlap'].mean():.2f}%")
        for cls, ours in OURS.items():
            do = dr[dr.method == ours].set_index("fid")
            if do.empty or not validity(dr[dr.method == ours], cls)["valid"]:
                out.append(f"  [{cls}] CE-EVT NOT valid -> claim fails in {reg}")
                continue
            valid_comp = [c for c in COMPARATORS[cls]
                          if not dr[dr.method == c].empty and validity(dr[dr.method == c], cls)["valid"]]
            if not valid_comp:
                out.append(f"  [{cls}] no valid comparator")
                continue
            best = min(valid_comp, key=lambda c: dr[dr.method == c]["excess_pp"].mean())
            for c in valid_comp:
                dc = dr[dr.method == c].set_index("fid")
                j = do.index.intersection(dc.index)
                a, b = do.loc[j, "excess_pp"], dc.loc[j, "excess_pp"]
                rel = (b.mean() - a.mean()) / b.mean() if b.mean() > 0 else np.nan
                rel_abs = (dc.loc[j, "overlap"].mean() - do.loc[j, "overlap"].mean()) / dc.loc[j, "overlap"].mean()
                p = stats.wilcoxon(a, b, alternative="less").pvalue if (a != b).any() else 1.0
                tests.append(dict(regime=reg, cls=cls, comparator=c, strongest=c == best, rel=rel, rel_abs=rel_abs,
                                  p=p, ours=a.mean(), comp=b.mean()))
    t = pd.DataFrame(tests)
    if not t.empty:
        order = np.argsort(t["p"].to_numpy())
        m = len(t)
        adj = np.empty(m)
        run = 0.0
        for r, i in enumerate(order):
            run = max(run, min(1.0, (m - r) * t["p"].iloc[i]))
            adj[i] = run
        t["p_holm"] = adj
        out.append("\n== CE-EVT vs valid comparators (excess overlap, pp); claim uses the strongest valid one")
        for _, r in t.iterrows():
            ok = r.strongest and r.rel >= 0.10 and r.p_holm < LEVEL
            out.append(f"  {r.regime[:2]} [{r.cls:8s}] vs {r.comparator:34s}{' *strongest*' if r.strongest else '            '} "
                       f"ours {r.ours:+.2f} vs {r.comp:+.2f}  rel {100 * r.rel:+.1f}%  abs-overlap rel {100 * r.rel_abs:+.1f}%  "
                       f"p_holm {r.p_holm:.4f}{'  CLAIM MET' if ok else ('  claim NOT met' if r.strongest else '')}")
        t.to_csv(os.path.join(SRC, "lowdata_tests.csv"), index=False)
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(SRC, "summary.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
