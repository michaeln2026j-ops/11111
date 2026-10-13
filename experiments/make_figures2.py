"""Publication figures (double-column, 7.2 in wide; PNG 300 dpi + vector PDF).

Usage: python3 experiments/make_figures2.py
"""
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from scipy.stats import beta, kurtosis, norm

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#a3a29c", "#e9e8e4"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.8,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "lines.linewidth": 1.6,
    "legend.frameon": False, "savefig.bbox": "tight", "savefig.dpi": 300, "figure.dpi": 110,
    "pdf.fonttype": 42,
})

OURS = {"CE-U (ours, uniform)": BLUE, "CE-A (ours, terrain-adaptive)": AQUA,
        "CE-pair (ours, union bound)": VIOLET, "CQR (Romano 2019)": MAGENTA}
LABEL = {
    "Nominal (no margin)": "Nominal (no margin)", "Fixed overlap 5 cm": "Fixed overlap 5 cm",
    "Fixed overlap 10 cm": "Fixed overlap 10 cm", "Fixed overlap 30 cm": "Fixed overlap 30 cm",
    "Slope rule (industry)": "Slope-compensation rule", "Gaussian pointwise": "Gaussian, pointwise",
    "Empirical pointwise quantile": "Empirical quantile, pointwise", "Pointwise conformal": "Conformal, pointwise",
    "Gaussian on score": "Gaussian chance constr.", "Cantelli bound on score": "Cantelli bound",
    "Scenario (Campi-Garatti)": "Scenario approach", "CVaR (empirical)": "CVaR",
    "Wasserstein DRO-CVaR": "Wasserstein DRO-CVaR", "Worst-case (max score)": "Robust worst-case",
    "QR (GBM, uncalibrated)": "Quantile regression (GBM)", "CQR (Romano 2019)": "CQR",
    "CE-pair (ours, union bound)": "CE-pair (ours)", "CE-U (ours, uniform)": "CE-U (ours)",
    "CE-A (ours, terrain-adaptive)": "CE-A (ours)", "CE-R (ours, risk alpha)": "CE-R (ours)",
}
ORDER = ["Nominal (no margin)", "Fixed overlap 5 cm", "Fixed overlap 10 cm", "Fixed overlap 30 cm",
         "Slope rule (industry)", "Gaussian pointwise", "Empirical pointwise quantile", "Pointwise conformal",
         "QR (GBM, uncalibrated)", "Gaussian on score", "Cantelli bound on score", "Scenario (Campi-Garatti)",
         "CVaR (empirical)", "Wasserstein DRO-CVaR", "Worst-case (max score)", "CQR (Romano 2019)",
         "CE-pair (ours, union bound)", "CE-U (ours, uniform)", "CE-A (ours, terrain-adaptive)"]


def load(name):
    p = os.path.join(RES, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".png"))
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    plt.close(fig)


def panel(ax, letter):
    ax.text(-0.02, 1.04, f"({letter})", transform=ax.transAxes, fontsize=8.5, fontweight="bold",
            ha="right", va="bottom", color=INK)


def cp_ci(k, n, a=0.05):
    lo = beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return lo, hi


def col(m):
    return OURS.get(m, INK2)


# ------------------------------------------------------------------ Fig 1 schematic
def fig_overview():
    fig = plt.figure(figsize=(7.2, 2.9))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 40)
    ax.axis("off")
    boxes = [
        (2, 22, 15, 13, "Past operations\n(RTK logs, $n$ runs)", "#eef4fc"),
        (20, 22, 22, 13, "Pass-to-pass score\n$S=\\sup_{k,x}\\,\\frac{e_{k+1}-e_k}{\\sigma_k+\\sigma_{k+1}}$\n(Lemma 1)", "#eef4fc"),
        (45, 22, 17, 13, "Conformal quantile $q$\nfixed-point / weighted\n(Thm. 1–3)", "#eef4fc"),
        (65, 22, 16, 13, "Eroded footprint\n$h_k = w/2 - q\\,\\sigma_k$", "#eef4fc"),
        (84, 22, 14, 13, "Greedy swath\nplacement\n(Prop. 5)", "#eef4fc"),
        (65, 3, 33, 12, "Execution: real terrain + RTK error\n(LQR-I / Stanley / pure pursuit)\n$\\Rightarrow\\ P(\\mathrm{no\\ missed\\ area}) \\geq 1-\\varepsilon$", "#eef8f3"),
        (24, 3, 38, 12, "Online update (ACI)\n$\\varepsilon_t \\leftarrow \\varepsilon_t + \\gamma\\,(\\varepsilon - \\mathbb{1}\\{\\mathrm{miss}_t\\})$\nhandles seasonal drift", "#fdf3ea"),
    ]
    for x, y, w, h, t, fc in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc,
                                    ec=INK2, lw=0.6))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=6.6, color=INK)
    arr = dict(arrowstyle="-|>", mutation_scale=8, lw=0.8, color=INK2)
    for x0, x1 in [(17.4, 19.6), (42.4, 44.6), (62.4, 64.6), (81.4, 83.6)]:
        ax.add_patch(FancyArrowPatch((x0, 28.5), (x1, 28.5), **arr))
    ax.add_patch(FancyArrowPatch((91, 21.6), (91, 15.4), **arr))
    ax.add_patch(FancyArrowPatch((64.6, 9), (62.4, 9), **arr))
    ax.add_patch(FancyArrowPatch((31, 15.4), (31, 21.6), **arr))
    ax.text(1, 38.5, "Conformal erosion: certified coverage planning under execution uncertainty",
            fontsize=8, fontweight="bold", color=INK)
    # inset: two passes and a gap
    ia = fig.add_axes([0.02, 0.05, 0.17, 0.30])
    xs = np.linspace(0, 10, 200)
    e1 = 0.25 * np.sin(xs * 0.8)
    e2 = -0.25 * np.sin(xs * 0.7 + 1) + 0.15
    ia.fill_between(xs, 0 + e1 - 1, 0 + e1 + 1, color=BLUE, alpha=0.35, lw=0)
    ia.fill_between(xs, 1.9 + e2 - 1, 1.9 + e2 + 1, color=AQUA, alpha=0.35, lw=0)
    gap = (1.9 + e2 - 1) > (e1 + 1)
    ia.fill_between(xs, e1 + 1, 1.9 + e2 - 1, where=gap, color=RED, lw=0)
    ia.set_xticks([])
    ia.set_yticks([])
    ia.grid(False)
    ia.set_title("red: missed strip between passes", fontsize=6, color=INK2, pad=2)
    save(fig, "fig1_overview")


# ------------------------------------------------------------------ Fig 2 data
def fig_data():
    meta = json.load(open(os.path.join(HERE, "data", "fields.json")))
    dem = {int(f[:-4]) for f in os.listdir(os.path.join(HERE, "data", "dem"))}
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.15), gridspec_kw=dict(width_ratios=[1.25, 1, 1, 1.2]))
    for kind, c in [("paddy", ORANGE), ("wheat", BLUE)]:
        x = [m for j, m in enumerate(meta) if m["kind"] == kind and j in dem]
        axs[0].scatter([m["lon"] for m in x], [m["lat"] for m in x], s=5, color=c, lw=0, alpha=0.8,
                       label=f"{'Paddy (hilly south)' if kind=='paddy' else 'Wheat (North China Plain)'}, n={len(x)}")
    axs[0].set_xlabel("Longitude (°E)")
    axs[0].set_ylabel("Latitude (°N)")
    axs[0].set_xlim(108, 122)
    axs[0].set_ylim(23, 41)
    axs[0].legend(loc="lower left", fontsize=5.6, handletextpad=0.2, markerscale=2)
    panel(axs[0], "a")
    try:
        import core
        sl = {k: [f.z_mean_slope for f in core.load_fields(k)] for k in ("paddy", "wheat")}
        bins = np.linspace(0, 8, 33)
        axs[1].hist(sl["wheat"], bins=bins, color=BLUE, alpha=0.75, label="wheat", edgecolor="white", lw=0.3)
        axs[1].hist(sl["paddy"], bins=bins, color=ORANGE, alpha=0.65, label="paddy", edgecolor="white", lw=0.3)
        axs[1].set_xlabel("Mean field slope (°), Copernicus DEM")
        axs[1].set_ylabel("Fields")
        axs[1].legend()
    except Exception:
        pass
    panel(axs[1], "b")
    r = np.load(os.path.join(HERE, "data", "rtk_error.npz"))
    e = (r["lat_err"] - r["lat_err"].mean()) * 100
    bins = np.linspace(-20, 20, 81)
    axs[2].hist(e, bins=bins, density=True, color=BLUE, edgecolor="white", lw=0.2)
    z = np.linspace(-20, 20, 400)
    axs[2].plot(z, norm.pdf(z, 0, e.std()), color=ORANGE, lw=1.2, label="Gaussian fit")
    axs[2].set_yscale("log")
    axs[2].set_ylim(1e-4, 1)
    axs[2].set_xlabel("Real RTK lateral error (cm)")
    axs[2].set_ylabel("Density")
    axs[2].text(0.03, 0.95, f"kurtosis {kurtosis(e):.0f}\nmax {np.abs(e).max():.0f} cm", transform=axs[2].transAxes,
                va="top", fontsize=6, color=INK2)
    axs[2].legend(loc="upper right")
    panel(axs[2], "c")
    P = np.load(os.path.join(HERE, "data", "citrus_passes.npy"), allow_pickle=True)
    ps = [p for p in P if p["seq"].startswith("05")]
    for p in ps:
        axs[3].plot(p["x"], p["row"] * p["spacing"] + p["e"], color=BLUE if p["dir"] > 0 else AQUA, lw=0.8)
    for k in sorted({p["row"] for p in ps}):
        axs[3].axhline(k * ps[0]["spacing"], color=MUTED, lw=0.5, ls="--", zorder=0)
    axs[3].set_xlabel("Along-row (m)")
    axs[3].set_ylabel("Lateral (m)")
    axs[3].set_title("Real orchard robot passes (CitrusFarm 13D)", fontsize=6.5, loc="left", color=INK2)
    panel(axs[3], "d")
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig2_data")


# ------------------------------------------------------------------ Fig 3 main
def dot_panel(ax_cov, ax_ov, d, methods, n_test, title_cov=True):
    ys = np.arange(len(methods))[::-1]
    for y, m in zip(ys, methods):
        x = d[d.method == m]
        ok = x.dropna(subset=["p_nomiss"])
        c = col(m)
        if len(ok):
            jit = (np.random.default_rng(0).random(len(ok)) - 0.5) * 0.45
            ax_cov.scatter(ok.p_nomiss, y + jit, s=3, color=c, alpha=0.35, lw=0)
            k = int(round((ok.p_nomiss * n_test).sum()))
            n = n_test * len(ok)
            lo, hi = cp_ci(k, n)
            mu = ok.p_nomiss.mean()
            ax_cov.plot([lo, hi], [y, y], color=c, lw=2.2, solid_capstyle="round")
            ax_cov.scatter([mu], [y], s=16, color=c, edgecolor="white", lw=0.8, zorder=3)
            ov = ok.overlap * 100
            se = ov.std() / math.sqrt(len(ov)) if len(ov) > 1 else 0
            ax_ov.barh(y, ov.mean(), height=0.62, color=c, alpha=0.9 if m in OURS else 0.55, edgecolor="white")
            ax_ov.errorbar(ov.mean(), y, xerr=1.96 * se, color=INK, lw=0.6, capsize=1.5)
            ax_ov.text(ov.mean() + 1.96 * se + 0.6, y, f"{ov.mean():.1f}", va="center", fontsize=5.6, color=INK2)
        ninf = int(x.p_nomiss.isna().sum())
        if ninf:
            ax_ov.text(0.98, y, f"{ninf} infeasible", transform=ax_ov.get_yaxis_transform(), ha="right",
                       va="center", fontsize=5.4, color=RED)
    ax_cov.axvline(0.9, color=RED, lw=0.8, ls="--")
    ax_cov.set_yticks(ys)
    ax_cov.set_yticklabels([LABEL.get(m, m) for m in methods])
    for t, m in zip(ax_cov.get_yticklabels(), methods):
        if m in OURS:
            t.set_color(OURS[m])
            t.set_fontweight("bold")
    ax_cov.set_xlim(-0.03, 1.03)
    ax_cov.set_xlabel("P(no missed area)  [dots: fields; bar: 95% CI]")
    ax_ov.set_yticks(ys)
    ax_ov.set_yticklabels([])
    ax_ov.set_xlabel("Overlap (%)")
    ax_ov.grid(axis="y", visible=False)
    ax_cov.grid(axis="y", visible=False)


def fig_main():
    ds = {k: (load(f"main_{k}_v3.csv") if load(f"main_{k}_v3.csv") is not None else load(f"main_{k}_v2.csv"))
          for k in ("paddy", "wheat")}
    if any(v is None for v in ds.values()):
        return
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 4.4), gridspec_kw=dict(width_ratios=[1.35, 0.8, 1.35, 0.8]))
    for i, (k, d) in enumerate(ds.items()):
        methods = [m for m in ORDER if m in d.method.unique()]
        dot_panel(axs[2 * i], axs[2 * i + 1], d, methods, 300)
        axs[2 * i].set_title(f"{'Paddy, hilly' if k=='paddy' else 'Wheat, plain'}: {d.field.nunique()} real fields",
                             loc="left")
        panel(axs[2 * i], "abcd"[2 * i])
        panel(axs[2 * i + 1], "abcd"[2 * i + 1])
        if i == 1:
            axs[2].set_yticklabels([])
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig3_main")


# ------------------------------------------------------------------ Fig 4 real robot
def fig_real():
    d = load("real.csv")
    if d is None:
        return
    fig = plt.figure(figsize=(7.2, 5.2))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1], height_ratios=[1.25, 1], hspace=0.55, wspace=0.08)
    ax0, ax1 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
    sub = gs[1, :].subgridspec(1, 2, width_ratios=[1.3, 1], wspace=0.3)
    ax2, ax3 = fig.add_subplot(sub[0]), fig.add_subplot(sub[1])
    x = d[(d.split == "random") & (d.K == 3) & (d.eps == 0.1)]
    methods = [m for m in ORDER if m in x.method.unique()]
    ys = np.arange(len(methods))[::-1]
    for y, m in zip(ys, methods):
        g = x[x.method == m].dropna(subset=["p_nomiss"])
        c = col(m)
        if len(g):
            q = np.percentile(g.p_nomiss, [5, 95])
            ax0.plot([q[0], q[1]], [y, y], color=c, lw=2.2, solid_capstyle="round")
            ax0.scatter([g.p_nomiss.mean()], [y], s=16, color=c, edgecolor="white", lw=0.8, zorder=3)
            ax1.barh(y, g.overlap.mean() * 100, height=0.62, color=c, alpha=0.9 if m in OURS else 0.55,
                     edgecolor="white")
            ax1.text(g.overlap.mean() * 100 + 1, y, f"{g.overlap.mean()*100:.0f}", va="center", fontsize=5.6,
                     color=INK2)
    ax0.axvline(0.9, color=RED, lw=0.8, ls="--")
    ax0.set_yticks(ys)
    ax0.set_yticklabels([LABEL.get(m, m) for m in methods])
    for t, m in zip(ax0.get_yticklabels(), methods):
        if m in OURS:
            t.set_color(OURS[m])
            t.set_fontweight("bold")
    ax0.set_xlabel("P(no missed area)")
    ax0.set_title("Random splits (300×): mean and 5–95% range", loc="left")
    ax1.set_yticks(ys)
    ax1.set_yticklabels([])
    ax1.set_xlabel("Overlap (%)")
    ax1.set_title("Cost", loc="left")
    for a_ in (ax0, ax1):
        a_.grid(axis="y", visible=False)
    sel = [("CE-U (ours, uniform)", BLUE), ("Scenario (Campi-Garatti)", MUTED), ("CVaR (empirical)", INK2),
           ("Gaussian on score", YELLOW)]
    splits = ["LOBO:13B", "LOBO:13D", "LOBO:14B", "LODO:07-16", "LODO:07-18"]
    xx = np.arange(len(splits))
    bw = 0.2
    for j, (m, c) in enumerate(sel):
        v = [d[(d.split == s_) & (d.K == 3) & (d.eps == 0.1) & (d.method == m)].p_nomiss.mean() for s_ in splits]
        ax2.bar(xx + (j - 1.5) * bw, v, width=bw - 0.02, color=c, label=LABEL[m], edgecolor="white")
    ax2.axhline(0.9, color=RED, lw=0.8, ls="--")
    ax2.set_xticks(xx)
    ax2.set_xticklabels(["13B", "13D", "14B", "07-16", "07-18"])
    ax2.set_xlabel("held-out block                       held-out day")
    ax2.set_ylim(0.6, 1.02)
    ax2.set_ylabel("P(no missed area)")
    ax2.set_title("Out-of-distribution: leave-one-block/day-out", loc="left")
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=4, fontsize=5.8)
    ax2.grid(axis="x", visible=False)
    a = load("real_aci.csv")
    if a is not None:
        for m, c in [("static (first day)", ORANGE), ("ACI (ours, online)", BLUE)]:
            g = a[(a.method == m) & (a.K == 3)].sort_values("t")
            cm = g.err.expanding().mean()
            ax3.plot(g.t.values, cm.values, color=c, label=f"{m}: overlap {g.overlap.mean()*100:.0f}%")
        ax3.axhline(0.1, color=RED, lw=0.8, ls="--")
        ax3.set_xlabel("Real operation strips in chronological order")
        ax3.set_ylabel("Cumulative miss frequency")
        ax3.set_title("Online deployment on the real stream", loc="left")
        ax3.legend(loc="upper right", fontsize=5.8)
        ax3.set_ylim(-0.01, 0.35)
    for a_, l in zip((ax0, ax1, ax2, ax3), "abcd"):
        panel(a_, l)
    save(fig, "fig4_real_robot")


# ------------------------------------------------------------------ Fig 5 validity
def fig_validity():
    d, n = load("validity_paddy.csv"), load("ncal_paddy.csv")
    if d is None:
        return
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.4))
    for ax, var, c, title in [(axs[0], "U", BLUE, "CE-U"), (axs[1], "A", AQUA, "CE-A")]:
        for m, cc, lab in [("CE", c, "conformal erosion (ours)"), ("Gaussian on score", ORANGE, "Gaussian chance constr.")]:
            x = d[(d.variant == var) & (d.method == m)]
            g = x.groupby("eps").p_nomiss
            mu, sd, cnt = g.mean(), g.std(), g.count()
            t = 1 - mu.index.values
            ax.errorbar(t, mu.values, yerr=1.96 * sd.values / np.sqrt(cnt.values), marker="o", ms=3.5, color=cc,
                        capsize=1.5, lw=1.3, label=lab)
        tt = np.linspace(0.65, 1, 10)
        ax.fill_between(tt, tt, np.minimum(tt + 1 / 101, 1), color=BLUE, alpha=0.12, lw=0, label="theoretical band")
        ax.plot(tt, tt, color=INK2, lw=0.6, ls=":")
        ax.set_xlabel("Target 1 − ε")
        ax.set_ylabel("Realised P(no missed area)")
        ax.set_title(f"{title}: reliability (12 fields × 4 draws)", loc="left")
        ax.set_xlim(0.66, 0.97)
        ax.set_ylim(0.66, 1.0)
        panel(ax, "ab"[0 if var == "U" else 1])
    axs[0].legend(loc="upper left", fontsize=5.8)
    if n is not None:
        g = [n[n.n_cal == k].p_nomiss.values for k in sorted(n.n_cal.unique())]
        bp = axs[2].boxplot(g, tick_labels=[str(k) for k in sorted(n.n_cal.unique())], widths=0.5, patch_artist=True,
                            medianprops=dict(color=INK, lw=0.8), boxprops=dict(lw=0.5), whiskerprops=dict(lw=0.5),
                            capprops=dict(lw=0.5), flierprops=dict(ms=2, markeredgewidth=0.3))
        for b in bp["boxes"]:
            b.set_facecolor("#cfe1f6")
        axs[2].axhline(0.9, color=RED, lw=0.8, ls="--")
        axs[2].set_xlabel("Calibration operations n")
        axs[2].set_ylabel("Realised P(no missed area)")
        axs[2].set_title("Sample efficiency (CE-A)", loc="left")
        panel(axs[2], "c")
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig5_validity")


# ------------------------------------------------------------------ Fig 6 cross-field
def fig_cross():
    parts = [x for x in (load("cross2_paddy.csv"), load("cross2_wheat.csv")) if x is not None]
    shift = [x for x in (load("cross.csv"), load("cross_reverse.csv")) if x is not None]
    if not parts:
        return
    d = pd.concat(parts)
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.8), gridspec_kw=dict(width_ratios=[1.2, 1.2, 1]))
    methods = [m for m in ORDER if m in d.method.unique()]
    for ax, kind, letter in [(axs[0], "paddy", "a"), (axs[1], "wheat", "b")]:
        x = d[d.kind == kind]
        if not len(x):
            continue
        for i, m in enumerate(methods):
            g = x[x.method == m].dropna(subset=["p_nomiss"])
            per = g.groupby("rep").p_nomiss.mean()
            ov = g.overlap.mean() * 100
            ax.errorbar(ov, per.mean(), yerr=1.96 * per.std() / math.sqrt(max(len(per), 1)),
                        fmt="o" if m in OURS else "s", ms=4.5, color=col(m), mec="white", mew=0.6, capsize=1.5, lw=0.8)
            ax.annotate(LABEL[m].replace(" (ours)", "*"), (ov, per.mean()), xytext=(3, 2),
                        textcoords="offset points", fontsize=5.4, color=col(m) if m in OURS else INK2)
        ax.axhline(0.9, color=RED, lw=0.8, ls="--")
        ax.set_xlabel("Overlap (%)")
        ax.set_ylabel("P(no missed area), unseen fields")
        ax.set_title(f"New {kind} fields, no history", loc="left")
        panel(ax, letter)
    if shift:
        s = pd.concat(shift)
        settings = [("in-region", "in-region"), ("shift wheat->paddy", "plain→hilly"), ("shift paddy->wheat", "hilly→plain")]
        ms = [("CE-U", BLUE), ("CE-A", AQUA), ("CE-AW (weighted)", VIOLET)]
        bw = 0.26
        for j, (m, c) in enumerate(ms):
            for i, (st, lab) in enumerate(settings):
                g = s[(s.setting == st) & (s.method == m)].groupby("rep").p_nomiss.mean()
                if not len(g):
                    continue
                axs[2].bar(i + (j - 1) * bw, g.mean(), width=bw - 0.03, color=c, edgecolor="white",
                           label=m if i == 1 else None)
                axs[2].errorbar(i + (j - 1) * bw, g.mean(), yerr=1.96 * g.std() / math.sqrt(len(g)), color=INK,
                                lw=0.6, capsize=1.5)
        axs[2].set_xticks(range(3))
        axs[2].set_xticklabels([l for _, l in settings])
        axs[2].axhline(0.9, color=RED, lw=0.8, ls="--")
        axs[2].set_ylim(0.6, 1.0)
        axs[2].set_title("Regional shift", loc="left")
        axs[2].legend(loc="lower right", fontsize=5.8)
        axs[2].grid(axis="x", visible=False)
        panel(axs[2], "c")
    fig.tight_layout(w_pad=0.8)
    save(fig, "fig6_cross_field")


# ------------------------------------------------------------------ Fig 7 ablation
def fig_ablation():
    d = load("ablation.csv")
    if d is None:
        return
    variants = ["full (ours)", "naive calibration (no fixed point)", "absolute-error score", "pointwise quantile (no sup)"]
    colors = [BLUE, YELLOW, MAGENTA, MUTED]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.3))
    xx = np.arange(2)
    bw = 0.2
    for j, (v, c) in enumerate(zip(variants, colors)):
        for i, kind in enumerate(["paddy", "wheat"]):
            g = d[(d.kind == kind) & (d.variant == v)].dropna(subset=["p_nomiss"])
            if not len(g):
                continue
            for ax, val, se in [(axs[0], g.p_nomiss.mean(), g.p_nomiss.std() / math.sqrt(len(g))),
                                (axs[1], g.overlap.mean() * 100, g.overlap.std() * 100 / math.sqrt(len(g)))]:
                ax.bar(i + (j - 1.5) * bw, val, width=bw - 0.02, color=c, edgecolor="white", label=v if i == 0 else None)
                ax.errorbar(i + (j - 1.5) * bw, val, yerr=1.96 * se, color=INK, lw=0.6, capsize=1.5)
    axs[0].axhline(0.9, color=RED, lw=0.8, ls="--")
    axs[0].set_ylabel("P(no missed area)")
    axs[1].set_ylabel("Overlap (%)")
    for a, l in zip(axs, "ab"):
        a.set_xticks(xx)
        a.set_xticklabels(["paddy (hilly)", "wheat (plain)"])
        a.grid(axis="x", visible=False)
        panel(a, l)
    axs[0].legend(loc="lower left", fontsize=5.8)
    fig.tight_layout()
    save(fig, "fig7_ablation")


# ------------------------------------------------------------------ Fig 8 sensitivity
def fig_sens():
    d = load("sens.csv")
    if d is None:
        return
    groups = [("controller", "Controller"), ("roll compensation", "Roll compensation c"),
              ("implement width (m)", "Implement width (m)"), ("GNSS error scale (x RTK)", "GNSS error (× RTK)")]
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.2))
    for ax, (g, title), l in zip(axs, groups, "abcd"):
        x = d[d.group == g].copy()
        num = pd.to_numeric(x["value"], errors="coerce")
        if num.notna().all():
            x["value"] = num
        agg = x.groupby("value").agg(p=("p_nomiss", "mean"), ov=("overlap", "mean"), q=("q", "mean"))
        labels = [str(v).replace("_", "-").replace("lqr-i", "LQR-I").replace("lqr", "LQR")
                  .replace("pure-pursuit", "PurePursuit").replace("stanley", "Stanley") for v in agg.index]
        ax.bar(range(len(agg)), agg.ov * 100, color=BLUE, width=0.6, edgecolor="white")
        for i, (p, ov) in enumerate(zip(agg.p, agg.ov)):
            ax.text(i, ov * 100 + 0.3, f"{p:.2f}", ha="center", va="bottom", fontsize=5.6, color=INK)
        ax.set_xticks(range(len(agg)))
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_title(title, loc="left")
        ax.grid(axis="x", visible=False)
        panel(ax, l)
    axs[0].set_ylabel("Certified overlap (%)\nnumbers: realised P(no miss)")
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig8_sensitivity")


# ------------------------------------------------------------------ Fig 9 drift
def fig_aci():
    d = load("aci.csv")
    if d is None:
        return
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.3))
    for m, c, lab in [("static", ORANGE, "static split conformal"), ("aci", BLUE, "adaptive conformal (ACI)")]:
        x = d[d.method == m]
        roll = x.groupby("t").err.mean().rolling(40, min_periods=10).mean()
        axs[0].plot(roll.index, roll.values, color=c, label=lab)
        qq = x.groupby("t").q.mean() * 100
        axs[1].plot(qq.index, qq.values, color=c, label=lab)
    axs[0].axhline(0.1, color=RED, lw=0.8, ls="--")
    axs[0].set_ylabel("Miss frequency (rolling 40)")
    axs[1].set_ylabel("Certified erosion q (cm)")
    m = d.groupby("t").moisture.mean()
    for a, l in zip(axs, "ab"):
        a.set_xlabel("Operation index (soil moisture 0.15 → 0.9)")
        panel(a, l)
    axs[0].legend(loc="upper left")
    fig.tight_layout()
    save(fig, "fig9_drift")


if __name__ == "__main__":
    for f in (fig_overview, fig_data, fig_main, fig_real, fig_validity, fig_cross, fig_ablation, fig_sens, fig_aci):
        try:
            f()
            print("ok", f.__name__)
        except Exception as exc:  # keep going; report
            import traceback
            traceback.print_exc()
            print("FAILED", f.__name__, exc)


# ------------------------------------------------------------------ Fig 10 system-level
FAMILY_STYLE = {"industry": ("s", "#8a8984"), "planner": ("D", ORANGE), "controller": ("^", YELLOW),
                "robust": ("v", VIOLET), "model-based": ("P", MAGENTA), "learning": ("X", GREEN),
                "conformal": ("h", RED), "chance-rule": ("o", "#c3c2b7"), "ours": ("*", BLUE)}


def fig_system(name="system"):
    d = load(f"{name}.csv")
    if d is None:
        return
    d = d.copy()
    d["p_miss"] = 1 - d["p_nomiss"]
    regs = list(d.regime.unique())
    n_test = 200
    fig, axs = plt.subplots(2, len(regs), figsize=(7.2, 5.6), squeeze=False)
    for j, rg in enumerate(regs):
        x = d[d.regime == rg]
        ax = axs[0, j]
        g = x.groupby(["system", "family"]).agg(pm=("p_miss", "mean"), ov=("overlap", "mean"),
                                                n=("field", "nunique")).reset_index()
        for _, r in g.iterrows():
            mk, c = FAMILY_STYLE.get(r.family, ("o", INK2))
            y = max(r.pm, 1.0 / (n_test * max(r.n, 1)))  # floor at the resolution of the test set
            ax.scatter(r.ov * 100, y, marker=mk, s=70 if r.family == "ours" else 28, color=c,
                       edgecolor="white", linewidth=0.6, zorder=3 if r.family == "ours" else 2)
        ax.axhline(0.1, color=RED, lw=0.8, ls="--")
        ax.set_yscale("log")
        ax.set_ylim(1.0 / (n_test * 60) / 1.5, 1.2)
        ax.set_xlabel("Overlap (%)")
        if j == 0:
            ax.set_ylabel("P(missed area > 0)  [log]")
        ax.set_title(rg, loc="left")
        panel(ax, "abc"[j])
        # bottom: fraction of fields meeting the target vs overlap, ours vs others
        ax2 = axs[1, j]
        from scipy.stats import binomtest
        meet = x.dropna(subset=["p_nomiss"]).groupby(["system", "family"]).apply(
            lambda t: np.mean([binomtest(int(round(p * n_test)), n_test, 0.9, alternative="less").pvalue >= 0.05
                               for p in t.p_nomiss]), include_groups=False).rename("meet").reset_index()
        meet = meet.merge(g[["system", "ov"]], on="system")
        for _, r in meet.iterrows():
            mk, c = FAMILY_STYLE.get(r.family, ("o", INK2))
            ax2.scatter(r.ov * 100, r.meet * 100, marker=mk, s=70 if r.family == "ours" else 28, color=c,
                        edgecolor="white", linewidth=0.6, zorder=3 if r.family == "ours" else 2)
        ax2.set_xlabel("Overlap (%)")
        if j == 0:
            ax2.set_ylabel("Fields meeting P(no miss) ≥ 0.9 (%)")
        ax2.set_ylim(-3, 103)
        panel(ax2, "def"[j])
    handles = [plt.Line2D([], [], ls="", marker=m, color=c, ms=7 if f == "ours" else 5, label=f)
               for f, (m, c) in FAMILY_STYLE.items()]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.04), fontsize=6.5)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "fig10_system")
