"""Shared figure style + Fig. 1 (method schematic) and Fig. 7 (validity).

Double-column width 7.2 in; PNG 300 dpi + vector PDF. The other figures are in make_figures_v5.py,
which is the script to run: python3 experiments/make_figures_v5.py

Colour semantics used in every figure:
  ours                 BLUE (CE-U), AQUA (CE-A), VIOLET (CE-AW, Fig. 8 only)
  published baselines  neutral greys
  crops                ORANGE = paddy, VIOLET = wheat (Fig. 2 and Fig. 6 only)
  target 1 - eps       RED dashed line;  missed area  RED
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from scipy.stats import beta, t as student_t

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#a3a29c", "#e9e8e4"
LIGHT = "#cdcbc4"  # light neutral grey (third baseline shade)
OURS_BAND = "#eef4fc"  # background band behind the rows of our method
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 7.5, "axes.labelsize": 7.2,
    "xtick.labelsize": 6.6, "ytick.labelsize": 6.6, "legend.fontsize": 6.4,
    "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "lines.linewidth": 1.4,
    "legend.frameon": False, "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "savefig.dpi": 300,
    "figure.dpi": 110, "pdf.fonttype": 42,
})

# canonical names (shared by every figure; make_tables.py imports LABEL and ORDER)
CROP_LABEL = {"paddy": "Paddy (mostly S. China)", "wheat": "Wheat (mostly N. China Plain)"}
FIELD_COL = {"paddy": ORANGE, "wheat": VIOLET}
GNSS_LABEL = {"rtk_fix": "RTK (AR on)", "rtk_float": "RTK float-only", "dgps": "DGPS", "spp": "SPP"}
REGIME_LABEL = {"R1 RTK flat 3 m": "Wheat, RTK, w = 3 m",
                "R2 RTK hilly-wet 1.5 m": "Paddy, RTK, wet soil, w = 1.5 m",
                "R3 DGPS hilly 6 m": "Paddy, DGPS, w = 6 m"}
OURS = {"CE-U (ours, uniform)": BLUE, "CE-A (ours, terrain-adaptive)": AQUA}
LABEL = {
    "Nominal (no margin)": "Nominal (no margin)", "Fixed overlap 5 cm": "Fixed overlap 5 cm (= vendor spec)",
    "Fixed overlap 10 cm": "Fixed overlap 10 cm", "Fixed overlap 30 cm": "Fixed overlap 30 cm",
    "Slope rule (industry)": "Slope-compensation rule", "Gaussian pointwise": "Gaussian, pointwise",
    "Empirical pointwise quantile": "Empirical quantile, pointwise", "Pointwise conformal": "Conformal, pointwise",
    "Gaussian on score": "Gaussian fit of S", "Cantelli bound on score": "Cantelli bound on S",
    "Scenario (Campi-Garatti)": "Scenario on S [Campi 2011]", "CVaR (empirical)": "CVaR of S [Rockafellar 2000]",
    "Wasserstein DRO-CVaR": "W-DRO-CVaR on S [Mohajerin Esfahani 2018]", "Worst-case (max score)": "Max of S (robust)",
    "QR (GBM, uncalibrated)": "Quantile regr., GBM (uncal.)", "CQR (Romano 2019)": "CQR [Romano 2019]",
    "CE-pair (ours, union bound)": "Pair union bound [Lindemann 2023], CE ref. plan",
    "CE-U (ours, uniform)": "CE-U (ours)", "CE-A (ours, terrain-adaptive)": "CE-A (ours)",
    "CE-R (ours, risk alpha)": "CE-R (ours)",
}
ORDER = ["Nominal (no margin)", "Fixed overlap 5 cm", "Fixed overlap 10 cm", "Fixed overlap 30 cm",
         "Slope rule (industry)", "Gaussian pointwise", "Empirical pointwise quantile", "Pointwise conformal",
         "QR (GBM, uncalibrated)", "Gaussian on score", "Cantelli bound on score", "Scenario (Campi-Garatti)",
         "CVaR (empirical)", "Wasserstein DRO-CVaR", "Worst-case (max score)", "CQR (Romano 2019)",
         "CE-pair (ours, union bound)", "CE-U (ours, uniform)", "CE-A (ours, terrain-adaptive)"]
# method groups for separators / headers (fig6, fig12)
GROUPS = [("Heuristic margins", ["Nominal (no margin)", "Fixed overlap 5 cm", "Fixed overlap 10 cm",
                                 "Fixed overlap 30 cm", "Slope rule (industry)"]),
          ("Pointwise statistics", ["Gaussian pointwise", "Empirical pointwise quantile", "Pointwise conformal"]),
          ("Learned, field features", ["QR (GBM, uncalibrated)", "CQR (Romano 2019)"]),
          ("Run-level score S + other quantile rules", ["Gaussian on score", "Cantelli bound on score",
                                                       "Scenario (Campi-Garatti)", "CVaR (empirical)",
                                                       "Wasserstein DRO-CVaR", "Worst-case (max score)",
                                                       "CE-pair (ours, union bound)"]),
          ("Ours", ["CE-U (ours, uniform)", "CE-A (ours, terrain-adaptive)"])]


def is_ours(m):
    return m in OURS


def load(name):
    p = os.path.join(RES, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def save(fig, name):
    """Save PNG + PDF; warn if the content is wider than the 7.2 in print width."""
    fig.canvas.draw()
    bb = fig.get_tightbbox(fig.canvas.get_renderer())
    if bb.width > 7.22:
        print(f"WARNING {name}: tight bbox {bb.width:.2f} in wide (> 7.2 in)")
    fig.savefig(os.path.join(FIG, name + ".png"))
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    plt.close(fig)


def panel(ax, letter, x=-0.02, y=1.02):
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=8, fontweight="bold",
            ha="right", va="bottom", color=INK)


def cp_ci(k, n, a=0.05):
    lo = beta.ppf(a / 2, k, n - k + 1) if k > 0 else 0.0
    hi = beta.ppf(1 - a / 2, k + 1, n - k) if k < n else 1.0
    return lo, hi


def t_ci(v):
    """Mean and 95% t half-width of the finite values of v (0 if fewer than 2)."""
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if not len(v):
        return np.nan, np.nan
    if len(v) < 2:
        return v.mean(), 0.0
    return v.mean(), student_t.ppf(0.975, len(v) - 1) * v.std(ddof=1) / np.sqrt(len(v))


# ------------------------------------------------------------------ Fig 1 schematic
def _sketch(ax):
    """(a) geometry of erosion: nominal spacing (gap) vs eroded spacing (no gap)."""
    xs = np.linspace(0, 10, 300)
    ek = 0.28 * np.sin(xs * 0.8)
    ek1 = -0.28 * np.sin(xs * 0.7 + 1.0) + 0.04
    w, qs = 2.0, 0.35
    for y0, sp, title in [(6.8, w, "(i) nominal spacing $w$: gap"),
                          (0.0, w - 2 * qs, r"(ii) eroded spacing $w-2q\sigma$: no gap")]:
        lo_k, hi_k = y0 + ek - w / 2, y0 + ek + w / 2
        lo_1, hi_1 = y0 + sp + ek1 - w / 2, y0 + sp + ek1 + w / 2
        ax.fill_between(xs, lo_k, hi_k, color=INK2, alpha=0.30, lw=0, zorder=1)
        ax.fill_between(xs, lo_1, hi_1, color=MUTED, alpha=0.35, lw=0, zorder=1)
        ax.fill_between(xs, hi_k, lo_1, where=lo_1 > hi_k, color=RED, interpolate=True, lw=0, zorder=3)
        for yc in (y0, y0 + sp):
            ax.plot([0, 10], [yc, yc], color=INK, lw=0.5, ls=(0, (3, 2)), zorder=4)
        ax.text(10.15, y0, "$y_k$", fontsize=6.4, va="center", color=INK)
        ax.text(10.15, y0 + sp, "$y_{k+1}$", fontsize=6.4, va="center", color=INK)
        ax.text(0.15, y0 - 0.6, "pass $k$", fontsize=6.2, color=INK, va="center")
        ax.text(0.15, y0 + sp + 0.62, "pass $k+1$", fontsize=6.2, color=INK, va="center")
        ax.text(0.0, y0 + sp + w / 2 + 0.5, title, fontsize=6.4, color=INK, va="bottom")
        xi = 60  # executed offset e_k(x) at one x
        ax.annotate("", xy=(xs[xi], y0 + ek[xi]), xytext=(xs[xi], y0), zorder=5,
                    arrowprops=dict(arrowstyle="-|>", mutation_scale=5, lw=0.6, color=INK, shrinkA=0, shrinkB=0))
        ax.text(xs[xi] + 0.15, y0 + ek[xi] / 2 - 0.05, "$e_k$", fontsize=6.0, color=INK, va="center")
        xa = 8.9  # implement width w on pass k+1
        j = int(np.argmin(np.abs(xs - xa)))
        ax.annotate("", xy=(xa, lo_1[j]), xytext=(xa, hi_1[j]), zorder=5,
                    arrowprops=dict(arrowstyle="<|-|>", mutation_scale=5, lw=0.6, color=INK, shrinkA=0, shrinkB=0))
        ax.text(xa + 0.15, y0 + sp + ek1[j] + 0.4, "$w$", fontsize=6.4, color=INK)
    y0 = 6.8  # (i): the missed strip
    gap = (y0 + w + ek1 - w / 2) - (y0 + ek + w / 2)
    i = int(np.argmax(gap))
    ax.annotate("missed strip", xy=(xs[i], y0 + ek[i] + w / 2 + gap[i] / 2), xytext=(6.6, y0 - 0.6),
                fontsize=6.2, color=RED, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", lw=0.5, color=RED, shrinkA=1, shrinkB=0))
    # (ii): planned half-width w/2 = eroded half-width h_k + erosion q sigma_k (about the planned line)
    xh = 4.3
    for yy in (w / 2 - qs, w / 2):
        ax.plot([xh - 0.35, xh + 0.35], [yy, yy], color=INK, lw=0.6, zorder=5)
    ar = dict(arrowstyle="<|-|>", mutation_scale=5, lw=0.6, color=INK, shrinkA=0, shrinkB=0)
    ax.annotate("", xy=(xh, w / 2 - qs), xytext=(xh, 0.0), arrowprops=ar, zorder=5)
    ax.annotate("", xy=(xh, w / 2), xytext=(xh, w / 2 - qs), arrowprops=ar, zorder=5)
    ax.text(xh - 0.15, (w / 2 - qs) / 2, "$h_k$", fontsize=6.2, color=INK, ha="right", va="center")
    ax.text(xh + 0.45, w / 2 - qs / 2, r"$q\sigma_k$", fontsize=6.2, color=INK, va="center")
    ov_mid = (w - 2 * qs + ek1 - w / 2 + ek + w / 2) / 2
    ax.annotate("overlap", xy=(xs[250], ov_mid[250]), xytext=(6.6, -0.6), fontsize=6.2, color=INK, ha="left",
                va="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=INK, shrinkA=1, shrinkB=0))
    ax.set_xlim(-0.1, 11.3)
    ax.set_ylim(-1.6, 11.7)
    ax.axis("off")


def fig_overview():
    fig = plt.figure(figsize=(7.2, 2.5))
    ia = fig.add_axes([0.0, 0.03, 0.27, 0.9])
    _sketch(ia)
    fig.text(0.003, 0.995, "(a)", fontsize=8, fontweight="bold", va="top")
    ax = fig.add_axes([0.285, 0.0, 0.71, 1.0])
    ax.set_xlim(-0.4, 52.0)
    ax.set_ylim(0, 25.5)
    ax.axis("off")
    fig.text(0.27, 0.995, "(b)", fontsize=8, fontweight="bold", va="top")
    BLU, GRN, ORG = "#eef4fc", "#eef8f3", "#fdf3ea"
    bw, gap = 11.4, 1.8
    xb = [i * (bw + gap) for i in range(4)]
    y1, h1 = 13.0, 9.6
    fs = 6.6

    def box(x, y, w_, h, fc):
        ax.add_patch(FancyBboxPatch((x, y), w_, h, boxstyle="round,pad=0.25,rounding_size=0.8", fc=fc,
                                    ec=INK2, lw=0.6))

    def txt(x, y, t, **kw):
        ax.text(x, y, t, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.3, **kw)

    for x in xb:
        box(x, y1, bw, h1, BLU)
    yc = y1 + h1 / 2
    txt(xb[0] + bw / 2, yc, "Calibration operations\n($n$ runs): executed pass\noffsets $e_k(x)$ vs. ground\n"
                           "truth (e.g. PPK or\nreference RTK)")
    txt(xb[1] + bw / 2, y1 + h1 - 1.1, "Pass-to-pass score")
    txt(xb[1] + bw / 2, y1 + 5.9, r"$S=\max_{k,x}\,\dfrac{e_{k+1}-e_k}{\sigma_k+\sigma_{k+1}}$")
    txt(xb[1] + bw / 2, y1 + 2.15, "(+ field-edge terms)\n" r"$\sigma_k = 1$ m (CE-U)," "\n"
        r"$\sigma_k = \hat\sigma_k$ (CE-A)")
    txt(xb[2] + bw / 2, yc, "Conformal quantile $q$\n(Thm. 1–3):\nfixed point in $\\lambda_{\\mathrm{ref}}$\n"
                           "(decision-dependent\nplan) or weighted\n(covariate shift)")
    txt(xb[3] + bw / 2, yc, "Eroded footprint\n$h_k = w/2 - q\\,\\sigma_k$\nused by any planner:\n"
                           "BCD + greedy (Prop. 5),\nFields2Cover,\n3-D terrain,\nfollow-previous-pass")
    xs_ = xb[2] + 0.6 * bw  # split of the bottom row
    box(xb[1], 0.6, xs_ - xb[1], 9.0, ORG)
    txt((xb[1] + xs_) / 2, 5.1, "ACI update [Gibbs & Candès 2021]\n"
                               r"$\varepsilon_{t+1} = \varepsilon_t + \gamma\,(\varepsilon - "
                               r"\mathbb{1}\{\mathrm{miss}_t\})$" "\n"
                               r"long-run miss rate $\to \varepsilon$ under drift" "\n"
                               "(sliding window of scores)")
    x5 = xs_ + 3.8
    box(x5, 0.6, xb[3] + bw - x5, 9.0, GRN)
    txt((x5 + xb[3] + bw) / 2, 5.1, "Closed-loop operation,\nany tracking controller\n(LQR-I, Stanley, pure\n"
                                   "pursuit, sideslip obs.,\noffset-free MPC)\n"
                                   r"Thm. 1: $P(\mathrm{no\ miss}) \geq 1-\varepsilon$" "\n"
                                   "(marginal, exchangeable)")
    hdr = dict(fontsize=6.6, color=INK2, fontstyle="italic", va="bottom")
    ax.text(xb[0], y1 + h1 + 0.5, "Offline calibration and planning", **hdr)
    ax.text(xb[1], 9.95, "Online adaptation (optional)", **hdr)
    ax.text(x5, 9.95, "Field operation", **hdr)
    arr = dict(arrowstyle="-|>", mutation_scale=7, lw=0.7, color=INK2)
    for i in range(3):
        ax.add_patch(FancyArrowPatch((xb[i] + bw + 0.3, yc), (xb[i + 1] - 0.3, yc), **arr))
    ax.add_patch(FancyArrowPatch((xb[3] + 0.75 * bw, y1 - 0.35), (xb[3] + 0.75 * bw, 9.95), **arr))
    ax.add_patch(FancyArrowPatch((x5 - 0.3, 3.0), (xs_ + 0.3, 3.0), **arr))
    ax.text((x5 + xs_) / 2, 3.4, "miss$_t$", fontsize=6.0, color=INK2, ha="center", va="bottom")
    xq = xb[2] + bw / 2
    ax.add_patch(FancyArrowPatch((xq, 9.95), (xq, y1 - 0.35), **arr))
    ax.text(xq + 0.4, (9.9 + y1) / 2, r"$\varepsilon_t$", fontsize=6.4, color=INK2, va="center")
    ax.text(xb[0] - 0.2, 9.4, "$e_k(x)$: lateral offset of pass $k$\nfrom its planned line $y_k$\n"
                              "at along-track position $x$\n"
                              r"$\sigma_k$: pass scale" "\n$w$: implement width\n" r"$q$: erosion per swath edge",
            fontsize=6.0, color=INK2, va="top", linespacing=1.3)
    save(fig, "fig1_overview")


# ------------------------------------------------------------------ Fig 7 validity
def fig_validity():
    """(a) reliability diagram (CE-U, CE-A, Gaussian fit of S), (b) planned overlap vs target,
    (c) calibration-set size. CIs: 95% t-interval over fields (draws averaged within a field)."""
    d, n = load("validity_paddy.csv"), load("ncal_paddy.csv")
    if d is None:
        return
    fig, axs = plt.subplots(1, 3, figsize=(7.1, 2.45), gridspec_kw=dict(width_ratios=[1.05, 1.05, 1.0]))
    series = [("U", "CE", BLUE, "o", True, "CE-U (ours)"), ("A", "CE", AQUA, "s", True, "CE-A (ours)"),
              ("U", "Gaussian on score", INK2, "^", True, "Gaussian fit of S")]
    offs = [-0.005, 0.0, 0.005]
    nf = d.field.nunique()
    for (var, m, c, mk, filled, lab), off in zip(series, offs):
        x = d[(d.variant == var) & (d.method == m)]
        for ax, col_, scale in [(axs[0], "p_nomiss", 1.0), (axs[1], "overlap", 100.0)]:
            pf = x.groupby(["eps", "field"])[col_].mean() * scale
            st = pf.groupby("eps").apply(lambda v: pd.Series(t_ci(v.values), index=["mu", "ci"]))
            st = st.unstack() if isinstance(st.index, pd.MultiIndex) else st
            tt = 1 - st.index.values
            ax.errorbar(tt + off, st["mu"].values, yerr=st["ci"].values, marker=mk, ms=3.2, color=c,
                        mfc=c if filled else "white", mec=c, mew=0.7, capsize=1.2, elinewidth=0.6, lw=0.9,
                        label=lab)
    tt = np.linspace(0.66, 1.0, 10)
    axs[0].plot(tt, tt, color=RED, lw=0.7, ls="--", label="target (lower bound)", zorder=0)
    axs[0].set_xlim(0.66, 1.0)
    axs[0].set_ylim(0.66, 1.0)
    axs[0].set_aspect("equal", adjustable="box")
    axs[0].set_ylabel("Realised P(no missed area)")
    axs[0].set_title("Reliability", loc="left", x=0.08)
    axs[0].legend(loc="lower right", fontsize=5.8, handlelength=1.5, borderaxespad=0.1, labelspacing=0.3)
    axs[1].set_ylabel("Planned overlap (% of field area)")
    axs[1].set_title("Cost of the certificate", loc="left", x=0.08)
    for ax in axs[:2]:
        ax.set_xticks([0.7, 0.8, 0.9, 0.95])
        ax.set_xlabel("Target 1 − ε")
    axs[1].set_xlim(0.66, 1.0)
    panel(axs[0], "a")
    panel(axs[1], "b")
    if n is not None:
        ks = sorted(n.n_cal.unique())
        g = [n[n.n_cal == k].p_nomiss.values for k in ks]
        bp = axs[2].boxplot(g, tick_labels=[str(k) for k in ks], widths=0.5, patch_artist=True, showmeans=True,
                            medianprops=dict(color=INK, lw=0.8), boxprops=dict(lw=0.5), whiskerprops=dict(lw=0.5),
                            capprops=dict(lw=0.5), flierprops=dict(ms=2, markeredgewidth=0.3),
                            meanprops=dict(marker="D", ms=2.6, mfc=AQUA, mec=INK, mew=0.3))
        for b in bp["boxes"]:
            b.set_facecolor("#d1efe3")
        axs[2].axhline(0.9, color=RED, lw=0.7, ls="--")
        axs[2].text(0.52, 0.897, "target", color=RED, fontsize=5.8, va="top", ha="left")
        axs[2].set_xlabel("Calibration operations n")
        axs[2].set_ylabel("Realised P(no missed area)")
        axs[2].set_title("Calibration-set size (CE-A, 1 − ε = 0.9)", loc="left", x=0.02)
        axs[2].grid(axis="x", visible=False)
        panel(axs[2], "c")
    fig.tight_layout(w_pad=1.2)
    print(f"  fig7: {nf} fields x {d.trial.nunique()} draws")
    save(fig, "fig7_validity")


if __name__ == "__main__":
    # the full figure set is produced by make_figures_v5.py; this module only provides Fig. 1 and Fig. 7
    for f in (fig_overview, fig_validity):
        f()
        print("ok", f.__name__)
