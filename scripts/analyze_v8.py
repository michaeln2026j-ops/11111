"""v8 confirmatory analysis, exactly as pre-registered (docs/theory_v8.md section 6).

    python3 scripts/analyze_v8.py        # merges results/system_v8_shard*of45.csv -> results/v8/system_v8.csv

Claim V (validity, Proposition 4), per regime: CE+ v8 pooled P(no miss) not significantly below 0.9
(one-sided, field-clustered: each field has its own independent calibration batch); CE+ v8 PAC fails the
per-field meet test (successes <= 172 of 200) on fewer than 9 of 30 fields.
Claim E (efficiency within the guarantee class), per regime: main-area overlap of CE+ v8 PAC below
CPP-PAC and Lindemann pair-level PAC; of CE+ v8 below CPP and Lindemann pair-level; one-sided paired
Wilcoxon per field, Holm over comparator x regime, level 0.05. Secondary: the same on overlap_applied.
"""
import glob
import os

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
OURS = {"marginal": "BCD + LQR-I + CE+ (ours, v8)", "PAC": "BCD + LQR-I + CE+ PAC (ours, v8)"}
COMP = {"marginal": ["Conformal predictive programming (Zhao et al.)",
                     "Conformal planning, pair-level union bound (Lindemann et al.)"],
        "PAC": ["Conformal predictive programming, PAC delta=0.1",
                "Conformal planning, pair-level union bound, PAC delta=0.1"]}


def main():
    files = sorted(glob.glob(os.path.join(RES, "system_v8_shard*of45.csv")))
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    os.makedirs(os.path.join(RES, "v8"), exist_ok=True)
    df.to_csv(os.path.join(RES, "v8", "system_v8.csv"), index=False)
    out = [f"v8 confirmatory: {len(files)} shard files, {df[['regime', 'field']].drop_duplicates().shape[0]} regime-fields"]
    tests = []
    for reg, dr in df.groupby("regime"):
        out.append(f"\n== {reg}: {dr.field.nunique()} fields")
        m = dr[dr.system == OURS["marginal"]]
        p = m["p_nomiss"].fillna(0.0).to_numpy()
        z = (p.mean() - 0.9) / max(p.std(ddof=1) / np.sqrt(len(p)), 1e-12)
        pv = stats.norm.cdf(z)
        out.append(f"  V marginal: CE+ v8 pooled P(no miss) {p.mean():.3f} (field-clustered one-sided p {pv:.3f}) "
                   f"-> {'MET' if pv >= 0.05 else 'NOT MET'}")
        pc = dr[dr.system == OURS["PAC"]]["p_nomiss"].fillna(0.0).to_numpy()
        fails = int((np.rint(pc * 200) <= 172).sum())
        out.append(f"  V PAC: CE+ v8 PAC fails the meet test on {fails}/{len(pc)} fields (claim: < 9) "
                   f"-> {'MET' if fails < 9 else 'NOT MET'}; pooled P {pc.mean():.3f}")
        for cls in ("marginal", "PAC"):
            o = dr[dr.system == OURS[cls]].set_index("field")
            for c in COMP[cls]:
                cc = dr[dr.system == c].set_index("field")
                j = o.index.intersection(cc.index)
                for metric, primary in (("overlap", True), ("overlap_applied", False)):
                    a, b = o.loc[j, metric], cc.loc[j, metric]
                    ok = a.notna() & b.notna()
                    a, b = a[ok], b[ok]
                    pw = stats.wilcoxon(a, b, alternative="less").pvalue if (a != b).any() else 1.0
                    tests.append(dict(regime=reg[:2], cls=cls, comp=c, metric=metric, primary=primary, ours=100 * a.mean(),
                                      them=100 * b.mean(), rel=(b.mean() - a.mean()) / b.mean(), p=pw,
                                      P_them=cc.loc[j, "p_nomiss"].mean(), n=len(a)))
    t = pd.DataFrame(tests)
    for primary in (True, False):
        s = t[t.primary == primary].copy()
        order, run, adj = np.argsort(s.p.to_numpy()), 0.0, np.empty(len(s))
        for r, i in enumerate(order):
            run = max(run, min(1.0, (len(s) - r) * s.p.iloc[i]))
            adj[i] = run
        s["p_holm"] = adj
        out.append(f"\n== claim E ({'primary: main-area overlap' if primary else 'secondary: overlap_applied'}), Holm over {len(s)}")
        for _, r in s.iterrows():
            out.append(f"  {r.regime} [{r.cls:8s}] vs {r.comp[:58]:58s} ours {r.ours:6.2f}% vs {r.them:6.2f}% "
                       f"(rel {100 * r.rel:+.1f}%, their P {r.P_them:.3f})  p_holm {r.p_holm:.4f}  "
                       f"{'MET' if r.p_holm < 0.05 else 'NOT MET'}")
    txt = "\n".join(out)
    print(txt)
    open(os.path.join(RES, "v8", "summary.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()
