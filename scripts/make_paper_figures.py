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
RED_MISS = "#d7301f"
INK, INK2, MUTED, GRID, SHADE = "#1a1a1a", "#4d4d4d", "#8c8c8c", "#e3e3e3", "#f2f2f0"
REGIME = {"R1": ("R1  RTK, flat, 3 m", BLUE, "o"), "R2": ("R2  RTK, hilly-wet, 1.5 m", ORANGE, "s"),
          "R3": ("R3  DGPS, hilly, 6 m", GREEN, "^")}
PIVOT = {"theory": ("XCE-T (analytic model)", BLUE, "o"), "raw": ("Pooled conformal (raw)", ORANGE, "s"),
         "scale law": ("Scale law", GREEN, "^"), "spec x scale law": ("Spec. × scale law", PURPLE, "D")}

# Figures are drawn at the Elsevier double-column width (190 mm) and appear at 72% in the 138 mm preprint text
# block; FS scales all type so that it stays at 7-8 pt there.
FS = 1.32
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"],
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic",
    "mathtext.bf": "Liberation Sans:bold",
    "font.size": 7 * FS, "axes.labelsize": 7.5 * FS, "xtick.labelsize": 7 * FS, "ytick.labelsize": 7 * FS,
    "legend.fontsize": 7 * FS,
    "axes.linewidth": 0.8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelcolor": INK, "ytick.labelcolor": INK,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.minor.width": 0.4, "ytick.minor.width": 0.4,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.minor.size": 1.5, "ytick.minor.size": 1.5,
    "xtick.direction": "out", "ytick.direction": "out",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
    "lines.linewidth": 1.5, "lines.markersize": 5, "errorbar.capsize": 2,
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
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=9 * FS, fontweight="bold", va="bottom", ha="right")
    if text:
        ax.text(x + 0.02, y, text, transform=ax.transAxes, fontsize=7.5 * FS, va="bottom", ha="left", color=INK2)


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
def _run_for_schematic():
    """One simulated run with a few missed strips on a real DGPS field (R3, field index 6), for Fig. 1."""
    import core
    import exp_system as E
    key = "R3"
    rname, reg = X.regime(key)
    w = reg["w"]
    F = core.load_fields(reg["kind"], w=w, seed=0)[6]
    r = pickle.load(open(os.path.join(RES, "lowdata_v3", "A_R3_6.pkl"), "rb"))
    lam = r["oracle_lam"]
    ys = core.plan(F, w, lam, E.UNIT)
    rng = np.random.default_rng(11)
    cond = E.make_cond(rng, 200, reg)
    Xs, Ds = E.sim_core(F, lambda: "lqr_i", reg)(ys, cond, rng)
    miss = core.evaluate(F, ys, Xs, Ds, w)
    xg = np.arange(np.ceil(F.M.bounds[0]), np.floor(F.M.bounds[2]) + 1, 1.0)

    def gaps_of(k):
        off = np.stack([core.pass_offsets(Xs[i], Ds[i][k:k + 1], xg)[0] for i in range(len(ys))])
        out = []
        for j, x in enumerate(xg):
            c = core._chord_x(F.M, x)
            if c is None:
                continue
            lo, hi = c
            reach = lo
            for cc in np.sort(ys + np.where(np.isnan(off[:, j]), 1e3, off[:, j])):
                if cc - w / 2 > reach and reach < hi:
                    out.append((x, reach, min(cc - w / 2, hi)))
                reach = max(reach, cc + w / 2)
            if reach < hi:
                out.append((x, reach, hi))
        return out
    # a run with an interior gap of moderate length (the most typical failure)
    cands = [k for k in np.argsort(-miss) if miss[k] > 0][:40]
    best, best_g = None, None
    for k in cands:
        g = gaps_of(k)
        xs = sorted(set(x for x, _, _ in g))
        if 8 <= len(xs) <= 30:
            best, best_g = k, g
            break
    if best is None:
        best = cands[0]
        best_g = gaps_of(best)
    return F, w, lam, ys, Xs, [d[best] for d in Ds], best_g


def fig_schematic():
    """Fig. 1: (a) one simulated run on a real DGPS field, (b) zoom on a missed strip, (c) cross-section and run score."""
    from matplotlib.patches import Polygon as MPoly, Rectangle
    F, w, lam, ys, Xs, D, gaps = _run_for_schematic()
    fig = plt.figure(figsize=(DOUBLE, 132 * MM))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.55], width_ratios=[1.2, 1.0], hspace=0.38, wspace=0.22)
    ax = fig.add_subplot(gs[0, 0])
    PX, PY = F.P.exterior.xy
    clip = MPoly(np.c_[PX, PY], closed=True, transform=ax.transData)
    ax.add_patch(MPoly(np.c_[PX, PY], closed=True, fc=SHADE, ec="none", zorder=0))
    MX, MY = F.M.exterior.xy
    for k, (x, d) in enumerate(zip(Xs, D)):
        if len(x) < 2:
            continue
        o = np.argsort(x)
        xx, dd = x[o], d[o]
        fb = ax.fill_between(xx, ys[k] + dd - w / 2, ys[k] + dd + w / 2, color=BLUE, alpha=0.18, lw=0, zorder=2)
        fb.set_clip_path(clip)
        ln, = ax.plot(xx, ys[k] + dd, color=BLUE, lw=0.45, zorder=3)
        ln.set_clip_path(clip)
    ax.plot(MX, MY, color=INK2, lw=0.6, ls=(0, (3, 2)), zorder=4)
    ax.plot(PX, PY, color=INK, lw=0.9, zorder=4)
    for x, y0, y1 in gaps:
        ax.add_patch(Rectangle((x - 0.5, (y0 + y1) / 2 - 1.0), 1.0, 2.0, color=RED_MISS, lw=0, zorder=5))
    xs = np.array([g[0] for g in gaps]); yc = np.array([(g[1] + g[2]) / 2 for g in gaps])
    bx, by = float(np.median(xs)), float(np.median(yc))
    zx, zy = 18.0, 4.5
    ax.add_patch(Rectangle((bx - zx, by - zy), 2 * zx, 2 * zy, fc="none", ec=INK, lw=0.7, zorder=6))
    minx, miny, maxx, maxy = F.P.bounds
    ax.plot([minx + 5, minx + 55], [miny - 6, miny - 6], color=INK, lw=1.2)
    ax.text(minx + 30, miny - 8, "50 m", ha="center", va="top", fontsize=6.5 * FS)
    ax.set_xlim(minx - 4, maxx + 4), ax.set_ylim(miny - 16, maxy + 4)
    ax.set_aspect("equal"), ax.axis("off")
    panel(ax, "a", "Simulated run on a real field (DGPS, 6 m)", x=0.03, y=1.0)
    ax.legend(handles=[Patch(fc=SHADE, ec="none", label="Headland"), Line2D([], [], color=INK2, ls=(0, (3, 2)), lw=0.6, label="Main-area boundary"),
                       Patch(fc=BLUE, alpha=0.18, label="Worked swath"), Line2D([], [], color=BLUE, lw=0.6, label="Executed path"),
                       Patch(color=RED_MISS, label="Missed strip (width exaggerated)")],
              loc="upper left", bbox_to_anchor=(0.0, 0.02), ncol=2, fontsize=6.2 * FS, handlelength=1.4, columnspacing=1.0)
    # (b) zoom: lines only, coordinates relative to the gap
    ax = fig.add_subplot(gs[0, 1])
    for k, (x, d) in enumerate(zip(Xs, D)):
        if len(x) < 2 or abs(ys[k] - by) > zy + w / 2 + 1:
            continue
        o = np.argsort(x)
        xx, dd = x[o], d[o]
        m = (xx > bx - zx - 2) & (xx < bx + zx + 2)
        X0 = xx[m] - bx
        ax.plot(X0, np.full(m.sum(), ys[k] - by), color=INK2, lw=0.7, ls=(0, (4, 3)), zorder=2)
        ax.plot(X0, ys[k] + dd[m] - by, color=BLUE, lw=1.2, zorder=3)
        for sgn in (-1, 1):
            ax.plot(X0, ys[k] + dd[m] + sgn * w / 2 - by, color=BLUE, lw=0.6, ls=(0, (1, 1)), zorder=2)
        ax.fill_between(X0, ys[k] + dd[m] - w / 2 - by, ys[k] + dd[m] + w / 2 - by, color=BLUE, alpha=0.07, lw=0, zorder=1)
    for x, y0, y1 in gaps:
        if abs(x - bx) <= zx and abs((y0 + y1) / 2 - by) <= zy:
            ax.add_patch(Rectangle((x - bx - 0.5, y0 - by), 1.0, max(y1 - y0, 0.04), color=RED_MISS, lw=0, zorder=4))
    ax.set_xlim(-zx, zx), ax.set_ylim(-zy - 3.2, zy + 0.3)
    ax.set_xlabel("Along-pass position (m)"), ax.set_ylabel("Lateral position (m)")
    ax.grid(False)
    panel(ax, "b", "Detail of the framed area", x=0.0)
    ax.legend(handles=[Line2D([], [], color=INK2, lw=0.7, ls=(0, (4, 3)), label="Planned centreline"),
                       Line2D([], [], color=BLUE, lw=1.2, label="Executed centreline"),
                       Line2D([], [], color=BLUE, lw=0.6, ls=(0, (1, 1)), label="Footprint edge"),
                       Patch(color=RED_MISS, label="Missed")], loc="lower center", ncol=2, fontsize=6.0 * FS, frameon=True,
              framealpha=0.92, edgecolor="none")
    gw = max((y1 - y0) for x, y0, y1 in gaps if abs(x - bx) <= zx and abs((y0 + y1) / 2 - by) <= zy)
    ax.text(0.98, 0.97, f"widest gap {100 * gw:.0f} cm", transform=ax.transAxes, ha="right", va="top", fontsize=6.5 * FS,
            color=RED_MISS, bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.9))
    # (c) cross-section (schematic)
    ax = fig.add_subplot(gs[1, :])
    W, L = 3.0, 0.35
    sp = W - 2 * L
    cen = [W / 2 - L, W / 2 - L + sp + 0.05, W / 2 - L + 2 * sp + 1.25, W / 2 - L + 3 * sp + 1.0]
    lo, hi = 0.0, cen[-1] + W / 2 - L
    rows = [1.0, 1.75, 1.0, 1.75]
    for i, (c, yr) in enumerate(zip(cen, rows)):
        ax.add_patch(Rectangle((c - W / 2, yr - 0.22), W, 0.44, fc=BLUE, alpha=0.22, ec=BLUE, lw=0.7))
        ax.plot([c, c], [yr - 0.22, yr + 0.22], color=BLUE, lw=1.3)
        ax.text(c, yr + 0.3, f"pass {i + 1}", ha="center", va="bottom", fontsize=6.3 * FS, color=INK2)
    # coverage along the chord: covered (blue), gap (red)
    g0, g1 = cen[1] + W / 2, cen[2] - W / 2
    ax.plot([lo, g0], [0.15, 0.15], color=BLUE, lw=3.5, solid_capstyle="butt")
    ax.plot([g1, hi], [0.15, 0.15], color=BLUE, lw=3.5, solid_capstyle="butt")
    ax.plot([g0, g1], [0.15, 0.15], color=RED_MISS, lw=3.5, solid_capstyle="butt")
    ax.plot([lo, lo], [0.0, 2.3], color=INK, lw=0.8)
    ax.plot([hi, hi], [0.0, 2.3], color=INK, lw=0.8)
    ax.text(lo, -0.08, r"$\ell$", ha="center", va="top", fontsize=7 * FS)
    ax.text(hi, -0.08, r"$u$", ha="center", va="top", fontsize=7 * FS)
    ax.text((g0 + g1) / 2, -0.08, "gap", ha="center", va="top", fontsize=6.5 * FS, color=RED_MISS)
    ax.text(lo - 0.15, 0.15, "coverage", ha="right", va="center", fontsize=6.3 * FS, color=INK2)

    def dim(x0, x1, y, txt, va="bottom"):
        ax.annotate("", xy=(x0, y), xytext=(x1, y), arrowprops=dict(arrowstyle="<->", lw=0.6, color=INK, shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y + (0.05 if va == "bottom" else -0.05), txt, ha="center", va=va, fontsize=6.5 * FS)
    ov0, ov1 = cen[1] - W / 2, cen[0] + W / 2
    for xx in (ov0, ov1):
        ax.plot([xx, xx], [0.55, 1.45], color=MUTED, lw=0.4, ls=":")
    ax.annotate("", xy=(ov0, 0.62), xytext=(ov1, 0.62), arrowprops=dict(arrowstyle="<->", lw=0.6, color=INK, shrinkA=0, shrinkB=0))
    ax.text(ov1 + 0.12, 0.62, r"$2\lambda_\mathrm{ref}$ overlap", ha="left", va="center", fontsize=6.5 * FS)
    dim(cen[0], cen[1], 2.55, r"$w-2\lambda_\mathrm{ref}$")
    dim(cen[1], cen[2], 2.55, r"$c_3-c_2>w$")
    ax.text(hi + 0.5, 1.35, "Coverage score of the run:\n" + r"$r^\star$ = largest half-gap or edge distance" + "\n"
            + r"$S=\lambda_\mathrm{ref}+\max_x\,(r^\star(x)-w/2)$" + "\n" + r"no strip missed $\Leftrightarrow S\leq\lambda_\mathrm{ref}$",
            fontsize=6.6 * FS, va="center", ha="left", linespacing=1.55)
    ax.set_xlim(lo - 1.8, hi + 7.0), ax.set_ylim(-0.45, 2.95)
    ax.axis("off")
    panel(ax, "c", r"Cross-section at one along-pass position (schematic): footprints of width $w$", x=0.0, y=0.98)
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
    """Model pivot accuracy: (a) analytic model (R3 with field-edge terms), (b) Monte Carlo twin, against the empirical
    0.9-quantile of 200 independent runs per field."""
    sys.path.insert(0, HERE)
    import rev_resample as RR
    eq = RR.edge_q()
    fig, axes = plt.subplots(1, 2, figsize=(DOUBLE, 92 * MM))
    lim = np.array([0.08, 0.75])
    ticks = [0.1, 0.15, 0.2, 0.3, 0.4, 0.6]
    for p_i, ax in enumerate(axes):
        ax.fill_between(lim, lim / 1.1, lim * 1.1, color=SHADE, lw=0, zorder=0)
        ax.plot(lim, lim, color=INK2, lw=0.7, zorder=1)
        for key, (lab, col, mk) in REGIME.items():
            sims, preds = [], []
            for d in ("lowdata_v2", "lowdata_v3"):
                for f in sorted(glob.glob(os.path.join(RES, d, f"A_{key}_*.pkl"))):
                    r = pickle.load(open(f, "rb"))
                    sims.append(np.quantile(pickle.load(open(f.replace("A_", "hist_"), "rb")), 0.9))
                    if p_i == 0:
                        q = X.inv_cdf(r["tgrid"], r["Fhat"], 0.9)
                        preds.append(eq.get((key, r["fid"]), q) if key == "R3" else q)
                    else:
                        preds.append(pickle.load(open(os.path.join(RES, "revision", f"twin_{key}_{r['fi']}.pkl"), "rb"))["q"])
            sims, preds = np.array(sims), np.array(preds)
            e = np.log(preds / sims)
            ax.scatter(sims, preds, s=13, marker=mk, color=col, edgecolor="white", linewidth=0.4, zorder=3,
                       label=f"{key} ({'DGPS' if key == 'R3' else 'RTK'}): bias {100 * e.mean():+.1f}%, sd {100 * e.std(ddof=1):.1f}%")
        ax.set_xscale("log"), ax.set_yscale("log"), ax.set_xlim(lim), ax.set_ylim(lim)
        log_ticks(ax.xaxis, ticks), log_ticks(ax.yaxis, ticks)
        ax.grid(True, which="major", axis="both")
        ax.set_aspect("equal")
        ax.set_xlabel("Simulated 0.9-quantile of coverage score (m)")
        ax.set_ylabel("Predicted 0.9-quantile (m)")
        ax.legend(loc="upper left", handletextpad=0.2, borderaxespad=0.2, fontsize=6.0 * FS)
        panel(ax, "ab"[p_i], "Analytic extreme-value model" if p_i == 0 else "Monte Carlo twin (1000 runs)")
    fig.subplots_adjust(wspace=0.3)
    save(fig, "fig_theory_vs_sim")


# --------------------------------------------------------------------------------------------- Fig. 3
def fig_v8():
    """Regret (overlap above the per-field oracle) of CE+ v8 vs CPP and Lindemann, fresh fields, both classes."""
    d = pd.read_csv(os.path.join(RES, "v8", "system_v8.csv"))
    sysn = {"Marginal guarantee": [("CE+ (ours)", "BCD + LQR-I + CE+ (ours, v8)", BLUE),
                                   ("CPrP (Zhao et al.)", "Conformal predictive programming (Zhao et al.)", ORANGE),
                                   ("UBCP (Lindemann et al.)",
                                    "Conformal planning, pair-level union bound (Lindemann et al.)", GREEN)],
            "PAC guarantee (δ = 0.1)": [
                ("CE+ (ours)", "BCD + LQR-I + CE+ PAC (ours, v8)", BLUE),
                ("CPrP (Zhao et al.)", "Conformal predictive programming, PAC delta=0.1", ORANGE),
                ("UBCP (Lindemann et al.)",
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
                        fontsize=5.6 * FS, color=INK2)
                top = max(top, m + 1.96 * se)
        ax.axhline(0, color=INK2, lw=0.6)
        ax.set_xticks(range(3), [tick3(k) for k in ("R1", "R2", "R3")])
        ax.tick_params(axis="x", length=0)
        ax.set_ylim(0, top * 1.12)
        ax.set_ylabel("Overlap above per-field oracle (pp)")
        panel(ax, "ab"[p_i], cls)
    fig.subplots_adjust(wspace=0.28)
    fig.legend(handles=[Patch(color=c, label=l) for l, _, c in sysn["Marginal guarantee"]],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.27))
    fig.text(0.5, -0.31, "Numbers above bars: pooled P(no miss); error bars: 95% confidence intervals over 30 fields.",
             ha="center", fontsize=6.3 * FS, color=INK2)
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
    specs = ((axes[0], "marginal", "cov", 0.895, "Mean miss-free rate", "Marginal rule", (0.86, 0.95)),
             (axes[1], "PAC", "p", 0.88, "Share with miss-free rate ≥ 0.9", "PAC rule", (0.6, 1.0)))
    for p_i, (ax, cls, col_, ref, ylab, head, yl) in enumerate(specs):
        ax.axhspan(yl[0], ref, color="#fbe9e2", lw=0, zorder=0)
        ax.axhline(ref, color=ORANGE, lw=0.7, ls=(0, (3, 2)), zorder=1)
        ax.text(3.45, ref, f"registered criterion {ref:g}", fontsize=6 * FS, color=ORANGE, ha="right",
                va="bottom" if p_i == 1 else "top")
        if p_i == 0:
            ax.axhline(0.9, color=INK2, lw=0.5, ls=(0, (1, 1.5)), zorder=1)
            ax.text(-0.45, 0.9, r"$1-\varepsilon$", fontsize=6 * FS, color=INK2, va="bottom", ha="left")
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
               loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.2))
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
    v = parse_rv2(os.path.join(RES, "revision", "rv2_resampling_edges45.txt"))
    order = [("MC twin", "XCE-MC (Monte Carlo twin)", BLUE), ("theory+edges", "XCE-T (analytic, edge terms)", LIGHTBLUE),
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
                ax.text(val + xmax * 0.015, i, f"{val:.1f} (refuses {100 * r.refuse:.0f}%)", va="center", fontsize=6.2 * FS)
            else:
                ax.barh(i, r.ex_dep, color=col, height=0.62, zorder=2, hatch=hatch, edgecolor="white", linewidth=0.4)
                ax.text(r.ex_dep + xmax * 0.015, i, f"{r.ex_dep:.1f}", va="center", fontsize=6.5 * FS)
        ax.set_yticks(range(len(order)), [lab for _, lab, _ in order])
        if p_i:
            plt.setp(ax.get_yticklabels(), visible=False)
        ax.invert_yaxis() if p_i == 0 else None
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, xmax * 1.45)
        ax.grid(True, axis="x"), ax.grid(False, axis="y")
        ax.set_xlabel("Excess overlap (pp)")
        panel(ax, "abc"[p_i], f"{'Marginal' if cls == 'marginal' else 'PAC'} rule, 60 fields")
    ax = axes[2]
    vv = v[(v.n == 25) & (v.cls == "marginal")].set_index("piv")
    ks = ["raw", "spec x scale law", "per-config scale", "CQR", "theory+edges", "MC twin"]
    labs = ["Raw", "Spec.", "Per-cfg", "CQR", "XCE-T", "XCE-MC"]
    cols = [ORANGE, MUTED, PURPLE, PURPLE, LIGHTBLUE, BLUE]
    for i, (k, c) in enumerate(zip(ks, cols)):
        ax.bar(i, vv.loc[k, "c3"], color=c, width=0.62, zorder=2)
        ax.text(i, vv.loc[k, "c3"] + 0.004, f"{vv.loc[k, 'c3']:.2f}", ha="center", fontsize=6 * FS)
    ax.axhline(0.9, color=INK2, lw=0.6, ls=(0, (3, 2)))
    ax.set_ylim(0.7, 1.03)
    ax.set_xticks(range(len(ks)), labs, rotation=35, ha="right")
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("Mean miss-free rate, DGPS fields")
    panel(ax, "c", "DGPS fields, 25 calib.")
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
        ax.axhline(th, color=BLUE, lw=1.4, label="Analytic model (no run data)")
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
    fig.legend(h[::-1], l[::-1], loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.27))
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
    ax.text(2.48, 1.0, "per-field optimum", fontsize=6 * FS, color=INK2, ha="right", va="bottom")
    ax.set_xlim(-0.5, 2.5), ax.set_ylim(0.8, 2.7)
    ax.set_xticks(range(3), [tick3(k) for k in ("R1", "R2", "R3")])
    ax.tick_params(axis="x", length=0)
    ax.set_ylabel("PAC margin / per-field optimum")
    ax.legend(handles=[(Patch(fc="#dbe8f8", ec="none"), Line2D([], [], color=BLUE, lw=1.4)),
                       Line2D([], [], color=ORANGE, marker="D", ls="none", ms=4, mec="white", mew=0.4)],
              labels=["Model prediction, mean ± SD", "Observed on fresh fields"], loc="upper left")
    save(fig, "fig_information_limit")


# --------------------------------------------------------------------------------------------- cost figure
def fig_cost():
    """Expected cost (overlap % + r x missed %) of practice and certified margins against the cost ratio r."""
    import glob as _g
    sys.path.insert(0, HERE)
    import rev_cost as RC
    rs = np.geomspace(1, 1000, 60)
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE, 56 * MM))
    for p_i, (ax, key) in enumerate(zip(axes, ("R1", "R2", "R3"))):
        recs = [pickle.load(open(f, "rb")) for f in sorted(_g.glob(os.path.join(RES, "revision", f"mm_nominal_{key}_*.pkl")))]
        recs = [r for r in recs if len(r["cur"]["lam"]) and r["cur"]["P"].max() >= 0.9]
        pols = {"Vendor rule": [], "Farmer-tuned": [], "Calibrated, ε = 0.1": []}
        opt = np.zeros(len(rs))
        for r in recs:
            c = r["cur"]
            for nm, lam in (("Vendor rule", RC.VENDOR[key]), ("Farmer-tuned", RC.FARMER[key]), ("Calibrated, ε = 0.1", RC.oracle(c))):
                pols[nm].append(RC.at(c, key, lam))
            grid = np.linspace(c["lam"][0], c["lam"][-1], 400)
            ov, em = 100 * np.interp(grid, c["lam"], c["ov"]), 100 * np.interp(grid, c["lam"], c["emiss"])
            opt += np.array([np.min(ov + rr * em) for rr in rs])
        opt /= len(recs)
        for (nm, v), col, ls in zip(pols.items(), (ORANGE, GREEN, BLUE), ("-", "-", "-")):
            v = np.array(v)
            ax.plot(rs, v[:, 1].mean() + rs * v[:, 2].mean(), color=col, lw=1.3, ls=ls, label=nm)
        ax.plot(rs, opt, color=INK, lw=1.0, ls=(0, (3, 2)), label="Cost-optimal margin (reference)")
        vv, cc = np.array(pols["Vendor rule"]), np.array(pols["Calibrated, ε = 0.1"])
        be = (cc[:, 1].mean() - vv[:, 1].mean()) / (vv[:, 2].mean() - cc[:, 2].mean())
        ax.axvline(be, color=MUTED, lw=0.5)
        ax.text(be / 1.12, 0.97, f"break-even\nr = {be:.0f}", transform=ax.get_xaxis_transform(), fontsize=6 * FS, va="top",
                ha="right", color=INK2, bbox=dict(fc="white", ec="none", pad=0.5))
        ax.set_xscale("log")
        ax.set_xlim(1, 1000)
        log_ticks(ax.xaxis, [1, 10, 100, 1000])
        ys = [l.get_ydata() for l in ax.get_lines() if len(l.get_ydata()) == len(rs)]
        ax.set_yscale("log")
        ax.set_ylim(min(y.min() for y in ys) * 0.8, max(y.max() for y in ys) * 1.25)
        log_ticks(ax.yaxis, [t for t in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000)
                             if min(y.min() for y in ys) * 0.8 <= t <= max(y.max() for y in ys) * 1.25])
        ax.set_xlabel("Cost ratio $r$")
        if p_i == 0:
            ax.set_ylabel("Expected cost (% of main area)")
        ax.grid(True, axis="both", which="major")
        panel(ax, "abc"[p_i], REGIME[key][0])
    fig.subplots_adjust(wspace=0.3)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.2))
    save(fig, "fig_cost")


# --------------------------------------------------------------------------------------------- graphical abstract
def fig_graphical_abstract():
    """Graphical abstract (CEA: >= 1328 x 531 px, read left to right): method flow and two headline results."""
    GFS = 1.1  # stand-alone image, read at full size
    fig = plt.figure(figsize=(DOUBLE, DOUBLE * 531 / 1328))
    ax = fig.add_axes([0.0, 0.0, 0.54, 1.0])
    ax.set_xlim(0, 10), ax.set_ylim(0, 4.2), ax.axis("off")
    ax.text(0.25, 3.95, "Calibrated pass overlap (simulation study)", fontsize=9 * GFS,
            fontweight="bold", va="center")
    steps = [("Logged runs", "target-field runs, or one run\nper field of other fields", SHADE),
             ("Coverage score", r"$S$ = widest gap or edge miss;" + "\nzero miss " + r"$\Leftrightarrow S\leq\lambda$", SHADE),
             ("Model scale", "extreme-value model or Monte Carlo\ntwin: each field's margin, no runs", "#dbe8f8"),
             ("Conformal calibration", "calibrated margin " + r"$\lambda$ (overlap $2\lambda$):" + "\nP(no miss) ≥ 1 − ε", "#dbe8f8")]
    hh, y0s = 0.7, [3.1, 2.25, 1.4, 0.55]
    for n, ((title, body, col), y0) in enumerate(zip(steps, y0s)):
        ax.add_patch(FancyBboxPatch((0.25, y0 - hh / 2), 9.5, hh, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fc=col, ec="none"))
        ax.text(0.72, y0, str(n + 1), color="white", fontsize=7.5 * GFS, fontweight="bold", ha="center", va="center", zorder=4,
                bbox=dict(boxstyle="circle,pad=0.35", fc=BLUE if n >= 2 else INK2, ec="none"))
        ax.text(1.2, y0, title, ha="left", va="center", fontsize=7.5 * GFS, fontweight="bold")
        ax.text(5.0, y0, body, ha="left", va="center", fontsize=6.5 * GFS, color=INK2, linespacing=1.25)
    d = pd.read_csv(os.path.join(RES, "v8", "system_v8.csv"))
    rows = [("CE+\n(ours)", "BCD + LQR-I + CE+ PAC (ours, v8)", BLUE),
            ("CPrP", "Conformal predictive programming, PAC delta=0.1", ORANGE),
            ("UBCP", "Conformal planning, pair-level union bound, PAC delta=0.1", GREEN)]
    v = parse_rv2(os.path.join(RES, "revision", "rv2_resampling_edges45.txt"))
    v = v[(v.n == 60) & (v.cls == "marginal")].set_index("piv")
    rows2 = [("Model\nscale", v.loc["theory+edges", "ex_dep"], BLUE), ("CQR", v.loc["CQR", "ex_dep"], PURPLE),
             ("Per-\nconfig.", v.loc["Mondrian", "ex_dep"], GREEN), ("Pooled", v.loc["raw", "ex_dep"], ORANGE)]
    for k, (x0, data, head) in enumerate((
            (0.61, [(l, d[d.system == nm].regret_pp.mean(), c) for l, nm, c in rows],
             "With field data\n(90 fields, PAC rule)"),
            (0.82, rows2, "Without field data\n(mixed fleet, marginal)"))):
        a = fig.add_axes([x0, 0.2, 0.165, 0.56])
        vals = [r[1] for r in data]
        a.bar(range(len(vals)), vals, color=[r[2] for r in data], width=0.62)
        for i, v_ in enumerate(vals):
            a.text(i, v_ + max(vals) * 0.03, f"{v_:.1f}", ha="center", fontsize=6.5 * GFS)
        a.set_xticks(range(len(vals)), [r[0] for r in data], fontsize=6.0 * GFS)
        a.tick_params(axis="x", length=0)
        a.set_ylim(0, max(vals) * 1.18)
        a.text(0.5, 1.08, head, transform=a.transAxes, ha="center", va="bottom", fontsize=7 * GFS, fontweight="bold",
               linespacing=1.2)
        if k == 0:
            a.set_ylabel("Overlap above optimum (pp)", fontsize=6.5 * GFS)
    save(fig, "graphical_abstract")


# --------------------------------------------------------------------------------------------- Fig. 1 (workflow)
def fig_workflow():
    """Fig. 1: workflow of the proposed calibration method."""
    from matplotlib.patches import FancyArrowPatch
    fig = plt.figure(figsize=(DOUBLE, 70 * MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100), ax.set_ylim(0, 38.6), ax.axis("off")
    TINT, TINT2 = "#e8f1fb", "#f2f2f0"

    def box(x, y, w, h, title, body, fc=TINT, ec=BLUE, num=None):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", fc=fc, ec=ec, lw=0.9))
        tx = x + 1.6
        if num is not None:
            ax.text(x + 2.6, y + h - 3.0, str(num), ha="center", va="center", color="white", fontsize=7.5 * FS,
                    fontweight="bold", bbox=dict(boxstyle="circle,pad=0.25", fc=BLUE, ec="none"))
            tx = x + 5.0
        ax.text(tx, y + h - 3.0, title, ha="left", va="center", fontsize=7.6 * FS, fontweight="bold", color=INK)
        ax.text(x + 1.6, y + h - 6.4, body, ha="left", va="top", fontsize=6.4 * FS, color=INK2, linespacing=1.35)

    def arrow(x0, y0, x1, y1, color=INK2, style="-|>", ls="-"):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=9, lw=1.0, color=color,
                                     linestyle=ls, shrinkA=0, shrinkB=0))

    top, h = 22.3, 15.8
    xs, w = [0.5, 25.5, 50.5, 75.5], 23.5
    box(xs[0], top, w, h, "Reference plan", "user's planner with a\ngenerous margin " + r"$\lambda_\mathrm{ref}$" +
        "\n(overlap " + r"$2\lambda_\mathrm{ref}$" + ")", num=1)
    box(xs[1], top, w, h, "Coverage score", "for each logged run:\nwidest gap or edge\nrecession of the executed\npasses " +
        r"$\Rightarrow$" + " one number " + r"$S$", num=2)
    box(xs[2], top, w, h, "Calibrated margin", "order statistic of the\nscores: a new run exceeds\n" + r"$\hat\lambda$" +
        " with probability " + r"$\leq\varepsilon$", num=3)
    box(xs[3], top, w, h, "Plan and deploy", "planner generates " + r"$\pi(\hat\lambda)$" + ";\ntransfer check: if " +
        r"$\hat\lambda>\lambda_\mathrm{ref}$" + ",\nrecalibrate on a larger\nreference plan", num=4)
    for i in range(3):
        arrow(xs[i] + w, top + h / 2, xs[i + 1], top + h / 2)
    # data sources feeding step 2/3
    bh = 14.5
    box(0.5, 1.0, 44.0, bh, "With field history (CE, CE-q, CE+)",
        "logged runs of the target field itself\n" + r"$n\geq9$" + " (marginal) or " + r"$n\geq22$" +
        " (PAC rule)\nmargin = " + r"$k_\star$" + "-th smallest score", fc=TINT2, ec=MUTED)
    box(48.0, 1.0, 51.5, bh, "Without field history (XCE)",
        "one logged run on each of " + r"$n$" + " other fields, divided by a\nmodel scale " + r"$\hat q_f$" +
        " (analytic model or Monte Carlo twin)\nmargin " + r"$\lambda_g=\hat q_g\,v^\star$",
        fc=TINT2, ec=MUTED)
    ax.text(36.5, top - 3.6, "logged runs", ha="left", va="center", fontsize=6.4 * FS, color=INK2,
            style="italic")
    arrow(30.0, 1.0 + bh, 33.0, top, color=MUTED)
    arrow(73.75, 1.0 + bh, 42.0, top, color=MUTED)
    save(fig, "fig_workflow")


if __name__ == "__main__":
    fig_workflow()
    fig_schematic()
    fig_theory()
    fig_v8()
    fig_validity()
    fig_mixed()
    fig_learning()
    fig_limit()
    fig_graphical_abstract()
    fig_cost()
