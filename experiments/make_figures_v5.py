"""v5 publication figures (real NOAA CORS GNSS error bank; system-level comparison).

Reuses the style of make_figures2 and replaces the figures whose inputs changed in v5:
  fig2_data       fields, slopes, REAL multi-station GNSS error tails per receiver grade, real robot passes
  fig3_system     forest plot: every published system x 3 regimes, P(no miss) per field + pooled CI,
                  extra overlap paid relative to the per-field oracle (regret)
  fig4_frontier   reliability-cost summary per regime: share of fields meeting the target vs regret
  fig5_main       E2 margin layers on one stack (BCD + LQR-I), 60 + 60 fields
  fig8_sens       controllers, roll compensation, implement width, receiver grade
  fig10_ablation  ablation in three regimes
Usage: python3 experiments/make_figures_v5.py
"""
import math
import os

import numpy as np
import pandas as pd
from scipy.stats import binomtest

import make_figures2 as M
from make_figures2 import (AQUA, BLUE, GRID, INK, INK2, MUTED, ORANGE, RED, VIOLET, YELLOW, MAGENTA, GREEN,
                           cp_ci, load, panel, plt, save)

HERE = os.path.dirname(os.path.abspath(__file__))
N_TEST_SYS = 200
FAMILIES = ["industry", "planner", "controller", "robust", "model-based", "learning", "conformal",
            "chance-rule", "ours"]
FAM_LABEL = {"industry": "Industry practice", "planner": "Coverage planners", "controller": "Path-tracking controllers",
             "robust": "Robust (tube MPC)", "model-based": "Model-based chance constr.", "learning": "Learning-based",
             "conformal": "Conformal (published)", "chance-rule": "Scalar chance rules", "ours": "Ours: CE layer"}
FAM_COLOR = {"industry": "#8a8984", "planner": ORANGE, "controller": YELLOW, "robust": VIOLET,
             "model-based": MAGENTA, "learning": GREEN, "conformal": RED, "chance-rule": "#9d9c94", "ours": BLUE}
SHORT = [  # (substring, short label) in order of precedence
    ("BCD + LQR-I + spec overlap", "BCD + LQR-I, vendor-spec overlap"),
    ("BCD + LQR-I + farmer-tuned", "BCD + LQR-I, farmer-tuned overlap"),
    ("vendor terrain comp. + spec", "Vendor terrain-comp. autosteer, spec overlap"),
    ("vendor terrain comp. + farmer", "Vendor terrain-comp. autosteer, farmer-tuned"),
    ("Fields2Cover (opt. heading)", "Fields2Cover [Mier 2023], spec overlap"),
    ("Hameed 3D terrain spacing (0", "3D terrain spacing [Hameed 2016]"),
    ("Hameed 3D terrain spacing +", "3D terrain spacing [Hameed 2016], spec overlap"),
    ("Follow-previous-pass guidance", "Follow-previous-pass guidance, spec overlap"),
    ("Lenain sideslip-observer ctrl", "Sideslip-observer ctrl [Lenain], spec overlap"),
    ("ESO sliding-mode", "ESO sliding-mode ctrl, spec overlap"),
    ("BCD + offset-free MPC + spec", "Offset-free MPC [Pannocchia], spec overlap"),
    ("Tube-MPC radius margin (W99)", "Tube MPC [Mayne 2005], 99% disturbance set"),
    ("Tube-MPC radius margin (Wmax)", "Tube MPC [Mayne 2005], max disturbance set"),
    ("Gaussian belief, pointwise", "Gaussian belief space, pointwise"),
    ("Gaussian belief, Rice", "Gaussian belief space, Rice extreme value"),
    ("Model-based MC chance", "Model-based Monte-Carlo chance constr."),
    ("GP cautious margin, Bonferroni", "GP cautious margin [Hewing 2020], Bonferroni"),
    ("GP cautious margin", "GP cautious margin [Hewing 2020]"),
    ("pair-level union bound (Lindemann", "Conformal planning [Lindemann 2023], pair-level"),
    ("union bound (Lindemann", "Conformal planning [Lindemann 2023], pointwise"),
    ("Conformal predictive programming", "Conformal predictive programming [Zhao 2024]"),
    ("Scenario approach", "Scenario approach [Campi-Garatti]"),
    ("Gaussian chance constraint", "Gaussian chance constraint"),
    ("Wasserstein DRO-CVaR", "Wasserstein DRO-CVaR"),
    ("BCD + LQR-I + CE", "CE on BCD + LQR-I"),
    ("Fields2Cover + LQR-I + CE", "CE on Fields2Cover + LQR-I"),
    ("Hameed 3D + LQR-I + CE", "CE on 3D terrain spacing + LQR-I"),
    ("Follow-previous-pass + LQR-I + CE", "CE on follow-previous-pass"),
    ("BCD + Lenain ctrl + CE", "CE on BCD + sideslip-observer ctrl"),
    ("BCD + offset-free MPC + CE", "CE on BCD + offset-free MPC"),
]


def short(name):
    for s, lab in SHORT:
        if s in name:
            return lab
    return name


def meets(ps, n_test, target):
    """Per-field one-sided binomial test: not significantly below the target (alpha 0.05)."""
    return np.array([binomtest(int(round(p * n_test)), n_test, target, alternative="less").pvalue >= 0.05
                     for p in ps])


def system_summary(d, target=0.9, n_test=N_TEST_SYS):
    rows = []
    for (rg, sysn, fam), g in d.groupby(["regime", "system", "family"]):
        ok = g.dropna(subset=["p_nomiss"])
        n_inf = len(g) - len(ok)
        if len(ok):
            k = int(round((ok.p_nomiss * n_test).sum()))
            lo, hi = cp_ci(k, n_test * len(ok))
            mt = meets(ok.p_nomiss, n_test, target)
        else:
            lo = hi = np.nan
            mt = np.array([])
        rows.append(dict(regime=rg, system=sysn, family=fam, n_fields=len(g), n_inf=n_inf,
                         p=ok.p_nomiss.mean() if len(ok) else np.nan, lo=lo, hi=hi,
                         meet=(mt.sum() / len(g)) if len(g) else np.nan,  # infeasible fields count as not meeting
                         reg_med=ok.regret_pp.median() if len(ok) else np.nan,
                         reg_q1=ok.regret_pp.quantile(0.25) if len(ok) else np.nan,
                         reg_q3=ok.regret_pp.quantile(0.75) if len(ok) else np.nan,
                         reg_mean=ok.regret_pp.mean() if len(ok) else np.nan,
                         overlap=ok.overlap.mean() * 100 if len(ok) else np.nan))
    return pd.DataFrame(rows)


def _system_order(S):
    """Rows grouped by family (FAMILIES order); within a family by mean overlap over regimes."""
    o = S.groupby(["system", "family"]).overlap.mean().reset_index()
    o["fi"] = o.family.map({f: i for i, f in enumerate(FAMILIES)}).fillna(len(FAMILIES))
    o = o.sort_values(["fi", "overlap"])
    return list(o.system), dict(zip(o.system, o.family))


def fig_system(name="system_v5", target=0.9):
    d = load(f"{name}.csv")
    if d is None:
        return None
    S = system_summary(d, target)
    regs = sorted(d.regime.unique())
    systems, fam = _system_order(S)
    nR = len(systems)
    H = 0.135 * nR + 1.55
    fig = plt.figure(figsize=(7.2, H))
    gs = fig.add_gridspec(1, 2 * len(regs), width_ratios=[1.0, 0.85] * len(regs), wspace=0.12,
                          left=0.33, right=0.995, top=1 - 0.3 / H, bottom=0.95 / H)
    ypos = {s: nR - 1 - i for i, s in enumerate(systems)}
    rng = np.random.default_rng(0)
    for j, rg in enumerate(regs):
        a_p, a_r = fig.add_subplot(gs[0, 2 * j]), fig.add_subplot(gs[0, 2 * j + 1])
        x = d[d.regime == rg]
        Sx = S[S.regime == rg].set_index("system")
        for s in systems:
            y = ypos[s]
            c = FAM_COLOR.get(fam[s], INK2)
            if s not in Sx.index:
                continue
            r = Sx.loc[s]
            g = x[(x.system == s)].dropna(subset=["p_nomiss"])
            if len(g):
                a_p.scatter(g.p_nomiss, y + (rng.random(len(g)) - 0.5) * 0.5, s=1.6, color=c, alpha=0.35, lw=0)
                a_p.plot([r.lo, r.hi], [y, y], color=c, lw=2.0, solid_capstyle="round")
                a_p.scatter([r.p], [y], s=9, color=c, edgecolor="white", lw=0.5, zorder=3)
                a_r.plot([r.reg_q1, r.reg_q3], [y, y], color=c, lw=2.0, solid_capstyle="round", alpha=0.85)
                a_r.scatter([r.reg_med], [y], s=9, color=c, edgecolor="white", lw=0.5, zorder=3)
            if r.n_inf:
                a_r.text(0.99, y, f"{int(r.n_inf)} inf.", transform=a_r.get_yaxis_transform(), ha="right",
                         va="center", fontsize=4.6, color=RED)
        for a_ in (a_p, a_r):
            a_.set_ylim(-0.7, nR - 0.3)
            a_.set_yticks(range(nR))
            a_.set_yticklabels([])
            a_.grid(axis="y", visible=False)
            a_.tick_params(axis="y", length=0)
        a_p.axvline(target, color=RED, lw=0.7, ls="--")
        a_p.set_xlim(-0.03, 1.03)
        a_p.set_xticks([0, 0.5, 0.9])
        a_p.set_xticklabels(["0", "0.5", "0.9"])
        a_r.axvline(0, color=INK2, lw=0.6)
        a_r.set_xscale("symlog", linthresh=1.0)
        a_r.set_xlim(-20, 400)
        a_r.set_xticks([-10, -1, 0, 1, 10, 100])
        a_r.set_xticklabels(["−10", "−1", "0", "1", "10", "100"])
        a_p.set_xlabel("P(no missed area)", fontsize=6.2)
        a_r.set_xlabel("Extra overlap vs\noracle (pp, symlog)", fontsize=6.2)
        nf = x.field.nunique()
        a_p.set_title(f"{rg}  ({nf} fields)", loc="left", fontsize=6.8, x=0.0)
        if j == 0:
            a_p.set_yticklabels([short(s) for s in systems[::-1]], fontsize=5.6)  # tick y = nR-1-i
            # colour row labels by family
            for t, yy in zip(a_p.get_yticklabels(), range(nR)):
                s = systems[nR - 1 - yy]
                t.set_color(FAM_COLOR.get(fam[s], INK) if fam[s] == "ours" else INK)
                if fam[s] == "ours":
                    t.set_fontweight("bold")
        # shade family blocks
        prev = None
        for s in systems:
            if prev is not None and fam[s] != fam[prev]:
                for a_ in (a_p, a_r):
                    a_.axhline(ypos[s] + 0.5, color=GRID, lw=0.8)
            prev = s
        if fam:
            lo_ours = min(ypos[s] for s in systems if fam[s] == "ours") if any(fam[s] == "ours" for s in systems) else None
            if lo_ours is not None:
                hi_ours = max(ypos[s] for s in systems if fam[s] == "ours")
                for a_ in (a_p, a_r):
                    a_.axhspan(lo_ours - 0.5, hi_ours + 0.5, color="#eaf2fc", zorder=0, lw=0)
    handles = [plt.Line2D([], [], color=FAM_COLOR[f], lw=2.5, label=FAM_LABEL[f]) for f in FAMILIES
               if f in set(fam.values())]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.6, 0.0), fontsize=5.6,
               handlelength=1.4, columnspacing=1.0)
    save(fig, "fig3_system")
    return S


def fig_frontier(S, target=0.9):
    if S is None:
        return
    regs = sorted(S.regime.unique())
    fig, axs = plt.subplots(1, len(regs), figsize=(7.2, 2.6), squeeze=False)
    for j, rg in enumerate(regs):
        ax = axs[0, j]
        x = S[S.regime == rg]
        for _, r in x.iterrows():
            c = FAM_COLOR.get(r.family, INK2)
            mk = "*" if r.family == "ours" else "o"
            xm = r.reg_mean if np.isfinite(r.reg_mean) else np.nan
            ax.scatter(xm, r.meet * 100, marker=mk, s=60 if r.family == "ours" else 18, color=c,
                       edgecolor="white", lw=0.5, zorder=3 if r.family == "ours" else 2, alpha=0.95)
        ax.set_xscale("symlog", linthresh=1.0)
        ax.set_xlim(-20, 400)
        ax.set_xticks([-10, -1, 0, 1, 10, 100])
        ax.set_xticklabels(["−10", "−1", "0", "1", "10", "100"])
        ax.axvline(0, color=INK2, lw=0.6)
        ax.set_ylim(-4, 104)
        ax.axhspan(80, 104, xmin=0, xmax=1, color="#eef8f3", zorder=0, lw=0)
        ax.set_xlabel("Mean extra overlap vs per-field oracle (pp)")
        if j == 0:
            ax.set_ylabel(f"Fields meeting P(no miss) ≥ {target:.1f} (%)")
        ax.set_title(rg, loc="left")
        panel(ax, "abc"[j])
        # annotate the best non-ours competitor (most fields meeting, then least regret) and ours mean
        comp = x[x.family != "ours"].sort_values(["meet", "reg_mean"], ascending=[False, True]).head(1)
        for _, r in comp.iterrows():
            ax.annotate(short(r.system), (r.reg_mean, r.meet * 100), xytext=(6, -14), textcoords="offset points",
                        fontsize=5.2, color=INK2, arrowprops=dict(arrowstyle="-", lw=0.4, color=MUTED))
    handles = [plt.Line2D([], [], ls="", marker="*" if f == "ours" else "o", color=FAM_COLOR[f],
                          ms=7 if f == "ours" else 4.5, label=FAM_LABEL[f]) for f in FAMILIES]
    fig.legend(handles=handles, loc="lower center", ncol=5, bbox_to_anchor=(0.5, -0.1), fontsize=6)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save(fig, "fig4_frontier")


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
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 4.4), gridspec_kw=dict(width_ratios=[1.35, 0.8, 1.35, 0.8]))
    for i, (k, d) in enumerate(ds.items()):
        methods = [m for m in M.ORDER if m in d.method.unique()]
        M.dot_panel(axs[2 * i], axs[2 * i + 1], d, methods, 300)
        axs[2 * i].set_title(f"{'Paddy, hilly' if k == 'paddy' else 'Wheat, plain'}: {d.field.nunique()} real fields",
                             loc="left")
        panel(axs[2 * i], "abcd"[2 * i])
        panel(axs[2 * i + 1], "abcd"[2 * i + 1])
        if i == 1:
            axs[2].set_yticklabels([])
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig5_main")


def fig_data():
    """(a) field locations, (b) slopes, (c) real GNSS error tails per grade (CCDF, 12 CORS pairs), (d) robot."""
    import json

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
    axs[1].set_xlabel("Mean field slope (°), Copernicus DEM")
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
        # Gaussian (Rayleigh) tail with the same rms, for reference
        s = np.sqrt(np.mean(h ** 2) / 2)
        z = np.geomspace(h[k][-1], h[0], 100)
        ax.loglog(z, np.exp(-z ** 2 / (2 * s ** 2)), color=c, lw=0.6, ls=":")
    ax.set_ylim(1e-6, 1.2)
    ax.set_xlim(0.1, 800)
    ax.set_xlabel("Horizontal GNSS error (cm)")
    ax.set_ylabel("P(error > x)")
    ax.legend(loc="lower left", fontsize=5.4)
    ax.text(0.98, 0.97, "12 NOAA CORS pairs × 8 days\ndotted: Gaussian, same rms", transform=ax.transAxes,
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
              ("implement width (m)", "Implement width (m)"), ("GNSS receiver grade", "GNSS receiver grade (CORS)")]
    fig, axs = plt.subplots(1, 4, figsize=(7.2, 2.3))
    for ax, (g, title), l in zip(axs, groups, "abcd"):
        x = d[d.group == g].copy()
        if not len(x):
            continue
        num = pd.to_numeric(x["value"], errors="coerce")
        if num.notna().all():
            x["value"] = num
        agg = x.groupby("value", sort=False).agg(p=("p_nomiss", "mean"), ov=("overlap", "mean"), q=("q", "mean"),
                                                 p0=("nominal_p_nomiss", "mean"))
        labels = [str(v).replace("pure_pursuit", "Pure pursuit").replace("stanley", "Stanley")
                  .replace("lqr_i", "LQR-I").replace("lqr", "LQR").replace("rtk_fix", "RTK fix")
                  .replace("rtk_float", "RTK float").replace("dgps", "DGPS") for v in agg.index]
        xx = np.arange(len(agg))
        ax.bar(xx, agg.ov * 100, color=BLUE, width=0.6, edgecolor="white")
        for i, (p, ov) in enumerate(zip(agg.p, agg.ov)):
            ax.text(i, ov * 100, f"{p:.2f}", ha="center", va="bottom", fontsize=5.6, color=INK)
        ax.set_yscale("log")
        ax.set_xticks(xx)
        ax.set_xticklabels(labels, rotation=25, ha="right")
        ax.set_title(title, loc="left")
        ax.grid(axis="x", visible=False)
        panel(ax, l)
    axs[0].set_ylabel("Certified overlap (%, log)\nlabels: realised P(no miss)")
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig8_sensitivity")


def fig_ablation():
    sets = [(load("ablation.csv"), "RTK, 3 m"), (load("ablation_hard.csv"), "RTK, wet, 1.5 m"),
            (load("ablation_dgps.csv"), "DGPS, 6 m")]
    sets = [(d, t) for d, t in sets if d is not None]
    if not sets:
        return
    variants = ["full (ours)", "naive calibration (no fixed point)", "absolute-error score", "pointwise quantile (no sup)"]
    colors = [BLUE, YELLOW, MAGENTA, MUTED]
    cols = []
    for d, t in sets:
        for kind in ("paddy", "wheat"):
            if (d.kind == kind).any():
                cols.append((d[d.kind == kind], f"{kind}, {t}"))
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.4))
    xx = np.arange(len(cols))
    bw = 0.2
    for j, (v, c) in enumerate(zip(variants, colors)):
        for i, (g0, _) in enumerate(cols):
            g = g0[g0.variant == v].dropna(subset=["p_nomiss"])
            if not len(g):
                continue
            for ax, val, se in [(axs[0], g.p_nomiss.mean(), g.p_nomiss.std() / math.sqrt(len(g))),
                                (axs[1], g.overlap.mean() * 100, g.overlap.std() * 100 / math.sqrt(len(g)))]:
                ax.bar(i + (j - 1.5) * bw, val, width=bw - 0.02, color=c, edgecolor="white",
                       label=v if i == 0 else None)
                ax.errorbar(i + (j - 1.5) * bw, val, yerr=1.96 * se, color=INK, lw=0.6, capsize=1.5)
    axs[0].axhline(0.9, color=RED, lw=0.8, ls="--")
    axs[0].set_ylabel("P(no missed area)")
    axs[1].set_ylabel("Overlap (%, log)")
    axs[1].set_yscale("log")
    for a, l in zip(axs, "ab"):
        a.set_xticks(xx)
        a.set_xticklabels([t for _, t in cols], rotation=15, ha="right")
        a.grid(axis="x", visible=False)
        panel(a, l)
    axs[0].legend(loc="lower left", fontsize=5.6)
    fig.tight_layout()
    save(fig, "fig10_ablation")


if __name__ == "__main__":
    import traceback
    S = None
    try:
        S = fig_system()
        print("ok fig_system")
    except Exception:
        traceback.print_exc()
    for f in (lambda: fig_frontier(S), fig_main, fig_data, fig_sens, fig_ablation, M.fig_overview, M.fig_real,
              M.fig_validity, M.fig_cross, M.fig_aci):
        try:
            f()
            print("ok", getattr(f, "__name__", "fig"))
        except Exception:
            traceback.print_exc()
