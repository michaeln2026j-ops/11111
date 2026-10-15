"""Publication figures for docs/paper/manuscript.md, built only from result files in the repository
(no re-simulation).

    python3 scripts/make_paper_figures.py      # -> figures/paper/<name>.pdf / .png / .tif

Style: Elsevier artwork sizes (single column 90 mm, double column 190 mm), Arial-metric sans serif
(Liberation Sans) at 7-8 pt, vector PDF with embedded TrueType fonts, 600 dpi PNG/TIFF, bold panel
letters, no in-figure titles (captions carry the description), one colour per method used consistently
in every figure, and marker shapes as a second, colour-independent encoding.
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
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402
from matplotlib.ticker import NullFormatter  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "figures", "paper")
sys.path.insert(0, os.path.join(ROOT, "experiments"))
import exp_lowdata as X  # noqa: E402

MM = 1 / 25.4
SINGLE, DOUBLE = 90 * MM, 190 * MM

# validated categorical palette (fixed order; dataviz reference palette), inks and neutrals
BLUE, ORANGE, GREEN, PURPLE = "#2a78d6", "#eb6834", "#1baf7a", "#6250d6"
LIGHTBLUE = "#7fb0ea"
INK, INK2, MUTED, GRID, SHADE = "#1a1a1a", "#4d4d4d", "#8c8c8c", "#e3e3e3", "#f2f2f0"
REGIME = {"R1": ("R1  RTK, flat, 3 m", BLUE, "o"), "R2": ("R2  RTK, hilly-wet, 1.5 m", ORANGE, "s"),
          "R3": ("R3  DGPS, hilly, 6 m", GREEN, "^")}
PIVOT = {"theory": ("CE-EVT-R (theory pivot)", BLUE, "o"), "raw": ("Pooled conformal (raw)", ORANGE, "s"),
         "scale law": ("Scale-law pivot", GREEN, "^"), "spec x scale law": ("Spec. × scale-law pivot", PURPLE, "D")}

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic",
    "mathtext.bf": "Liberation Sans:bold",
    "font.size": 7, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7,
    "axes.linewidth": 0.6, "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelcolor": INK, "ytick.labelcolor": INK,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "lines.linewidth": 1.2, "lines.markersize": 4, "errorbar.capsize": 2,
    "legend.frameon": False, "legend.handlelength": 1.6, "legend.handletextpad": 0.5, "legend.columnspacing": 1.4,
    "legend.borderaxespad": 0.3, "figure.dpi": 150, "savefig.dpi": 600, "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02, "pdf.fonttype": 42, "ps.fonttype": 42, "figure.facecolor": "white",
    "axes.facecolor": "white"})


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, f"{name}.pdf"))
    fig.savefig(os.path.join(OUT, f"{name}.png"), dpi=600)
    fig.savefig(os.path.join(OUT, f"{name}.tif"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print("wrote", name)


def panel(ax, letter, text=None, x=-0.02, y=1.04):
    """Bold panel letter at the top-left corner of the axes, with an optional short panel heading."""
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")
    if text:
        ax.text(x + 0.02, y, text, transform=ax.transAxes, fontsize=7.5, va="bottom", ha="left", color=INK2)


def tick3(key):
    """Three-line regime tick label: 'R1' / 'RTK, flat' / '3 m'."""
    name, desc = REGIME[key][0].split("  ")
    head, width = desc.rsplit(", ", 1)
    return f"{name}\n{head}\n{width}"


def log_ticks(axis, ticks):
    axis.set_minor_formatter(NullFormatter())
    axis.set_ticks(ticks)
    axis.set_ticklabels([f"{t:g}" for t in ticks])


# --------------------------------------------------------------------------------------------- Fig. 1
def fig_schematic():
    """Plan view: planned lines with erosion, executed paths, an interior gap and a field-edge miss."""
    w, lam = 3.0, 0.35
    sp = w - 2 * lam
    x = np.linspace(0, 60, 600)
    ys = [w / 2 - lam + k * sp for k in range(4)]
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
    fig, ax = plt.subplots(figsize=(DOUBLE, 62 * MM))
    ytop = ys[3] + w / 2 + 0.35
    ax.axhspan(-1.3, 0, color=SHADE, zorder=0, lw=0)
    ax.text(59.3, -0.65, "outside the field", ha="right", va="center", fontsize=7, color=MUTED, style="italic")
    ax.axhline(0, color=INK, lw=1.0, zorder=5)
    ax.text(0.6, 0.12, "field boundary", fontsize=6.5, color=INK2, va="bottom")
    for k, (y, e) in enumerate(zip(ys, dev)):
        ax.fill_between(x, y + e - w / 2, y + e + w / 2, color=BLUE, alpha=0.13, lw=0, zorder=1)
        ax.plot(x, y + e - w / 2, color=BLUE, lw=0.35, alpha=0.6, zorder=2)
        ax.plot(x, y + e + w / 2, color=BLUE, lw=0.35, alpha=0.6, zorder=2)
        ax.plot(x, np.full_like(x, y), color=INK2, lw=0.7, ls=(0, (4, 3)), zorder=3)
        ax.plot(x, y + e, color=BLUE, lw=1.2, zorder=4)
        ax.text(60.6, y, f"pass {k + 1}", fontsize=6.5, color=INK2, va="center", ha="left")
    top1, bot2 = ys[1] + dev[1] + w / 2, ys[2] + dev[2] - w / 2
    ax.fill_between(x, top1, bot2, where=bot2 > top1, color=ORANGE, lw=0, zorder=6)
    bot0 = ys[0] + dev[0] - w / 2
    ax.fill_between(x, 0, bot0, where=bot0 > 0, color=ORANGE, lw=0, zorder=6)
    ygap = (ys[1] + ys[2]) / 2
    ax.annotate("interior gap:\nadjacent passes drift apart", xy=(38.5, ygap), xytext=(44, ygap - 2.2),
                fontsize=6.5, ha="left", va="center", color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6, shrinkA=0, shrinkB=1),
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=GRID, lw=0.5), zorder=8)
    ax.annotate("field-edge miss:\noutermost pass drifts inward", xy=(12.5, 0.12), xytext=(18, -0.65),
                fontsize=6.5, ha="left", va="center", color=INK,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6, shrinkA=0, shrinkB=1), zorder=8)
    xi = np.searchsorted(x, 24)
    yl, yh = ys[3] + dev[3][xi] - w / 2, ys[2] + dev[2][xi] + w / 2
    ax.annotate("", xy=(24, yl), xytext=(24, yh), arrowprops=dict(arrowstyle="<->", color=INK, lw=0.6,
                                                                 shrinkA=0, shrinkB=0), zorder=8)
    ax.text(24.8, (yl + yh) / 2, r"overlap $2\lambda$", fontsize=6.5, va="center", ha="left", zorder=8,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.annotate("", xy=(4, ys[0]), xytext=(4, ys[1]), arrowprops=dict(arrowstyle="<->", color=INK, lw=0.6,
                                                                     shrinkA=0, shrinkB=0), zorder=8)
    ax.text(4.8, (ys[0] + ys[1]) / 2, r"$w-2\lambda$", fontsize=6.5, va="center", ha="left", zorder=8,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
    ax.set_xlim(0, 60), ax.set_ylim(-1.3, ytop)
    ax.set_xlabel("Along-pass distance (m)"), ax.set_ylabel("Lateral position (m)")
    ax.grid(False)
    ax.legend(handles=[Line2D([], [], color=INK2, ls=(0, (4, 3)), lw=0.7, label=r"Planned line (spacing $w-2\lambda$)"),
                       Line2D([], [], color=BLUE, lw=1.2, label="Executed path"),
                       Patch(fc=BLUE, alpha=0.13, ec=BLUE, lw=0.35, label=r"Implement footprint (width $w$)"),
                       Patch(color=ORANGE, label="Missed area")],
              loc="upper center", ncol=4, bbox_to_anchor=(0.5, -0.2))
    save(fig, "fig_schematic")


# --------------------------------------------------------------------------------------------- Fig. 2
def theory_points(key):
    q, s = [], []
    for d in ("lowdata_v2", "lowdata_v3"):
        for f in sorted(glob.glob(os.path.join(RES, d, f"A_{key}_*.pkl"))):
            r = pickle.load(open(f, "rb"))
            hb = f.replace("A_", "hist_")
            if not os.path.exists(hb) or not np.all(np.isfinite(r["Fhat"])):
                continue
            q.append(X.inv_cdf(r["tgrid"], r["Fhat"], 0.9))
            s.append(np.quantile(pickle.load(open(hb, "rb")), 0.9))
    return np.array(s), np.array(q)


def fig_theory():
    """Theory 0.9-quantile vs the empirical 0.9-quantile of 200 independent runs, per field."""
    fig, ax = plt.subplots(figsize=(SINGLE, SINGLE * 0.95))
    lim = np.array([0.08, 0.75])
    ax.fill_between(lim, lim / 1.1, lim * 1.1, color=SHADE, lw=0, zorder=0)
    ax.plot(lim, lim, color=INK2, lw=0.7, zorder=1)
    ax.text(0.62, 0.62 / 1.1 * 0.95, "±10%", fontsize=6.5, color=MUTED, ha="center", va="top", rotation=45)
    stats = []
    for key, (lab, col, mk) in REGIME.items():
        s, q = theory_points(key)
        e = np.log(q / s)
        stats.append(f"{key}: bias {np.mean(e) * 100:+.1f}%, sd {np.std(e, ddof=1) * 100:.1f}%  (n = {len(q)})")
        ax.scatter(s, q, s=14, marker=mk, color=col, edgecolor="white", linewidth=0.4, zorder=3,
                   label=f"{lab} (n = {len(q)})")
    txt = open(os.path.join(RES, "lowdata_v3", "check_boundary_R3.txt")).read()
    rows = re.findall(r"q_new ([\d.]+)\s+sim ([\d.]+)", txt)
    qe, se = np.array([float(a) for a, _ in rows]), np.array([float(b) for _, b in rows])
    ee = np.log(qe / se)
    ax.scatter(se, qe, s=20, marker="^", facecolor="none", edgecolor=INK, linewidth=0.7, zorder=4,
               label=f"R3 with field-edge terms (n = {len(qe)})")
    stats.append(f"R3 + edges: bias {np.mean(ee) * 100:+.1f}%, sd {np.std(ee, ddof=1) * 100:.1f}%")
    ax.set_xscale("log"), ax.set_yscale("log"), ax.set_xlim(lim), ax.set_ylim(lim)
    ticks = [0.1, 0.15, 0.2, 0.3, 0.4, 0.6]
    log_ticks(ax.xaxis, ticks), log_ticks(ax.yaxis, ticks)
    ax.grid(True, which="major", axis="both")
    ax.set_aspect("equal")
    ax.set_xlabel("Simulated 0.9-quantile of run score (m)")
    ax.set_ylabel("Theory-predicted 0.9-quantile (m)")
    ax.legend(loc="upper left", handletextpad=0.2, borderaxespad=0.2, fontsize=6.3)
    print("  fig_theory:", "; ".join(stats))
    save(fig, "fig_theory_vs_sim")


# --------------------------------------------------------------------------------------------- Fig. 3
def fig_v8():
    """Regret (overlap above the per-field oracle) of CE+ v8 vs CPP and Lindemann, fresh fields, both classes."""
    d = pd.read_csv(os.path.join(RES, "v8", "system_v8.csv"))
    sysn = {"Marginal guarantee": [("CE+ (ours)", "BCD + LQR-I + CE+ (ours, v8)", BLUE),
                                   ("CPP (Zhao et al.)", "Conformal predictive programming (Zhao et al.)", ORANGE),
                                   ("Pair-level conformal (Lindemann et al.)",
                                    "Conformal planning, pair-level union bound (Lindemann et al.)", GREEN)],
            "PAC guarantee (δ = 0.1)": [
                ("CE+ (ours)", "BCD + LQR-I + CE+ PAC (ours, v8)", BLUE),
                ("CPP (Zhao et al.)", "Conformal predictive programming, PAC delta=0.1", ORANGE),
                ("Pair-level conformal (Lindemann et al.)",
                 "Conformal planning, pair-level union bound, PAC delta=0.1", GREEN)]}
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE, 58 * MM))
    bw = 0.25
    for p_i, (ax, (cls, rows)) in enumerate(zip(axes, sysn.items())):
        top = 0
        for r_i, key in enumerate(("R1", "R2", "R3")):
            dr = d[d.regime.str.startswith(key)]
            for s_i, (lab, nm, col) in enumerate(rows):
                v = dr[dr.system == nm]
                m, se = v.regret_pp.mean(), v.regret_pp.std(ddof=1) / np.sqrt(len(v))
                xx = r_i + (s_i - 1) * (bw + 0.02)
                ax.bar(xx, m, width=bw, color=col, edgecolor="white", linewidth=0.4, zorder=2)
                ax.errorbar(xx, m, yerr=1.96 * se, color=INK, lw=0.6, capsize=1.6, capthick=0.6, zorder=3)
                ax.text(xx, m + 1.96 * se + 0.25, f"{v.p_nomiss.mean():.2f}", ha="center", va="bottom",
                        fontsize=5.6, color=INK2)
                top = max(top, m + 1.96 * se)
        ax.axhline(0, color=INK2, lw=0.6)
        ax.set_xticks(range(3), [tick3(k) for k in ("R1", "R2", "R3")])
        ax.tick_params(axis="x", length=0)
        ax.set_ylim(0, top * 1.12)
        ax.set_ylabel("Overlap above per-field oracle (pp)")
        panel(ax, "ab"[p_i], cls)
    fig.subplots_adjust(wspace=0.28)
    fig.legend(handles=[Patch(color=c, label=l) for l, _, c in sysn["Marginal guarantee"]],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.16))
    fig.text(0.5, -0.215, "Numbers above bars: pooled P(no miss); error bars: 95% confidence intervals over 30 fields.",
             ha="center", fontsize=6.3, color=INK2)
    save(fig, "fig_v8_regret")


# --------------------------------------------------------------------------------------------- Fig. 4 / 5
def parse_validity(path):
    rows = []
    sc = None
    for line in open(path):
        m = re.match(r"== (\S+):", line)
        if m:
            sc = m.group(1)
        m = re.match(r"\s+\[(\w+)\s*\]\s+(.+?)\s+mean coverage ([\d.]+) \(se ([\d.]+)\).*P\(cov>=0.9\) ([\d.]+)\s+"
                     r"(\w+)\s+mean excess ([+\-\d.]+)", line)
        if m:
            rows.append(dict(sc=sc, cls=m.group(1), method=m.group(2).strip(), cov=float(m.group(3)),
                             se=float(m.group(4)), p=float(m.group(5)), ok=m.group(6), ex=float(m.group(7))))
    return pd.DataFrame(rows)


def fig_validity():
    v = parse_validity(os.path.join(RES, "lowdata_v3", "validity_resample_extended_curves.txt"))
    meths = ["theory", "raw", "scale law", "spec x scale law"]
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE, 60 * MM))
    specs = ((axes[0], "marginal", "cov", 0.895, "Mean coverage", "Marginal rule", (0.86, 0.95)),
             (axes[1], "PAC", "p", 0.88, "Share of replicates with coverage ≥ 0.9", "PAC rule", (0.6, 1.0)))
    for p_i, (ax, cls, col_, ref, ylab, head, yl) in enumerate(specs):
        ax.axhspan(yl[0], ref, color="#fbe9e2", lw=0, zorder=0)
        ax.axhline(ref, color=ORANGE, lw=0.7, ls=(0, (3, 2)), zorder=1)
        ax.text(3.45, ref, f"registered criterion {ref:g}", fontsize=6, color=ORANGE, ha="right",
                va="bottom" if p_i == 1 else "top")
        if p_i == 0:
            ax.axhline(0.9, color=INK2, lw=0.5, ls=(0, (1, 1.5)), zorder=1)
            ax.text(-0.45, 0.9, r"$1-\varepsilon$", fontsize=6, color=INK2, va="bottom", ha="left")
        for s_i, sc in enumerate(("R1", "R2", "R3", "mixed")):
            vv = v[(v.sc == sc) & (v.cls == cls)]
            for m_i, m in enumerate(meths):
                r = vv[vv.method == m]
                if r.empty:
                    continue
                lab, col, mk = PIVOT[m]
                xx = s_i + (m_i - 1.5) * 0.17
                y = r[col_].iloc[0]
                if col_ == "cov":
                    ax.errorbar(xx, y, yerr=1.96 * r.se.iloc[0], color=col, lw=0.6, capsize=0, zorder=2)
                ax.scatter(xx, y, color=col, marker=mk, s=16, edgecolor="white", linewidth=0.4, zorder=3)
        for s_i in range(1, 4):
            ax.axvline(s_i - 0.5, color=GRID, lw=0.5, zorder=0)
        ax.set_xlim(-0.5, 3.5), ax.set_ylim(*yl)
        ax.set_xticks(range(4), ["R1", "R2", "R3", "Mixed fleet"])
        ax.tick_params(axis="x", length=0)
        ax.set_ylabel(ylab)
        panel(ax, "ab"[p_i], head)
    fig.subplots_adjust(wspace=0.25)
    fig.legend(handles=[Line2D([], [], color=PIVOT[m][1], marker=PIVOT[m][2], ls="none", ms=4.5, label=PIVOT[m][0])
                        for m in ("theory", "raw", "scale law", "spec x scale law")],
               loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.1))
    save(fig, "fig_coverage_check")


def parse_rv2(path):
    rows, n = [], None
    for line in open(path):
        m = re.match(r"== mixed fleet, \d+ fields, n_cal = (\d+)", line)
        if m:
            n = int(m.group(1))
        m = re.match(r"\s+(.+?)\s+(marginal|PAC)\s+([\d.]+)\s+(PASS|FAIL)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([+\-\d.nan]+)\s+([+\-\d.nan]+)", line)
        if m and n:
            rows.append(dict(n=n, piv=m.group(1).strip(), cls=m.group(2), cov=float(m.group(3)), refuse=float(m.group(5)),
                             c1=float(m.group(6)), c2=float(m.group(7)), c3=float(m.group(8)), ex_dep=float(m.group(9)),
                             ex_cap=float(m.group(10))))
    return pd.DataFrame(rows)


def fig_mixed():
    """Experiment B5: excess overlap of the scale pivots (n_cal = 60) and DGPS-configuration coverage."""
    v = parse_rv2(os.path.join(RES, "revision", "rv2_resampling.txt"))
    order = [("MC twin", "XCE-MC (Monte Carlo twin)", BLUE), ("theory+edges", "XCE-T (analytic model)", LIGHTBLUE),
             ("CQR", "CQR (learned, config.-aware)", PURPLE), ("per-config scale", "Per-configuration scale", PURPLE),
             ("Mondrian", "Mondrian (per configuration)", GREEN), ("spec x scale law", "Spec. × scale law", MUTED),
             ("raw", "Raw pooling", ORANGE)]
    fig = plt.figure(figsize=(DOUBLE, 52 * MM))
    gs = fig.add_gridspec(1, 4, width_ratios=[1, 1, 0.22, 0.75], wspace=0.08)
    axes = [fig.add_subplot(gs[0]), None, fig.add_subplot(gs[3])]
    axes[1] = fig.add_subplot(gs[1], sharey=axes[0])
    for p_i, cls in enumerate(("marginal", "PAC")):
        ax = axes[p_i]
        vv = v[(v.n == 60) & (v.cls == cls)].set_index("piv")
        xmax = max(vv.loc[k, "ex_dep"] for k, _, _ in order if np.isfinite(vv.loc[k, "ex_dep"]))
        for i, (k, lab, col) in enumerate(order):
            r = vv.loc[k]
            hatch = None
            if r.refuse > 0.01:
                val = r.ex_dep
                ax.barh(i, val, color=col, height=0.62, alpha=0.45, zorder=2)
                ax.text(val + xmax * 0.015, i, f"{val:.1f} (refuses {100 * r.refuse:.0f}%)", va="center", fontsize=6.2)
            else:
                ax.barh(i, r.ex_dep, color=col, height=0.62, zorder=2, hatch=hatch, edgecolor="white", linewidth=0.4)
                ax.text(r.ex_dep + xmax * 0.015, i, f"{r.ex_dep:.1f}", va="center", fontsize=6.5)
        ax.set_yticks(range(len(order)), [lab for _, lab, _ in order])
        if p_i:
            plt.setp(ax.get_yticklabels(), visible=False)
        ax.invert_yaxis() if p_i == 0 else None
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, xmax * 1.45)
        ax.grid(True, axis="x"), ax.grid(False, axis="y")
        ax.set_xlabel("Excess overlap (pp)")
        panel(ax, "abc"[p_i], f"{'Marginal' if cls == 'marginal' else 'PAC'} rule, 60 calibration fields")
    ax = axes[2]
    vv = v[(v.n == 25) & (v.cls == "marginal")].set_index("piv")
    ks = ["raw", "spec x scale law", "per-config scale", "CQR", "theory+edges", "MC twin"]
    labs = ["Raw", "Spec.", "Per-cfg", "CQR", "XCE-T", "XCE-MC"]
    cols = [ORANGE, MUTED, PURPLE, PURPLE, LIGHTBLUE, BLUE]
    for i, (k, c) in enumerate(zip(ks, cols)):
        ax.bar(i, vv.loc[k, "c3"], color=c, width=0.62, zorder=2)
        ax.text(i, vv.loc[k, "c3"] + 0.004, f"{vv.loc[k, 'c3']:.2f}", ha="center", fontsize=6)
    ax.axhline(0.9, color=INK2, lw=0.6, ls=(0, (3, 2)))
    ax.set_ylim(0.7, 1.0)
    ax.set_xticks(range(len(ks)), labs, rotation=35, ha="right")
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Mean coverage, DGPS fields")
    panel(ax, "c", "DGPS configuration, 25 fields")
    save(fig, "fig_mixed_fleet")


# --------------------------------------------------------------------------------------------- Fig. 6
def fig_learning():
    txt = open(os.path.join(RES, "lowdata_v2", "feature_learning_curve.txt")).read()
    blocks = re.split(r"\n(?=R\d:)", txt.strip())
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE, 56 * MM))
    for p_i, (ax, b) in enumerate(zip(axes, blocks)):
        key = b[:2]
        th = float(re.search(r"log-error sd ([\d.]+)", b).group(1))
        rows = re.findall(r"^\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$", b, re.M)
        m = np.array([int(r[0]) for r in rows])
        o = np.array([float(r[1]) for r in rows])
        one = np.array([float(r[2]) for r in rows])
        _, u = np.unique(m, return_index=True)
        m, o, one = m[u], o[u], one[u]
        ax.plot(m, one, color=ORANGE, marker="s", ms=3.5, mec="white", mew=0.4, label="Feature regression, 1 run per field")
        ax.plot(m, o, color=GREEN, marker="^", ms=3.8, mec="white", mew=0.4,
                label="Feature regression, oracle targets (100s of runs per field)")
        ax.axhline(th, color=BLUE, lw=1.4, label="Theory (no run data)")
        ax.set_yscale("log")
        tk = [t for t in (0.02, 0.03, 0.05, 0.1, 0.2, 0.4) if min(o.min(), th) * 0.8 <= t <= one.max() * 1.25]
        log_ticks(ax.yaxis, tk)
        ax.set_xlim(0, m.max() + 3)
        ax.set_xlabel("Number of training fields")
        if p_i == 0:
            ax.set_ylabel("SD of log(predicted / true margin)")
        panel(ax, "abc"[p_i], REGIME[key][0])
    fig.subplots_adjust(wspace=0.32)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h[::-1], l[::-1], loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.17))
    save(fig, "fig_learning_curve")


# --------------------------------------------------------------------------------------------- Fig. 7
def fig_limit():
    obs = {"R1": 1.018, "R2": 1.207, "R3": 1.645}
    pred = {"R1": (1.30, 0.35), "R2": (1.26, 0.33), "R3": (1.85, 0.74)}  # scripts/predict_limit.py, docs/theory_limit.md
    fig, ax = plt.subplots(figsize=(SINGLE, 62 * MM))
    for i, k in enumerate(("R1", "R2", "R3")):
        m, s = pred[k]
        ax.add_patch(plt.Rectangle((i - 0.22, m - s), 0.24, 2 * s, fc="#dbe8f8", ec="none", zorder=1))
        ax.plot([i - 0.22, i + 0.02], [m, m], color=BLUE, lw=1.4, zorder=2)
        ax.scatter(i + 0.14, obs[k], marker="D", s=20, color=ORANGE, edgecolor="white", linewidth=0.4, zorder=3)
    ax.axhline(1, color=INK2, lw=0.6, ls=(0, (3, 2)))
    ax.text(2.48, 1.0, "per-field optimum", fontsize=6, color=INK2, ha="right", va="bottom")
    ax.set_xlim(-0.5, 2.5), ax.set_ylim(0.8, 2.7)
    ax.set_xticks(range(3), [REGIME[k][0].replace("  ", "\n", 1) for k in ("R1", "R2", "R3")])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("PAC margin / per-field optimum")
    ax.legend(handles=[(Patch(fc="#dbe8f8", ec="none"), Line2D([], [], color=BLUE, lw=1.4)),
                       Line2D([], [], color=ORANGE, marker="D", ls="none", ms=4, mec="white", mew=0.4)],
              labels=["Theory prediction, mean ± SD", "Observed on fresh fields"], loc="upper left")
    save(fig, "fig_information_limit")


# --------------------------------------------------------------------------------------------- graphical abstract
def fig_graphical_abstract():
    """Graphical abstract (CEA: >= 1328 x 531 px, read left to right): method flow and two headline results."""
    fig = plt.figure(figsize=(DOUBLE, DOUBLE * 531 / 1328))
    ax = fig.add_axes([0.0, 0.0, 0.54, 1.0])
    ax.set_xlim(0, 10), ax.set_ylim(0, 4.2), ax.axis("off")
    ax.text(0.25, 3.95, "Certified coverage planning under execution uncertainty", fontsize=9,
            fontweight="bold", va="center")
    steps = [("Logged runs", "target-field runs, or one run\nper field of other fields", SHADE),
             ("Exact run score", r"$S$ = widest gap or edge miss;" + "\nzero miss " + r"$\Leftrightarrow S\leq\lambda$", SHADE),
             ("Five-layer theory", "Lyapunov → Kac–Rice → product\n→ mixture → Gumbel scale law", "#dbe8f8"),
             ("Conformal calibration", "certified margin " + r"$\lambda$ (overlap $2\lambda$):" + "\nP(no miss) ≥ 1 − ε", "#dbe8f8")]
    hh, y0s = 0.7, [3.1, 2.25, 1.4, 0.55]
    for n, ((title, body, col), y0) in enumerate(zip(steps, y0s)):
        ax.add_patch(FancyBboxPatch((0.25, y0 - hh / 2), 9.5, hh, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=col, ec="none"))
        ax.text(0.72, y0, str(n + 1), color="white", fontsize=7.5, fontweight="bold", ha="center", va="center", zorder=4,
                bbox=dict(boxstyle="circle,pad=0.35", fc=BLUE if n >= 2 else INK2, ec="none"))
        ax.text(1.2, y0, title, ha="left", va="center", fontsize=7.5, fontweight="bold")
        ax.text(4.6, y0, body, ha="left", va="center", fontsize=6.5, color=INK2, linespacing=1.25)
    d = pd.read_csv(os.path.join(RES, "v8", "system_v8.csv"))
    rows = [("CE+\n(ours)", "BCD + LQR-I + CE+ PAC (ours, v8)", BLUE),
            ("CPP", "Conformal predictive programming, PAC delta=0.1", ORANGE),
            ("Pair-\nlevel", "Conformal planning, pair-level union bound, PAC delta=0.1", GREEN)]
    v = parse_validity(os.path.join(RES, "lowdata_v3", "validity_resample_extended_curves.txt"))
    v = v[(v.sc == "mixed") & (v.cls == "marginal")].set_index("method")
    rows2 = [("Theory\npivot", v.loc["theory", "ex"], BLUE), ("Spec. ×\nscale", v.loc["spec x scale law", "ex"], PURPLE),
             ("Pooled", v.loc["raw", "ex"], ORANGE)]
    for k, (x0, data, head) in enumerate((
            (0.61, [(l, d[d.system == nm].regret_pp.mean(), c) for l, nm, c in rows],
             "With field data\n90 fresh fields, PAC rule"),
            (0.82, rows2, "Zero target-field data\nmixed fleet, marginal rule"))):
        a = fig.add_axes([x0, 0.2, 0.165, 0.56])
        vals = [r[1] for r in data]
        a.bar(range(3), vals, color=[r[2] for r in data], width=0.62)
        for i, v_ in enumerate(vals):
            a.text(i, v_ + max(vals) * 0.03, f"{v_:.1f}", ha="center", fontsize=6.5)
        a.set_xticks(range(3), [r[0] for r in data], fontsize=6.3)
        a.tick_params(axis="x", length=0)
        a.set_ylim(0, max(vals) * 1.18)
        a.text(0.5, 1.08, head, transform=a.transAxes, ha="center", va="bottom", fontsize=7, fontweight="bold",
               linespacing=1.2)
        if k == 0:
            a.set_ylabel("Overlap above optimum (pp)", fontsize=6.5)
    save(fig, "graphical_abstract")


if __name__ == "__main__":
    fig_schematic()
    fig_theory()
    fig_v8()
    fig_validity()
    fig_mixed()
    fig_learning()
    fig_limit()
    fig_graphical_abstract()
