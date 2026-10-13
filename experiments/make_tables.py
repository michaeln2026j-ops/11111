"""Final statistical tables for all experiments -> results/tables.md

Coverage: pooled Clopper-Pearson 95% CI over all executions; "fields >= target"
uses a per-field binomial test (one-sided, alpha 0.05) against 1 - eps.
Overlap: mean +/- 95% CI over fields; paired Wilcoxon signed-rank test against
CE-U on the same fields with Holm correction across methods.
"""
import math
import os

import numpy as np
import pandas as pd
from scipy.stats import beta, binomtest, wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
from make_figures2 import LABEL, ORDER  # noqa: E402


def cp(k, n, a=0.05):
    lo = beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return lo, hi


def holm(ps):
    idx = np.argsort(ps)
    out = np.empty(len(ps))
    m = len(ps)
    run = 0.0
    for r, i in enumerate(idx):
        run = max(run, min(1.0, (m - r) * ps[i]))
        out[i] = run
    return out


def load(n):
    p = os.path.join(RES, n)
    return pd.read_csv(p) if os.path.exists(p) else None


def main_table(lines, kind, d, n_test=300, eps=0.1):
    lines.append(f"\n### E2 主对比（仿真执行）— {kind}：{d.field.nunique()} 块真实田块 × 每方法 {n_test} 次执行，目标 P(无漏) ≥ {1-eps:.2f}\n")
    lines.append("| 方法 | P(无漏) [95% CI] | 不显著低于目标的田块 | E[漏] (‱) | 重叠 % [95% CI] | 不可行 | vs CE-U 重叠 (Holm p) |")
    lines.append("|---|---|---|---|---|---|---|")
    ref = d[d.method == "CE-U (ours, uniform)"].set_index("field").overlap
    rows, ps = [], []
    for m in [o for o in ORDER + ["CE-R (ours, risk alpha)"] if o in d.method.unique()]:
        x = d[d.method == m]
        ok = x.dropna(subset=["p_nomiss"])
        k = int(round((ok.p_nomiss * n_test).sum()))
        n = n_test * len(ok)
        lo, hi = cp(k, n) if n else (np.nan, np.nan)
        meet = np.mean([binomtest(int(round(p * n_test)), n_test, 1 - eps, alternative="less").pvalue >= 0.05
                        for p in ok.p_nomiss]) if len(ok) else np.nan
        ov = ok.overlap * 100
        ci = 1.96 * ov.std() / math.sqrt(len(ov)) if len(ov) > 1 else 0
        j = ok.set_index("field").overlap.to_frame().join(ref.rename("ref"), how="inner")
        p = wilcoxon(j.overlap, j.ref).pvalue if m != "CE-U (ours, uniform)" and len(j) > 5 and (j.overlap != j.ref).any() else np.nan
        rows.append([m, ok.p_nomiss.mean(), lo, hi, meet, ok.e_miss.mean() * 1e4, ov.mean(), ci,
                     int(x.p_nomiss.isna().sum())])
        ps.append(p)
    ps = np.array(ps)
    adj = np.full(len(ps), np.nan)
    fin = np.isfinite(ps)
    adj[fin] = holm(ps[fin])
    for r, pa in zip(rows, adj):
        m = r[0]
        name = f"**{LABEL.get(m, m)}**" if "ours" in m else LABEL.get(m, m)
        if m.startswith("CE-R"):
            name += "（风险证书：E[漏] ≤ 30‱）"
        lines.append(f"| {name} | {r[1]:.3f} [{r[2]:.3f}, {r[3]:.3f}] | {r[4]*100:.0f}% | {r[5]:.2f} | "
                     f"{r[6]:.1f} ± {r[7]:.1f} | {r[8]} | {'—' if not np.isfinite(pa) else f'{pa:.1e}'} |")


def main():
    L = ["# 实验统计表（make_tables.py 自动生成）"]
    for kind in ("paddy", "wheat"):
        d = load(f"main_{kind}_v3.csv")
        if d is None:
            d = load(f"main_{kind}_v2.csv")
        if d is not None:
            main_table(L, kind, d)
    r = load("real.csv")
    if r is not None:
        for K in (3, 5):
            x = r[(r.split == "random") & (r.K == K) & (r.eps == 0.1)]
            L.append(f"\n### E8 真实机器人（CitrusFarm）随机划分 300 次，{K} 行作业带，ε = 0.1\n")
            L.append("| 方法 | P(无漏) 均值 | 5–95% 区间 | 重叠 % | 校准单元数 | 测试单元数 |")
            L.append("|---|---|---|---|---|---|")
            for m in [o for o in ORDER if o in x.method.unique()]:
                g = x[x.method == m].dropna(subset=["p_nomiss"])
                if not len(g):
                    continue
                q = np.percentile(g.p_nomiss, [5, 95])
                nm = f"**{LABEL[m]}**" if "ours" in m else LABEL[m]
                L.append(f"| {nm} | {g.p_nomiss.mean():.3f} | [{q[0]:.3f}, {q[1]:.3f}] | {g.overlap.mean()*100:.1f} | "
                         f"{int(g.n_cal.mean())} | {int(g.n_test.mean())} |")
            y = r[(r.split != "random") & (r.K == K) & (r.eps == 0.1)]
            L.append(f"\n**分布外留出（{K} 行）**：P(无漏)\n")
            sel = ["CE-U (ours, uniform)", "Scenario (Campi-Garatti)", "CVaR (empirical)", "Gaussian on score",
                   "Worst-case (max score)", "Cantelli bound on score"]
            L.append("| 留出 | " + " | ".join(LABEL[s] for s in sel) + " |")
            L.append("|---" * (len(sel) + 1) + "|")
            for sp in ["LOBO:13B", "LOBO:13D", "LOBO:14B", "LODO:07-16", "LODO:07-18"]:
                vals = [y[(y.split == sp) & (y.method == s)] for s in sel]
                L.append(f"| {sp} | " + " | ".join(f"{v.p_nomiss.mean():.3f} ({v.overlap.mean()*100:.0f}%)"
                                                   for v in vals) + " |")
        a = load("real_aci.csv")
        if a is not None:
            L.append("\n**真实时间序列上的在线部署**（目标漏作业频率 0.10）\n")
            L.append("| K | 方法 | 漏作业频率 | 重叠 % | 作业带数 |")
            L.append("|---|---|---|---|---|")
            for (K, m), g in a.groupby(["K", "method"]):
                L.append(f"| {K} | {m} | {g.err.mean():.3f} | {g.overlap.mean()*100:.1f} | {len(g)} |")
    for tag, title in [("", "默认工况（RTK，3 m 幅宽）"), ("_hard", "困难工况（GNSS 误差 ×3，1.5 m 幅宽）")]:
        ab = load(f"ablation{tag}.csv")
        if ab is None:
            continue
        L.append(f"\n### E9 消融 — {title}\n")
        L.append("| 作物 | 变体 | P(无漏) | 重叠 % | 腐蚀量 (cm) | 田块数 |")
        L.append("|---|---|---|---|---|---|")
        for (k, v), g in ab.groupby(["kind", "variant"]):
            L.append(f"| {k} | {v} | {g.p_nomiss.mean():.3f} | {g.overlap.mean()*100:.1f} | {g.lam.mean()*100:.1f} | "
                     f"{g.field.nunique()} |")
    for kind in ("paddy", "wheat"):
        c = load(f"cross2_{kind}.csv")
        if c is None:
            continue
        L.append(f"\n### E3b 跨田块（新田块无历史）— {kind}：学习类与鲁棒类对照\n")
        L.append("| 方法 | P(无漏) 均值 ± 95% CI（按重复） | 重叠 % | 重复次数 |")
        L.append("|---|---|---|---|")
        for m in [o for o in ORDER if o in c.method.unique()]:
            g = c[c.method == m].dropna(subset=["p_nomiss"])
            per = g.groupby("rep").p_nomiss.mean()
            ci = 1.96 * per.std() / math.sqrt(len(per)) if len(per) > 1 else np.nan
            nm = f"**{LABEL[m]}**" if "ours" in m else LABEL[m]
            L.append(f"| {nm} | {per.mean():.3f} ± {ci:.3f} | {g.overlap.mean()*100:.1f} | {len(per)} |")
    open(os.path.join(RES, "tables.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
