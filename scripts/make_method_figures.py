"""Method figures: framework (four modules with a recalibration loop) and the five-step procedure.
Print palette (muted process colours), heavy strokes, line icons only (no bar charts).

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

# print palette: cobalt, sage green, ochre, burgundy (+ light tints), dark ink, firebrick for feedback
INK, GREY, LIGHT = "#222222", "#5a5a5a", "#8c8c8c"
PAL = [("#2b5797", "#e4ecf6"), ("#3a7d44", "#e7f1e8"), ("#b8741a", "#f8efdf"), ("#8b2e3c", "#f4e4e6")]
RED = "#b22222"
SW_F, SW_E = "#b9cde6", "#2b5797"
LW_PANEL, LW_CARD, LW_ICON, LW_ARROW = 1.6, 1.1, 1.4, 1.8

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"],
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans", "mathtext.it": "Liberation Sans:italic",
    "mathtext.bf": "Liberation Sans:bold", "pdf.fonttype": 42, "ps.fonttype": 42})


def rbox(ax, x, y, w, h, fc, ec, lw=LW_CARD, r=1.0, z=2, ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                zorder=z, ls=ls))


def arrow(ax, p0, p1, col=INK, lw=LW_ARROW, ls="-", ms=11, z=6):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=ms, color=col, lw=lw, ls=ls, zorder=z,
                                 shrinkA=0, shrinkB=0, joinstyle="miter", capstyle="butt"))


def chevron(ax, x0, x1, y, h=3.4, col="#4a4a4a"):
    """Solid block arrow from x0 to x1 centred at y."""
    head = min(1.8, 0.55 * (x1 - x0))
    pts = [(x0, y - h / 4), (x1 - head, y - h / 4), (x1 - head, y - h / 2), (x1, y), (x1 - head, y + h / 2),
           (x1 - head, y + h / 4), (x0, y + h / 4)]
    ax.add_patch(Polygon(pts, closed=True, fc=col, ec="none", zorder=6))


def icon_runs(ax, x, y, w, h, seed=1, n=3):
    rng = np.random.default_rng(seed)
    xs = np.linspace(x, x + w, 120)
    for i in range(n):
        y0 = y + h * (i + 0.5) / n
        ax.plot([x, x + w], [y0, y0], color=LIGHT, lw=0.9, ls=(0, (3, 2)), zorder=5)
        e = np.convolve(rng.normal(0, 1, 140), np.ones(21) / 21, "valid")[:120]
        e = e / (np.abs(e).max() + 1e-9)
        ax.plot(xs, y0 + 0.30 * h / n * e, color=SW_E, lw=LW_ICON, zorder=6)


def icon_gap(ax, x, y, w, h):
    """Two adjacent executed swaths with planned overlap; where they drift apart a missed strip opens."""
    xs = np.linspace(x, x + w, 160)
    bump = np.exp(-((xs - (x + 0.6 * w)) / (0.12 * w)) ** 2)
    wig = 0.02 * h * np.sin(xs / w * 9.0)
    lo_top = y + 0.56 * h - 0.20 * h * bump + wig
    hi_bot = y + 0.44 * h + 0.20 * h * bump + wig
    ax.fill_between(xs, y + 0.02 * h + wig, lo_top, color=SW_F, alpha=0.8, lw=0, zorder=4)
    ax.fill_between(xs, hi_bot, y + 0.98 * h + wig, color=SW_F, alpha=0.8, lw=0, zorder=4)
    ax.fill_between(xs, hi_bot, lo_top, where=lo_top > hi_bot, color="#7f9fcb", lw=0, zorder=4.5)
    for e in (y + 0.02 * h + wig, lo_top, hi_bot, y + 0.98 * h + wig):
        ax.plot(xs, e, color=SW_E, lw=1.1, zorder=5)
    ax.fill_between(xs, lo_top, hi_bot, where=hi_bot > lo_top, color=RED, lw=0, zorder=6)


def icon_ecdf(ax, x, y, w, h, q=0.8, col="#b8741a"):
    """Empirical CDF of the scores; the order statistic is where the steps cross 1 - eps."""
    s = np.array([0.08, 0.15, 0.2, 0.27, 0.33, 0.38, 0.46, 0.55, 0.66, 0.8])
    n = len(s)
    ax.plot([x, x + w], [y, y], color=INK, lw=1.0, zorder=5)
    ax.plot([x, x], [y, y + h], color=INK, lw=1.0, zorder=5)
    px, py = [x], [y]
    for i, v in enumerate(s):
        px += [x + v * w, x + v * w]
        py += [py[-1], y + h * (i + 1) / (n + 1)]
    px.append(x + w)
    py.append(py[-1])
    ax.plot(px, py, color=INK, lw=LW_ICON, zorder=6)
    k = int(np.ceil((n + 1) * q)) - 1
    xk, yk = x + s[k] * w, y + h * q
    ax.plot([x, x + w], [yk, yk], color=col, lw=1.1, ls=(0, (3, 2)), zorder=5)
    ax.plot([xk, xk], [y, y + h * (k + 1) / (n + 1)], color=col, lw=1.1, ls=(0, (3, 2)), zorder=5)
    ax.plot(xk, y + h * (k + 1) / (n + 1), "o", ms=4.2, color=col, zorder=7)
    return xk, yk


def diamond(ax, cx, cy, s, txt, ec, fs=8):
    ax.add_patch(Polygon([(cx - s, cy), (cx, cy + 0.62 * s), (cx + s, cy), (cx, cy - 0.62 * s)], closed=True,
                         fc="white", ec=ec, lw=LW_CARD + 0.3, zorder=5))
    ax.text(cx, cy, txt, ha="center", va="center", fontsize=fs, zorder=6, color=INK)


def icon_field(ax, x, y, w, h, n=7):
    pts = np.array([(0.04, 0.10), (0.96, 0.02), (0.92, 0.88), (0.30, 0.98), (0.02, 0.70)])
    poly = Polygon([(x + a * w, y + b * h) for a, b in pts], closed=True, fc="white", ec=INK, lw=LW_ICON, zorder=5)
    ax.add_patch(poly)
    for i in range(n):
        yy = y + h * (i + 0.5) / n
        band = ax.fill_between([x, x + w], yy + 0.5 * h / n - 0.035 * h, yy + 0.5 * h / n + 0.035 * h,
                               color="#7f9fcb", lw=0, zorder=5.5)
        band.set_clip_path(poly)
        ln, = ax.plot([x, x + w], [yy, yy], color=SW_E, lw=1.0, zorder=6)
        ln.set_clip_path(poly)
    ax.add_patch(Polygon([(x + a * w, y + b * h) for a, b in pts], closed=True, fc="none", ec=INK, lw=LW_ICON,
                         zorder=7))


def icon_terrain(ax, x, y, w, h):
    pts = [(x, y + 0.2 * h), (x + 0.78 * w, y), (x + w, y + 0.72 * h), (x + 0.42 * w, y + h), (x + 0.05 * w, y + 0.86 * h)]
    ax.add_patch(Polygon(pts, closed=True, fc="#eef4ea", ec="#3a7d44", lw=LW_ICON, zorder=4))
    for k in range(3):
        xx = np.linspace(x + 0.1 * w, x + 0.9 * w, 40)
        ax.plot(xx, y + (0.32 + 0.2 * k) * h + 0.05 * h * np.sin(xx * 1.1 + k), color="#6f9a5a", lw=0.9, zorder=5)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}), ("tif", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), bbox_inches="tight", pad_inches=0.04, facecolor="white", **kw)
    plt.close(fig)
    print("wrote", name)


def framework():
    fig = plt.figure(figsize=(7.48, 3.5))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 120), ax.set_ylim(10.5, 66.5), ax.axis("off")
    fs, fsh = 7.8, 8.6
    yb, yt, hh = 12.0, 53.0, 6.2
    xs = [19.5, 44.0, 68.5, 93.0]
    w = 21.5
    heads = ["1  Coverage score", "2  Model scale", "3  Conformal calibration", "4  Transfer check"]

    # input column
    ax.text(10.0, yt - 3.0, "Input", ha="center", va="center", fontsize=fsh + 0.4, fontweight="bold", color=INK)
    rbox(ax, 1.0, 32.0, 16.0, 15.0, "white", GREY, lw=LW_CARD)
    icon_runs(ax, 2.6, 39.0, 12.8, 7.2, seed=3)
    ax.text(9.0, 35.2, "Logged runs\n(independent\npositioning)", ha="center", va="center", fontsize=fs - 0.8,
            linespacing=1.1, color=INK)
    rbox(ax, 1.0, 14.0, 16.0, 16.5, "white", GREY, lw=LW_CARD)
    icon_terrain(ax, 3.0, 20.6, 12.0, 8.4)
    ax.text(9.0, 16.9, "Field boundary, terrain,\nGNSS grade, controller", ha="center", va="center",
            fontsize=fs - 1.0, linespacing=1.1, color=INK)

    # module panels with solid header bars
    for i, x0 in enumerate(xs):
        acc, tint = PAL[i]
        rbox(ax, x0, yb, w, yt - yb, tint, acc, lw=LW_PANEL, r=1.2)
        rbox(ax, x0, yt - hh, w, hh, acc, acc, lw=LW_PANEL, r=1.2, z=3)
        ax.add_patch(plt.Rectangle((x0, yt - hh), w, 1.6, fc=acc, ec=acc, lw=LW_PANEL, zorder=3))
        ax.text(x0 + w / 2, yt - hh / 2, heads[i], ha="center", va="center", fontsize=fsh - 0.3, color="white",
                fontweight="bold", zorder=4)
    cx = [x0 + w / 2 for x0 in xs]

    def card(i, y, h, title=None, body=None, fsb=fs):
        rbox(ax, xs[i] + 1.3, y, w - 2.6, h, "white", PAL[i][0], lw=LW_CARD, r=0.8, z=3)
        if title:
            ax.text(cx[i], y + h - 1.9, title, ha="center", va="center", fontsize=fs - 0.6, color=PAL[i][0],
                    fontweight="bold", zorder=5)
        if body:
            ax.text(cx[i], y + (h - 2.6) / 2 + 0.2 if title else y + h / 2, body, ha="center", va="center",
                    fontsize=fsb, color=INK, zorder=5)

    # module 1
    card(0, 34.0, 11.5)
    icon_gap(ax, xs[0] + 2.8, 35.2, w - 9.0, 9.2)
    ax.text(xs[0] + w - 2.0, 39.8, "missed\nstrip", ha="right", va="center", fontsize=fs - 1.4, color=RED, zorder=7,
            linespacing=1.0, fontweight="bold")
    card(0, 24.5, 7.5, "covering radius", r"$r^\star(x)\leq w/2$ ?")
    card(0, 14.5, 8.0, "coverage score", r"$S=\lambda_\mathrm{ref}+\max_x[r^\star(x)-w/2]$", fsb=fs - 0.7)
    # module 2
    lev = [("L1  linearised loop", r"$\mathbf{P}_{t+1}=\mathbf{A}_t\mathbf{P}_t\mathbf{A}_t^{\top}+\mathbf{B}_t\mathbf{B}_t^{\top}$"),
           ("L2  Kac–Rice bound", r"$\mu_j(t\,|\,C)$"),
           ("L3  product over pairs", r"$\hat q_f=F_\pi^{-1}(1-\varepsilon)$")]
    for k, (tt, bb) in enumerate(lev):
        y0 = 37.0 - 9.0 * k
        card(1, y0, 7.6, tt, bb)
        if k < 2:
            arrow(ax, (cx[1], y0), (cx[1], y0 - 1.4), col=PAL[1][0], ms=7, lw=1.4)
    ax.text(cx[1], 15.6, "or: Monte Carlo twin", ha="center", va="center", fontsize=fs - 0.8, color=GREY,
            style="italic")
    # module 3
    card(2, 34.0, 11.5)
    xk, yk = icon_ecdf(ax, xs[2] + 3.4, 35.4, w - 7.0, 8.4)
    ax.text(xs[2] + 2.5, yk, r"$1-\varepsilon$", ha="left", va="bottom", fontsize=fs - 1.2, color=PAL[2][0], zorder=7)
    ax.text(xk + 0.5, 35.7, r"$\hat\lambda$", ha="left", va="bottom", fontsize=fs - 0.4, color=PAL[2][0], zorder=7)
    card(2, 24.5, 7.5, "scale-free ratio", r"$V_i=S_i/\hat q_{f_i}$")
    card(2, 14.5, 8.0, "rank: marginal / PAC", r"$k_\star=\lceil(n+1)(1-\varepsilon)\rceil$", fsb=fs - 0.4)
    # module 4
    rbox(ax, xs[3] + 1.3, 34.0, w - 2.6, 11.5, "white", PAL[3][0], lw=LW_CARD, r=0.8, z=3)
    diamond(ax, cx[3], 39.8, 6.2, r"$\hat\lambda\leq\lambda_\mathrm{ref}$ ?", ec=PAL[3][0])
    ax.text(cx[3] + 0.7, 33.0, "yes", ha="left", va="center", fontsize=fs - 0.8, color="#2f6b38", fontweight="bold")
    arrow(ax, (cx[3], 39.8 - 3.85), (cx[3], 32.0), col="#2f6b38", ms=8, lw=1.5)
    card(3, 24.5, 7.5, "deployed plan", r"$\pi(\hat\lambda)$, spacing $w-2\hat\lambda$")
    card(3, 14.5, 8.0, "miss probability", r"$\leq\kappa\,\varepsilon$  (coupling)")

    # data flow
    ym, yo = 39.8, 28.25
    arrow(ax, (17.0, ym), (xs[0] - 0.1, ym))
    for i, lab in enumerate((r"$\{S_i\}$", r"$\{V_i\}$", r"$\hat\lambda$")):
        x0, x1 = xs[i] + w, xs[i + 1]
        arrow(ax, (x0 + 0.1, ym), (x1 - 0.1, ym))
        ax.text((x0 + x1) / 2, ym + 1.0, lab, ha="center", va="bottom", fontsize=fs)
    ax.plot([17.0, 18.3, 18.3], [22.0, 22.0, 57.0], color=INK, lw=LW_ARROW, zorder=5, solid_joinstyle="miter")
    ax.plot([18.3, cx[1]], [57.0, 57.0], color=INK, lw=LW_ARROW, zorder=5)
    arrow(ax, (cx[1], 57.0), (cx[1], yt + 0.1))
    ax.text((18.3 + cx[1]) / 2 + 2, 57.7, "field attributes only (no runs)", ha="center", va="bottom", fontsize=fs - 0.4)
    # output
    xo = xs[3] + w
    arrow(ax, (xs[3] + w - 1.3, yo), (xo + 4.4, yo))
    ax.text(xo + 4.9, yo + 3.5, "Output", ha="left", va="center", fontsize=fsh + 0.4, fontweight="bold")
    ax.text(xo + 4.9, yo - 2.6, "line spacing\n+ miss\nprobability", ha="left", va="center", fontsize=fs - 0.6,
            linespacing=1.15)
    # recalibration loop: "no" exit -> right of module 4 -> over the top -> back into the run input
    yl = 62.0
    xr = xs[3] + w + 2.2
    dash = dict(color=RED, lw=LW_ARROW, ls=(0, (4, 2.5)), zorder=6)
    ax.plot([cx[3] + 6.2, xr, xr, 4.0, 4.0], [39.8, 39.8, yl, yl, 50.5], **dash)
    arrow(ax, (4.0, 50.5), (4.0, 47.1), col=RED, ls=(0, (4, 2.5)), ms=11)
    ax.text(cx[3] + 6.6, 40.5, "no", ha="left", va="bottom", fontsize=fs - 0.8, color=RED, fontweight="bold")
    ax.text(70.0, yl + 0.8, r"transfer check failed: enlarge $\lambda_\mathrm{ref}$, log new runs on the larger "
            "reference plan and recalibrate", ha="center", va="bottom", fontsize=fs - 0.3, color=RED)
    save(fig, "fig_framework")


def workflow():
    fig = plt.figure(figsize=(7.48, 3.55))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 120), ax.set_ylim(0, 57), ax.axis("off")
    fs = 7.6
    w, gap = 20.4, 3.9
    xs = [1.2 + i * (w + gap) for i in range(5)]
    yb, yt, hh = 16.0, 49.0, 6.6
    cols = [PAL[0][0], PAL[0][0], PAL[2][0], PAL[3][0], PAL[1][0]]
    tints = [PAL[0][1], PAL[0][1], PAL[2][1], PAL[3][1], PAL[1][1]]
    heads = ["Log reference\nruns", "Score each run", "Order statistic", "Transfer check", "Deploy"]
    notes = [["generous margin $\\lambda_\\mathrm{ref}$", "implement positioned", "independently"],
             ["covering radius on", "every 1 m section;", "$S\\leq\\lambda_\\mathrm{ref}\\Leftrightarrow$ no miss"],
             ["$k_\\star$-th smallest score;", "PAC: binomial rank;", "no runs: ratio to $\\hat q_f$"],
             ["deployed plan must not", "add passes; otherwise", "re-log and recalibrate"],
             ["spacing $w-2\\hat\\lambda$ to the", "guidance terminal;", "$\\Pr[\\mathrm{miss}]\\leq\\varepsilon$"]]
    outs = [r"$n$ runs $\{e_k(x)\}$", r"scores $S_1,\dots,S_n$", r"margin $\hat\lambda$", r"accepted $\hat\lambda$",
            r"line spacing"]
    for i, x0 in enumerate(xs):
        rbox(ax, x0, yb, w, yt - yb, tints[i], cols[i], lw=LW_PANEL, r=1.2)
        rbox(ax, x0, yt - hh, w, hh, cols[i], cols[i], lw=LW_PANEL, r=1.2, z=3)
        ax.add_patch(plt.Rectangle((x0, yt - hh), w, 1.6, fc=cols[i], ec=cols[i], lw=LW_PANEL, zorder=3))
        ax.add_patch(plt.Circle((x0 + 3.0, yt - hh / 2), 2.0, fc="white", ec="none", zorder=4))
        ax.text(x0 + 3.0, yt - hh / 2, str(i + 1), ha="center", va="center", color=cols[i], fontsize=fs + 0.8,
                fontweight="bold", zorder=5)
        ax.text(x0 + 5.8, yt - hh / 2, heads[i], ha="left", va="center", fontsize=fs + 0.2, fontweight="bold",
                color="white", linespacing=1.0, zorder=5)
        rbox(ax, x0 + 1.2, 28.2, w - 2.4, 13.4, "white", cols[i], lw=LW_CARD, r=0.8, z=3)
        for k, t in enumerate(notes[i]):
            ax.text(x0 + w / 2, 25.6 - 2.9 * k, t, ha="center", va="center", fontsize=fs - 0.9, color=INK, zorder=5)
        if i < 4:
            chevron(ax, x0 + w + 0.5, xs[i + 1] - 0.5, 35.0)
        # output tag under each step
        rbox(ax, x0 + 1.2, 8.4, w - 2.4, 4.6, "white", GREY, lw=1.0, r=2.2, z=3)
        ax.text(x0 + w / 2, 10.7, outs[i], ha="center", va="center", fontsize=fs - 0.7, color=INK, zorder=5)
        ax.plot([x0 + w / 2, x0 + w / 2], [yb, 13.0], color=GREY, lw=1.0, zorder=2)
    # icons (inside the white card, y 28.2-41.6)
    icon_runs(ax, xs[0] + 2.6, 29.6, w - 5.2, 10.6, seed=7)
    icon_gap(ax, xs[1] + 2.6, 29.6, w - 5.2, 10.6)
    xk, yk = icon_ecdf(ax, xs[2] + 5.4, 29.6, w - 8.2, 10.6)
    ax.text(xs[2] + 5.0, yk, r"$1-\varepsilon$", ha="right", va="center", fontsize=fs - 1.6, color=PAL[2][0], zorder=8)
    diamond(ax, xs[3] + w / 2, 34.9, 7.8, r"$\hat\lambda\leq\lambda_\mathrm{ref}$ ?", ec=PAL[3][0], fs=fs + 0.2)
    icon_field(ax, xs[4] + 3.0, 29.4, w - 6.0, 11.4)
    # recalibration loop (no) from step 4 back to step 1, above the headers
    yl = 54.0
    dash = dict(color=RED, lw=LW_ARROW, ls=(0, (4, 2.5)), zorder=6)
    ax.plot([xs[3] + w / 2, xs[3] + w / 2, xs[0] + w / 2], [yt, yl, yl], **dash)
    arrow(ax, (xs[0] + w / 2, yl), (xs[0] + w / 2, yt + 0.1), col=RED, ls=(0, (4, 2.5)), ms=11)
    ax.text((xs[0] + xs[3] + w) / 2, yl + 0.7, r"no: enlarge $\lambda_\mathrm{ref}$, re-log and recalibrate",
            ha="center", va="bottom", fontsize=fs, color=RED, fontweight="bold")
    # phase brackets
    for (a, b, lab) in ((xs[0], xs[1] + w, "field data → coverage scores"),
                        (xs[2], xs[4] + w, "coverage scores → calibrated line spacing")):
        ax.plot([a + 0.5, a + 0.5, b - 0.5, b - 0.5], [6.4, 5.2, 5.2, 6.4], color=GREY, lw=1.2)
        ax.text((a + b) / 2, 4.2, lab, ha="center", va="top", fontsize=fs, color=GREY, fontweight="bold")
    save(fig, "fig_workflow")


if __name__ == "__main__":
    framework()
    workflow()
