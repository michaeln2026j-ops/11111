"""Statistical tables for all experiments -> results/tables.md (Chinese headings).

Conventions (v6):
- P(no miss) is reported as the mean over FIELDS (or repeats) with a field-clustered 95% t interval:
  all test runs of one field share that field's calibration draw, so runs are not independent.
- "达标田块" = fields whose P(no miss) is not significantly below the target (one-sided binomial test,
  alpha = 0.05, on that field's own test runs); infeasible / abstaining fields count as NOT meeting.
- Overlap: mean +/- 95% t interval over fields; paired Wilcoxon signed-rank test against CE-U on the same
  fields, Holm-corrected across methods.
- Excess overlap vs the reference oracle (system level): the oracle is a per-field fixed point of the
  (1-eps) quantile of exact scores at the plan pi(lam) itself on the default stack BCD + LQR-I using
  TEST-distribution runs; it is a common cost reference, not a lower bound for other stacks.
"""
import math
import os

import numpy as np
import pandas as pd
from scipy.stats import binomtest, t as tdist, wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
TAG = os.environ.get("CE_TAG", "_v6")  # result tag of the main / system experiments
RES = os.path.join(HERE, "..", "results")
from make_figures2 import LABEL, ORDER  # noqa: E402

LABEL = dict(LABEL)
LABEL.update({"CE-U (ours, pi(lam_ref))": "CE-U (ours, 部署参考计划)"})
ORDER = list(ORDER)
if "CE-U (ours, pi(lam_ref))" not in ORDER:
    ORDER.insert(ORDER.index("CE-U (ours, uniform)") + 1, "CE-U (ours, pi(lam_ref))")


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


def tci(v):
    """mean and half-width of the 95% t interval over clusters (fields / repeats)."""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return np.nan, np.nan
    if len(v) == 1:
        return v[0], np.nan
    return v.mean(), tdist.ppf(0.975, len(v) - 1) * v.std(ddof=1) / math.sqrt(len(v))


def fmt(m, h, d=3):
    if not np.isfinite(m):
        return "—"
    return f"{m:.{d}f}" if not np.isfinite(h) else f"{m:.{d}f} ± {h:.{d}f}"


def meets(ps, n_test, target):
    return np.array([bool(np.isfinite(p)) and binomtest(int(round(p * n_test)), n_test, target,
                                                        alternative="less").pvalue >= 0.05 for p in ps])


def name(m):
    s = LABEL.get(m, m)
    return f"**{s}**" if "ours" in m else s


# ----------------------------------------------------------------------------- E1 validity
def sec_validity(L):
    d, n = load("validity_paddy.csv"), load("ncal_paddy.csv")
    if d is None:
        return
    L.append("\n### E1 有效性：目标 1−ε 与实现的 P(无漏)（水稻，按田块聚类 95% CI；每田块 4 次独立校准）\n")
    L.append("| 变体 | 方法 | ε | 目标 | P(无漏) | 校准参考计划仍支配的比例 | 田块数 |")
    L.append("|---|---|---|---|---|---|---|")
    for (var, m, e), g in d.groupby(["variant", "method", "eps"]):
        per = g.groupby("field").p_nomiss.mean()
        dom = g.dominated.mean() if "dominated" in g else np.nan
        L.append(f"| CE-{var} | {m} | {e} | {1-e:.2f} | {fmt(*tci(per))} | {dom:.2f} | {len(per)} |")
    if n is not None:
        L.append("\n**校准样本量**（CE-A，ε = 0.1）\n")
        L.append("| n_cal | P(无漏) | 单次标准差 | 次数 |")
        L.append("|---|---|---|---|")
        for k, g in n.groupby("n_cal"):
            per = g.groupby("field").p_nomiss.mean()
            L.append(f"| {k} | {fmt(*tci(per))} | {g.p_nomiss.std():.3f} | {len(g)} |")
    dg = load("diag_validity.csv")
    if dg is not None:
        nc = int(dg.n_cal.iloc[0])
        L.append(f"\n**校准协议诊断**（分数层面覆盖 P(S ≤ q) 的理论带为 [0.900, {0.9 + 1/(nc+1):.3f}]，n = {nc}）\n")
        L.append("| 协议 | P(S ≤ q)（分数层面） | P(无漏) 部署 π(q) | P(无漏) 部署 π(λ_ref) | 参考计划支配比例 | 田块 × 重复 |")
        L.append("|---|---|---|---|---|---|")
        for p, g in dg.groupby("protocol"):
            fl = g.groupby("field")
            lr = fmt(*tci(fl.p_nomiss_lamref.mean())) if "p_nomiss_lamref" in g else "—"
            L.append(f"| {p} | {fmt(*tci(fl.score_cov.mean()))} | {fmt(*tci(fl.p_nomiss.mean()))} | {lr} | "
                     f"{g.dominated.mean():.2f} | {g.field.nunique()} × {g.rep.nunique()} |")


# ----------------------------------------------------------------------------- E2 main
def main_table(L, kind, d, n_test=300, eps=0.1):
    L.append(f"\n### E2 主对比（BCD + LQR-I）— {kind}：{d.field.nunique()} 块真实田块 × 每方法 {n_test} 次执行，"
             f"目标 P(无漏) ≥ {1-eps:.2f}\n")
    L.append("| 方法 | P(无漏)（田块均值 ± 95% CI） | 达标田块 | E[漏] (‱) | 重叠 %（± 95% CI） | 不可行 | vs CE-U 重叠 (Holm p) |")
    L.append("|---|---|---|---|---|---|---|")
    ref = d[d.method == "CE-U (ours, uniform)"].set_index("field").overlap
    rows, ps = [], []
    for m in [o for o in ORDER + ["CE-R (ours, risk alpha)"] if o in d.method.unique()]:
        x = d[d.method == m]
        ok = x.dropna(subset=["p_nomiss"])
        meet = meets(x.p_nomiss, n_test, 1 - eps).mean() if len(x) else np.nan
        j = ok.set_index("field").overlap.to_frame().join(ref.rename("ref"), how="inner")
        p = (wilcoxon(j.overlap, j.ref).pvalue if m != "CE-U (ours, uniform)" and len(j) > 5
             and (j.overlap != j.ref).any() else np.nan)
        rows.append([m, tci(ok.p_nomiss), meet, ok.e_miss.mean() * 1e4, tci(ok.overlap * 100),
                     int(x.p_nomiss.isna().sum())])
        ps.append(p)
    ps = np.array(ps)
    adj = np.full(len(ps), np.nan)
    fin = np.isfinite(ps)
    adj[fin] = holm(ps[fin])
    for r, pa in zip(rows, adj):
        m = r[0]
        nm = name(m) + ("（风险证书：E[漏] ≤ 30‱）" if m.startswith("CE-R") else "")
        L.append(f"| {nm} | {fmt(*r[1])} | {r[2]*100:.0f}% | {r[3]:.2f} | {fmt(*r[4], d=1)} | {r[5]} | "
                 f"{'—' if not np.isfinite(pa) else f'{pa:.1e}'} |")
    if "dominated_U" in d:
        u = d[d.method == "CE-U (ours, uniform)"]
        L.append(f"\nCE-U 认证批的参考计划仍支配（q ≤ λ_ref）的田块比例：{u.dominated_U.mean():.2f}；"
                 f"q 中位数 {u.q_U.median()*100:.1f} cm，λ_ref 中位数 {u.lam_ref_U.median()*100:.1f} cm。")


# ----------------------------------------------------------------------------- E2b system
FAM_ORDER = ["industry", "planner", "controller", "robust", "model-based", "learning", "conformal",
             "chance-rule", "ours"]
FAM_ZH = {"industry": "行业实践", "planner": "覆盖规划器", "controller": "跟踪控制器", "robust": "鲁棒",
          "model-based": "模型化机会约束", "learning": "学习类", "conformal": "共形（已发表）",
          "chance-rule": "标量机会规则", "ours": "本文"}


def sec_system(L, n_test=200, target=0.9):
    sy = load(f"system{TAG}.csv")
    if sy is None:
        return
    for rg, x in sy.groupby("regime"):
        nf = x.field.nunique()
        L.append(f"\n### E2b 系统级对比 — {rg}：{nf} 块真实田块 × 每系统 {n_test} 次执行（公共随机数），"
                 f"目标 P(无漏) ≥ {target:.2f}\n")
        L.append("| 类别 | 系统 | 可行田块 | P(无漏)（田块均值 ± 95% CI） | 达标田块 | 漏作业 (m²/ha) | 重叠 %（± CI） | "
                 "相对参考 oracle 多付重叠 (pp, 中位数) | 行数 |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        rows = []
        for (sysn, fam), g in x.groupby(["system", "family"]):
            ok = g.dropna(subset=["p_nomiss"])
            meet = int(meets(g.p_nomiss, n_test, target).sum())
            ov = tci(ok.overlap * 100)
            key = (FAM_ORDER.index(fam) if fam in FAM_ORDER else 99, ov[0] if np.isfinite(ov[0]) else 1e9)
            nm_ = f"**{sysn}**" if fam == "ours" else sysn
            if not len(ok):
                rows.append((key, f"| {FAM_ZH.get(fam, fam)} | {nm_} | 0/{len(g)} | 不可行 | 0/{len(g)} | — | — | — | — |"))
                continue
            rows.append((key, f"| {FAM_ZH.get(fam, fam)} | {nm_} | {len(ok)}/{len(g)} | {fmt(*tci(ok.p_nomiss))} | "
                              f"{meet}/{len(g)} | {ok.e_miss.mean()*1e4:.1f} | {fmt(*ov, d=1)} | "
                              f"{ok.regret_pp.median():+.1f} | {ok.passes.mean():.1f} |"))
        for _, line in sorted(rows):
            L.append(line)
        notes = []
        if "oracle_p" in x:
            o = x.drop_duplicates("field")
            notes.append(f"参考 oracle 计划自身的 P(无漏)（200 次独立检验）均值 {o.oracle_p.mean():.3f}，"
                         f"oracle 腐蚀量中位数 {o.oracle_lam.median()*100:.1f} cm")
        if "dominated" in x:
            ours = x[(x.family == "ours") & x.dominated.notna()]
            if len(ours):
                notes.append(f"本文各行认证批参考计划仍支配的比例 {ours.dominated.astype(bool).mean():.2f}")
        if notes:
            L.append("\n" + "；".join(notes) + "。")


# ----------------------------------------------------------------------------- E3 cross-field
def sec_cross(L):
    parts = [x for x in (load("cross.csv"), load("cross_reverse.csv")) if x is not None]
    if parts:
        c = pd.concat(parts, ignore_index=True)
        if "deploy" not in c:
            c["deploy"] = "pi(q)"
        L.append("\n### E3 跨田块证书与分布迁移（每块校准田只用 1 次历史作业；按重复聚类 95% CI）\n")
        L.append("| 设定 | 方法 | 部署 | P(无漏) | 重叠 % | 弃权/不可行 | 参考计划支配比例 | 重复 |")
        L.append("|---|---|---|---|---|---|---|---|")
        for (st, m, dep), g in c.groupby(["setting", "method", "deploy"]):
            per = g.groupby("rep").p_nomiss.mean()
            ab = g.p_nomiss.isna().mean()
            dom = g.dominated.mean() if "dominated" in g else np.nan
            L.append(f"| {st} | {m} | {dep} | {fmt(*tci(per))} | {g.overlap.mean()*100:.1f} | {ab*100:.1f}% | "
                     f"{dom:.2f} | {len(per)} |")
        if "area_ha" in c:
            L.append("\n**按测试田块面积三分位分层**（π(q) 部署；覆盖保证是对田块总体的边际保证）\n")
            L.append("| 设定 | 方法 | 小田块 | 中田块 | 大田块 |")
            L.append("|---|---|---|---|---|")
            x = c[(c.deploy == "pi(q)") & c.method.isin(["CE-U", "CE-A", "CE-AW (weighted)"])].copy()
            for (st, m), g in x.groupby(["setting", "method"]):
                q = g.area_ha.quantile([1 / 3, 2 / 3]).values
                b = np.digitize(g.area_ha, q)
                vals = [g[b == i].p_nomiss.mean() for i in range(3)]
                L.append(f"| {st} | {m} | " + " | ".join(f"{v:.3f}" for v in vals) + " |")
    for kind in ("paddy", "wheat"):
        c = load(f"cross2_{kind}.csv")
        if c is None:
            continue
        L.append(f"\n### E3b 新田块（无历史）— {kind}：学习类、鲁棒类与本文（按重复聚类 95% CI）\n")
        L.append("| 方法 | P(无漏) | 重叠 % | 参考计划支配比例 | 不可行 | 重复 |")
        L.append("|---|---|---|---|---|---|")
        for m in [o for o in ORDER if o in c.method.unique()]:
            g = c[c.method == m]
            per = g.groupby("rep").p_nomiss.mean()
            dom = g.dominated.mean() if "dominated" in g else np.nan
            L.append(f"| {name(m)} | {fmt(*tci(per))} | {g.overlap.mean()*100:.1f} | {dom:.2f} | "
                     f"{int(g.p_nomiss.isna().sum())} | {len(per)} |")


# ----------------------------------------------------------------------------- E4 / E6 / E9 / E10
def sec_sens(L):
    sv = load("sens.csv")
    if sv is None:
        return
    L.append("\n### E4 灵敏度（控制器 / 横滚补偿 / 幅宽 / 真实 GNSS 接收机等级；水稻 10 块田）\n")
    L.append("| 因素 | 取值 | 认证腐蚀 q (cm) | P(无漏)（± CI） | 重叠 % | 无余量时 P(无漏) | 支配比例 | 田块数 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for (g, v), x in sv.groupby(["group", "value"], sort=False):
        dom = x.dominated.mean() if "dominated" in x else np.nan
        L.append(f"| {g} | {v} | {x.q.mean()*100:.1f} | {fmt(*tci(x.p_nomiss))} | {x.overlap.mean()*100:.1f} | "
                 f"{x.nominal_p_nomiss.mean():.3f} | {dom:.2f} | {x.field.nunique()} |")


def sec_aci(L):
    a = load("aci.csv")
    if a is None:
        return
    T = int(a.t.max() + 1)
    L.append(f"\n### E6 季节漂移（土壤湿度 0.15 → 0.9，{T} 次作业，目标漏作业频率 0.10；按田块聚类 95% CI）\n")
    L.append("| 方法 | 漏作业频率（全程） | 前半程 | 后半程 | 平均腐蚀 q (cm) | 田块数 |")
    L.append("|---|---|---|---|---|---|")
    zh = {"static": "静态（只用干季校准）", "rolling": "滚动窗口重校准（最近 150 次）", "aci": "ACI γ = 0.01",
          "aci_g0.005": "ACI γ = 0.005", "aci_g0.03": "ACI γ = 0.03"}
    for m, g in a.groupby("method"):
        per = g.groupby("field").err.mean()
        h1 = g[g.t < T / 2].groupby("field").err.mean()
        h2 = g[g.t >= T / 2].groupby("field").err.mean()
        L.append(f"| {zh.get(m, m)} | {fmt(*tci(per))} | {h1.mean():.3f} | {h2.mean():.3f} | {g.q.mean()*100:.1f} | "
                 f"{g.field.nunique()} |")


def sec_ablation(L):
    for tag, title in [("", "默认工况（CORS RTK fix，3 m 幅宽）"), ("_hard", "困难工况（CORS RTK fix，湿土，1.5 m 幅宽）"),
                       ("_dgps", "亚米级工况（CORS DGPS，6 m 幅宽）")]:
        ab = load(f"ablation{tag}.csv")
        if ab is None:
            continue
        L.append(f"\n### E9 消融 — {title}\n")
        L.append("| 作物 | 变体 | P(无漏)（± CI） | 重叠 % | 腐蚀量 (cm) | 田块数 |")
        L.append("|---|---|---|---|---|---|")
        for (k, v), g in ab.groupby(["kind", "variant"]):
            L.append(f"| {k} | {v} | {fmt(*tci(g.p_nomiss))} | {g.overlap.mean()*100:.1f} | {g.lam.mean()*100:.1f} | "
                     f"{g.field.nunique()} |")


def sec_sweep(L, target=0.9, n_test=200):
    for kind in ("paddy", "wheat"):
        s = load(f"sweep_{kind}.csv")
        if s is None:
            continue
        L.append(f"\n### E10 固定全局重叠的响应（{kind}，{s.field.nunique()} 块田；"
                 "事后按测试结果选出的最佳全局重叠属于 oracle 信息）\n")
        L.append("| 固定重叠 (cm) | P(无漏) 田块均值 | 达标田块 | 重叠 % |")
        L.append("|---|---|---|---|")
        for o, g in s.groupby("overlap_setting_cm"):
            L.append(f"| {o:g} | {g.p_nomiss.mean():.3f} | {meets(g.p_nomiss, n_test, target).mean()*100:.0f}% | "
                     f"{g.overlap.mean()*100:.1f} |")


# ----------------------------------------------------------------------------- E8 real robot
def sec_real(L):
    r = load("real.csv")
    if r is None:
        return
    sel = ["CE-U (ours, uniform)", "CE-pair (ours, union bound)", "Gaussian on score", "Scenario (Campi-Garatti)",
           "CVaR (empirical)", "Worst-case (max score)", "Cantelli bound on score", "Conformal, pointwise"]
    sel = [m for m in sel if m in r.method.unique()]
    for eps in sorted(r.eps.unique()):
        for K in sorted(r.K.unique()):
            x = r[(r.split == "random") & (r.K == K) & (r.eps == eps)]
            if not len(x):
                continue
            L.append(f"\n### E8 真实机器人（CitrusFarm，仿真器外回放）随机划分 {x.rep.nunique()} 次，{K} 行作业带，"
                     f"ε = {eps}（随机划分下有效性由可交换性保证，这里是有限样本校核）\n")
            L.append("| 方法 | P(无漏) 均值 | 5–95% 区间 | 重叠 % | 校准/测试单元 |")
            L.append("|---|---|---|---|---|")
            for m in [o for o in ORDER if o in x.method.unique()]:
                g = x[x.method == m].dropna(subset=["p_nomiss"])
                if not len(g):
                    continue
                q = np.percentile(g.p_nomiss, [5, 95])
                L.append(f"| {name(m)} | {g.p_nomiss.mean():.3f} | [{q[0]:.3f}, {q[1]:.3f}] | {g.overlap.mean()*100:.1f} | "
                         f"{int(g.n_cal.mean())}/{int(g.n_test.mean())} |")
            y = r[(r.split != "random") & (r.K == K) & (r.eps == eps)]
            if len(y):
                L.append(f"\n**分组留出**（{K} 行，ε = {eps}；LOBO 留一地块，LODO 留一天，LOSO 留一序列），"
                         "单元格：P(无漏)（重叠 %）\n")
                L.append("| 留出 | " + " | ".join(LABEL.get(s, s) for s in sel) + " |")
                L.append("|---" * (len(sel) + 1) + "|")
                for sp in sorted(y.split.unique()):
                    vals = [y[(y.split == sp) & (y.method == s)] for s in sel]
                    L.append(f"| {sp} | " + " | ".join(
                        (f"{v.p_nomiss.mean():.3f} ({v.overlap.mean()*100:.0f}%)" if len(v) and v.p_nomiss.notna().any()
                         else "—") for v in vals) + " |")
    a = load("real_aci.csv")
    if a is not None:
        L.append("\n**真实时间序列上的在线部署**（CE + ACI [Gibbs & Candès 2021]；可行性演示，样本少，不作优劣结论）\n")
        L.append("| K | 方法 | 漏作业频率 | 重叠 % | 作业带数 |")
        L.append("|---|---|---|---|---|")
        for (K, m), g in a.groupby(["K", "method"]):
            mm = m.replace("ACI (ours, online)", "CE + ACI (online)")
            L.append(f"| {K} | {mm} | {g.err.mean():.3f} | {g.overlap.mean()*100:.1f} | {len(g)} |")


def main():
    L = ["# 实验统计表（make_tables.py 自动生成，v6）",
         "",
         "口径：P(无漏) 为田块（或重复）均值，95% CI 为按田块（或重复）聚类的 t 区间；达标田块 = 单侧二项检验不显著低于目标，"
         "不可行/弃权计为未达标；重叠采用 Holm 校正的配对 Wilcoxon 检验，以 CE-U 为参照。"]
    sec_validity(L)
    for kind in ("paddy", "wheat"):
        d = next((x for x in (load(f"main_{kind}{t}.csv") for t in (TAG, "_v5", "_v4", "_v3", "_v2")) if x is not None),
                 None)
        if d is not None:
            main_table(L, kind, d)
    sec_system(L)
    sec_cross(L)
    sec_sens(L)
    sec_aci(L)
    sec_ablation(L)
    sec_sweep(L)
    sec_real(L)
    open(os.path.join(RES, "tables.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
