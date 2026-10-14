"""E-low analysis, exactly as pre-registered.

    python3 scripts/analyze_lowdata.py                              # v1: docs/prereg_lowdata.md section 4
    python3 scripts/analyze_lowdata.py results/lowdata_v2 --v2      # v2: docs/prereg_lowdata_v2.md section 3-4

v1 validity: marginal = field-clustered one-sided test of pooled P(no miss) vs 0.9 (kept as registered; it
ignores the shared calibration pool, see prereg v2 section 0); PAC = number of fields failing the per-field
meet test vs Bin(F, delta + alpha).
v2 validity: pooled P(no miss) not below the 5% quantile of Beta(k, n_cal + 1 - k), the distribution of the
coverage given the (shared) calibration set.
Efficiency: mean excess overlap (pp over the per-field oracle), relative improvement over each comparator of
the same class, one-sided paired Wilcoxon per field, Holm over all comparisons. v2: a comparator with mean
excess <= 0.5 pp leaves no room -> non-inferiority (ours <= comparator + 0.25 pp) instead.
"""
import argparse
import glob
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
EPS, DELTA, ALPHA_MEET, N_TEST, LEVEL = 0.1, 0.1, 0.043, 200, 0.05
MEET_MAX_FAIL = 172  # meet test fails iff successes <= 172 of 200 (theory_v8 Prop 4)
NO_ROOM, NI_MARGIN = 0.5, 0.25

V1 = dict(ours={"marginal": "CE-EVT (ours)", "PAC": "CE-EVT PAC (ours)"},
          comp={"marginal": ["Pooled conformal, raw scores", "Farmer-tuned global overlap", "Spec overlap (2x p2p)"],
                "PAC": ["Pooled conformal, raw scores PAC", "Farmer-tuned global overlap", "Spec overlap (2x p2p)"]},
          claims=None)
V2 = dict(ours={"marginal": "CE-EVT-R (ours, ratio pivot)", "PAC": "CE-EVT-R PAC (ours, ratio pivot)"},
          comp={"marginal": ["Pooled conformal, raw scores", "Ablation: pooled, scale-law normalised",
                             "Farmer-tuned global overlap", "Spec overlap (2x p2p)"],
                "PAC": ["Pooled conformal, raw scores PAC", "Ablation: pooled, scale-law normalised PAC",
                        "Farmer-tuned global overlap", "Spec overlap (2x p2p)"]},
          claims=[("R1", "PAC", "Pooled conformal, raw scores PAC"), ("R3", "marginal", "Pooled conformal, raw scores")])


def order_k(n, eps, delta=None):
    if delta is None:
        return int(math.ceil((n + 1) * (1 - eps)))
    for k in range(1, n + 1):
        if stats.binom.cdf(k - 1, n, 1 - eps) >= 1 - delta:
            return k
    return n + 1


def validity(d, cls, v2):
    p = d["p_nomiss"].fillna(0.0).to_numpy()  # a method that cannot deploy on a field fails there
    if v2:
        n_cal = int(d["n_cal"].iloc[0])
        k = order_k(n_cal, EPS, DELTA if cls == "PAC" else None)
        lo = stats.beta.ppf(0.05, k, n_cal + 1 - k) if k <= n_cal else 1.0
        return dict(P=p.mean(), n_fields=len(p), p_value=float(p.mean() >= lo), lo=lo, valid=p.mean() >= lo)
    if cls == "marginal":
        m, se = p.mean(), p.std(ddof=1) / np.sqrt(len(p))
        pval = stats.norm.cdf((m - (1 - EPS)) / max(se, 1e-12))
        return dict(P=m, n_fields=len(p), p_value=pval, valid=pval >= LEVEL)
    succ = np.rint(p * N_TEST).astype(int)
    k = int((succ <= MEET_MAX_FAIL).sum())
    pval = stats.binom.sf(k - 1, len(p), DELTA + ALPHA_MEET)
    return dict(P=p.mean(), n_fields=len(p), fails=k, p_value=pval, valid=pval >= LEVEL)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default=os.path.join(HERE, "..", "results", "lowdata"))
    ap.add_argument("--v2", action="store_true")
    a = ap.parse_args()
    cfg = V2 if a.v2 else V1
    files = sorted(glob.glob(os.path.join(a.src, "lowdata_R*.csv")))
    if not files:
        sys.exit("no results")
    df = pd.concat([pd.read_csv(f) for f in files])
    out, tests = [], []
    for reg, dr in df.groupby("regime"):
        n_inf = int(dr.get("infeasible", pd.Series(dtype=float)).fillna(False).astype(bool).sum())
        out.append(f"\n== {reg}: {dr['fid'].nunique()} test fields, infeasible deployments {n_inf}")
        for meth, dm in dr.groupby("method"):
            cls = "PAC" if "PAC" in meth else "marginal"
            v = validity(dm, cls, a.v2)
            extra = f"Beta 5% {v['lo']:.3f}" if a.v2 else f"p={v['p_value']:.3f}" + (f", fails {v['fails']}" if "fails" in v else "")
            out.append(f"  {meth:42s} [{cls:8s}] P={v['P']:.3f} valid={'yes' if v['valid'] else 'NO '} ({extra})  "
                       f"excess={dm['excess_pp'].mean():+.2f} pp  overlap={100 * dm['overlap'].mean():.2f}%")
        for cls, ours in cfg["ours"].items():
            do = dr[dr.method == ours].set_index("fid")
            if do.empty or not validity(dr[dr.method == ours], cls, a.v2)["valid"]:
                out.append(f"  [{cls}] {ours} NOT valid in {reg}")
                continue
            for c in cfg["comp"][cls]:
                dc_all = dr[dr.method == c]
                if dc_all.empty or not validity(dc_all, cls, a.v2)["valid"]:
                    continue
                dc = dc_all.set_index("fid")
                j = do.index.intersection(dc.index)
                av, bv = do.loc[j, "excess_pp"], dc.loc[j, "excess_pp"]
                no_room = a.v2 and bv.mean() <= NO_ROOM
                if no_room:  # non-inferiority: ours <= comparator + margin
                    diff = av - bv - NI_MARGIN
                    p = stats.wilcoxon(diff, alternative="less").pvalue if (diff != 0).any() else 1.0
                    rel = np.nan
                else:
                    p = stats.wilcoxon(av, bv, alternative="less").pvalue if (av != bv).any() else 1.0
                    rel = (bv.mean() - av.mean()) / bv.mean() if bv.mean() > 0 else np.nan
                rel_abs = (dc.loc[j, "overlap"].mean() - do.loc[j, "overlap"].mean()) / dc.loc[j, "overlap"].mean()
                tests.append(dict(regime=reg[:2], cls=cls, comparator=c, mode="non-inferiority" if no_room else "superiority",
                                  rel=rel, rel_abs=rel_abs, p=p, ours=av.mean(), comp=bv.mean()))
    t = pd.DataFrame(tests)
    if not t.empty:
        order = np.argsort(t["p"].to_numpy())
        m, run, adj = len(t), 0.0, np.empty(len(t))
        for r, i in enumerate(order):
            run = max(run, min(1.0, (m - r) * t["p"].iloc[i]))
            adj[i] = run
        t["p_holm"] = adj
        out.append("\n== ours vs valid comparators (excess overlap, pp; Holm over all rows)")
        for _, r in t.iterrows():
            if r["mode"] == "superiority":
                verdict = "better >=10%" if (r.rel >= 0.10 and r.p_holm < LEVEL) else "not >=10% better"
                rel = f"rel {100 * r.rel:+.1f}%"
            else:
                verdict = "non-inferior" if r.p_holm < LEVEL else "non-inferiority NOT shown"
                rel = "no room   "
            out.append(f"  {r.regime} [{r.cls:8s}] vs {r.comparator:42s} ours {r.ours:+.2f} vs {r.comp:+.2f}  {rel}  "
                       f"abs-overlap rel {100 * r.rel_abs:+.1f}%  p_holm {r.p_holm:.4f}  {verdict}")
        if cfg["claims"]:
            out.append("\n== pre-registered claims")
            for reg_, cls, comp in cfg["claims"]:
                row = t[(t.regime == reg_) & (t.cls == cls) & (t.comparator == comp)]
                ok = (not row.empty and row["mode"].iloc[0] == "superiority" and row.rel.iloc[0] >= 0.10
                      and row.p_holm.iloc[0] < LEVEL)
                out.append(f"  {reg_} {cls} vs {comp}: {'MET' if ok else 'NOT MET'}")
        t.to_csv(os.path.join(a.src, "lowdata_tests.csv"), index=False)
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(a.src, "summary.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
