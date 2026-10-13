"""Figures and statistical tables for the paper (reads results/*.csv).

Usage: python3 experiments/make_figures.py
Outputs: figures/*.png, results/tables.md
"""
import json
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import beta, norm, wilcoxon

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

# reference categorical palette (light mode), fixed order
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150,
    "savefig.bbox": "tight", "legend.frameon": False, "lines.linewidth": 2,
})

OURS = ["CE-U (ours, uniform)", "CE-A (ours, terrain-adaptive)"]
ORDER = ["Nominal (no margin)", "Fixed overlap 5 cm", "Fixed overlap 10 cm", "Gaussian pointwise",
         "Empirical pointwise quantile", "Gaussian on score", "Cantelli bound on score",
         "Worst-case (max score)", "CE-U (ours, uniform)", "CE-A (ours, terrain-adaptive)",
         "CE-R (ours, risk alpha)"]


def cp_ci(k, n, a=0.05):
    lo = beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return lo, hi


def load(name):
    p = os.path.join(RES, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def main_table(lines):
    for kind in ("paddy", "wheat"):
        d = load(f"main_{kind}_v2.csv")
        if d is None:
            d = load(f"main_{kind}.csv")
        if d is None:
            continue
        n_test = 300
        lines.append(f"\n### E2 main comparison: {kind} ({d.field.nunique()} real fields, "
                     f"{n_test} executions per method per field, target P(no miss) >= 0.90)\n")
        lines.append("| Method | P(no miss) [95% CI] | Fields meeting target | E[missed area] (‱) | "
                     "Overlap (%) | Passes | Infeasible fields | Overlap vs CE-U (Wilcoxon p) |")
        lines.append("|---|---|---|---|---|---|---|---|")
        ref = d[d.method == "CE-U (ours, uniform)"].set_index("field")
        for m in [o for o in ORDER if o in d.method.unique()]:
            x = d[d.method == m]
            ok = x.dropna(subset=["p_nomiss"])
            k = int(round((ok.p_nomiss * n_test).sum()))
            n = n_test * len(ok)
            lo, hi = cp_ci(k, n) if n else (np.nan, np.nan)
            meet = (ok.p_nomiss >= 0.9 - 1.96 * math.sqrt(0.09 / n_test)).mean() if len(ok) else np.nan
            inf = int(x.p_nomiss.isna().sum())
            j = ok.set_index("field").join(ref[["overlap"]], rsuffix="_ref", how="inner")
            if m != "CE-U (ours, uniform)" and len(j) > 5 and (j.overlap - j.overlap_ref).abs().sum() > 0:
                p = wilcoxon(j.overlap, j.overlap_ref).pvalue
                ps = f"{p:.1e}"
            else:
                ps = "-"
            lines.append(f"| {m} | {ok.p_nomiss.mean():.3f} [{lo:.3f}, {hi:.3f}] | {meet*100:.0f}% | "
                         f"{ok.e_miss.mean()*1e4:.2f} | {ok.overlap.mean()*100:.1f} | {ok.passes.mean():.1f} | "
                         f"{inf} | {ps} |")
        fig_main(d, kind)


def fig_main(d, kind):
    fig, ax = plt.subplots(figsize=(5.2, 3.4))
    ms = [o for o in ORDER if o in d.method.unique() and "CE-R" not in o]
    for i, m in enumerate(ms):
        x = d[d.method == m].dropna(subset=["p_nomiss"])
        col = C[0] if "CE-U" in m else C[2] if "CE-A" in m else INK2
        mk = "o" if "ours" in m else "s"
        ax.scatter(x.overlap.mean() * 100, x.p_nomiss.mean(), s=46, color=col, marker=mk,
                   edgecolor="white", linewidth=1.5, zorder=3)
        ax.annotate(m.replace(" (ours, uniform)", " (ours)").replace(" (ours, terrain-adaptive)", " (ours)"),
                    (x.overlap.mean() * 100, x.p_nomiss.mean()), textcoords="offset points",
                    xytext=(6, -3), fontsize=7, color=INK)
    ax.axhline(0.9, color=C[7], lw=1, ls="--")
    ax.text(0.2, 0.915, "target 1 - ε = 0.90", color=INK2, fontsize=7)
    ax.set_xlabel("Overlap (% of main area)")
    ax.set_ylabel("P(no missed area)")
    ax.set_title(f"Coverage guarantee vs. overlap cost ({kind})", fontsize=9, color=INK, loc="left")
    fig.savefig(os.path.join(FIG, f"fig_main_{kind}.png"))
    plt.close(fig)


def fig_validity(lines):
    d = load("validity_paddy.csv")
    if d is None:
        return
    fig, axs = plt.subplots(1, 2, figsize=(7, 3.0), sharey=True)
    for ax, var, title in zip(axs, ["U", "A"], ["CE-U", "CE-A"]):
        for j, (m, col) in enumerate([("CE", C[0] if var == "U" else C[2]), ("Gaussian on score", C[1])]):
            x = d[(d.variant == var) & (d.method == m)]
            g = x.groupby("eps").p_nomiss
            mu, sd, n = g.mean(), g.std(), g.count()
            t = 1 - mu.index.values
            ax.errorbar(t, mu.values, yerr=1.96 * sd.values / np.sqrt(n.values), marker="o", ms=5,
                        color=col, capsize=2, label=("conformal (ours)" if m == "CE" else m))
        ax.plot([0.65, 1], [0.65, 1], color=INK2, lw=1, ls=":")
        ax.plot([0.65, 1], [0.65 + 1 / 101, 1 + 1 / 101], color=GRID, lw=1)
        ax.set_xlabel("Target 1 - ε")
        ax.set_title(title, loc="left", fontsize=9)
    axs[0].set_ylabel("Realised P(no miss)")
    axs[0].legend(fontsize=7, loc="upper left")
    fig.savefig(os.path.join(FIG, "fig_validity.png"))
    plt.close(fig)
    lines.append("\n### E1 validity (paddy, 12 fields x 4 calibration draws x 300 executions)\n")
    lines.append("| Variant | Method | ε | target | realised mean | realised min field | overlap % |")
    lines.append("|---|---|---|---|---|---|---|")
    for (v, m, e), x in d.groupby(["variant", "method", "eps"]):
        lines.append(f"| {v} | {m} | {e} | {1-e:.2f} | {x.p_nomiss.mean():.3f} | "
                     f"{x.groupby('field').p_nomiss.mean().min():.3f} | {x.overlap.mean()*100:.1f} |")
    n = load("ncal_paddy.csv")
    if n is not None:
        lines.append("\n### E1b calibration-set size (CE-A, ε = 0.1)\n")
        lines.append("| n_cal | realised P(no miss) mean | sd across draws | overlap % |")
        lines.append("|---|---|---|---|")
        for k, x in n.groupby("n_cal"):
            lines.append(f"| {k} | {x.p_nomiss.mean():.3f} | {x.p_nomiss.std():.3f} | {x.overlap.mean()*100:.1f} |")


def fig_cross(lines):
    d = load("cross.csv")
    if d is None:
        return
    lines.append("\n### E3 cross-field certificates and regional shift (ε = 0.1)\n")
    lines.append("| Setting | Method | P(no miss) mean | 95% CI | overlap % | repeats |")
    lines.append("|---|---|---|---|---|---|")
    for (s, m), x in d.groupby(["setting", "method"]):
        per_rep = x.groupby("rep").p_nomiss.mean()
        ci = 1.96 * per_rep.std() / math.sqrt(max(len(per_rep), 1))
        lines.append(f"| {s} | {m} | {x.p_nomiss.mean():.3f} | ±{ci:.3f} | {x.overlap.mean()*100:.1f} | {len(per_rep)} |")
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    keys = list(d.groupby(["setting", "method"]).groups.keys())
    for i, (s, m) in enumerate(keys):
        x = d[(d.setting == s) & (d.method == m)].groupby("rep").p_nomiss.mean()
        ax.bar(i, x.mean(), width=0.6, color=C[i % len(C)], edgecolor="white")
        ax.errorbar(i, x.mean(), yerr=1.96 * x.std() / math.sqrt(len(x)), color=INK, capsize=3, lw=1)
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([f"{s}\n{m}" for s, m in keys], fontsize=6)
    ax.axhline(0.9, color=C[7], lw=1, ls="--")
    ax.set_ylim(0.5, 1.02)
    ax.set_ylabel("P(no miss) on unseen fields")
    fig.savefig(os.path.join(FIG, "fig_cross.png"))
    plt.close(fig)


def fig_sens(lines):
    d = load("sens.csv")
    if d is None:
        return
    groups = list(d.group.unique())
    fig, axs = plt.subplots(1, len(groups), figsize=(2.3 * len(groups), 2.6))
    lines.append("\n### E4/E5 sensitivity (paddy, CE-U, ε = 0.1)\n")
    lines.append("| Factor | Value | P(no miss) | q (cm) | overlap % | nominal E[miss] (‱) |")
    lines.append("|---|---|---|---|---|---|")
    for ax, g in zip(np.atleast_1d(axs), groups):
        x = d[d.group == g]
        agg = x.groupby("value").agg(p=("p_nomiss", "mean"), q=("q", "mean"), ov=("overlap", "mean"),
                                     nm=("nominal_e_miss", "mean"))
        for v, r in agg.iterrows():
            lines.append(f"| {g} | {v} | {r.p:.3f} | {r.q*100:.1f} | {r.ov*100:.1f} | {r.nm*1e4:.2f} |")
        labels = [str(v) for v in agg.index]
        ax.bar(range(len(agg)), agg.ov * 100, color=C[0], width=0.6, edgecolor="white")
        ax2 = ax.twinx() if False else None
        for i, p in enumerate(agg.p):
            ax.text(i, agg.ov.iloc[i] * 100, f"{p:.2f}", ha="center", va="bottom", fontsize=6, color=INK)
        ax.set_xticks(range(len(agg)))
        ax.set_xticklabels(labels, fontsize=7, rotation=30)
        ax.set_title(g, fontsize=8, loc="left")
    np.atleast_1d(axs)[0].set_ylabel("Certified overlap (%)\n(labels: realised P(no miss))")
    fig.savefig(os.path.join(FIG, "fig_sens.png"))
    plt.close(fig)


def fig_aci(lines):
    d = load("aci.csv")
    if d is None:
        return
    fig, ax = plt.subplots(figsize=(5.2, 2.8))
    lines.append("\n### E6 seasonal drift (soil moisture 0.15 -> 0.9), target miss frequency 0.10\n")
    lines.append("| Method | long-run miss frequency | last-100 miss freq. | mean passes |")
    lines.append("|---|---|---|---|")
    for i, m in enumerate(["static", "aci"]):
        x = d[d.method == m]
        roll = x.groupby("t").err.mean().rolling(40, min_periods=10).mean()
        ax.plot(roll.index, roll.values, color=C[1] if m == "static" else C[0],
                label="static split conformal" if m == "static" else "adaptive conformal (ACI)")
        last = x[x.t >= x.t.max() - 99]
        lines.append(f"| {m} | {x.err.mean():.3f} | {last.err.mean():.3f} | {x.passes.mean():.1f} |")
    ax.axhline(0.1, color=C[7], lw=1, ls="--")
    ax.set_xlabel("Operation index (moisture increases →)")
    ax.set_ylabel("Miss frequency (rolling 40)")
    ax.legend(fontsize=7)
    fig.savefig(os.path.join(FIG, "fig_aci.png"))
    plt.close(fig)


def fig_data(lines):
    meta = json.load(open(os.path.join(HERE, "data", "fields.json")))
    dem = {int(f[:-4]) for f in os.listdir(os.path.join(HERE, "data", "dem"))}
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for i, kind in enumerate(["paddy", "wheat"]):
        x = [m for j, m in enumerate(meta) if m["kind"] == kind and j in dem]
        axs[0].scatter([m["lon"] for m in x], [m["lat"] for m in x], s=8, color=C[i], label=kind,
                       edgecolor="white", linewidth=0.4)
    axs[0].set_xlabel("Longitude (°E)")
    axs[0].set_ylabel("Latitude (°N)")
    axs[0].legend(fontsize=7)
    axs[0].set_title("Real field locations (harvester GNSS)", fontsize=8, loc="left")
    r = np.load(os.path.join(HERE, "data", "rtk_error.npz"))
    e = (r["lat_err"] - r["lat_err"].mean()) * 100
    bins = np.linspace(-20, 20, 81)
    axs[1].hist(e, bins=bins, density=True, color=C[0], edgecolor="white", linewidth=0.3)
    z = np.linspace(-20, 20, 400)
    axs[1].plot(z, norm.pdf(z, 0, e.std()), color=C[1], lw=1.5, label="Gaussian fit")
    axs[1].set_yscale("log")
    axs[1].set_ylim(1e-4, 1)
    axs[1].set_xlabel("Real RTK lateral error (cm)")
    axs[1].legend(fontsize=7)
    axs[1].set_title("Heavy tail of real RTK error", fontsize=8, loc="left")
    fig.savefig(os.path.join(FIG, "fig_data.png"))
    plt.close(fig)
    from scipy.stats import kurtosis
    lines.append("\n### Data summary\n")
    for kind in ["paddy", "wheat"]:
        x = [m for j, m in enumerate(meta) if m["kind"] == kind]
        lines.append(f"- {kind}: {len(x)} fields extracted from harvester trajectories "
                     f"(median {np.median([m['area_m2'] for m in x])/1e4:.2f} ha)")
    lines.append(f"- DEM patches (Copernicus GLO-30): {len(dem)} fields")
    lines.append(f"- RTK lateral error: n={len(e)} epochs, sd={e.std():.2f} cm, max |e|={np.abs(e).max():.1f} cm, "
                 f"excess kurtosis={kurtosis(e):.1f}")


def main():
    lines = ["# Experiment tables (auto-generated by make_figures.py)"]
    fig_data(lines)
    main_table(lines)
    fig_validity(lines)
    fig_cross(lines)
    fig_sens(lines)
    fig_aci(lines)
    open(os.path.join(RES, "tables.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
