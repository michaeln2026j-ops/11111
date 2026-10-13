"""v5 publication figures (real NOAA CORS GNSS error bank; system-level comparison).

Only figure types that are standard in agricultural-robotics / coverage-planning / control journals:
schematic, study-area scatter map, histograms, error CCDF, coverage (skip/overlap) maps of a real field,
horizontal / vertical grouped bar charts with 95% CI error bars, dot plots, box plots, reliability
diagrams and time series. Linear axes only, apart from the log-log GNSS error CCDF.

Statistics used in every bar / dot figure (stated in the captions):
  P(no missed area)   mean over fields (or over random splits) with a 95% t-interval over fields;
                      runs inside a field share one calibration draw, so runs are not pooled as iid
  overlap, missed     mean over fields with a 95% t-interval over fields
  fields meeting      share of fields whose P(no missed area) is not significantly below 1 - eps
  target              (one-sided exact binomial test, alpha = 0.05), as in make_tables.py

  fig1_overview    method schematic + erosion geometry          (make_figures2.fig_overview)
  fig2_data        study fields, real GNSS error tails (CCDF), in-field slopes, real robot deviations
  fig3_coverage    coverage maps of one real field, same sampled operating condition, four margin rules
  fig4_system      horizontal bars: published systems x 3 regimes (P, fields meeting target, overlap, missed)
  fig5_stacks      horizontal bars: six planner/controller stacks with vendor-spec overlap vs with CE
  fig6_main        horizontal bars: margin rules on BCD + LQR-I, paddy vs wheat (E2)
  fig7_validity    reliability diagram, overlap vs target, calibration-size box plot (make_figures2)
  fig8_cross       box plots over splits (P) + bars (overlap): unseen fields (E3b), regional shift (E3a)
  fig9_sensitivity dot plot (P) + bars (overlap): controller, roll compensation, width, receiver grade (E4)
  fig10_drift      time series: static vs ACI-updated CE under a simulated soil-moisture ramp (E6)
  fig11_ablation   grouped bars: ablation in four settings (E9)
  fig12_real_robot box plots, dot plots and a step plot: real orchard robot (CitrusFarm, E8)
Usage: python3 experiments/make_figures_v5.py [fig_name ...]
"""
import copy
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.transforms import blended_transform_factory, offset_copy
from scipy.stats import binomtest

import make_figures2 as M
from make_figures2 import (AQUA, BLUE, GRID, INK, INK2, LIGHT, MUTED, OURS_BAND, RED, VIOLET, YELLOW,
                           GREEN, cp_ci, load, panel, plt, save, t_ci)

HERE = os.path.dirname(os.path.abspath(__file__))
SYS = "system" + os.environ.get("CE_TAG", "_v6")  # system-level result file
N_TEST_SYS = 200  # exp_system --n-test default; checked against the data in _check_n_test
TARGET = 0.9
REG_GREY = ["#cdcbc4", "#8f8d86", "#4a4945"]  # regimes R1-R3, baselines
REG_BLUE = ["#a9c8ee", BLUE, "#174a8a"]  # regimes R1-R3, ours
EDGE_OURS = dict(edgecolor=INK, lw=0.6)

# Fig. 4: one row per published method family member (strongest run-level variant of each family;
# weaker variants (pointwise belief / GP, tube W_max) are in Table E2b)
FAM4 = [
    ("Industry practice", [
        ("BCD + LQR-I + spec overlap (2x vendor p2p)", "Vendor-spec overlap (any stack, Fig. 5)"),
        ("BCD + LQR-I + farmer-tuned global overlap", "Farmer-tuned global overlap"),
        ("BCD + vendor terrain comp. + farmer-tuned", "Terrain-comp. autosteer, farmer-tuned")]),
    ("Robust / model-based", [
        ("Tube-MPC radius margin (W99)", "Tube MPC, W99 [Mayne 2005]"),
        ("Gaussian belief, Rice extreme-value", "Gaussian belief + Rice [Schirmer 2019]"),
        ("Model-based MC chance constraint", "MC chance constr. [Blackmore 2010]")]),
    ("Learning-based", [
        ("GP cautious margin, Bonferroni (Hewing et al.)", "GP margin, Bonferroni [Hewing 2020]")]),
    ("Conformal", [
        ("Conformal planning, union bound (Lindemann et al.)", "CP planning, point-level [Lindemann 2023]"),
        ("Conformal planning, pair-level union bound (Lindemann et al.)", "CP planning, pair-level [Lindemann 2023]"),
        ("Conformal predictive programming (Zhao et al.)", "CPP [Zhao 2024]")]),
    ("Chance-constraint rules on S", [
        ("Scenario approach (PAC, beta=0.01)", "Scenario on S [Campi 2011]"),
        ("Gaussian chance constraint", "Gaussian fit of S"),
        ("Wasserstein DRO-CVaR", "W-DRO-CVaR on S [Mohajerin Esfahani 2018]")]),
    ("Ours", [("BCD + LQR-I + CE (ours)", "CE-U on BCD / LQR-I (ours)")]),
]
# Fig. 5: (label 'planner / controller', spec-overlap system, CE system)
STACKS = [
    ("BCD / LQR-I", "BCD + LQR-I + spec overlap (2x vendor p2p)", "BCD + LQR-I + CE (ours)"),
    ("Fields2Cover [Mier 2023] / LQR-I", "Fields2Cover (opt. heading) + spec overlap", "Fields2Cover + LQR-I + CE (ours)"),
    ("3-D terrain [Hameed 2016] / LQR-I", "Hameed 3D terrain spacing + spec overlap", "Hameed 3D + LQR-I + CE (ours)"),
    ("Follow-prev.-pass [patent] / LQR-I", "Follow-previous-pass guidance + spec overlap",
     "Follow-previous-pass + LQR-I + CE (ours)"),
    ("BCD / sideslip obs. [Lenain 2006]", "BCD + Lenain sideslip-observer ctrl + spec overlap",
     "BCD + Lenain ctrl + CE (ours)"),
    ("BCD / offset-free MPC [Pannocchia 2003]", "BCD + offset-free MPC + spec overlap",
     "BCD + offset-free MPC + CE (ours)"),
]
FARMER = "BCD + LQR-I + farmer-tuned global overlap"


# ------------------------------------------------------------------------------------ statistics
def field_p(ps):
    """Mean P(no miss) over fields with a 95% t-interval over fields (clipped to [0, 1])."""
    mu, ci = t_ci(ps)
    if not np.isfinite(mu):
        return np.nan, np.nan, np.nan
    return mu, max(mu - ci, 0.0), min(mu + ci, 1.0)


def meet_frac(ps, n_test, target=TARGET):
    """Share of fields whose P(no miss) is not significantly below the target (one-sided binomial)."""
    ps = np.asarray(ps, float)
    ps = ps[np.isfinite(ps)]
    if not len(ps):
        return np.nan
    return float(np.mean([binomtest(int(round(p * n_test)), n_test, target, alternative="less").pvalue >= 0.05
                          for p in ps]))


def _check_n_test(p, n):
    p = np.asarray(p, float)
    p = p[np.isfinite(p)]
    assert np.allclose(p * n, np.round(p * n), atol=1e-6), f"P values are not multiples of 1/{n}"


def sys_row(x, s, n_test=N_TEST_SYS):
    """Statistics of one system over the fields of one regime."""
    g = x[x.system == s]
    fin = g[np.isfinite(g.p_nomiss)]
    out = dict(n=g.field.nunique(), nf=fin.field.nunique())
    out["p"], out["lo"], out["hi"] = field_p(fin.p_nomiss)
    out["meet"] = meet_frac(fin.p_nomiss, n_test) * 100
    out["ov"], out["ovci"] = t_ci(fin.overlap * 100)
    out["em"], out["emci"] = t_ci(fin.e_miss * 1e4)
    out["oracle"] = float(g.oracle_overlap.mean() * 100) if "oracle_overlap" in g else np.nan
    out["vals"] = fin.p_nomiss.values
    if out["nf"] < 0.5 * max(out["n"], 1):  # mostly infeasible: do not average over the few feasible fields
        for k in ("p", "lo", "hi", "meet", "ov", "ovci", "em", "emci"):
            out[k] = np.nan
        out["vals"] = np.array([])
    return out


# ------------------------------------------------------------------------------------ bar helpers
def _fmt_val(v):
    if not np.isfinite(v):
        return ""
    a = abs(v)
    return f"{v:.0f}" if a >= 10 else (f"{v:.1f}" if a >= 1 else f"{v:.2f}")


def _layout(rows, row_h=1.0, hdr_h=0.7):
    """y positions (top -> bottom) of data rows and group-header rows."""
    y, ys, hdr, labs = 0.0, [], [], []
    for r in rows:
        if isinstance(r, tuple) and r[0] == "hdr":
            y -= hdr_h
            hdr.append((y, r[1]))
        else:
            y -= row_h
            ys.append(y)
            labs.append(r)
    return np.array(ys), hdr, labs


def _hdr_tr(ax):
    """x in axes, y in data units, shifted 2 pt right so that the header's white box does not cut the y spine."""
    return offset_copy(blended_transform_factory(ax.transAxes, ax.transData), fig=ax.figure, x=2.0, units="points")


def _decorate(ax, ys, hdr, labs, ours, xlim, xlabel, target, fs, headers_left, row_h, hdr_h, bar_frac=0.8):
    top = 0.05
    for yh, t in hdr:
        above = ys[ys > yh]
        if len(above):  # separator just below the lowest bar / box of the previous row
            ax.axhline(above.min() - row_h * bar_frac / 2 - 0.1, color=GRID, lw=0.7, zorder=1)
        else:  # header of the first group: no separator, the axis starts just above it
            top = yh + 0.42
        if headers_left:  # header text sits next to the first row of its own group
            ax.text(0.0, yh - 0.05, t, transform=_hdr_tr(ax), ha="left", va="center", fontsize=fs - 0.2, color=INK2,
                    fontstyle="italic", zorder=5, bbox=dict(fc="white", ec="none", pad=0.2))
    for i in ours:
        ax.axhspan(ys[i] - row_h / 2, ys[i] + row_h / 2, color=OURS_BAND, zorder=0, lw=0)
    if target is not None:
        ax.axvline(target, color=RED, lw=0.7, ls="--", zorder=3)
    ax.set_yticks(ys)
    ax.set_yticklabels(labs, fontsize=fs)
    for i, t in enumerate(ax.get_yticklabels()):
        if i in ours:
            t.set_fontweight("bold")
            t.set_color(INK)
    ax.set_ylim(min(ys) - row_h / 2 - 0.1, top)
    ax.set_xlim(*xlim)
    ax.set_xlabel(xlabel)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0, pad=2)


def hbars(ax, rows, series, xlabel="", target=None, xmax=None, xlim=None, fs=6.2, values=False,
          small=0.04, cap_fmt="{:.0f}%", headers_left=True, ours=(), row_h=1.0, hdr_h=0.95, bar_frac=0.8):
    """Horizontal grouped bars, rows top -> bottom.

    rows:   list of row labels; ('hdr', text) is a group header row (no bars, light separator).
    series: list of dicts with keys name, color (str or list per data row), mu, lo, hi (abs. bounds or
            None), and optional edge (bool or list), present (bool list: slot drawn), note (str list).
    Bars longer than xmax are cut at xmax, marked with a white break and labelled with cap_fmt.
    values=True labels every bar, otherwise only bars shorter than small * axis span (a zero is drawn
    as a short tick at 0 and labelled, so that it is visibly a zero, not missing data). The labels of
    one row are merged into one text, in series order ("a / b / c"). Returns the data-row positions."""
    ys, hdr, labs = _layout(rows, row_h, hdr_h)
    nrow = len(ys)
    present = np.array([np.asarray(s.get("present", [True] * nrow), bool) for s in series])
    allv = [v for s in series for v in np.asarray(s["mu"], float) if np.isfinite(v)]
    top = xmax if xmax is not None else max(allv + [1e-9])
    xlim = xlim if xlim is not None else (0, top * 1.2)
    span = xlim[1] - xlim[0]
    bh = row_h * bar_frac / max(present.sum(0).max(), 1)
    for i in range(nrow):
        idx = np.nonzero(present[:, i])[0]
        k = len(idx)
        lab_txt, lab_end, notes, caps, row_end = [], 0.0, [], [], 0.0
        for jj, j in enumerate(idx):
            s = series[j]
            pos = ys[i] + ((k - 1) / 2 - jj) * bh
            mu = float(np.asarray(s["mu"], float)[i])
            c = s["color"][i] if isinstance(s["color"], (list, tuple)) else s["color"]
            edge = s.get("edge", False)
            edge = edge[i] if isinstance(edge, (list, tuple, np.ndarray)) else edge
            note = (s.get("note") or [None] * nrow)[i]
            ekw = EDGE_OURS if edge else dict(edgecolor="white", lw=0.3)
            if not np.isfinite(mu):
                ax.text(span * 0.01, pos, note or "n/a", ha="left", va="center", fontsize=5.6, color=INK)
                continue
            shown = mu if xmax is None else min(mu, xmax)
            ax.barh(pos, shown, height=bh * 0.88, color=c, zorder=2, **ekw)
            end = shown
            if s.get("lo") is not None and (xmax is None or mu <= xmax):
                lo, hi = float(np.asarray(s["lo"], float)[i]), float(np.asarray(s["hi"], float)[i])
                if np.isfinite(lo) and np.isfinite(hi) and hi > lo:
                    ax.errorbar(mu, pos, xerr=[[mu - lo], [hi - mu]], fmt="none", ecolor=INK, elinewidth=0.5,
                                capsize=1.0, capthick=0.5, zorder=3)
                    end = max(end, hi)
            row_end = max(row_end, end)
            if xmax is not None and mu > xmax:
                for dx in (0.955, 0.975):
                    ax.plot([xmax * dx, xmax * (dx + 0.012)], [pos - bh * 0.5, pos + bh * 0.5], color="white",
                            lw=1.0, zorder=4, solid_capstyle="butt")
                caps.append((pos, cap_fmt.format(mu)))
                continue
            if mu < 0.004 * span:
                ax.plot([0, 0], [pos - bh * 0.42, pos + bh * 0.42], color=INK2, lw=0.9, zorder=4,
                        solid_capstyle="butt")
            lab_txt.append((_fmt_val(mu), values or mu < small * span))
            lab_end = max(lab_end, end)
            if note:
                notes.append(note)
        if any(f for _, f in lab_txt):  # label every bar of the row, in series order
            t = " / ".join(v for v, _ in lab_txt)
            ax.text(lab_end + span * 0.015, ys[i], t, ha="left", va="center", fontsize=5.6, color=INK2, zorder=4)
        if caps:  # label at the cut bar(s) themselves, not at the row centre
            ax.text(max(xmax, row_end) + span * 0.012, float(np.mean([p_ for p_, _ in caps])),
                    " / ".join(t_ for _, t_ in caps), ha="left", va="center", fontsize=5.6, color=INK, zorder=4)
        if notes:
            ax.text(span * 0.015 + xlim[0], ys[i] - row_h * 0.5, "; ".join(notes), ha="left", va="bottom",
                    fontsize=5.4, color=INK2, zorder=4)
    _decorate(ax, ys, hdr, labs, ours, xlim, xlabel, target, fs, headers_left, row_h, hdr_h, bar_frac)
    return ys


def hboxes(ax, rows, series, xlabel="", target=None, xlim=(0, 1.0), fs=6.2, headers_left=True, ours=(),
           row_h=1.0, hdr_h=0.95, bar_frac=0.8, whis=(5, 95)):
    """Horizontal box plots of per-field values, laid out like hbars (one box per series and row).
    series: list of dicts with name, color (str or list), vals (list of arrays), optional edge, note,
    present. Box = quartiles, whiskers = 5th-95th percentile, dots = fields outside, diamond = mean.
    Boxes whose median lies left of xlim[0] are not drawn; the row then states their means (off scale)."""
    ys, hdr, labs = _layout(rows, row_h, hdr_h)
    nrow = len(ys)
    present = np.array([np.asarray(s.get("present", [True] * nrow), bool) for s in series])
    bh = row_h * bar_frac / max(present.sum(0).max(), 1)
    span = xlim[1] - xlim[0]
    for i in range(nrow):
        idx = np.nonzero(present[:, i])[0]
        k = len(idx)
        notes, off = [], []
        for jj, j in enumerate(idx):
            s = series[j]
            pos = ys[i] + ((k - 1) / 2 - jj) * bh
            v = np.asarray(s["vals"][i], float)
            v = v[np.isfinite(v)]
            note = (s.get("note") or [None] * nrow)[i]
            if note:
                notes.append(note)
            if not len(v):
                continue
            if np.median(v) < xlim[0]:
                off.append((pos, _fmt_val(v.mean()) if v.mean() >= 0.005 else "0.00"))
                continue
            c = s["color"][i] if isinstance(s["color"], (list, tuple)) else s["color"]
            edge = s.get("edge", False)
            edge = edge[i] if isinstance(edge, (list, tuple, np.ndarray)) else edge
            ec = INK if edge else INK2
            ax.boxplot([v], positions=[pos], widths=bh * 0.86, orientation="horizontal", whis=whis,
                       patch_artist=True, manage_ticks=False, showmeans=True, zorder=3,
                       boxprops=dict(facecolor=c, edgecolor=ec, lw=0.5), medianprops=dict(color=INK, lw=0.8),
                       whiskerprops=dict(color=ec, lw=0.5), capprops=dict(color=ec, lw=0.5),
                       flierprops=dict(marker="o", ms=1.4, mfc=ec, mec="none", alpha=0.7),
                       meanprops=dict(marker="D", ms=2.2, mfc="white", mec=INK, mew=0.4))
        txt = []
        if off and len(off) == k and k > 1:  # whole row off scale: one merged statement
            txt.append(f"off scale (< {xlim[0]:g}): mean " + " / ".join(t for _, t in off))
        else:  # single slots off scale: arrow at the axis + mean value
            for pos, t in off:
                ax.plot(xlim[0] + span * 0.012, pos, marker="<", ms=2.6, color=INK2, mec="none", zorder=4,
                        clip_on=False)
                ax.text(xlim[0] + span * 0.03, pos, t, ha="left", va="center", fontsize=5.4, color=INK2, zorder=4)
        txt += notes
        if txt:
            ax.text(xlim[0] + span * 0.015, ys[i], "; ".join(txt), ha="left", va="center", fontsize=5.5,
                    color=INK2, zorder=4, bbox=dict(fc="white", ec="none", pad=0.4))
    _decorate(ax, ys, hdr, labs, ours, xlim, xlabel, target, fs, headers_left, row_h, hdr_h, bar_frac)
    return ys


def vbars(ax, labels, series, ylabel="", target=None, ymax=None, fs=6.2, small=0.03, values=False, rot=0,
          vfmt=None):
    """Vertical grouped bars. series: list of dicts (name, color, mu, lo, hi[, edge, hatch, labels]).
    Bars below small * axis span (or every bar with values=True) are labelled with their value."""
    n, m = len(labels), len(series)
    bw = 0.8 / m
    xx = np.arange(n)
    allv = [v for s in series for v in list(np.asarray(s["mu"], float)) + list(np.asarray(s.get("hi") if
            s.get("hi") is not None else s["mu"], float)) if np.isfinite(v)]
    top = ymax if ymax is not None else max(allv + [1e-9]) * 1.08
    for j, s in enumerate(series):
        mu = np.asarray(s["mu"], float)
        pos = xx + (j - (m - 1) / 2) * bw
        ekw = EDGE_OURS if s.get("edge") else dict(edgecolor="white", lw=0.3)
        ax.bar(pos, np.nan_to_num(mu), width=bw * 0.9, color=s["color"], hatch=s.get("hatch"), label=s["name"],
               zorder=2, **ekw)
        if s.get("lo") is not None:
            lo, hi = np.asarray(s["lo"], float), np.asarray(s["hi"], float)
            ok = np.isfinite(mu) & np.isfinite(lo) & np.isfinite(hi)
            ax.errorbar(pos[ok], mu[ok], yerr=[mu[ok] - lo[ok], hi[ok] - mu[ok]], fmt="none", ecolor=INK,
                        elinewidth=0.5, capsize=1.1, capthick=0.5, zorder=3)
        for i, (p_, v) in enumerate(zip(pos, mu)):
            if not np.isfinite(v):
                ax.text(p_, top * 0.01, "n/a", ha="center", va="bottom", fontsize=5.6, color=INK, rotation=90)
                continue
            extra = (s.get("labels") or [None] * n)[i]
            if values or v < small * top or extra:
                hi_ = np.asarray(s["hi"], float)[i] if s.get("hi") is not None else v
                hi_ = hi_ if np.isfinite(hi_) else v
                if v < 0.004 * top:
                    ax.plot([p_ - bw * 0.42, p_ + bw * 0.42], [0, 0], color=INK2, lw=0.9, zorder=4,
                            solid_capstyle="butt")
                t = extra if extra else (vfmt.format(v) if vfmt else _fmt_val(v))
                ax.text(p_, max(hi_, v) + top * 0.012, t, ha="center", va="bottom", fontsize=5.6, color=INK2,
                        rotation=90 if len(t) > 3 else 0, zorder=4)
    if target is not None:
        ax.axhline(target, color=RED, lw=0.7, ls="--", zorder=3)
    ax.set_xticks(xx)
    ax.set_xticklabels(labels, rotation=rot, ha="right" if rot else "center", fontsize=fs,
                       rotation_mode="anchor" if rot else "default")
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_ylim(0, top)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)


def target_handle(label="target 1 − ε = 0.9"):
    return Line2D([], [], color=RED, ls="--", lw=0.7, label=label)


def box_handles(lo=0.6):
    return [Line2D([], [], ls="", marker="D", ms=3.0, mfc="white", mec=INK, mew=0.5,
                   label="per-field box: quartiles, whiskers 5–95%, ◇ mean"),
            Line2D([], [], ls="", marker="<", ms=3.0, color=INK2, label=f"mean below {lo:g} (off scale)")]


# ------------------------------------------------------------------------------------ Fig 4
REG_SHORT = {"R1 RTK flat 3 m": "wheat RTK", "R2 RTK hilly-wet 1.5 m": "paddy RTK wet", "R3 DGPS hilly 6 m":
             "paddy DGPS"}


def _feas_note(st_list, regs):
    """Per data row: 'feasible on a, b, c of N fields' (regime order) if infeasible on some fields."""
    out = []
    for j in range(len(st_list[regs[0]])):
        r = [st_list[rg][j] for rg in regs]
        out.append(f"feasible on {' / '.join(str(x['nf']) for x in r)} of {r[0]['n']}"
                   if any(x["nf"] < x["n"] for x in r) else None)
    return out


def fig_system(name=SYS):
    d = load(f"{name}.csv")
    if d is None:
        return
    _check_n_test(d.p_nomiss, N_TEST_SYS)
    regs = sorted(d.regime.unique())
    rows, sysl, ours = [], [], []
    for fam, members in FAM4:
        members = [(s, l) for s, l in members if s in set(d.system)]
        if not members:
            continue
        rows.append(("hdr", fam))
        for s, l in members:
            if fam == "Ours":
                ours.append(len(sysl))
            rows.append(l)
            sysl.append(s)
    st = {rg: [sys_row(d[d.regime == rg], s) for s in sysl] for rg in regs}
    nrow = len(sysl)
    notes = _feas_note(st, regs)

    def colors(i):
        return [REG_BLUE[i] if j in ours else REG_GREY[i] for j in range(nrow)]

    def ser(key, ci):
        return [dict(name=M.REGIME_LABEL.get(rg, rg), mu=[x[key] for x in st[rg]],
                     lo=[x[key] - x[ci] for x in st[rg]], hi=[x[key] + x[ci] for x in st[rg]],
                     color=colors(i), edge=[j in ours for j in range(nrow)]) for i, rg in enumerate(regs)]

    boxes = [dict(name=rg, vals=[x["vals"] for x in st[rg]], color=colors(i), edge=[j in ours for j in range(nrow)],
                  note=notes if i == 0 else None) for i, rg in enumerate(regs)]
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 5.0), sharey=True, gridspec_kw=dict(width_ratios=[1.15, 1.0, 0.9]))
    kw = dict(ours=ours, row_h=1.0, hdr_h=0.95, bar_frac=0.84)
    hboxes(axs[0], rows, boxes, "P(no missed area) per field", target=TARGET, xlim=(0.6, 1.005), **kw)
    allov = [x["ov"] for rg in regs for x in st[rg] if np.isfinite(x["ov"])]
    # only outliers (> 100% overlap, Tube MPC) are cut; the cap is the largest other mean, rounded up to 10%
    rest = [v for v in allov if v <= 100]
    cap = 10.0 * math.ceil(max(rest) / 10.0) if max(allov) > 100 else None
    rest_hi = [x["ov"] + x["ovci"] for rg in regs for x in st[rg] if np.isfinite(x["ov"]) and x["ov"] <= 100]
    hbars(axs[1], rows, ser("ov", "ovci"), "Planned overlap (% of field area)", xmax=cap,
          xlim=(0, max((cap or max(allov)) * 1.32, max(rest_hi) * 1.05)), headers_left=False, small=0.006, **kw)
    allem = [x["em"] + x["emci"] for rg in regs for x in st[rg] if np.isfinite(x["em"])]
    hbars(axs[2], rows, ser("em", "emci"), "Mean missed area (m² ha⁻¹)", values=True,
          xlim=(0, max(allem) * 1.55), headers_left=False, **kw)
    for a, l in zip(axs, "abc"):
        panel(a, l, x=0.0, y=1.005)
        a.tick_params(axis="y", labelleft=a is axs[0])
    nf = {rg: d[d.regime == rg].field.nunique() for rg in regs}
    hd = [(Patch(facecolor=REG_GREY[i], edgecolor=INK2, lw=0.5), Patch(facecolor=REG_BLUE[i], **EDGE_OURS))
          for i in range(len(regs))]
    labs = [f"{M.REGIME_LABEL.get(rg, rg)} ({nf[rg]} fields)" for rg in regs]
    bh_ = box_handles()
    fig.legend(hd + [target_handle()] + bh_, labs + ["target 1 − ε = 0.9"] + [b.get_label() for b in bh_],
               loc="upper center", ncol=2, fontsize=6.2,
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.0)}, bbox_to_anchor=(0.6, 1.0),
               handlelength=2.6, columnspacing=1.5, labelspacing=0.3,
               title="Regime, top to bottom in each row (grey: baselines, blue: CE-U, ours)", title_fontsize=6.2)
    fig.tight_layout(w_pad=0.5, rect=(0, 0, 0.995, 0.9))
    save(fig, "fig4_system")


# ------------------------------------------------------------------------------------ Fig 5
def fig_stacks(name=SYS):
    d = load(f"{name}.csv")
    if d is None:
        return
    regs = sorted(d.regime.unique())
    stacks = [s for s in STACKS if s[1] in set(d.system) and s[2] in set(d.system)]
    labels = [s[0] for s in stacks]
    ns = len(stacks)
    titles = []
    fig, axs = plt.subplots(len(regs), 3, figsize=(7.2, 1.3 * len(regs) + 0.75), squeeze=False,
                            gridspec_kw=dict(width_ratios=[1.0, 1.0, 1.0]))
    for i, rg in enumerate(regs):
        x = d[d.regime == rg]
        base = [sys_row(x, s[1]) for s in stacks]
        ours = [sys_row(x, s[2]) for s in stacks]
        farm = sys_row(x, FARMER) if FARMER in set(x.system) else None
        pres_f = [j == 0 and farm is not None for j in range(ns)]

        def three(key, ci=None, lo=None, hi=None, notes=False):
            def arr(rr, k):
                return [r[k] for r in rr]
            fr = [farm if j == 0 and farm is not None else {k: np.nan for k in base[0]} for j in range(ns)]
            out = []
            for nm, rr, c, pres, edge in [("+ vendor-spec overlap (2× p2p)", base, MUTED, [True] * ns, False),
                                          ("+ farmer-tuned global overlap", fr, LIGHT, pres_f, False),
                                          ("+ CE (ours)", ours, BLUE, [True] * ns, True)]:
                if ci is not None:
                    lo_ = [r[key] - r[ci] for r in rr]
                    hi_ = [r[key] + r[ci] for r in rr]
                elif lo is not None:
                    lo_, hi_ = arr(rr, lo), arr(rr, hi)
                else:
                    lo_ = hi_ = None
                note = [(f"{r['nf']}/{r['n']} feasible" if notes and np.isfinite(r["nf"]) and r["nf"] < r["n"]
                         else None) for r in rr]
                out.append(dict(name=nm, color=c, mu=arr(rr, key), lo=lo_, hi=hi_, present=pres, edge=edge,
                                note=note))
            return out

        fr0 = farm if farm is not None else None
        bx = [dict(name="spec", color=MUTED, vals=[r["vals"] for r in base]),
              dict(name="farmer", color=LIGHT, present=pres_f, vals=[fr0["vals"] if (j == 0 and fr0) else []
                                                                     for j in range(ns)]),
              dict(name="CE", color=BLUE, edge=True, vals=[r["vals"] for r in ours])]
        star = [r["nf"] < r["n"] for r in ours]
        labels_i = [l + (" *" if f else "") for l, f in zip(labels, star)]
        foot = "; ".join(f"* CE feasible on {r['nf']}" for r in ours if r["nf"] < r["n"])
        titles.append(f"{M.REGIME_LABEL.get(rg, rg)}, {x.field.nunique()} fields" + (f" ({foot})" if foot else ""))
        hboxes(axs[i, 0], labels_i, bx, "", target=TARGET, xlim=(0.6, 1.005), bar_frac=0.84)
        ov = [r["ov"] + r["ovci"] for r in base + ours if np.isfinite(r["ov"])] + [farm["ov"] if farm else 0]
        ys = hbars(axs[i, 1], labels, three("ov", ci="ovci"), "", xlim=(0, max(ov) * 1.12), bar_frac=0.84,
                   small=0.006)
        if farm is not None and np.isfinite(ours[0]["oracle"]):
            axs[i, 1].plot([ours[0]["oracle"]] * 2, [ys[0] - 0.42, ys[0] + 0.42], color=INK, lw=1.3, zorder=5,
                           solid_capstyle="butt")
        em = [r["em"] + r["emci"] for r in base + ours if np.isfinite(r["em"])] + [farm["em"] if farm else 0]
        hbars(axs[i, 2], labels, three("em", ci="emci"), "", values=True, xlim=(0, max(em) * 1.45), bar_frac=0.84)
        for j in range(3):
            if j:
                panel(axs[i, j], "abcdefghijklmno"[i * 3 + j], x=-0.01, y=1.0)
            axs[i, j].tick_params(axis="y", labelleft=j == 0)
    for j, t in enumerate(["P(no missed area) per field", "Planned overlap (% of field area)",
                           "Mean missed area (m² ha⁻¹)"]):
        axs[-1, j].set_xlabel(t)
    h = [Patch(color=MUTED, label="+ vendor-spec overlap (2× p2p: 5 cm RTK, 40 cm DGPS)"),
         Patch(color=LIGHT, label="+ farmer-tuned global overlap"),
         Patch(facecolor=BLUE, label="+ CE (ours)", **EDGE_OURS),
         Line2D([], [], color=INK, lw=1.3, marker="", label="per-field oracle (test-tuned)"),
         target_handle()] + box_handles()
    fig.legend(handles=h, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.0), fontsize=6.2, columnspacing=1.2)
    fig.tight_layout(h_pad=1.4, w_pad=0.8, rect=(0, 0, 1, 1 - 0.52 / (1.3 * len(regs) + 0.75)))
    for i, t in enumerate(titles):
        p = axs[i, 0].get_position()
        fig.text(0.004, p.y1 + 0.012, f"({'abcdefghijklmno'[i * 3]})", fontsize=8, fontweight="bold", va="bottom")
        fig.text(0.04, p.y1 + 0.012, t, fontsize=6.8, va="bottom", color=INK)
    save(fig, "fig5_stacks")


# ------------------------------------------------------------------------------------ Fig 3
def _cover_columns(F, ys, off, w, gx):
    """Exact lateral coverage per along-track column of the main area F.M.
    off: (K, len(gx)) executed offsets (nan = pass absent). Returns gap list [(x, y0, y1)], margin list
    [(x, y, overlap_m)] for adjacent passes, and the evaluated length per column."""
    import core
    gaps, margins, tot = [], [], 0.0
    for j, x in enumerate(gx):
        c = core._chord_x(F.M, x)
        if c is None:
            continue
        lo, hi = c
        tot += hi - lo
        ok = np.isfinite(off[:, j])
        L_ = np.sort(np.c_[ys[ok] + off[ok, j] - w / 2, ys[ok] + off[ok, j] + w / 2], axis=0)
        order = np.argsort(L_[:, 0])
        left, right = L_[order, 0], L_[order, 1]
        reach = lo
        for a, b in zip(left, right):
            if a > reach and a > lo and reach < hi:
                gaps.append((x, reach, min(a, hi)))
            elif lo < a < hi and reach > a:
                margins.append((x, (a + reach) / 2, reach - a))
            reach = max(reach, b)
        if reach < hi:
            gaps.append((x, reach, hi))
    return gaps, margins, tot


def _count_grid(F, ys, X, Dr, w, gx, gy):
    import core
    cnt = np.zeros((len(gy), len(gx)), np.int16)
    for k, y in enumerate(ys):
        o = core.pass_offsets(X[k], Dr[k], gx)[0]
        ok = np.isfinite(o)
        lo, hi = y + o - w / 2, y + o + w / 2
        cnt += ((gy[:, None] >= lo[None, :]) & (gy[:, None] <= hi[None, :]) & ok[None, :]).astype(np.int16)
    return cnt


def fig_coverage(name=SYS, regime=None, n_cond=16):
    """Coverage (skip / overlap) maps of one real field under four margin rules.

    Field choice uses geometry only: among the evaluation fields of the regime with a main area of
    1-3 ha, the one whose bounding box is closest to square (readable at print size). All four plans
    are executed under the SAME sampled operating condition (soil, GNSS CORS segment and start time,
    mounting error); the process noise differs because the plans have different numbers of passes.
    The shown condition is the one of n_cond independent draws (not the evaluated test runs) whose
    vendor-spec missed area is closest to that method's 200-run mean on this field."""
    import core
    from shapely import contains_xy
    import exp_system as ES
    d = load(f"{name}.csv")
    if d is None:
        return
    regime = regime or [r for r in sorted(d.regime.unique()) if r.startswith("R1")][0]
    reg = ES.REGIMES.get(regime)
    if reg is None:
        return
    w = reg["w"]
    x = d[d.regime == regime]
    fields = {F.fid: F for F in core.load_fields(reg["kind"], w=w, seed=0) if F.fid in set(x.field)}
    cand = [F for F in fields.values() if 1.0e4 <= F.M.area <= 3.0e4]
    F = min(cand, key=lambda F: abs(math.log((F.P.bounds[3] - F.P.bounds[1]) / (F.P.bounds[2] - F.P.bounds[0]))))
    xf = x[x.field == F.fid].set_index("system")
    methods = [("Vendor-spec overlap (2× p2p)", "BCD + LQR-I + spec overlap (2x vendor p2p)"),
               ("Tube MPC, W99 [Mayne 2005]", "Tube-MPC radius margin (W99)"),
               ("CP pair-level [Lindemann 2023]", "Conformal planning, pair-level union bound (Lindemann et al.)"),
               ("CE-U (ours)", "BCD + LQR-I + CE (ours)")]
    methods = [(l, s) for l, s in methods if s in xf.index and np.isfinite(xf.loc[s, "param"])]
    cond = core.Condition(np.random.default_rng(2024), n_cond, **ES.cond_kw(reg))
    minx, miny, maxx, maxy = F.M.bounds
    gx = np.arange(math.ceil(minx) + 0.25, maxx, 0.5)
    bx0, by0, bx1, by1 = F.P.bounds
    gxm = np.arange(bx0, bx1, 0.5)
    gym = np.arange(by0, by1, 0.05)
    GX, GY = np.meshgrid(gxm, gym)
    inM, inP = contains_xy(F.M, GX, GY), contains_xy(F.P, GX, GY)
    sims = []
    for lab, s in methods:
        lam = float(xf.loc[s, "param"])
        ys = core.plan(F, w, lam, lambda f, y: 1.0)
        X, D = core.simulate(F, ys, cond, np.random.default_rng(99))
        sims.append((lab, s, lam, ys, X, D))
    # pick the condition (run) whose vendor-spec missed area is closest to the 200-run mean
    lab0, s0, lam0, ys0, X0, D0 = sims[0]
    ref = float(xf.loc[s0, "e_miss"]) * F.M.area
    areas = []
    for r in range(n_cond):
        off = np.stack([core.pass_offsets(X0[k], D0[k][r:r + 1], gx)[0] for k in range(len(ys0))])
        g, _, _ = _cover_columns(F, ys0, off, w, gx)
        areas.append(sum(b - a for _, a, b in g) * 0.5)
    run = int(np.argmin(np.abs(np.array(areas) - ref)))
    cmap = ListedColormap(["#f3f2ee", "#d8d6cf", "#6f6d66", RED])  # headland, once, >=2, missed
    nm = len(sims)
    fig = plt.figure(figsize=(7.2, 3.9))
    gs = fig.add_gridspec(2, nm, height_ratios=[4.4, 1.0], hspace=0.58, wspace=0.1,
                          left=0.01, right=0.985, top=0.865, bottom=0.06)
    for i, (lab, s, lam, ys, X, D) in enumerate(sims):
        r = xf.loc[s]
        Dr = [Dk[run:run + 1] for Dk in D]
        off = np.stack([core.pass_offsets(X[k], Dr[k], gx)[0] for k in range(len(ys))])
        gaps, margins, tot = _cover_columns(F, ys, off, w, gx)
        area = sum(b - a for _, a, b in gaps) * 0.5
        cnt = _count_grid(F, ys, X, Dr, w, gxm, gym)
        img = np.full(cnt.shape, np.nan)
        img[inP] = 0
        img[inM] = np.where(cnt[inM] >= 2, 2, np.where(cnt[inM] == 1, 1, 3))
        ax = fig.add_subplot(gs[0, i])
        ax.imshow(np.ma.masked_invalid(img), origin="lower", extent=(gxm[0] - 0.25, gxm[-1] + 0.25, gym[0] - 0.025,
                  gym[-1] + 0.025), cmap=cmap, vmin=-0.5, vmax=3.5, interpolation="nearest", aspect="equal",
                  rasterized=True)
        ax.plot(*F.M.exterior.xy, color=INK2, lw=0.5)
        ax.plot(*F.P.exterior.xy, color=MUTED, lw=0.4)
        if gaps:
            seg = [[(gx_ - 0.25, (a + b) / 2), (gx_ + 0.25, (a + b) / 2)] for gx_, a, b in gaps]
            ax.add_collection(LineCollection(seg, colors=RED, linewidths=0.7, zorder=5))
        widths = np.array([b - a for _, a, b in gaps]) * 100
        if gaps:  # zoom window at the widest gap
            gx_, a, b = gaps[int(np.argmax(widths))]
            zc, ztxt = (gx_, (a + b) / 2), f"widest gap {widths.max():.0f} cm"
        else:  # ... or at the narrowest overlap between adjacent passes
            mg = min(margins, key=lambda t: t[2])
            zc, ztxt = (mg[0], mg[1]), f"narrowest overlap {mg[2] * 100:.0f} cm"
        ax.plot(*zc, marker="s", ms=4.5, mfc="none", mec=INK, mew=0.7, zorder=6)
        ax.set_xlim(bx0 - 2, bx1 + 2)
        ax.set_ylim(by0 - 2, by1 + 2)
        ax.axis("off")
        ptxt = f"{r.p_nomiss:.3f}"
        lam_txt = (f"erosion λ = {lam * 100:.1f} cm, cert. q = {r.q_cert * 100:.1f} cm"
                   if np.isfinite(r.get("q_cert", np.nan)) else f"erosion λ = {lam * 100:.1f} cm (overlap 2λ)")
        ax.set_title(f"({'abcd'[i]}) {lab}\n{lam_txt}\n{len(ys)} passes, planned overlap {r.overlap * 100:.1f}%",
                     fontsize=5.9, loc="left", x=0.0, pad=2)
        mean_m2 = float(r.e_miss) * F.M.area

        def pct(a_):
            v_ = a_ / F.M.area * 100
            return "0%" if a_ == 0 else ("< 0.01%" if v_ < 0.01 else f"{v_:.2f}%")
        stat = (f"this run: missed {area:.1f} m² ({pct(area)})"
                + (f"\ngaps median {np.median(widths):.0f} cm, max {widths.max():.0f} cm" if gaps else "\nno gap")
                + f"\n200 runs: mean {mean_m2:.1f} m² ({pct(mean_m2)}),"
                f"\nP(no missed area) = {ptxt}")
        ax.text(0.0, -0.01, stat, transform=ax.transAxes, ha="left", va="top", fontsize=5.8, color=INK,
                linespacing=1.2)
        if i == 0:  # 50 m scale bar (upper left, outside the field)
            ax.plot([bx0, bx0 + 50], [by1 - 22] * 2, color=INK, lw=1.2, solid_capstyle="butt")
            ax.text(bx0 + 25, by1 - 20.5, "50 m", ha="center", va="bottom", fontsize=5.8)
        # true-scale zoom: 6 m along x 1.5 m lateral around zc
        zx = np.arange(zc[0] - 3, zc[0] + 3, 0.05)
        zy = np.arange(zc[1] - 0.75, zc[1] + 0.75, 0.0025)
        zc_ = _count_grid(F, ys, X, Dr, w, zx, zy)
        ZX, ZY = np.meshgrid(zx, zy)
        zin = contains_xy(F.M, ZX, ZY)
        zim = np.where(zin, np.where(zc_ >= 2, 2, np.where(zc_ == 1, 1, 3)), 0).astype(float)
        az = fig.add_subplot(gs[1, i])
        az.imshow(zim, origin="lower", extent=(-3, 3, -0.75, 0.75), cmap=cmap, vmin=-0.5, vmax=3.5,
                  interpolation="nearest", aspect="equal", rasterized=True)
        az.set_xticks([-3, 0, 3])
        az.set_xticklabels(["0", "3", "6 m"], fontsize=5.6)
        az.set_yticks([])
        az.tick_params(length=1.5, pad=1)
        az.grid(False)
        for sp in az.spines.values():
            sp.set_visible(True)
            sp.set_linewidth(0.5)
        az.set_title(f"true-scale zoom of □ (6 m × 1.5 m)\n{ztxt}", fontsize=5.8, loc="left", x=0.0, pad=2)
    h = [Patch(color="#d8d6cf", label="covered once"), Patch(color="#6f6d66", label="overlap (≥ 2 swaths)"),
         Line2D([], [], color=RED, lw=1.2, label="missed (map: line width not to scale; zoom: true scale)"),
         Patch(facecolor="#f3f2ee", edgecolor=MUTED, lw=0.4, label="headland (not evaluated)")]
    fig.legend(handles=h, loc="upper center", ncol=4, fontsize=6.0, bbox_to_anchor=(0.5, 1.0), columnspacing=1.2)
    print(f"  fig3: field {F.fid} ({F.M.area / 1e4:.2f} ha main area, bbox slope {F.z_mean_slope:.1f} deg), "
          f"{regime}, condition draw {run} of {n_cond}")
    save(fig, "fig3_coverage")


# ------------------------------------------------------------------------------------ Fig 6
def fig_main():
    ds = {}
    for k in ("paddy", "wheat"):
        for tag in (os.environ.get("CE_TAG", "_v6"), "_v5", "_v4", "_v3"):
            d = load(f"main_{k}{tag}.csv")
            if d is not None:
                ds[k] = d
                break
    if len(ds) < 2:
        return
    have = set.intersection(*[set(d.method.unique()) for d in ds.values()])
    rows, meth, ours = [], [], []
    for gname, ms in M.GROUPS:
        ms = [m for m in ms if m in have]
        if not ms:
            continue
        rows.append(("hdr", gname))
        for m in ms:
            if M.is_ours(m):
                ours.append(len(meth))
            rows.append(M.LABEL.get(m, m))
            meth.append(m)
    st = {}
    for k, d in ds.items():
        _check_n_test(d.p_nomiss, 300)
        R = []
        for m in meth:
            g = d[d.method == m].dropna(subset=["p_nomiss"])
            p, lo, hi = field_p(g.p_nomiss)
            ov, oc = t_ci(g.overlap * 100)
            em, ec = t_ci(g.e_miss * 1e4)
            R.append(dict(p=p, lo=lo, hi=hi, meet=meet_frac(g.p_nomiss, 300) * 100, ov=ov, ovci=oc, em=em, emci=ec))
        st[k] = R

    def ser(key, lo=None, hi=None, ci=None):
        out = []
        for k, d in ds.items():
            R = st[k]
            mu = [r[key] for r in R]
            if ci:
                lo_, hi_ = [r[key] - r[ci] for r in R], [r[key] + r[ci] for r in R]
            elif lo:
                lo_, hi_ = [r[lo] for r in R], [r[hi] for r in R]
            else:
                lo_ = hi_ = None
            out.append(dict(name=f"{M.CROP_LABEL[k]}, {d.field.nunique()} fields", color=M.FIELD_COL[k], mu=mu,
                            lo=lo_, hi=hi_))
        return out

    fig, axs = plt.subplots(1, 3, figsize=(7.2, 4.4), sharey=True, gridspec_kw=dict(width_ratios=[1.1, 1.0, 1.0]))
    kw = dict(ours=ours, row_h=1.0, hdr_h=0.95, bar_frac=0.8)
    boxes = [dict(name=k, color=M.FIELD_COL[k], vals=[d[d.method == m].p_nomiss.dropna().values for m in meth])
             for k, d in ds.items()]
    hboxes(axs[0], rows, boxes, "P(no missed area) per field", target=TARGET, xlim=(0.6, 1.005), **kw)
    ovmax = max(r["ov"] + r["ovci"] for R in st.values() for r in R)
    hbars(axs[1], rows, ser("ov", ci="ovci"), "Planned overlap (% of field area)", xlim=(0, ovmax * 1.08),
          headers_left=False, small=0.006, **kw)
    emmax = max(r["em"] + r["emci"] for R in st.values() for r in R)
    hbars(axs[2], rows, ser("em", ci="emci"), "Mean missed area (m² ha⁻¹)", values=True,
          xlim=(0, emmax * 1.3), headers_left=False, **kw)
    for a, l in zip(axs, "abc"):
        panel(a, l, x=0.0, y=1.005)
        a.tick_params(axis="y", labelleft=a is axs[0])
    h = [Patch(facecolor=M.FIELD_COL[k], edgecolor=INK2, lw=0.5, label=s_["name"])
         for k, s_ in zip(ds, ser("p", "lo", "hi"))] + [target_handle(), box_handles()[0]]
    fig.legend(handles=h, loc="upper left", ncol=2, fontsize=6.2, bbox_to_anchor=(0.0, 1.0), columnspacing=1.2)
    fig.text(0.995, 0.99, "BCD + LQR-I, RTK (AR on), w = 3 m,\nε = 0.1, n = 100 calibration runs,\n"
             "300 test runs per field", ha="right", va="top", fontsize=6.0, color=INK2)
    fig.tight_layout(w_pad=0.5, rect=(0, 0, 0.995, 0.915))
    save(fig, "fig6_main")


# ------------------------------------------------------------------------------------ Fig 8
CROSS_LABEL = {"QR (GBM, uncalibrated)": "Quantile regr., GBM (uncal.)", "CQR (Romano 2019)": "CQR [Romano 2019]",
               "Gaussian on score": "Gaussian fit of S", "Scenario (Campi-Garatti)": "Scenario on S [Campi 2011]",
               "CVaR (empirical)": "CVaR of S [Rockafellar 2000]",
               "Wasserstein DRO-CVaR": "W-DRO-CVaR on S [Mohajerin E. 2018]",
               "Worst-case (max score)": "Max of S (robust)", "CE-U (ours, uniform)": "CE-U (ours)"}


def fig_cross():
    parts = {k: load(f"cross2_{k}.csv") for k in ("paddy", "wheat")}
    parts = {k: v for k, v in parts.items() if v is not None}
    shift = [x for x in (load("cross.csv"), load("cross_reverse.csv")) if x is not None]
    if not parts:
        return
    d = pd.concat(parts.values())
    rows, meth, ours = [], [], []
    for gname, ms in M.GROUPS:
        ms = [m for m in ms if m in set(d.method)]
        if not ms:
            continue
        rows.append(("hdr", gname.replace("Run-level score S + other quantile rules", "Pooled run-level score S")))
        for m in ms:
            if M.is_ours(m):
                ours.append(len(meth))
            rows.append(CROSS_LABEL.get(m, M.LABEL.get(m, m)))
            meth.append(m)
    # Max of S picks the same plan as Scenario on S in every split of some crops: mark the row label
    same = []
    for kind, x in parts.items():
        if "Scenario (Campi-Garatti)" in meth and "Worst-case (max score)" in meth:
            a_ = x[x.method == "Scenario (Campi-Garatti)"].groupby("rep").lam.first()
            b_ = x[x.method == "Worst-case (max score)"].groupby("rep").lam.first()
            if len(a_) and np.allclose(a_.values, b_.reindex(a_.index).values):
                same.append(kind)
    if same:
        j = meth.index("Worst-case (max score)")
        k_ = [i_ for i_, r_ in enumerate(rows) if not isinstance(r_, tuple)][j]
        rows[k_] = rows[k_] + " *"
    fig = plt.figure(figsize=(7.2, 4.7))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.75, 0.85], hspace=0.6, wspace=0.14,
                          left=0.222, right=0.975, top=0.865, bottom=0.08)
    axs = [fig.add_subplot(gs[0, j]) for j in range(4)]
    for a in axs[1:]:
        a.sharey(axs[0])
    letters = iter("abcdef")
    nreps, ntest = [], []
    for i, kind in enumerate(parts):
        x = parts[kind]
        Pv, O = [], []
        for m in meth:
            g = x[x.method == m]
            Pv.append(g.groupby("rep").p_nomiss.mean().values)  # per split: mean over its unseen test fields
            mo, co = t_ci(g.groupby("rep").overlap.mean().values * 100)
            O.append((mo, co))
        nrep = x.rep.nunique()
        nreps.append(nrep)
        col = [BLUE if j in ours else MUTED for j in range(len(meth))]
        edge = [j in ours for j in range(len(meth))]
        a1, a2 = axs[2 * i], axs[2 * i + 1]
        hboxes(a1, rows, [dict(name="P", color=col, edge=edge, vals=Pv)], "P(no missed area) per split",
               target=TARGET, xlim=(0.6, 1.005), ours=ours, headers_left=(i == 0))
        hbars(a2, rows, [dict(name="O", color=col, edge=edge, mu=[o[0] for o in O],
                              lo=[o[0] - o[1] for o in O], hi=[o[0] + o[1] for o in O])],
              "Planned overlap (%)", xlim=(0, max(o[0] + o[1] for o in O) * 1.12), ours=ours, headers_left=False)
        ncal = int(x.n_cal.iloc[0])
        ntest.append(int(x.groupby("rep").field.nunique().iloc[0]))
        a1.text(0.0, 1.075, f"Unseen {kind} fields: {nrep} splits, {ncal} calibration fields",
                transform=a1.transAxes, fontsize=6.6, ha="left", va="bottom")
        panel(a1, next(letters), x=0.0, y=1.0)
        panel(a2, next(letters), x=0.0, y=1.0)
        a1.set_xticks([0.6, 0.8, 1.0])
        a1.set_xticklabels(["0.6", "0.8", "1"])
        for a in (a1, a2):
            a.tick_params(axis="y", labelleft=a is axs[0])
    if shift:
        s = pd.concat(shift)
        settings = [("in-region", "In-region\n(paddy → paddy)"), ("shift wheat->paddy", "Shift wheat → paddy"),
                    ("shift paddy->wheat", "Shift paddy → wheat")]
        settings = [(st, l) for st, l in settings if (s.setting == st).any()]
        meths = [("CE-U", "CE-U (ours)", BLUE), ("CE-A", "CE-A (ours)", AQUA), ("CE-AW (weighted)",
                                                                               "CE-AW (ours, weighted)", VIOLET)]
        resP = {m: [] for m, _, _ in meths}
        resO = {m: [] for m, _, _ in meths}
        labs = []
        for st_, lab in settings:
            g = s[s.setting == st_]
            aw = g[g.method == "CE-AW (weighted)"]
            if len(aw):  # common (rep, field) set on which CE-AW produced a plan
                keys = set(zip(aw.rep, aw.field))
                full = g[g.method == "CE-U"]
                abst = 1 - len(aw) / max(len(full), 1)
                lab = f"{lab}, {g.rep.nunique()} splits\n(CE-AW abstains on {abst * 100:.0f}%)"
                g = g[[k in keys for k in zip(g.rep, g.field)]]
            else:
                lab = f"{lab.replace(chr(10), ' ')}\n{g.rep.nunique()} splits"
            labs.append(lab)
            for m, _, _ in meths:
                gm = g[g.method == m]
                if not len(gm):
                    resP[m].append(np.array([]))
                    resO[m].append((np.nan, np.nan))
                    continue
                resP[m].append(gm.groupby("rep").p_nomiss.mean().values)
                resO[m].append(t_ci(gm.groupby("rep").overlap.mean().values * 100))
        b1 = fig.add_subplot(gs[1, 0:2])
        b2 = fig.add_subplot(gs[1, 2:4], sharey=b1)
        pres = {m: [len(v) > 0 for v in resP[m]] for m, _, _ in meths}
        serP = [dict(name=l, color=c, edge=True, present=pres[m], vals=resP[m]) for m, l, c in meths]
        serO = [dict(name=l, color=c, edge=True, present=pres[m], mu=[v[0] for v in resO[m]],
                     lo=[v[0] - v[1] for v in resO[m]], hi=[v[0] + v[1] for v in resO[m]]) for m, l, c in meths]
        hboxes(b1, labs, serP, "P(no missed area) per split", target=TARGET, xlim=(0.6, 1.005), bar_frac=0.84)
        omax = max(v[0] + v[1] for m, _, _ in meths for v in resO[m] if np.isfinite(v[0]))
        hbars(b2, labs, serO, "Planned overlap (%)", xlim=(0, omax * 1.12), bar_frac=0.84)
        b2.tick_params(axis="y", labelleft=False)
        b1.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0])
        b1.set_xticklabels(["0.6", "0.7", "0.8", "0.9", "1"])
        b1.text(0.0, 1.1, "Regional shift, calibration → test", transform=b1.transAxes,
                fontsize=6.6, ha="left", va="bottom")
        panel(b1, next(letters), x=0.0, y=1.0)
        panel(b2, next(letters), x=0.0, y=1.0)
        b2.legend(handles=[Patch(facecolor=c, label=l, **EDGE_OURS) for _, l, c in meths], loc="lower right",
                  fontsize=6.0, bbox_to_anchor=(1.0, 1.1), ncol=3, columnspacing=1.0, borderaxespad=0.0)
    nt = "/".join(sorted({str(n) for n in ntest}))
    h = [Patch(color=MUTED, label="baseline"), Patch(facecolor=BLUE, label="CE-U (ours)", **EDGE_OURS),
         target_handle(), Line2D([], [], color=INK, lw=0.6, marker="|", ms=4, mew=0.6,
                                 label="overlap bars: mean ± 95% CI over splits")]
    fig.legend(handles=h, loc="upper left", ncol=4, fontsize=6.2, bbox_to_anchor=(0.005, 1.0), columnspacing=1.4)
    fig.legend(handles=[Line2D([], [], ls="", marker="D", ms=3.0, mfc="white", mec=INK, mew=0.5,
                               label=f"P boxes over splits (one value per split = mean over its {nt} test fields): "
                                     "quartiles, whiskers 5–95%, ◇ mean")],
               loc="upper left", fontsize=6.2, bbox_to_anchor=(0.005, 0.968))
    if same:
        fig.text(0.975, 1.0, "* " + " and ".join(same) + ": Max of S selects the same plan\n"
                 "as Scenario on S in every split", ha="right", va="top", fontsize=6.0, color=INK2)
    save(fig, "fig8_cross")


# ------------------------------------------------------------------------------------ Fig 2
def _infield_slope(F):
    from shapely import contains_xy
    ny, nx = F.gx_map.shape
    X, Y = np.meshgrid(F.gx0 + np.arange(nx), F.gy0 + np.arange(ny))
    msk = contains_xy(F.P, X, Y)
    sl = np.degrees(np.arctan(np.hypot(F.gx_map, F.gy_map)))
    return float(sl[msk].mean()) if msk.any() else np.nan


def fig_data():
    """(a) study fields, (b) real GNSS error tails per grade (CCDF), (c) in-field slopes, (d) robot deviations."""
    import core
    meta = json.load(open(os.path.join(HERE, "data", "fields.json")))
    dem = {int(f[:-4]) for f in os.listdir(os.path.join(HERE, "data", "dem")) if f.endswith(".npz")}
    used = {k: core.load_fields(k) for k in ("paddy", "wheat")}
    fig = plt.figure(figsize=(7.2, 4.2))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.2, 1.0, 1.05], height_ratios=[1, 1], left=0.075, right=0.99,
                          top=0.95, bottom=0.24, wspace=0.42, hspace=0.62)
    # (a) map | (b) GNSS error CCDF (legend to its right) / (c) in-field slopes | (d) robot deviations
    axs = [fig.add_subplot(gs[:, 0]), fig.add_subplot(gs[1, 1]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, 2])]
    ax = axs[0]
    ids = {F.fid for v in used.values() for F in v}
    exc = [m for j, m in enumerate(meta) if j in dem and j not in ids]
    ax.scatter([m["lon"] for m in exc], [m["lat"] for m in exc], s=4, facecolor="none", edgecolor=MUTED, lw=0.4,
               label=f"excluded (< 0.4 ha or no headland), n = {len(exc)}", zorder=1)
    for kind in ("paddy", "wheat"):
        Fs = used[kind]
        ax.scatter([F.meta["lon"] for F in Fs], [F.meta["lat"] for F in Fs], s=5, color=M.FIELD_COL[kind], lw=0,
                   alpha=0.85, label=f"{M.CROP_LABEL[kind]}, n = {len(Fs)}", zorder=2)
    box = (108.0, 123.5, 23.0, 41.5)
    ax.set_xlim(box[0], box[1])
    ax.set_ylim(box[2], box[3])
    ax.set_aspect(1 / math.cos(math.radians(32)))
    ax.set_xticks([110, 115, 120])
    ax.set_xlabel("Longitude (°E)")
    ax.set_ylabel("Latitude (°N)")

    km = 300.0  # scale bar at 40 N (map is in geographic coordinates; length valid at that latitude)
    dl = km / (111.32 * math.cos(math.radians(40)))
    ax.plot([108.6, 108.6 + dl], [40.3, 40.3], color=INK, lw=1.2, solid_capstyle="butt")
    ax.text(108.6 + dl / 2, 40.55, "300 km (at 40°N)", ha="center", va="bottom", fontsize=5.6)
    # locator inset with every used field (some lie outside the main extent)
    allF = [F for v in used.values() for F in v]
    out = [F for F in allF if not (box[0] <= F.meta["lon"] <= box[1] and box[2] <= F.meta["lat"] <= box[3])]
    ia = ax.inset_axes([0.5, 0.015, 0.49, 0.26])
    for kind in ("paddy", "wheat"):
        ia.scatter([F.meta["lon"] for F in used[kind]], [F.meta["lat"] for F in used[kind]], s=1.5,
                   color=M.FIELD_COL[kind], lw=0)
    ia.add_patch(Rectangle((box[0], box[2]), box[1] - box[0], box[3] - box[2], fill=False, ec=INK, lw=0.5))
    ia.set_xlim(76, 136)
    ia.set_ylim(20, 49)
    ia.set_aspect(1 / math.cos(math.radians(34)))
    ia.set_xticks([])
    ia.set_yticks([])
    ia.grid(False)
    ia.set_facecolor("white")
    for sp in ia.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
        sp.set_color(INK2)
    hh, ll = ax.get_legend_handles_labels()
    hh.append(Patch(facecolor="white", edgecolor=INK2, lw=0.5))
    ll.append(f"inset: all {len(allF)} used fields ({len(out)} outside the main map)")
    ax.legend(hh, ll, loc="upper left", fontsize=6.0, handletextpad=0.3, markerscale=1.6, borderaxespad=0.0,
              bbox_to_anchor=(-0.08, -0.12), labelspacing=0.3)
    assert all(76 <= F.meta["lon"] <= 136 and 20 <= F.meta["lat"] <= 49 for F in allF)
    panel(ax, "a", y=1.005)
    sl = {k: np.array([_infield_slope(F) for F in used[k]]) for k in ("paddy", "wheat")}
    bins = np.arange(0, 8.51, 0.5)
    vals = [np.clip(sl[k], 0, 8.25) for k in ("paddy", "wheat")]
    axs[1].hist(vals, bins=bins, color=[M.FIELD_COL["paddy"], M.FIELD_COL["wheat"]], histtype="bar", rwidth=0.9,
                weights=[np.full(len(v), 1 / len(v)) for v in vals],
                label=[f"{M.CROP_LABEL[k].split(' (')[0]} (median {np.median(sl[k]):.1f}°)" for k in ("paddy", "wheat")])
    axs[1].set_xticks([0, 2, 4, 6, 8.25])
    axs[1].set_xticklabels(["0", "2", "4", "6", "≥8"])
    axs[1].set_xlabel("Mean in-field slope (°)\nCopernicus GLO-30 DEM")
    axs[1].set_ylabel("Fraction of fields")
    axs[1].legend(loc="upper right", fontsize=5.8)
    axs[1].grid(axis="x", visible=False)
    panel(axs[1], "c", y=1.0)
    ax = axs[2]
    neff = None
    for g, c, ls, lab, ref in [("rtk_fix", INK, "-", "RTK, AR on (85% fixed)", True),
                               ("rtk_float", MUTED, (0, (4, 1.5)), "RTK float-only", False),
                               ("dgps", GREEN, "-", "DGPS", True)][::-1]:
        B = core.gnss_bank(g)
        h = np.sort(np.hypot(B["en"], B["ee"]))[::-1] * 100
        p = np.arange(1, len(h) + 1) / len(h)
        k = np.unique(np.geomspace(1, len(h), 500).astype(int)) - 1
        ax.loglog(h[k], p[k], color=c, lw=1.2 if ls == "-" else 1.0, ls=ls, label=lab, zorder=3 if g == "rtk_fix" else 2)
        if ref:
            s = np.sqrt(np.mean(h ** 2) / 2)  # 2-D Gaussian with the same RMS: Rayleigh exceedance
            z = np.geomspace(h[k][-1], h[0], 100)
            ax.loglog(z, np.exp(-z ** 2 / (2 * s ** 2)), color=c, lw=0.6, ls=":")
        neff = len(h) / 30.0  # 30 s CORS epochs
    ax.axhspan(1e-5, 10 / neff, color=GRID, zorder=0, lw=0)
    ax.text(0.45, 10 / neff * 0.85, "< 10 independent 30 s epochs", fontsize=5.4, color=INK2, va="top")
    ax.set_ylim(1e-5, 1.2)
    ax.set_xlim(0.3, 700)
    ax.set_xlabel("Horizontal GNSS error (cm)")
    ax.set_ylabel("Exceedance probability")
    hh, ll = ax.get_legend_handles_labels()
    hh = hh[::-1] + [Line2D([], [], color=INK2, lw=0.6, ls=":")]
    ll = ll[::-1] + ["2-D Gaussian (Rayleigh), same RMS"]
    ax.legend(hh, ll, loc="center left", fontsize=6.0, borderaxespad=0.0, bbox_to_anchor=(1.04, 0.5),
              handlelength=2.0, labelspacing=0.45, title="US NOAA CORS, static antennas,\n96 station-days per grade",
              title_fontsize=6.0, alignment="left")
    panel(ax, "b", y=1.0)
    P = np.load(os.path.join(HERE, "data", "citrus_passes.npy"), allow_pickle=True)
    ps = [p for p in P if p["seq"].startswith("05")]
    for p in ps:
        out_ = p["dir"] > 0
        axs[3].plot(p["x"] - p["x"].min(), p["e"] * 100, color=INK2 if out_ else MUTED, lw=0.7,
                    ls="-" if out_ else (0, (3, 1.2)))
    axs[3].axhline(0, color=INK, lw=0.5, zorder=0)
    axs[3].set_xlabel("Distance along row (m)")
    axs[3].set_ylabel("Lateral deviation from\nfitted row line (cm)")
    axs[3].legend(handles=[Line2D([], [], color=INK2, lw=0.8, label="outbound passes"),
                           Line2D([], [], color=MUTED, lw=0.8, ls=(0, (3, 1.2)), label="return passes")],
                  loc="upper left", fontsize=5.8, ncol=2, borderaxespad=0.1, columnspacing=0.8)
    lim = np.nanmax([np.abs(p["e"]).max() for p in ps]) * 100 * 1.35
    axs[3].set_ylim(-lim, lim)
    panel(axs[3], "d", y=1.0)
    print(f"  fig2: paddy {len(used['paddy'])}, wheat {len(used['wheat'])}, excluded {len(exc)}; "
          f"in-field slope median paddy {np.median(sl['paddy']):.2f}, wheat {np.median(sl['wheat']):.2f}; "
          f"robot panel: {len(ps)} of {len(P)} passes")
    save(fig, "fig2_data")


# ------------------------------------------------------------------------------------ Fig 9
SENS = [("controller", "Path-tracking controller", ["pure_pursuit", "stanley", "lqr", "lqr_i"],
         ["Pure\npursuit", "Stanley", "LQR", "LQR +\nintegral"], "lqr_i"),
        ("roll compensation", "Roll-compensation fraction c (–)", [0.0, 0.5, 0.85, 0.95],
         ["0", "0.5", "0.85", "0.95"], 0.85),
        ("implement width (m)", "Implement width w (m)", [1.5, 3.0, 6.0, 12.0], ["1.5", "3", "6", "12"], 3.0),
        ("GNSS receiver grade", "GNSS receiver grade", ["rtk_fix", "rtk_float", "dgps"],
         ["RTK\n(AR on)", "RTK float-\nonly", "DGPS"], "rtk_fix")]


def fig_sens():
    d = load("sens.csv")
    if d is None:
        return
    fig, axs = plt.subplots(2, 4, figsize=(7.2, 3.7), gridspec_kw=dict(height_ratios=[1, 1.05]))
    rng = np.random.default_rng(0)
    for j, (g, xl, order, ticks, default) in enumerate(SENS):
        x = d[d.group == g].copy()
        if not len(x):
            continue
        num = pd.to_numeric(x["value"], errors="coerce")
        if num.notna().all():
            x["value"] = num
        if g == "implement width (m)":  # fields with < 5 nominal passes have too few adjacent pairs
            x = x[x.nominal_passes >= 5]
        a, b = axs[0, j], axs[1, j]
        P, O, Q, nfs = [], [], [], []
        for i, v in enumerate(order):
            xv = x[x.value == v]
            pv = xv.p_nomiss.values
            P.append(field_p(pv))
            O.append(t_ci(xv.overlap.values * 100))
            Q.append(xv.q.mean() * 100)
            nfs.append(xv.field.nunique())
            a.scatter(i + (rng.random(len(pv)) - 0.5) * 0.3, pv, s=5, color=MUTED, lw=0, alpha=0.8, zorder=2)
        xx = np.arange(len(order))
        a.errorbar(xx, [p[0] for p in P], yerr=[[p[0] - p[1] for p in P], [p[2] - p[0] for p in P]], fmt="o",
                   ms=3.5, color=BLUE, mec=INK, mew=0.4, ecolor=INK, elinewidth=0.7, capsize=1.6, zorder=4)
        a.axhline(TARGET, color=RED, lw=0.7, ls="--", zorder=1)
        a.set_ylim(0.78, 1.01)
        a.set_xlim(-0.6, len(order) - 0.4)
        a.set_xticks(xx)
        a.set_xticklabels([])
        a.grid(axis="x", visible=False)
        a.set_title(xl, loc="left", fontsize=6.6, x=0.0)
        tl = [t + (f"\n(n = {n})" if n != max(nfs) else "") for t, n in zip(ticks, nfs)]
        dflt = [v == default for v in order]
        b.bar(xx, [o[0] for o in O], width=0.6, color=BLUE, zorder=2,
              edgecolor=[INK if f else "white" for f in dflt], lw=[0.8 if f else 0.3 for f in dflt],
              hatch=None)
        for i, f in enumerate(dflt):
            if f:
                b.bar(xx[i], O[i][0], width=0.6, color="none", edgecolor=INK, lw=0.8, hatch="////", zorder=3)
        b.errorbar(xx, [o[0] for o in O], yerr=[o[1] for o in O], fmt="none", ecolor=INK, elinewidth=0.5,
                   capsize=1.4, zorder=4)
        top = 25.0 if g != "GNSS receiver grade" else 72.0
        for i, (o, q) in enumerate(zip(O, Q)):
            b.text(i, o[0] + o[1] + top * 0.02, f"q={q:.0f}", ha="center", va="bottom", fontsize=5.6, color=INK2)
        b.set_ylim(0, top)
        b.set_xlim(-0.6, len(order) - 0.4)
        b.set_xticks(xx)
        b.set_xticklabels(tl, fontsize=6.0)
        b.set_xlabel(xl.replace("Path-tracking controller", "Controller").replace("GNSS receiver grade",
                                                                                   "Receiver grade"), fontsize=6.6)
        b.grid(axis="x", visible=False)
        panel(a, "abcd"[j], x=-0.02, y=1.08)
        panel(b, "efgh"[j], x=-0.02, y=1.05)
        if j:
            a.set_yticklabels([])
        if 0 < j < 3:
            b.set_yticklabels([])
    axs[0, 0].set_ylabel("P(no missed area)")
    axs[1, 0].set_ylabel("Planned overlap (%)\nlabels: erosion q (cm)")
    axs[1, 3].set_ylabel("Planned overlap (%)", fontsize=6.6)
    h = [Line2D([], [], ls="", marker="o", ms=3.5, color=BLUE, mec=INK, mew=0.4, label="mean over fields ± 95% CI"),
         Line2D([], [], ls="", marker="o", ms=2.5, color=MUTED, label="single field (200 test runs)"),
         target_handle(), Patch(facecolor=BLUE, edgecolor=INK, hatch="////", lw=0.8, label="default configuration")]
    fig.legend(handles=h, loc="upper center", ncol=4, fontsize=6.2, bbox_to_anchor=(0.5, 1.0), columnspacing=1.2)
    fig.tight_layout(h_pad=0.7, w_pad=0.5, rect=(0, 0, 1, 0.94))
    save(fig, "fig9_sensitivity")


# ------------------------------------------------------------------------------------ Fig 10
def fig_drift():
    d = load("aci.csv")
    if d is None:
        return
    nf = d.field.nunique()
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.35), sharex=True)
    win = 40
    for m, c, lab in [("static", INK2, "CE, static calibration (60 dry runs)"),
                      ("aci", BLUE, "CE + ACI update [Gibbs & Candès 2021]")]:
        x = d[d.method == m]
        pv = x.pivot(index="t", columns="field", values="err")
        k = pv.sum(axis=1).rolling(win, min_periods=win).sum()
        n = pv.notna().sum(axis=1).rolling(win, min_periods=win).sum()
        rate = k / n
        ci = np.array([cp_ci(int(kk), int(nn)) if np.isfinite(kk) else (np.nan, np.nan) for kk, nn in zip(k, n)])
        axs[0].fill_between(rate.index, ci[:, 0], ci[:, 1], color=c, alpha=0.18, lw=0)
        axs[0].plot(rate.index, rate.values, color=c, lw=1.2, label=lab)
        cum = x.groupby("t").err.mean().expanding().mean()
        axs[0].plot(cum.index, cum.values, color=c, lw=0.8, ls=(0, (3, 1.5)))
        q = x.pivot(index="t", columns="field", values="q") * 100
        mu, sd = q.mean(axis=1), q.std(axis=1)
        axs[1].fill_between(mu.index, mu - sd, mu + sd, color=c, alpha=0.18, lw=0)
        axs[1].plot(mu.index, mu.values, color=c, lw=1.2, label=lab)
        pas = x.groupby("t").passes.mean()
        print(f"  fig10 {m}: overall miss rate {x.err.mean():.3f}, mean q {x.q.mean()*100:.2f} cm, "
              f"mean passes {pas.mean():.2f}")
    axs[0].axhline(0.1, color=INK, ls=(0, (4, 2)), lw=0.7, label="target ε = 0.1")
    axs[0].set_ylim(0, 0.75)
    axs[0].set_ylabel("Missed-area rate\n= 1 − P(no missed area)")
    axs[0].set_title(f"Realised miss rate, {nf} paddy fields\n(solid: trailing {win} operations; dashed: cumulative)",
                     loc="left", fontsize=6.4, x=0.0)
    hh, ll = axs[0].get_legend_handles_labels()
    axs[0].legend(hh, ll, loc="upper left", fontsize=5.8, borderaxespad=0.2)
    axs[1].set_ylim(0, 17)
    axs[1].set_ylabel("Erosion per swath edge q (cm)")
    axs[1].set_title(f"Erosion q (mean ± sd over {nf} fields)", loc="left", fontsize=6.4, x=0.0)
    axs[1].legend(loc="lower right", fontsize=5.8)
    panel(axs[0], "a", y=1.0)
    panel(axs[1], "b", y=1.0)
    for a in axs:
        a.set_xlabel("Operation index (simulated soil-moisture index 0.15 → 0.90)")
        a.set_xlim(0, d.t.max())
    fig.tight_layout(w_pad=1.0)
    save(fig, "fig10_drift")


# ------------------------------------------------------------------------------------ Fig 11
def fig_ablation():
    # (data, receiver line, extra condition line); the implement width is read from the data (column w)
    sets = [(load("ablation.csv"), "RTK", None), (load("ablation_hard.csv"), "RTK", "wet soil"),
            (load("ablation_dgps.csv"), "DGPS", None)]
    sets = [(d, reg, extra) for d, reg, extra in sets if d is not None]
    if not sets:
        return
    variants = [("full (ours)", "CE, full (ours)", BLUE),
                ("naive calibration (no fixed point)", "CE calibrated on nominal plan (no fixed point)", YELLOW),
                ("absolute-error score", "CE with absolute-error score", VIOLET),
                ("pointwise quantile (no sup)", "CE with pointwise quantile (no sup over x)", MUTED)]
    cols = []
    for d, reg, extra in sets:
        for kind in ("paddy", "wheat"):
            if (d.kind == kind).any():
                g = d[d.kind == kind]
                ws = sorted(g.w.unique())
                assert len(ws) == 1, f"several widths in one ablation setting: {ws}"
                lines = [f"{kind.capitalize()}, {reg}"] + ([extra] if extra else []) + [f"w = {ws[0]:g} m",
                                                                                       f"{g.field.nunique()} fields"]
                cols.append((g, "\n".join(lines)))
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7))
    ser_p, ser_o = [], []
    for v, lab, c in variants:
        P = [field_p(g0[g0.variant == v].p_nomiss.values) for g0, _ in cols]
        O = [t_ci(g0[g0.variant == v].overlap.values * 100) for g0, _ in cols]
        lam = [g0[g0.variant == v].lam.mean() * 100 for g0, _ in cols]
        ser_p.append(dict(name=lab, color=c, mu=[p[0] for p in P], lo=[p[1] for p in P], hi=[p[2] for p in P],
                          edge=v.startswith("full")))
        ser_o.append(dict(name=lab, color=c, mu=[o[0] for o in O], lo=[o[0] - o[1] for o in O],
                          hi=[o[0] + o[1] for o in O], labels=[f"{l_:.0f}" for l_ in lam], edge=v.startswith("full")))
    vbars(axs[0], [t for _, t in cols], ser_p, "P(no missed area)", target=TARGET, ymax=1.08, fs=6.0, small=0.03)
    om = max(np.nanmax(np.asarray(s["hi"], float)) for s in ser_o)
    vbars(axs[1], [t for _, t in cols], ser_o, "Planned overlap (%)\nlabels: erosion q (cm)", ymax=om * 1.2, fs=6.0,
          small=0.0)
    panel(axs[0], "a", y=1.0)
    panel(axs[1], "b", y=1.0)
    h, l = axs[0].get_legend_handles_labels()
    h, l = h + [target_handle()], l + ["target 1 − ε = 0.9"]
    fig.legend(h, l, loc="upper center", ncol=3, fontsize=6.2, bbox_to_anchor=(0.5, 1.0), columnspacing=1.5)
    fig.tight_layout(w_pad=1.0, rect=(0, 0, 1, 0.86))
    save(fig, "fig11_ablation")


# ------------------------------------------------------------------------------------ Fig 12
def fig_real():
    d = load("real.csv")
    if d is None:
        return
    x = d[(d.split == "random") & (d.eps == 0.1)]
    rows, meth, ours = [], [], []
    for gname, ms in M.GROUPS:
        ms = [m for m in ms if m in set(x.method)]
        if not ms:
            continue
        rows.append(("hdr", gname))
        for m in ms:
            if M.is_ours(m):
                ours.append(len(meth))
            rows.append(M.LABEL.get(m, m))
            meth.append(m)
    fig = plt.figure(figsize=(7.2, 5.6))
    gt = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.25], left=0.297, right=0.985, top=0.885, bottom=0.43,
                          wspace=0.38)
    a0 = fig.add_subplot(gt[0, 0])
    a1 = fig.add_subplot(gt[0, 1], sharey=a0)
    # (a)/(b): box plots over 300 random calibration/test splits, K = 3 and K = 5 rows per strip
    HDR, BW, OFF = 1.0, 0.34, 0.2  # header step, box width, K = 3 / K = 5 offset from the row centre
    PLO = 0.6  # left end of the P axis (same convention as Figs. 4-6); boxes with median below it are not drawn
    y, ys, hdr = 0.0, [], []
    for r in rows:
        if isinstance(r, tuple):
            y -= HDR
            hdr.append((y, r[1]))
        else:
            y -= 1.0
            ys.append(y)
    ys = np.array(ys)
    q95 = 0.0
    for ax, col_, scale, xl in [(a0, "p_nomiss", 1.0, "P(no missed area) per split"),
                                (a1, "overlap", 100.0, "Planned overlap (% of strip area)")]:
        off_txt = {}
        for K, fc, off in [(3, MUTED, OFF), (5, "white", -OFF)]:
            vals = [x[(x.K == K) & (x.method == m)][col_].dropna().values * scale for m in meth]
            if col_ == "overlap":
                q95 = max(q95, max(np.percentile(v, 95) for v in vals if len(v)))
            keep = [k_ for k_, v in enumerate(vals) if len(v) and (col_ != "p_nomiss" or np.median(v) >= PLO)]
            for k_, v in enumerate(vals):
                if len(v) and k_ not in keep:
                    off_txt.setdefault(k_, []).append(f"{v.mean():.2f}")
            bp = ax.boxplot([vals[k_] for k_ in keep], positions=ys[keep] + off, widths=BW, orientation="horizontal",
                            whis=(5, 95), showfliers=False, patch_artist=True, manage_ticks=False,
                            medianprops=dict(color=INK, lw=0.8), boxprops=dict(lw=0.5, color=INK2),
                            whiskerprops=dict(lw=0.5, color=INK2), capprops=dict(lw=0.5, color=INK2))
            for b_, k_ in zip(bp["boxes"], keep):
                m = meth[k_]
                b_.set_facecolor(BLUE if (M.is_ours(m) and K == 3) else ("#a9c8ee" if M.is_ours(m) else fc))
        for k_, t in off_txt.items():  # rows off the P scale: state the means (K = 3 / K = 5)
            ax.text(PLO + 0.006, ys[k_], f"off scale, mean {' / '.join(t)}", ha="left", va="center", fontsize=5.5,
                    color=INK2, zorder=4, bbox=dict(fc="white", ec="none", pad=0.4))
        top = 0.1
        for yh, t in hdr:
            above = ys[ys > yh]
            if len(above):  # separator just below the K = 5 box of the previous row
                ax.axhline(above.min() - OFF - BW / 2 - 0.12, color=GRID, lw=0.7)
            else:
                top = yh + 0.45
            if ax is a0:
                ax.text(0.0, yh - 0.05, t, transform=_hdr_tr(ax), fontsize=6.0, color=INK2, fontstyle="italic",
                        va="center", zorder=5, bbox=dict(fc="white", ec="none", pad=0.2))
        for i in ours:
            ax.axhspan(ys[i] - 0.5, ys[i] + 0.5, color=OURS_BAND, zorder=0, lw=0)
        ax.set_xlabel(xl)
        ax.grid(axis="y", visible=False)
        ax.set_ylim(ys.min() - 0.6, top)
    a0.axvline(TARGET, color=RED, lw=0.7, ls="--", zorder=3)
    a0.set_xlim(PLO, 1.005)
    a0.set_xticks([0.6, 0.7, 0.8, 0.9, 1.0])
    a0.set_xticklabels(["0.6", "0.7", "0.8", "0.9", "1"])
    labs = [M.LABEL.get(m, m) for m in meth]
    sc = x[x.method == "Scenario (Campi-Garatti)"]
    wc = x[x.method == "Worst-case (max score)"]
    if len(sc) and np.allclose(sc.sort_values(["K", "rep"]).lam.values, wc.sort_values(["K", "rep"]).lam.values):
        labs[meth.index("Worst-case (max score)")] += " (= Scenario here)"
    a0.set_yticks(ys)
    a0.set_yticklabels(labs, fontsize=6.2)
    for i, t in enumerate(a0.get_yticklabels()):
        if i in ours:
            t.set_fontweight("bold")
            t.set_color(INK)
    a0.tick_params(axis="y", length=0)
    a1.tick_params(axis="y", labelleft=False, length=0)
    a1.set_xlim(0, q95 * 1.04)
    panel(a0, "a", x=0.0, y=1.01)
    panel(a1, "b", x=0.0, y=1.01)
    gb = fig.add_gridspec(1, 2, left=0.075, right=0.99, top=0.27, bottom=0.075, wspace=0.06)
    # (c)/(d): held-out block / day / sequence, dot plot with CP 95% CI on n_eff = n_test // K
    sel = [("CE-U (ours, uniform)", BLUE, "o"), ("Gaussian on score", LIGHT, "^"), ("CVaR (empirical)", INK2, "s"),
           ("Scenario (Campi-Garatti)", MUTED, "D")]
    splits = [s_ for s_ in ["LOBO:13B", "LOBO:13D", "LOBO:14B", "LODO:07-16", "LODO:07-18", "LOSO:01", "LOSO:03",
                            "LOSO:04", "LOSO:05", "LOSO:07"] if (d.split == s_).any()]
    bax = []
    for j, K in enumerate((3, 5)):
        ax = fig.add_subplot(gb[0, j], sharey=bax[0] if bax else None)
        bax.append(ax)
        for k, (m, c, mk) in enumerate(sel):
            mu, lo, hi = [], [], []
            for s_ in splits:
                g = d[(d.split == s_) & (d.K == K) & (d.eps == 0.1) & (d.method == m)]
                p = float(g.p_nomiss.mean())
                ne = max(int(g.n_test.iloc[0]) // K, 1)
                l_, h_ = cp_ci(int(round(p * ne)), ne)
                mu.append(p)
                lo.append(l_)
                hi.append(h_)
            xx = np.arange(len(splits)) + (k - 1.5) * 0.18
            mu, lo, hi = map(np.array, (mu, lo, hi))
            ax.errorbar(xx, mu, yerr=[mu - lo, hi - mu], fmt=mk, ms=2.8, color=c, mec=INK if c != INK2 else c,
                        mew=0.3, ecolor=c if c != LIGHT else MUTED, elinewidth=0.6, capsize=0,
                        label=M.LABEL.get(m, m), zorder=3 if k == 0 else 2)
        ax.axhline(TARGET, color=RED, lw=0.7, ls="--")
        nb = sum(s_.startswith("LOBO") for s_ in splits)
        nd = sum(s_.startswith("LODO") for s_ in splits)
        for b_ in (nb - 0.5, nb + nd - 0.5):
            ax.axvline(b_, color=GRID, lw=0.8)
        ax.set_xticks(range(len(splits)))
        ax.set_xticklabels([s_.split(":")[1] for s_ in splits], fontsize=5.8)
        tr = ax.get_xaxis_transform()
        for c_, t in [((nb - 1) / 2, "block"), (nb + (nd - 1) / 2, "day"), (nb + nd + (len(splits) - nb - nd - 1) / 2,
                                                                          "sequence")]:
            ax.text(c_, -0.16, f"held-out {t}", transform=tr, ha="center", va="top", fontsize=6.0, color=INK)
        ax.set_ylim(0.0, 1.04)
        ax.set_xlim(-0.6, len(splits) - 0.4)
        ax.grid(axis="x", visible=False)
        ax.text(0.02, 0.03, f"K = {K} rows per strip", transform=ax.transAxes, fontsize=6.2, color=INK,
                va="bottom", ha="left")
        if j == 0:
            ax.set_ylabel("P(no missed area)")
            ax.legend(loc="lower left", fontsize=6.0, ncol=4, borderaxespad=0.0, handletextpad=0.3,
                      columnspacing=1.5, bbox_to_anchor=(0.06, 1.1))
        else:
            ax.tick_params(axis="y", labelleft=False)
        panel(ax, "cd"[j], x=0.0, y=1.01)
    a = load("real_aci.csv")
    if a is not None:
        ax = fig.add_subplot(gt[0, 2].subgridspec(2, 1, height_ratios=[0.42, 1.0], hspace=0.0)[1])
        for m, c, lab, ls in [("static (first day)", INK2, "CE, static (calibrated on day 1)", (0, (3, 1.5))),
                              ("ACI (ours, online)", BLUE, "CE + ACI [Gibbs & Candès 2021]", "-")]:
            g = a[(a.method == m) & (a.K == 3)].sort_values("t")
            kk, nn = int(g.err.sum()), len(g)
            ax.step(g.t.values, g.q.values * 100, where="post", color=c, lw=1.1, ls=ls,
                    label=f"{lab}\n{kk}/{nn} strips missed, overlap {g.overlap.mean() * 100:.1f}%")
            mt = g.t.values[g.err.values > 0]
            ax.scatter(mt, np.full(len(mt), 58 if c == BLUE else 54), marker="x", s=12, color=c, lw=0.8, zorder=4)
        ax.text(0.5, 56, "misses:", fontsize=5.6, color=INK2, va="center")
        ax.set_ylim(50, 90)
        ax.set_xlabel("Strip index, day 2 (07-18), K = 3")
        ax.set_ylabel("Erosion q (cm)")
        ax.legend(loc="lower left", fontsize=5.8, borderaxespad=0.0, labelspacing=0.5, handlelength=1.8,
                  bbox_to_anchor=(-0.02, 1.03), title="Online deployment, 34 strips",
                  title_fontsize=6.0, alignment="left")
        panel(ax, "e", x=-0.12, y=1.48)
    h = [Patch(facecolor=MUTED, edgecolor=INK2, lw=0.5, label="K = 3 rows per strip"),
         Patch(facecolor="white", edgecolor=INK2, lw=0.5, label="K = 5 rows per strip"),
         Patch(facecolor=BLUE, edgecolor=INK2, lw=0.5, label="ours (K = 3 dark, K = 5 light)"), target_handle()]
    fig.legend(handles=h, loc="upper center", ncol=4, fontsize=6.2, bbox_to_anchor=(0.5, 1.0), columnspacing=1.2,
               title="(a, b): 300 random calibration/test splits; box = quartiles, whiskers = 5th–95th percentile;"
                     " off scale: mean for K = 3 / K = 5;  (c, d): 95% CP interval on n_test / K strips",
               title_fontsize=6.0)
    save(fig, "fig12_real_robot")


JOBS = [fig_data, fig_coverage, fig_system, fig_stacks, fig_main, fig_cross, fig_sens, fig_drift, fig_ablation,
        fig_real, M.fig_overview, M.fig_validity]

if __name__ == "__main__":
    import traceback
    want = set(sys.argv[1:])
    for f in JOBS:
        if want and f.__name__ not in want:
            continue
        try:
            f()
            print("ok", f.__name__)
        except Exception:
            traceback.print_exc()
            print("FAILED", f.__name__)
