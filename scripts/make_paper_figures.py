"""Figures for docs/paper/draft.md, built only from result files in the repository (no re-simulation).

    python3 scripts/make_paper_figures.py      # -> figures/paper/fig*.png / .pdf
"""
import glob
import os
import pickle
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "figures", "paper")
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import exp_lowdata as X  # noqa: E402

# reference palette (light): categorical slots in fixed order, text inks, recessive grid
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#dedcd5", "#fcfcfb"
plt.rcParams.update({
    "font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.spines.top": False,
    "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white", "lines.linewidth": 2,
    "legend.frameon": False, "savefig.dpi": 300, "font.family": "DejaVu Sans"})
REG = {"R1": "R1 RTK flat 3 m", "R2": "R2 RTK hilly-wet 1.5 m", "R3": "R3 DGPS hilly 6 m"}


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def fig_v8():
    """Regret (overlap above the per-field oracle) of CE+ v8 vs CPP and Lindemann, fresh fields, both classes."""
    d = pd.read_csv(os.path.join(RES, "v8", "system_v8.csv"))
    sysn = {"marginal": [("CE+ v8 (ours)", "BCD + LQR-I + CE+ (ours, v8)", C1),
                         ("CPP", "Conformal predictive programming (Zhao et al.)", C2),
                         ("Lindemann pair-level", "Conformal planning, pair-level union bound (Lindemann et al.)", C3)],
            "PAC": [("CE+ v8 PAC (ours)", "BCD + LQR-I + CE+ PAC (ours, v8)", C1),
                    ("CPP-PAC", "Conformal predictive programming, PAC delta=0.1", C2),
                    ("Lindemann pair-level PAC", "Conformal planning, pair-level union bound, PAC delta=0.1", C3)]}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6), sharey=False)
    for ax, (cls, rows) in zip(axes, sysn.items()):
        for r_i, key in enumerate(("R1", "R2", "R3")):
            dr = d[d.regime.str.startswith(key)]
            for s_i, (lab, nm, col) in enumerate(rows):
                v = dr[dr.system == nm]
                m, se = v.regret_pp.mean(), v.regret_pp.std(ddof=1) / np.sqrt(len(v))
                x = r_i + (s_i - 1) * 0.24
                ax.bar(x, m, width=0.2, color=col, label=lab if r_i == 0 else None, zorder=2)
                ax.errorbar(x, m, yerr=1.96 * se, color=INK2, lw=1, capsize=2, zorder=3)
                ax.text(x, max(m, 0) + 1.96 * se + 0.3, f"{v.p_nomiss.mean():.2f}", ha="center", va="bottom",
                        fontsize=6, color=INK2, rotation=90)
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(range(3), ["R1", "R2", "R3"])
        ax.set_title(f"{cls} class", color=INK, fontsize=9)
        ax.set_ylabel("overlap above oracle (pp)")
        ax.set_ylim(top=ax.get_ylim()[1] * 1.12)
    fig.suptitle("v8 confirmatory comparison on 90 fresh fields (numbers above bars: pooled P(no miss))",
                 fontsize=8, color=INK2, y=1.02)
    fig.subplots_adjust(wspace=0.3)
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color=C1, label="CE+ v8 (ours)"), Patch(color=C2, label="CPP (Zhao et al.)"),
                        Patch(color=C3, label="Lindemann pair-level")], loc="lower center", ncol=3, fontsize=7,
               bbox_to_anchor=(0.5, -0.08))
    save(fig, "fig_v8_regret")


def fig_theory():
    """Theory 0.9-quantile vs the empirical 0.9-quantile of 200 independent runs, per field."""
    fig, ax = plt.subplots(figsize=(3.4, 3.2))
    for key, col in zip(("R1", "R2", "R3"), (C1, C2, C3)):
        q, s = [], []
        for d in ("lowdata_v2", "lowdata_v3"):
            for f in glob.glob(os.path.join(RES, d, f"A_{key}_*.pkl")):
                r = pickle.load(open(f, "rb"))
                hb = f.replace("A_", "hist_")
                if not os.path.exists(hb) or not np.all(np.isfinite(r["Fhat"])):
                    continue
                q.append(X.inv_cdf(r["tgrid"], r["Fhat"], 0.9)), s.append(np.quantile(pickle.load(open(hb, "rb")), 0.9))
        ax.scatter(s, q, s=12, color=col, edgecolor="white", linewidth=0.5, label=f"{key} ({len(q)} fields)", zorder=3)
    # R3 with the field-edge terms (Theorem 2.4)
    txt = open(os.path.join(RES, "lowdata_v3", "check_boundary_R3.txt")).read()
    rows = re.findall(r"q_new ([\d.]+)\s+sim ([\d.]+)", txt)
    ax.scatter([float(b) for _, b in rows], [float(a) for a, _ in rows], s=16, facecolor="none", edgecolor=C4,
               linewidth=1, label="R3 with edge terms", zorder=4)
    lim = [0.08, 0.7]
    ax.plot(lim, lim, color=INK2, lw=0.8, zorder=1)
    ax.set_xscale("log"), ax.set_yscale("log"), ax.set_xlim(lim), ax.set_ylim(lim)
    ticks = [0.1, 0.15, 0.2, 0.3, 0.4, 0.6]
    from matplotlib.ticker import NullFormatter
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_minor_formatter(NullFormatter())
    ax.set_xticks(ticks, [f"{t:g}" for t in ticks]), ax.set_yticks(ticks, [f"{t:g}" for t in ticks])
    ax.set_xlabel("simulated 0.9-quantile of the run score (m)")
    ax.set_ylabel("theory-predicted 0.9-quantile (m)")
    ax.legend(fontsize=7, loc="upper left")
    save(fig, "fig_theory_vs_sim")


def parse_validity(path):
    rows = []
    sc = None
    for line in open(path):
        m = re.match(r"== (\S+):", line)
        if m:
            sc = m.group(1)
        m = re.match(r"\s+\[(\w+)\s*\]\s+(.+?)\s+mean coverage ([\d.]+).*P\(cov>=0.9\) ([\d.]+)\s+(\w+)\s+mean excess ([+\-\d.]+)", line)
        if m:
            rows.append(dict(sc=sc, cls=m.group(1), method=m.group(2).strip(), cov=float(m.group(3)),
                             p=float(m.group(4)), ok=m.group(5), ex=float(m.group(6))))
    return pd.DataFrame(rows)


def fig_validity():
    v = parse_validity(os.path.join(RES, "lowdata_v3", "validity_resample_extended_curves.txt"))
    meths = ["raw", "scale law", "spec x scale law", "theory"]
    cols = dict(zip(meths, (C2, C3, C4, C1)))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
    fig.subplots_adjust(wspace=0.38)
    for ax, cls, col_, ref, lab in ((axes[0], "marginal", "cov", 0.9, "mean coverage\n(4000 replicates)"),
                                     (axes[1], "PAC", "p", 0.88, "share of replicates\nwith coverage ≥ 0.9")):
        for s_i, sc in enumerate(("R1", "R2", "R3", "mixed")):
            vv = v[(v.sc == sc) & (v.cls == cls)]
            for m_i, m in enumerate(meths):
                r = vv[vv.method == m]
                if r.empty:
                    continue
                ax.scatter(s_i + (m_i - 1.5) * 0.15, r[col_].iloc[0], color=cols[m], s=18, zorder=3,
                           label=m.replace("theory", "CE-EVT-R (theory)") if s_i == 3 else None)
        ax.axhline(ref, color=INK2, lw=0.8, ls="--")
        ax.set_xticks(range(4), ["R1", "R2", "R3", "mixed"])
        ax.set_ylabel(lab)
        ax.set_title(f"{cls} class (criterion: dashed line)", fontsize=9, color=INK)
    axes[1].legend(fontsize=7, loc="lower right")
    save(fig, "fig_coverage_check")


def fig_mixed():
    v = parse_validity(os.path.join(RES, "lowdata_v3", "validity_resample_extended_curves.txt"))
    v = v[v.sc == "mixed"]
    order = ["scale law", "raw", "spec x scale law", "theory"]
    labels = {"theory": "CE-EVT-R (theory pivot)", "raw": "pooled conformal (raw)", "scale law": "scale-law pivot",
              "spec x scale law": "spec × scale-law pivot"}
    cols = {"theory": C1, "raw": C2, "scale law": C3, "spec x scale law": C4}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.0), sharey=True)
    for ax, cls in zip(axes, ("marginal", "PAC")):
        for i, m in enumerate(order):
            r = v[(v.cls == cls) & (v.method == m)].iloc[0]
            ax.barh(i, r.ex, color=cols[m], height=0.6, zorder=2)
            ax.text(r.ex + 0.8, i, f"{r.ex:.1f}", va="center", fontsize=7, color=INK)
        ax.set_yticks(range(len(order)), [labels[m] for m in order])
        ax.set_xlabel("mean overlap above oracle (pp)")
        ax.set_title(f"mixed fleet, {cls} class", fontsize=9, color=INK)
        ax.grid(axis="y", visible=False)
    save(fig, "fig_mixed_fleet")


def fig_limit():
    obs = {"R1": 1.018, "R2": 1.207, "R3": 1.645}
    pred = {"R1": (1.30, 0.35), "R2": (1.26, 0.33), "R3": (1.85, 0.74)}  # scripts/predict_limit.py, docs/theory_limit.md
    fig, ax = plt.subplots(figsize=(3.2, 2.4))
    for i, k in enumerate(("R1", "R2", "R3")):
        m, s = pred[k]
        ax.errorbar(i - 0.08, m, yerr=s, fmt="o", color=C1, ms=5, capsize=3, label="theory prediction (mean ± sd)" if i == 0 else None)
        ax.scatter(i + 0.08, obs[k], marker="D", s=24, color=C2, zorder=3, label="observed (fresh fields)" if i == 0 else None)
    ax.axhline(1, color=INK2, lw=0.8)
    ax.set_xticks(range(3), ["R1", "R2", "R3"])
    ax.set_ylabel("PAC margin / per-field optimum\n(ideal scale)")
    ax.legend(fontsize=7, loc="upper left")
    save(fig, "fig_information_limit")


def fig_learning():
    txt = open(os.path.join(RES, "lowdata_v2", "feature_learning_curve.txt")).read()
    blocks = re.split(r"\n(?=R\d:)", txt.strip())
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.3), sharey=False)
    for ax, b in zip(axes, blocks):
        key = b[:2]
        th = float(re.search(r"log-error sd ([\d.]+)", b).group(1))
        rows = re.findall(r"^\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$", b, re.M)
        m = np.array([int(r[0]) for r in rows]); o = np.array([float(r[1]) for r in rows]); one = np.array([float(r[2]) for r in rows])
        _, u = np.unique(m, return_index=True)
        m, o, one = m[u], o[u], one[u]
        ax.plot(m, one, color=C2, marker="o", ms=4, label="features, trained on 1 run/field")
        ax.plot(m, o, color=C3, marker="s", ms=4, label="features, trained on oracle (100s of runs/field)")
        ax.axhline(th, color=C1, lw=2, label="theory (zero data)")
        ax.set_yscale("log")
        from matplotlib.ticker import NullFormatter
        ax.yaxis.set_minor_formatter(NullFormatter())
        tk = [t for t in (0.02, 0.03, 0.05, 0.1, 0.2, 0.4) if min(o.min(), th) * 0.8 <= t <= one.max() * 1.25]
        ax.set_yticks(tk, [f"{t:g}" for t in tk])
        ax.set_xlabel("training fields")
        ax.set_title(REG[key], fontsize=8, color=INK)
        if key == "R1":
            ax.set_ylabel("sd of log(predicted / true optimum)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7, bbox_to_anchor=(0.5, -0.2))
    fig.subplots_adjust(wspace=0.3)
    save(fig, "fig_learning_curve")


if __name__ == "__main__":
    fig_v8()
    fig_theory()
    fig_validity()
    fig_mixed()
    fig_limit()
    fig_learning()


def fig_schematic():
    """Plan view: planned lines with erosion, executed paths, an interior gap and a field-edge miss."""
    rng = np.random.default_rng(3)
    w, lam = 3.0, 0.35
    sp = w - 2 * lam
    fig, ax = plt.subplots(figsize=(7.0, 2.6))
    x = np.linspace(0, 60, 400)
    lo = 0.0
    ys = [lo + w / 2 - lam + k * sp for k in range(4)]
    # smooth executed deviations; pass 2 drifts up and pass 1 down around x ~ 35 to open a gap,
    # pass 0 drifts up near x ~ 12 to leave the field edge uncovered
    dev = []
    for k in range(4):
        e = 0.12 * np.sin(x / 7 + k) + 0.05 * np.sin(x / 2.3 + 2 * k)
        if k == 1:
            e -= 0.55 * np.exp(-((x - 36) / 4) ** 2)
        if k == 2:
            e += 0.45 * np.exp(-((x - 36) / 4) ** 2)
        if k == 0:
            e += 0.65 * np.exp(-((x - 12) / 3.5) ** 2)
        dev.append(e)
    ax.axhspan(-1.4, lo, color="#efeee9", zorder=0)
    ax.text(59.5, -0.75, "outside the field", ha="right", va="center", fontsize=7, color=INK2)
    ax.axhline(lo, color=INK, lw=1.2)
    for k, (y, e) in enumerate(zip(ys, dev)):
        ax.fill_between(x, y + e - w / 2, y + e + w / 2, color=C1, alpha=0.18, lw=0, zorder=1)
        ax.plot(x, np.full_like(x, y), color=INK2, lw=0.8, ls="--", zorder=2)
        ax.plot(x, y + e, color=C1, lw=1.5, zorder=3)
    # mark interior gap and edge miss
    top1 = ys[1] + dev[1] + w / 2
    bot2 = ys[2] + dev[2] - w / 2
    gap = bot2 > top1
    ax.fill_between(x, top1, bot2, where=gap, color=C2, alpha=0.9, lw=0, zorder=4)
    ax.annotate("interior gap: adjacent passes drift apart", xy=(39, (ys[1] + ys[2]) / 2 + 0.05),
                xytext=(40.5, (ys[1] + ys[2]) / 2 + 0.05), fontsize=7, color=INK, va="center",
                bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
    bot0 = ys[0] + dev[0] - w / 2
    ax.fill_between(x, lo, bot0, where=bot0 > lo, color=C2, alpha=0.9, lw=0, zorder=4)
    ax.annotate("field-edge miss: outermost pass drifts inward", xy=(12, lo - 0.05), xytext=(16, -0.75),
                fontsize=7, color=INK, ha="left", va="center", arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    # erosion annotation
    yb = (ys[2] + ys[3]) / 2 + dev[2][np.searchsorted(x, 22)] / 2 + dev[3][np.searchsorted(x, 22)] / 2
    ax.text(22, yb, "darker band: overlap of width 2λ", fontsize=7, va="center", color=INK,
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
    ax.set_xlim(0, 60), ax.set_ylim(-1.4, ys[3] + w / 2 + 0.3)
    ax.set_xlabel("along-pass distance (m)"), ax.set_ylabel("lateral position (m)")
    ax.grid(False)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[Line2D([], [], color=INK2, ls="--", lw=0.8, label="planned line (spacing w − 2λ)"),
                       Line2D([], [], color=C1, lw=1.5, label="executed path"),
                       Patch(color=C1, alpha=0.18, label="implement footprint (width w)"),
                       Patch(color=C2, label="missed area")], loc="upper center", ncol=4, fontsize=7,
              bbox_to_anchor=(0.5, -0.2))
    save(fig, "fig_schematic")


if __name__ == "__main__":
    fig_schematic()


def fig_graphical_abstract():
    """Graphical abstract (CEA: >= 1328 x 531 px): method flow and two headline results from the repository."""
    from matplotlib.patches import FancyBboxPatch
    fig = plt.figure(figsize=(13.28 / 2.54 * 2, 5.31 / 2.54 * 2))
    ax = fig.add_axes([0, 0, 0.56, 1])
    ax.set_xlim(0, 10), ax.set_ylim(0, 4), ax.axis("off")
    steps = [("1  Logged runs", "target-field runs, or one run per other field", "#efeee9"),
             ("2  Exact run score", "S = largest gap or edge miss; zero miss ⇔ S ≤ λ", "#efeee9"),
             ("3  Five-layer theory", "Lyapunov → Kac–Rice → product → mixture → Gumbel:\n"
              "each field's score quantile from controller, terrain, GNSS", "#dbe8f8"),
             ("4  Conformal calibration", "certified overlap λ: P(no miss) ≥ 1 − ε", "#dbe8f8")]
    ys_ = [3.05, 2.2, 1.25, 0.4]
    hs = [0.6, 0.6, 0.8, 0.6]
    for (title, body, col), y0, hh in zip(steps, ys_, hs):
        ax.add_patch(FancyBboxPatch((0.3, y0 - hh / 2), 9.4, hh, boxstyle="round,pad=0.03", fc=col, ec=INK2, lw=0.8))
        ax.text(0.5, y0, title, ha="left", va="center", fontsize=9, color=INK, weight="bold")
        ax.text(4.1, y0, body, ha="left", va="center", fontsize=7.5, color=INK)
    for y_a, y_b in ((3.05 - 0.3, 2.2 + 0.3), (2.2 - 0.3, 1.25 + 0.4), (1.25 - 0.4, 0.4 + 0.3)):
        ax.annotate("", xy=(1.4, y_b + 0.02), xytext=(1.4, y_a - 0.02), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1))
    ax.text(5.0, 3.75, "Certified coverage planning under execution uncertainty", ha="center", fontsize=11, color=INK, weight="bold")
    # right: headline numbers from the repository
    d = pd.read_csv(os.path.join(RES, "v8", "system_v8.csv"))
    rows = [("CE+ (ours)", "BCD + LQR-I + CE+ PAC (ours, v8)", C1), ("CPP", "Conformal predictive programming, PAC delta=0.1", C2),
            ("Lindemann", "Conformal planning, pair-level union bound, PAC delta=0.1", C3)]
    a2 = fig.add_axes([0.62, 0.2, 0.16, 0.62])
    vals = [d[d.system == nm].regret_pp.mean() for _, nm, _ in rows]
    a2.bar(range(3), vals, color=[c for *_, c in rows], width=0.6)
    for i, v_ in enumerate(vals):
        a2.text(i, v_ + 0.3, f"{v_:.1f}", ha="center", fontsize=7)
    a2.set_xticks(range(3), [r[0] for r in rows], fontsize=7, rotation=20)
    a2.set_title("With field data\n(PAC, 90 fresh fields)\noverlap above optimum, pp", fontsize=7.5, color=INK)
    a2.grid(axis="x", visible=False)
    v = parse_validity(os.path.join(RES, "lowdata_v3", "validity_resample_extended_curves.txt"))
    v = v[(v.sc == "mixed") & (v.cls == "marginal")].set_index("method")
    a3 = fig.add_axes([0.82, 0.2, 0.16, 0.62])
    order = [("theory", "theory pivot", C1), ("spec x scale law", "spec×scale", C4), ("raw", "pooled", C2)]
    vals = [v.loc[m, "ex"] for m, _, _ in order]
    a3.bar(range(3), vals, color=[c for *_, c in order], width=0.6)
    for i, v_ in enumerate(vals):
        a3.text(i, v_ + 0.5, f"{v_:.1f}", ha="center", fontsize=7)
    a3.set_xticks(range(3), [o[1] for o in order], fontsize=7, rotation=20)
    a3.set_title("Zero target-field data\n(mixed machine fleet)\noverlap above optimum, pp", fontsize=7.5, color=INK)
    a3.grid(axis="x", visible=False)
    save(fig, "graphical_abstract")


if __name__ == "__main__":
    fig_graphical_abstract()
