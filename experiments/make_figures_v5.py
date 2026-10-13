"""v5 publication figures (real NOAA CORS GNSS error bank; system-level comparison).

Only figure types that are standard in agricultural robotics / coverage-planning / control journals:
coverage maps of real fields, grouped bar charts with 95% CI error bars, box plots, reliability
diagrams, error CDFs and time-series curves. Complete numbers for every system are in the tables
(make_tables.py).
  fig1_overview    method schematic                       (make_figures2.fig_overview)
  fig2_data        fields, slopes, real GNSS error tails (CCDF), real robot passes
  fig3_coverage    coverage map of one real field: industry overlap vs tube MPC vs ours, same run
  fig4_system      grouped bars: representative published systems x 3 regimes (P(no miss), overlap)
  fig5_stacks      paired bars: six planner/controller stacks with spec overlap vs with CE (ours)
  fig6_main        grouped bars: margin rules on BCD + LQR-I, paddy vs wheat (E2)
  fig7_validity    reliability diagram + calibration-size box plot (E1)
  fig8_cross       grouped bars: unseen fields, regional shift (E3)
  fig9_sens        bars: controller, roll compensation, implement width, receiver grade (E4)
  fig10_drift      time series: static vs adaptive conformal under seasonal drift (E6)
  fig11_ablation   grouped bars: ablation in three regimes (E9)
  fig12_real       grouped bars + curve: real orchard robot (CitrusFarm, E8)
Usage: python3 experiments/make_figures_v5.py
"""
import json
import math
import os

import numpy as np
import pandas as pd

import make_figures2 as M
from make_figures2 import (AQUA, BLUE, GRID, INK, INK2, MUTED, ORANGE, RED, VIOLET, YELLOW, MAGENTA, GREEN,
                           cp_ci, load, panel, plt, save)

HERE = os.path.dirname(os.path.abspath(__file__))
N_TEST_SYS = 200
TARGET = 0.9
REG_COLORS = [BLUE, ORANGE, AQUA]

# representative system per published method (all on the default BCD + LQR-I stack unless the method
# is itself a planner / controller); the full list is in the tables
REPRESENTATIVE = [
    ("BCD + LQR-I + spec overlap (2x vendor p2p)", "Vendor-spec overlap"),
    ("BCD + LQR-I + farmer-tuned global overlap", "Farmer-tuned overlap"),
    ("BCD + vendor terrain comp. + spec overlap", "Terrain-comp. autosteer"),
    ("Fields2Cover (opt. heading) + spec overlap", "Fields2Cover [Mier 2023]"),
    ("Hameed 3D terrain spacing + spec overlap", "3D terrain [Hameed 2016]"),
    ("Follow-previous-pass guidance + spec overlap", "Follow previous pass"),
    ("BCD + Lenain sideslip-observer ctrl + spec overlap", "Sideslip observer [Lenain]"),
    ("BCD + offset-free MPC + spec overlap", "Offset-free MPC"),
    ("Tube-MPC radius margin (W99)", "Tube MPC [Mayne 2005]"),
    ("Gaussian belief, Rice extreme-value", "Gaussian belief (Rice)"),
    ("Model-based MC chance constraint", "Monte-Carlo chance constr."),
    ("GP cautious margin (Hewing et al.)", "GP margin [Hewing 2020]"),
    ("Conformal planning, pair-level union bound (Lindemann et al.)", "CP planning [Lindemann 2023]"),
    ("Conformal predictive programming (Zhao et al.)", "CPP [Zhao 2024]"),
    ("Scenario approach (PAC, beta=0.01)", "Scenario approach"),
    ("BCD + LQR-I + CE (ours)", "CE (ours)"),
]
STACKS = [
    ("BCD + LQR-I", "BCD + LQR-I + spec overlap (2x vendor p2p)", "BCD + LQR-I + CE (ours)"),
    ("Fields2Cover\n+ LQR-I", "Fields2Cover (opt. heading) + spec overlap", "Fields2Cover + LQR-I + CE (ours)"),
    ("3D terrain\n+ LQR-I", "Hameed 3D terrain spacing + spec overlap", "Hameed 3D + LQR-I + CE (ours)"),
    ("Follow prev.\npass", "Follow-previous-pass guidance + spec overlap", "Follow-previous-pass + LQR-I + CE (ours)"),
    ("BCD + sideslip\nobserver", "BCD + Lenain sideslip-observer ctrl + spec overlap", "BCD + Lenain ctrl + CE (ours)"),
    ("BCD + offset-\nfree MPC", "BCD + offset-free MPC + spec overlap", "BCD + offset-free MPC + CE (ours)"),
]


# ------------------------------------------------------------------------------------ helpers
def pooled_p(ps, n_test):
    """Mean P(no miss) over fields and the pooled Clopper-Pearson 95% CI."""
    ps = np.asarray(ps, float)
    ps = ps[np.isfinite(ps)]
    if not len(ps):
        return np.nan, np.nan, np.nan
    k = int(round((ps * n_test).sum()))
    lo, hi = cp_ci(k, n_test * len(ps))
    return ps.mean(), lo, hi


def mean_ci(v):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    if not len(v):
        return np.nan, 0.0
    return v.mean(), (1.96 * v.std(ddof=1) / math.sqrt(len(v)) if len(v) > 1 else 0.0)


def grouped_bars(ax, labels, series, ylabel, target=None, ymax=None, fmt="{:.0f}", rot=35, fs=5.8):
    """series: list of (name, color, means, err_lo, err_hi) with err as absolute bounds or None.
    Bars above ymax are cut at ymax and labelled with their value."""
    n, m = len(labels), len(series)
    bw = 0.8 / m
    xx = np.arange(n)
    for j, (nm, c, mu, lo, hi) in enumerate(series):
        mu = np.asarray(mu, float)
        pos = xx + (j - (m - 1) / 2) * bw
        shown = mu if ymax is None else np.minimum(mu, ymax)
        ax.bar(pos, np.nan_to_num(shown), width=bw * 0.92, color=c, edgecolor="white", lw=0.3, label=nm)
        if lo is not None:
            lo_, hi_ = np.asarray(lo, float), np.asarray(hi, float)
            ok = np.isfinite(mu) & np.isfinite(lo_) & np.isfinite(hi_) & (mu <= (np.inf if ymax is None else ymax))
            ax.errorbar(pos[ok], mu[ok], yerr=[mu[ok] - lo_[ok], hi_[ok] - mu[ok]], fmt="none", ecolor=INK,
                        elinewidth=0.5, capsize=1.2, capthick=0.5)
        for p_, v in zip(pos, mu):
            if not np.isfinite(v):
                ax.text(p_, 0.0, "n/a", rotation=90, ha="center", va="bottom", fontsize=4.6, color=INK2)
            elif ymax is not None and v > ymax:
                ax.text(p_, ymax * 1.005, fmt.format(v), rotation=90, ha="center", va="bottom", fontsize=4.6,
                        color=INK)
    if target is not None:
        ax.axhline(target, color=RED, lw=0.7, ls="--")
    ax.set_xticks(xx)
    ax.set_xticklabels(labels, rotation=rot, ha="right" if rot else "center", fontsize=fs)
    ax.set_xlim(-0.6, n - 0.4)
    if ymax is not None:
        ax.set_ylim(0, ymax * 1.12)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)


def _regimes(d):
    return sorted(d.regime.unique())


def _sys_stats(d, systems, n_test=N_TEST_SYS):
    """{regime: (P mean, lo, hi, overlap mean, overlap ci)} arrays over `systems`."""
    out = {}
    for rg in _regimes(d):
        x = d[d.regime == rg]
        P, LO, HI, OV, OC = [], [], [], [], []
        for s in systems:
            g = x[x.system == s]
            p, lo, hi = pooled_p(g.p_nomiss, n_test)
            ov, oc = mean_ci(g.overlap * 100)
            P.append(p); LO.append(lo); HI.append(hi); OV.append(ov); OC.append(oc)
        out[rg] = tuple(np.array(v) for v in (P, LO, HI, OV, OC))
    return out


# ------------------------------------------------------------------------------------ figures
def fig_system(name="system_v5"):
    d = load(f"{name}.csv")
    if d is None:
        return
    reps = [(s, l) for s, l in REPRESENTATIVE if s in set(d.system)]
    systems, labels = [s for s, _ in reps], [l for _, l in reps]
    st = _sys_stats(d, systems)
    regs = _regimes(d)
    fig, axs = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True)
    ser_p = [(rg, REG_COLORS[i], st[rg][0], st[rg][1], st[rg][2]) for i, rg in enumerate(regs)]
    grouped_bars(axs[0], labels, ser_p, "P(no missed area)", target=TARGET)
    axs[0].set_ylim(0, 1.08)
    axs[0].legend(loc="upper left", ncol=3, fontsize=6, bbox_to_anchor=(0, 1.16))
    ser_o = [(rg, REG_COLORS[i], st[rg][3], st[rg][3] - st[rg][4], st[rg][3] + st[rg][4]) for i, rg in enumerate(regs)]
    finite = np.concatenate([st[rg][3][np.isfinite(st[rg][3])] for rg in regs])
    cap = np.percentile(finite, 85) * 1.3 if len(finite) else None
    grouped_bars(axs[1], labels, ser_o, "Overlap ratio (%)", ymax=cap)
    for t in axs[1].get_xticklabels():
        if "ours" in t.get_text():
            t.set_color(BLUE)
            t.set_fontweight("bold")
    panel(axs[0], "a")
    panel(axs[1], "b")
    fig.tight_layout(h_pad=0.6)
    save(fig, "fig4_system")


def fig_stacks(name="system_v5"):
    d = load(f"{name}.csv")
    if d is None:
        return
    regs = _regimes(d)
    stacks = [s for s in STACKS if s[1] in set(d.system) and s[2] in set(d.system)]
    fig, axs = plt.subplots(2, len(regs), figsize=(7.2, 3.9), squeeze=False)
    labels = [s[0] for s in stacks]
    for j, rg in enumerate(regs):
        x = d[d.regime == rg]
        base = _sys_stats(x, [s[1] for s in stacks])[rg]
        ours = _sys_stats(x, [s[2] for s in stacks])[rg]
        grouped_bars(axs[0, j], labels, [("+ vendor-spec overlap", MUTED, base[0], base[1], base[2]),
                                         ("+ CE (ours)", BLUE, ours[0], ours[1], ours[2])],
                     "P(no missed area)" if j == 0 else "", target=TARGET, rot=0, fs=4.6)
        axs[0, j].set_ylim(0, 1.08)
        axs[0, j].set_title(rg, loc="left")
        grouped_bars(axs[1, j], labels, [("+ vendor-spec overlap", MUTED, base[3], base[3] - base[4], base[3] + base[4]),
                                         ("+ CE (ours)", BLUE, ours[3], ours[3] - ours[4], ours[3] + ours[4])],
                     "Overlap ratio (%)" if j == 0 else "", rot=0, fs=4.6)
        panel(axs[0, j], "abc"[j])
        panel(axs[1, j], "def"[j])
    axs[0, 0].legend(loc="center left", fontsize=5.8)
    fig.tight_layout(h_pad=0.8, w_pad=0.5)
    save(fig, "fig5_stacks")


def fig_coverage(name="system_v5", regime=None):
    """Coverage map: one real field, one operation (same random condition) under three margins."""
    import core
    import exp_lib as L
    from shapely import contains_xy
    d = load(f"{name}.csv")
    if d is None:
        return
    import exp_system as ES
    regime = regime or [r for r in _regimes(d) if r.startswith("R1")][0]
    reg = ES.REGIMES.get(regime)
    if reg is None:
        return
    w = reg["w"]
    x = d[d.regime == regime]
    spec = x[x.system == "BCD + LQR-I + spec overlap (2x vendor p2p)"].set_index("field")
    tube = x[x.system == "Tube-MPC radius margin (W99)"].set_index("field")
    ours = x[x.system == "BCD + LQR-I + CE (ours)"].set_index("field")
    cand = [f for f in ours.index if f in spec.index and f in tube.index and np.isfinite(ours.loc[f, "param"])
            and np.isfinite(tube.loc[f, "param"]) and spec.loc[f, "p_nomiss"] < 0.5 and ours.loc[f, "p_nomiss"] >= 0.9]
    if not cand:
        return
    fields = {F.fid: F for F in core.load_fields(reg["kind"], w=w, seed=0)}
    cand = [f for f in cand if f in fields]
    F = min((fields[f] for f in cand), key=lambda F: abs(F.M.area - 2.0e4))  # a ~2 ha field reads well
    methods = [("Vendor-spec overlap", float(spec.loc[F.fid, "param"]), spec.loc[F.fid]),
               ("Tube MPC [Mayne 2005]", float(tube.loc[F.fid, "param"]), tube.loc[F.fid]),
               ("CE (ours)", float(ours.loc[F.fid, "param"]), ours.loc[F.fid])]
    bx0, by0, bx1, by1 = F.P.bounds
    hw = min(max((by1 - by0) / (bx1 - bx0), 0.3), 1.6)  # panel height / width of the field
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.25 * hw + 0.75))
    for ax, (nm, lam, r) in zip(axs, methods):
        ys = core.plan(F, w, lam, lambda f, y: 1.0)
        cond = core.Condition(np.random.default_rng(2024), 1, **ES.cond_kw(reg))
        X, D = core.simulate(F, ys, cond, np.random.default_rng(99))
        ax.fill(*F.P.exterior.xy, color="#f2f1ed", zorder=0)
        ax.plot(*F.M.exterior.xy, color=INK2, lw=0.7, zorder=4)
        for k, y in enumerate(ys):
            ax.fill_between(X[k], y + D[k][0] - w / 2, y + D[k][0] + w / 2, color=BLUE if k % 2 == 0 else AQUA,
                            alpha=0.32, lw=0, zorder=1)
        minx, miny, maxx, maxy = F.M.bounds
        gx = np.arange(minx, maxx, 0.5)
        gy = np.arange(miny, maxy, 0.01)
        cov = np.zeros((len(gy), len(gx)), bool)
        for k, y in enumerate(ys):
            o = core.pass_offsets(X[k], D[k][0:1], gx)[0]
            cov |= (gy[:, None] >= (y + o - w / 2)[None, :]) & (gy[:, None] <= (y + o + w / 2)[None, :])
        GX, GY = np.meshgrid(gx, gy)
        miss = contains_xy(F.M, GX, GY) & ~cov
        jj, ii = np.nonzero(miss.T)
        ax.scatter(gx[jj], gy[ii], s=2.2, color=RED, zorder=3, lw=0)
        ax.set_aspect("equal")
        bx0, by0, bx1, by1 = F.P.bounds
        ax.set_xlim(bx0 - 2, bx1 + 2)
        ax.set_ylim(by0 - 2, by1 + 2)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        area = float(miss.sum()) * 0.5 * 0.01
        ax.set_title(f"{nm}\nmargin {lam*100:.1f} cm, {len(ys)} passes, overlap {r.overlap*100:.1f}%\n"
                     f"this run: missed {area:.1f} m²; 200 runs: P(no miss) = {r.p_nomiss:.2f}",
                     fontsize=5.8, loc="left")
    fig.suptitle(f"Real field #{F.fid} ({F.M.area/1e4:.1f} ha, mean slope {F.z_mean_slope:.1f}°), {regime}; "
                 "red: missed area (markers enlarged)", fontsize=7, x=0.01, ha="left")
    fig.tight_layout(w_pad=0.6, rect=(0, 0, 1, 0.97))
    save(fig, "fig3_coverage")


def fig_main():
    ds = {}
    for k in ("paddy", "wheat"):
        for tag in ("_v5", "_v4", "_v3"):
            d = load(f"main_{k}{tag}.csv")
            if d is not None:
                ds[k] = d
                break
    if len(ds) < 2:
        return
    methods = [m for m in M.ORDER if all(m in d.method.unique() for d in ds.values())]
    labels = [M.LABEL.get(m, m) for m in methods]
    fig, axs = plt.subplots(2, 1, figsize=(7.2, 4.4), sharex=True)
    ser_p, ser_o = [], []
    for (k, d), c in zip(ds.items(), [ORANGE, BLUE]):
        P = [pooled_p(d[d.method == m].p_nomiss, 300) for m in methods]
        O = [mean_ci(d[d.method == m].overlap * 100) for m in methods]
        nm = f"{'Paddy (hilly)' if k == 'paddy' else 'Wheat (plain)'}, {d.field.nunique()} fields"
        ser_p.append((nm, c, [p[0] for p in P], [p[1] for p in P], [p[2] for p in P]))
        ser_o.append((nm, c, [o[0] for o in O], [o[0] - o[1] for o in O], [o[0] + o[1] for o in O]))
    grouped_bars(axs[0], labels, ser_p, "P(no missed area)", target=TARGET)
    axs[0].set_ylim(0, 1.08)
    axs[0].legend(loc="upper left", fontsize=6, ncol=2, bbox_to_anchor=(0, 1.16))
    finite = np.concatenate([np.array(s[2], float) for s in ser_o])
    grouped_bars(axs[1], labels, ser_o, "Overlap ratio (%)", ymax=np.nanpercentile(finite, 85) * 1.3)
    for t in axs[1].get_xticklabels():
        if "ours" in t.get_text():
            t.set_color(BLUE)
            t.set_fontweight("bold")
    panel(axs[0], "a")
    panel(axs[1], "b")
    fig.tight_layout(h_pad=0.6)
    save(fig, "fig6_main")


def fig_cross():
    parts = [x for x in (load("cross2_paddy.csv"), load("cross2_wheat.csv")) if x is not None]
    shift = [x for x in (load("cross.csv"), load("cross_reverse.csv")) if x is not None]
    if not parts:
        return
    d = pd.concat(parts)
    methods = [m for m in M.ORDER if m in d.method.unique()]
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6), gridspec_kw=dict(width_ratios=[1.6, 1.6, 1]))
    for i, (kind, c) in enumerate([("paddy", ORANGE), ("wheat", BLUE)]):
        x = d[d.kind == kind]
        if not len(x):
            continue
        P, O = [], []
        for m in methods:
            per = x[x.method == m].groupby("rep").p_nomiss.mean()
            P.append(mean_ci(per.values))
            O.append(x[x.method == m].overlap.mean() * 100)
        grouped_bars(axs[i], [M.LABEL.get(m, m) for m in methods],
                     [("P(no miss)", c, [p[0] for p in P], [p[0] - p[1] for p in P], [p[0] + p[1] for p in P])],
                     "P(no missed area), unseen fields" if i == 0 else "", target=TARGET, fs=5.2)
        axs[i].set_ylim(0, 1.08)
        for xx, o in enumerate(O):
            axs[i].text(xx, 1.02, f"{o:.0f}%", ha="center", fontsize=4.4, color=INK2)
        axs[i].set_title(f"New {kind} fields (labels: overlap)", loc="left")
        panel(axs[i], "ab"[i])
    if shift:
        s = pd.concat(shift)
        settings = [("in-region", "in-region"), ("shift wheat->paddy", "plain→hilly"), ("shift paddy->wheat", "hilly→plain")]
        ser = []
        for m, c in [("CE-U", BLUE), ("CE-A", AQUA), ("CE-AW (weighted)", VIOLET)]:
            vals = [mean_ci(s[(s.setting == st) & (s.method == m)].groupby("rep").p_nomiss.mean().values)
                    for st, _ in settings]
            ser.append((m, c, [v[0] for v in vals], [v[0] - v[1] for v in vals], [v[0] + v[1] for v in vals]))
        grouped_bars(axs[2], [l for _, l in settings], ser, "", target=TARGET, rot=0, fs=5.6)
        axs[2].set_ylim(0, 1.08)
        axs[2].legend(loc="lower right", fontsize=5.4)
        axs[2].set_title("Regional shift", loc="left")
        panel(axs[2], "c")
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig8_cross")


def fig_data():
    """(a) field locations, (b) slopes, (c) real GNSS error tails per grade (CCDF), (d) robot passes."""
    import core
    meta = json.load(open(os.path.join(HERE, "data", "fields.json")))
    dem = {int(f[:-4]) for f in os.listdir(os.path.join(HERE, "data", "dem"))}
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.2), gridspec_kw=dict(width_ratios=[1.2, 1, 1.15, 1.2]))
    for kind, c in [("paddy", ORANGE), ("wheat", BLUE)]:
        x = [m for j, m in enumerate(meta) if m["kind"] == kind and j in dem]
        axs[0].scatter([m["lon"] for m in x], [m["lat"] for m in x], s=5, color=c, lw=0, alpha=0.8,
                       label=f"{'Paddy (hilly south)' if kind == 'paddy' else 'Wheat (N. China Plain)'}, n={len(x)}")
    axs[0].set_xlabel("Longitude (°E)")
    axs[0].set_ylabel("Latitude (°N)")
    axs[0].set_xlim(108, 122)
    axs[0].set_ylim(23, 41)
    axs[0].legend(loc="lower left", fontsize=5.4, handletextpad=0.2, markerscale=2)
    panel(axs[0], "a")
    sl = {k: [f.z_mean_slope for f in core.load_fields(k)] for k in ("paddy", "wheat")}
    bins = np.linspace(0, 8, 33)
    axs[1].hist(sl["wheat"], bins=bins, color=BLUE, alpha=0.75, label="wheat", edgecolor="white", lw=0.3)
    axs[1].hist(sl["paddy"], bins=bins, color=ORANGE, alpha=0.65, label="paddy", edgecolor="white", lw=0.3)
    axs[1].set_xlabel("Mean field slope (°)")
    axs[1].set_ylabel("Fields")
    axs[1].legend()
    panel(axs[1], "b")
    ax = axs[2]
    for g, c, lab in [("rtk_fix", BLUE, "RTK fix"), ("rtk_float", AQUA, "RTK float"), ("dgps", ORANGE, "DGPS"),
                      ("spp", MUTED, "SPP")]:
        B = core.gnss_bank(g)
        h = np.sort(np.hypot(B["en"], B["ee"]))[::-1] * 100
        p = np.arange(1, len(h) + 1) / len(h)
        k = np.unique(np.geomspace(1, len(h), 400).astype(int)) - 1
        ax.loglog(h[k], p[k], color=c, lw=1.3, label=lab)
        s = np.sqrt(np.mean(h ** 2) / 2)  # Rayleigh tail with the same rms
        z = np.geomspace(h[k][-1], h[0], 100)
        ax.loglog(z, np.exp(-z ** 2 / (2 * s ** 2)), color=c, lw=0.6, ls=":")
    ax.set_ylim(1e-6, 1.2)
    ax.set_xlim(0.1, 800)
    ax.set_xlabel("Horizontal GNSS error (cm)")
    ax.set_ylabel("Exceedance probability")
    ax.legend(loc="lower left", fontsize=5.4)
    ax.text(0.98, 0.97, "NOAA CORS, 12 pairs × 8 days\ndotted: Gaussian, same rms", transform=ax.transAxes,
            ha="right", va="top", fontsize=5.2, color=INK2)
    panel(ax, "c")
    P = np.load(os.path.join(HERE, "data", "citrus_passes.npy"), allow_pickle=True)
    ps = [p for p in P if p["seq"].startswith("05")]
    for p in ps:
        axs[3].plot(p["x"], p["row"] * p["spacing"] + p["e"], color=BLUE if p["dir"] > 0 else AQUA, lw=0.8)
    for k in sorted({p["row"] for p in ps}):
        axs[3].axhline(k * ps[0]["spacing"], color=MUTED, lw=0.5, ls="--", zorder=0)
    axs[3].set_xlabel("Along-row (m)")
    axs[3].set_ylabel("Lateral (m)")
    axs[3].set_title("Real orchard robot passes (CitrusFarm)", fontsize=6.3, loc="left", color=INK2)
    panel(axs[3], "d")
    fig.tight_layout(w_pad=0.9)
    save(fig, "fig2_data")


def fig_sens():
    d = load("sens.csv")
    if d is None:
        return
    groups = [("controller", "Controller"), ("roll compensation", "Roll compensation c"),
              ("implement width (m)", "Implement width (m)"), ("GNSS receiver grade", "GNSS receiver grade")]
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.3))
    for ax, (g, title), l in zip(axs, groups, "abcd"):
        x = d[d.group == g].copy()
        if not len(x):
            continue
        num = pd.to_numeric(x["value"], errors="coerce")
        if num.notna().all():
            x["value"] = num
        agg = x.groupby("value", sort=False).agg(p=("p_nomiss", "mean"), q=("q", "mean"), qs=("q", "std"),
                                                 n=("field", "nunique"))
        labels = [str(v).replace("pure_pursuit", "Pure pursuit").replace("stanley", "Stanley")
                  .replace("lqr_i", "LQR-I").replace("lqr", "LQR").replace("rtk_fix", "RTK fix")
                  .replace("rtk_float", "RTK float").replace("dgps", "DGPS") for v in agg.index]
        xx = np.arange(len(agg))
        ax.bar(xx, agg.q * 100, color=BLUE, width=0.6, edgecolor="white")
        ax.errorbar(xx, agg.q * 100, yerr=1.96 * agg.qs * 100 / np.sqrt(agg.n), fmt="none", ecolor=INK,
                    elinewidth=0.5, capsize=1.5)
        for i, (p, q) in enumerate(zip(agg.p, agg.q)):
            ax.text(i, q * 100 * 1.02, f"{p:.2f}", ha="center", va="bottom", fontsize=5.6, color=INK)
        ax.set_xticks(xx)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_title(title, loc="left")
        ax.set_ylim(0, agg.q.max() * 100 * 1.25)
        ax.grid(axis="x", visible=False)
        panel(ax, l)
    axs[0].set_ylabel("Certified margin q (cm)\nlabels: realised P(no miss)")
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig9_sensitivity")


def fig_ablation():
    sets = [(load("ablation.csv"), "RTK, 3 m"), (load("ablation_hard.csv"), "RTK, wet, 1.5 m"),
            (load("ablation_dgps.csv"), "DGPS, 6 m")]
    sets = [(d, t) for d, t in sets if d is not None]
    if not sets:
        return
    variants = [("full (ours)", "Full method (ours)", BLUE), ("naive calibration (no fixed point)", "No fixed point", YELLOW),
                ("absolute-error score", "Absolute-error score", MAGENTA),
                ("pointwise quantile (no sup)", "Pointwise quantile (no sup)", MUTED)]
    cols = []
    for d, t in sets:
        for kind in ("paddy", "wheat"):
            if (d.kind == kind).any():
                cols.append((d[d.kind == kind], f"{kind}\n{t}"))
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4))
    ser_p, ser_o = [], []
    for v, lab, c in variants:
        P = [mean_ci(g0[g0.variant == v].p_nomiss.values) for g0, _ in cols]
        O = [mean_ci(g0[g0.variant == v].overlap.values * 100) for g0, _ in cols]
        ser_p.append((lab, c, [p[0] for p in P], [p[0] - p[1] for p in P], [p[0] + p[1] for p in P]))
        ser_o.append((lab, c, [o[0] for o in O], [o[0] - o[1] for o in O], [o[0] + o[1] for o in O]))
    grouped_bars(axs[0], [t for _, t in cols], ser_p, "P(no missed area)", target=TARGET, rot=0, fs=5.6)
    axs[0].set_ylim(0, 1.08)
    grouped_bars(axs[1], [t for _, t in cols], ser_o, "Overlap ratio (%)", rot=0, fs=5.6)
    axs[0].legend(loc="lower left", fontsize=5.4)
    panel(axs[0], "a")
    panel(axs[1], "b")
    fig.tight_layout()
    save(fig, "fig11_ablation")


def fig_real():
    d = load("real.csv")
    if d is None:
        return
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.5), gridspec_kw=dict(width_ratios=[1.6, 1.1, 1]))
    x = d[(d.split == "random") & (d.eps == 0.1)]
    methods = [m for m in M.ORDER if m in x.method.unique()]
    ser = []
    for K, c in [(3, BLUE), (5, AQUA)]:
        vals = [x[(x.K == K) & (x.method == m)].p_nomiss.dropna() for m in methods]
        mu = [v.mean() if len(v) else np.nan for v in vals]
        ser.append((f"{K}-row strips", c, mu, [np.percentile(v, 5) if len(v) else np.nan for v in vals],
                    [np.percentile(v, 95) if len(v) else np.nan for v in vals]))
    grouped_bars(axs[0], [M.LABEL.get(m, m) for m in methods], ser, "P(no missed area)", target=TARGET, fs=5.2)
    axs[0].set_ylim(0, 1.08)
    axs[0].legend(loc="lower right", fontsize=5.4)
    axs[0].set_title("Random splits (300×), bars: 5–95%", loc="left")
    sel = [("CE-U (ours, uniform)", BLUE), ("Scenario (Campi-Garatti)", MUTED), ("CVaR (empirical)", INK2),
           ("Gaussian on score", YELLOW)]
    splits = ["LOBO:13B", "LOBO:13D", "LOBO:14B", "LODO:07-16", "LODO:07-18"]
    ser = [(M.LABEL[m], c, [d[(d.split == s_) & (d.K == 3) & (d.eps == 0.1) & (d.method == m)].p_nomiss.mean()
                            for s_ in splits], None, None) for m, c in sel]
    grouped_bars(axs[1], ["13B", "13D", "14B", "07-16", "07-18"], ser, "", target=TARGET, rot=0, fs=5.6)
    axs[1].set_ylim(0.5, 1.05)
    axs[1].set_xlabel("held-out block            held-out day")
    axs[1].legend(loc="lower left", fontsize=5.0)
    axs[1].set_title("Leave-one-block/day-out", loc="left")
    a = load("real_aci.csv")
    if a is not None:
        for m, c in [("static (first day)", ORANGE), ("ACI (ours, online)", BLUE)]:
            g = a[(a.method == m) & (a.K == 3)].sort_values("t")
            axs[2].plot(g.t.values, g.err.expanding().mean().values, color=c, label=m)
        axs[2].axhline(0.1, color=RED, lw=0.8, ls="--")
        axs[2].set_xlabel("Operation strips (chronological)")
        axs[2].set_ylabel("Cumulative miss frequency")
        axs[2].set_title("Online deployment", loc="left")
        axs[2].legend(loc="upper right", fontsize=5.4)
        axs[2].set_ylim(-0.01, 0.35)
    for a_, l in zip(axs, "abc"):
        panel(a_, l)
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig12_real_robot")


def _rename(src, dst):
    for ext in (".png", ".pdf"):
        p = os.path.join(M.FIG, src + ext)
        if os.path.exists(p):
            os.replace(p, os.path.join(M.FIG, dst + ext))


if __name__ == "__main__":
    import traceback
    jobs = [fig_data, fig_coverage, fig_system, fig_stacks, fig_main, fig_cross, fig_sens, fig_ablation, fig_real,
            M.fig_overview, M.fig_validity, M.fig_aci]
    for f in jobs:
        try:
            f()
            print("ok", f.__name__)
        except Exception:
            traceback.print_exc()
    _rename("fig5_validity", "fig7_validity")
    _rename("fig9_drift", "fig10_drift")
