"""Method figures: framework (four modules with feedback loop) and five-step procedure.
Line icons only (trajectories, swath bands, empirical CDF, decision diamond, field outline).

    python scripts/make_method_figures.py   -> figures/paper/fig_framework.*, fig_workflow.*
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures", "paper")

INK, MUTED, LINE = "#1f2937", "#6b7280", "#9ca3af"
RED = "#dc2626"
ACC = [("#2563eb", "#eef4ff"), ("#0f9488", "#ecfaf7"), ("#c26a06", "#fff7eb"), ("#7c3aed", "#f5f1ff")]
SWATH, SWATH_E = "#c7dbf7", "#2563eb"

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"],
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic",
    "mathtext.bf": "Liberation Sans:bold", "pdf.fonttype": 42, "ps.fonttype": 42})


def rbox(ax, x, y, w, h, fc, ec, lw=0.8, r=1.0, z=2, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                zorder=z, ls=ls))


def arrow(ax, p0, p1, col=INK, lw=0.9, ls="-", ms=7, z=6, cs="arc3"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=ms, color=col, lw=lw, ls=ls, zorder=z,
                                 connectionstyle=cs, shrinkA=0, shrinkB=0))


def icon_runs(ax, x, y, w, h, seed=1, n=3):
    """Planned centrelines (dashed grey) and executed paths (blue)."""
    rng = np.random.default_rng(seed)
    xs = np.linspace(x, x + w, 120)
    for i in range(n):
        y0 = y + h * (i + 0.5) / n
        ax.plot([x, x + w], [y0, y0], color=LINE, lw=0.6, ls=(0, (2.5, 1.5)), zorder=5)
        e = np.convolve(rng.normal(0, 1, 140), np.ones(21) / 21, "valid")[:120]
        e = e / (np.abs(e).max() + 1e-9)
        ax.plot(xs, y0 + 0.16 * h / n * 2 * e, color=SWATH_E, lw=1.0, zorder=6)


def icon_gap(ax, x, y, w, h):
    """Plan view of two adjacent executed swaths with a planned overlap; where they drift apart a missed
    strip (red) opens."""
    xs = np.linspace(x, x + w, 160)
    bump = np.exp(-((xs - (x + 0.6 * w)) / (0.12 * w)) ** 2)
    wig = 0.02 * h * np.sin(xs / w * 9.0)
    lo_top = y + 0.56 * h - 0.20 * h * bump + wig          # upper edge of the lower swath
    hi_bot = y + 0.44 * h + 0.20 * h * bump + wig          # lower edge of the upper swath
    ax.fill_between(xs, y + 0.02 * h + wig, lo_top, color=SWATH, alpha=0.75, lw=0, zorder=4)
    ax.fill_between(xs, hi_bot, y + 0.98 * h + wig, color=SWATH, alpha=0.75, lw=0, zorder=4)
    ax.fill_between(xs, hi_bot, lo_top, where=lo_top > hi_bot, color="#8fb5ea", lw=0, zorder=4.5)
    for e in (y + 0.02 * h + wig, lo_top, hi_bot, y + 0.98 * h + wig):
        ax.plot(xs, e, color=SWATH_E, lw=0.7, zorder=5)
    ax.fill_between(xs, lo_top, hi_bot, where=hi_bot > lo_top, color=RED, lw=0, zorder=6)


def icon_ecdf(ax, x, y, w, h, eps_y=0.8, col="#c26a06"):
    """Empirical CDF of scores; the k*-th order statistic is where the steps cross 1 - eps."""
    s = np.array([0.08, 0.15, 0.2, 0.27, 0.33, 0.38, 0.46, 0.55, 0.66, 0.8])
    n = len(s)
    ax.plot([x, x + w], [y, y], color=INK, lw=0.7, zorder=5)
    ax.plot([x, x], [y, y + h], color=INK, lw=0.7, zorder=5)
    px, py = [x], [y]
    for i, v in enumerate(s):
        xx = x + v * w
        px += [xx, xx]
        py += [py[-1], y + h * (i + 1) / (n + 1)]
    px.append(x + w)
    py.append(py[-1])
    ax.plot(px, py, color=INK, lw=1.0, zorder=6, drawstyle="default")
    k = int(np.ceil((n + 1) * eps_y)) - 1
    xk = x + s[k] * w
    yk = y + h * eps_y
    ax.plot([x, x + w], [yk, yk], color=col, lw=0.8, ls=(0, (3, 2)), zorder=5)
    ax.plot([xk, xk], [y, y + h * (k + 1) / (n + 1)], color=col, lw=0.8, ls=(0, (3, 2)), zorder=5)
    ax.plot(xk, y + h * (k + 1) / (n + 1), "o", ms=3.2, color=col, zorder=7)
    return xk, yk


def diamond(ax, cx, cy, s, txt, ec="#7c3aed", fs=8):
    ax.add_patch(Polygon([(cx - s, cy), (cx, cy + 0.62 * s), (cx + s, cy), (cx, cy - 0.62 * s)], closed=True,
                         fc="white", ec=ec, lw=1.0, zorder=5))
    ax.text(cx, cy, txt, ha="center", va="center", fontsize=fs, zorder=6)


def icon_field(ax, x, y, w, h, n=7):
    """Irregular field outline with evenly spaced pass centrelines and overlap bands."""
    pts = np.array([(0.04, 0.10), (0.96, 0.02), (0.92, 0.88), (0.30, 0.98), (0.02, 0.70)])
    poly = Polygon([(x + a * w, y + b * h) for a, b in pts], closed=True, fc="white", ec=INK, lw=0.9, zorder=5)
    ax.add_patch(poly)
    for i in range(n):
        yy = y + h * (i + 0.5) / n
        band = ax.fill_between([x, x + w], yy + 0.5 * h / n - 0.035 * h, yy + 0.5 * h / n + 0.035 * h,
                               color=SWATH, lw=0, zorder=5.5)
        band.set_clip_path(poly)
        ln, = ax.plot([x, x + w], [yy, yy], color=SWATH_E, lw=0.7, zorder=6)
        ln.set_clip_path(poly)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}), ("tif", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), bbox_inches="tight", pad_inches=0.04, facecolor="white", **kw)
    plt.close(fig)
    print("wrote", name)


def framework():
    fig = plt.figure(figsize=(7.48, 3.75))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 120), ax.set_ylim(0, 60), ax.axis("off")
    fs, fsh = 7.6, 8.4
    yb, yt, hh = 12.0, 53.0, 6.0                          # panel bottom, top, header height
    xs = [19.5, 44.0, 68.5, 93.0]
    w = 21.5
    heads = ["1  Coverage score", "2  Model scale", "3  Conformal calibration", "4  Transfer check"]

    # input column
    ax.text(9.0, yt - 3.0, "Input", ha="center", va="center", fontsize=fsh, fontweight="bold", color=INK)
    rbox(ax, 1.0, 32.0, 16.0, 15.0, "white", LINE)
    icon_runs(ax, 2.6, 39.0, 12.8, 7.2, seed=3)
    ax.text(9.0, 35.2, "Logged runs\n(independent\npositioning)", ha="center", va="center", fontsize=fs - 0.8,
            linespacing=1.1, color=INK)
    rbox(ax, 1.0, 14.0, 16.0, 16.5, "white", LINE)
    poly = [(3.0, 21.0), (12.5, 20.2), (15.2, 26.8), (8.0, 29.0), (3.6, 27.2)]
    ax.add_patch(Polygon(poly, closed=True, fc="#f3f7ee", ec="#4d7c0f", lw=0.9, zorder=4))
    for k in range(3):
        xx = np.linspace(4.0, 14.0, 40)
        ax.plot(xx, 22.6 + 1.6 * k + 0.4 * np.sin(xx * 1.1 + k), color="#84a35a", lw=0.5, zorder=5)
    ax.text(9.0, 16.9, "Field boundary, terrain,\nGNSS grade, controller", ha="center", va="center",
            fontsize=fs - 0.8, linespacing=1.1, color=INK)

    # module panels
    for i, x0 in enumerate(xs):
        acc, tint = ACC[i]
        rbox(ax, x0, yb, w, yt - yb, tint, acc, lw=0.9, r=1.2)
        rbox(ax, x0, yt - hh, w, hh, acc, acc, lw=0.9, r=1.2, z=3)
        ax.add_patch(plt.Rectangle((x0, yt - hh), w, 1.5, fc=acc, ec="none", zorder=3))
        ax.text(x0 + w / 2, yt - hh / 2, heads[i], ha="center", va="center", fontsize=fsh - 0.4, color="white",
                fontweight="bold", zorder=4)
    cx = [x0 + w / 2 for x0 in xs]

    def card(i, y, h, title=None, body=None, fsb=fs):
        rbox(ax, xs[i] + 1.3, y, w - 2.6, h, "white", ACC[i][0], lw=0.6, r=0.8, z=3)
        if title and body:
            ax.text(cx[i], y + h - 1.9, title, ha="center", va="center", fontsize=fs - 0.6, color=MUTED, zorder=5)
            ax.text(cx[i], y + (h - 2.6) / 2 + 0.2, body, ha="center", va="center", fontsize=fsb, color=INK, zorder=5)
        elif body:
            ax.text(cx[i], y + h / 2, body, ha="center", va="center", fontsize=fsb, color=INK, zorder=5)

    # module 1
    card(0, 34.0, 11.5)
    icon_gap(ax, xs[0] + 2.8, 35.2, w - 9.0, 9.2)
    ax.text(xs[0] + w - 2.0, 39.8, "missed\nstrip", ha="right", va="center", fontsize=fs - 1.4, color=RED, zorder=7,
            linespacing=1.0)
    card(0, 24.5, 7.5, "covering radius", r"$r^\star(x)\leq w/2$ ?")
    card(0, 14.5, 8.0, "coverage score of a run", r"$S=\lambda_\mathrm{ref}+\max_x[r^\star(x)-w/2]$", fsb=fs - 0.6)
    # module 2
    lev = [("L1  linearised loop", r"$\mathbf{P}_{t+1}=\mathbf{A}_t\mathbf{P}_t\mathbf{A}_t^{\top}+\mathbf{B}_t\mathbf{B}_t^{\top}$"),
           ("L2  Kac–Rice exceedance", r"$\mu_j(t\,|\,C)$"),
           ("L3  product over pairs", r"$\hat q_f=F_\pi^{-1}(1-\varepsilon)$")]
    for k, (tt, bb) in enumerate(lev):
        y0 = 37.0 - 9.0 * k
        card(1, y0, 7.6, tt, bb)
        if k < 2:
            arrow(ax, (cx[1], y0), (cx[1], y0 - 1.4), col=ACC[1][0], ms=5)
    ax.text(cx[1], 15.6, "or: Monte Carlo twin", ha="center", va="center", fontsize=fs - 0.8, color=MUTED)
    # module 3
    card(2, 34.0, 11.5)
    xk, yk = icon_ecdf(ax, xs[2] + 3.2, 35.3, w - 6.8, 8.6)
    ax.text(xs[2] + 2.6, yk, r"$1-\varepsilon$", ha="left", va="bottom", fontsize=fs - 1.2, color=ACC[2][0], zorder=7)
    ax.text(xk + 0.4, 35.6, r"$\hat\lambda$", ha="left", va="bottom", fontsize=fs - 0.6, color=ACC[2][0], zorder=7)
    card(2, 24.5, 7.5, "normalise by model scale", r"$V_i=S_i/\hat q_{f_i}$")
    card(2, 14.5, 8.0, "rank (marginal or PAC)", r"$k_\star=\lceil(n+1)(1-\varepsilon)\rceil$", fsb=fs - 0.4)
    # module 4
    rbox(ax, xs[3] + 1.3, 34.0, w - 2.6, 11.5, "white", ACC[3][0], lw=0.6, r=0.8, z=3)
    diamond(ax, cx[3], 39.8, 6.2, r"$\hat\lambda\leq\lambda_\mathrm{ref}$ ?", ec=ACC[3][0])
    ax.text(cx[3] + 0.6, 33.0, "yes", ha="left", va="center", fontsize=fs - 1, color="#15803d")
    arrow(ax, (cx[3], 39.8 - 3.85), (cx[3], 32.0), col="#15803d", ms=5)
    card(3, 24.5, 7.5, "deployed plan", r"$\pi(\hat\lambda)$, spacing $w-2\hat\lambda$")
    card(3, 14.5, 8.0, "miss probability", r"$\leq\kappa\,\varepsilon$ (coupling)")

    # data flow
    ym = 39.8
    yo = 28.25
    arrow(ax, (17.0, 40.0), (xs[0], 40.0))
    for i, lab in enumerate((r"$\{S_i\}$", r"$\{V_i\}$", r"$\hat\lambda$")):
        x0, x1 = xs[i] + w, xs[i + 1]
        if i == 0:                                   # scores skip the model-scale column
            pass
        arrow(ax, (x0, ym), (x1, ym))
        ax.text((x0 + x1) / 2, ym + 0.8, lab, ha="center", va="bottom", fontsize=fs - 0.4)
    ax.plot([17.0, 18.2, 18.2], [22.0, 22.0, 56.5], color=INK, lw=0.9, zorder=5)
    ax.plot([18.2, cx[1]], [56.5, 56.5], color=INK, lw=0.9, zorder=5)
    arrow(ax, (cx[1], 56.5), (cx[1], yt))
    ax.text((18.2 + cx[1]) / 2 + 2, 57.1, "field attributes only (no runs)", ha="center", va="bottom", fontsize=fs - 0.6)
    # output
    xo = xs[3] + w
    arrow(ax, (xs[3] + w - 1.3, yo), (xo + 4.2, yo))
    ax.text(xo + 4.8, yo + 3.4, "Output", ha="left", va="center", fontsize=fsh, fontweight="bold")
    ax.text(xo + 4.8, yo - 2.4, "line spacing\n+ miss\nprobability", ha="left", va="center", fontsize=fs - 0.6,
            linespacing=1.15)
    # feedback loop: from the "no" corner down the inner margin of module 4, then back to the input
    yl = 5.0
    xr = xs[3] + w - 0.65
    dash = dict(color=RED, lw=0.9, ls=(0, (3, 2)), zorder=6)
    ax.plot([cx[3] + 6.2, xr], [39.8, 39.8], **dash)
    ax.text(cx[3] + 6.6, 40.4, "no", ha="left", va="bottom", fontsize=fs - 1, color=RED)
    ax.plot([xr, xr, 9.0], [39.8, yl, yl], **dash)
    arrow(ax, (9.0, yl), (9.0, 14.0), col=RED, ls=(0, (3, 2)), ms=6)
    ax.text(60.0, yl + 0.8, r"transfer check failed: enlarge $\lambda_\mathrm{ref}$, log new runs on the larger "
            "reference plan and recalibrate", ha="center", va="bottom", fontsize=fs - 0.4, color=RED)
    save(fig, "fig_framework")


def workflow():
    fig = plt.figure(figsize=(7.48, 2.55))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 120), ax.set_ylim(0, 41), ax.axis("off")
    fs = 7.6
    xs = [3.0 + i * 23.4 for i in range(5)]
    w, yb, h = 19.6, 8.0, 25.0
    steps = [("Log runs on a\nreference plan", r"plan $\pi(\lambda_\mathrm{ref})$"),
             ("Score each run", r"widest gap $\rightarrow S_i$"),
             ("Take an order\nstatistic", r"$\hat\lambda=S_{(k_\star)}$"),
             ("Transfer check", "yes: go to step 5"),
             ("Deploy", r"spacing $w-2\hat\lambda$")]
    acc = ["#2563eb", "#2563eb", "#c26a06", "#7c3aed", "#7c3aed"]
    for i, (x0, (tt, ff)) in enumerate(zip(xs, steps)):
        rbox(ax, x0, yb, w, h, "white", "#cbd5e1", lw=0.8, r=1.4)
        ax.add_patch(plt.Circle((x0 + 2.6, yb + h - 2.6), 1.7, fc=acc[i], ec="none", zorder=4))
        ax.text(x0 + 2.6, yb + h - 2.6, str(i + 1), ha="center", va="center", color="white", fontsize=fs,
                fontweight="bold", zorder=5)
        ax.text(x0 + 5.2, yb + h - 2.6, tt, ha="left", va="center", fontsize=fs, fontweight="bold", color=INK,
                linespacing=1.05)
        ax.text(x0 + w / 2, yb + 2.4, ff, ha="center", va="center", fontsize=fs - 0.2, color=INK)
        if i < 4:
            arrow(ax, (x0 + w + 0.4, yb + h / 2), (xs[i + 1] - 0.4, yb + h / 2), col=MUTED, ms=7)
    ix, iy, iw, ih = 2.6, 6.0, w - 5.2, 11.5              # icon box offsets inside a card
    icon_runs(ax, xs[0] + ix, yb + iy, iw, ih, seed=7)
    icon_gap(ax, xs[1] + ix, yb + iy + 1.0, iw, ih - 1.0)
    ax.text(xs[1] + ix + 0.6 * iw, yb + iy - 0.4, "missed strip", ha="center", va="top", fontsize=fs - 1.4, color=RED)
    xk, yk = icon_ecdf(ax, xs[2] + ix + 1.0, yb + iy, iw - 1.0, ih)
    ax.text(xs[2] + ix + 0.2, yk + 0.2, r"$1-\varepsilon$", ha="left", va="bottom", fontsize=fs - 1.6, color="#c26a06",
            zorder=8)
    diamond(ax, xs[3] + w / 2, yb + iy + ih / 2, 7.6, r"$\hat\lambda\leq\lambda_\mathrm{ref}$ ?", ec="#7c3aed", fs=fs)
    icon_field(ax, xs[4] + ix + 1.0, yb + iy - 0.5, iw - 2.0, ih + 1.0)
    # recalibration loop
    yl = yb + h + 3.6
    ax.plot([xs[3] + w / 2, xs[3] + w / 2], [yb + h, yl], color=RED, lw=0.9, ls=(0, (3, 2)))
    ax.plot([xs[3] + w / 2, xs[0] + w / 2], [yl, yl], color=RED, lw=0.9, ls=(0, (3, 2)))
    arrow(ax, (xs[0] + w / 2, yl), (xs[0] + w / 2, yb + h), col=RED, ls=(0, (3, 2)), ms=6)
    ax.text((xs[0] + xs[3] + w) / 2, yl + 0.6, r"no: enlarge $\lambda_\mathrm{ref}$ and recalibrate",
            ha="center", va="bottom", fontsize=fs - 0.4, color=RED)
    # phase labels
    for (a, b, lab) in ((xs[0], xs[1] + w, "data: trajectories to scores"),
                        (xs[2], xs[4] + w, "calibration: scores to line spacing")):
        ax.plot([a + 0.5, a + 0.5, b - 0.5, b - 0.5], [yb - 1.2, yb - 2.2, yb - 2.2, yb - 1.2], color=MUTED, lw=0.7)
        ax.text((a + b) / 2, yb - 3.0, lab, ha="center", va="top", fontsize=fs - 0.4, color=MUTED)
    save(fig, "fig_workflow")


if __name__ == "__main__":
    framework()
    workflow()
