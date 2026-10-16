"""Workflow figure (Fig. 1 EN / 图 2 ZH) in block-diagram style: input boxes, five blue stage
columns with icons drawn from primitives, grey block arrows, output box and grouping braces.

    python scripts/make_workflow_figure.py      -> figures/paper/fig_workflow{,_zh}.{pdf,png,tif}
"""
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures", "paper")

BLUE, BLUE_D, ARROW = "#1f5aa6", "#123d73", "#9a9a9a"
INK, INK2, RED, GREEN, ORANGE = "#1a1a1a", "#4d4d4d", "#d7301f", "#2e7d32", "#e08214"

TXT = {
    "en": dict(
        inp="Input", out="Output",
        in1="Logged runs", in2="Field boundary\n& terrain",
        st=["Stage 1:\nReference\nruns", "Stage 2:\nCoverage\nscore", "Stage 3:\nConformal\ncalibration",
            "Stage 4:\nTransfer\ncheck", "Stage 5:\nDeployed\nplan"],
        s1=r"plan $\pi(\lambda_\mathrm{ref})$" + "\nrecord $e_k(x)$",
        s2=r"$S=\lambda_\mathrm{ref}$" + "\n" + r"$+\max_x\,[r^\star(x)-w/2]$",
        s3a=r"$\hat\lambda=S_{(k_\star)}$", s3b=r"$k_\star=\lceil(n+1)(1-\varepsilon)\rceil$",
        s3c="no records:\n" + r"$V_i=S_i/\hat q_{f_i}$",
        s4=r"$\hat\lambda\leq\lambda_\mathrm{ref}$?", yes="yes", no="no",
        s5a=r"spacing $w-2\hat\lambda$", s5b=r"$\Pr[\mathrm{miss}]\leq\varepsilon$",
        o1="Line spacing\n& miss\nprobability",
        loop="no: recalibrate on a larger reference plan",
        b1="Data: trajectories → coverage scores", b2="Calibration: scores → line spacing",
        gap="gap"),
    "zh": dict(
        inp="输入", out="输出",
        in1="作业记录", in2="田块边界\n与地形",
        st=["阶段1：\n基准规划\n作业", "阶段2：\n覆盖分数\n计算", "阶段3：\n共形\n校准",
            "阶段4：\n推广\n检查", "阶段5：\n实施\n规划"],
        s1="基准规划" + r"$\pi(\lambda_\mathrm{ref})$" + "\n记录轨迹" + r"$e_k(x)$",
        s2=r"$S=\lambda_\mathrm{ref}$" + "\n" + r"$+\max_x\,[r^\star(x)-w/2]$",
        s3a=r"$\hat\lambda=S_{(k_\star)}$", s3b=r"$k_\star=\lceil(n+1)(1-\varepsilon)\rceil$",
        s3c="无记录田块：\n" + r"$V_i=S_i/\hat q_{f_i}$",
        s4=r"$\hat\lambda\leq\lambda_\mathrm{ref}$?", yes="是", no="否",
        s5a="作业行距" + r"$w-2\hat\lambda$", s5b="漏作业概率" + r"$\leq\varepsilon$",
        o1="作业行距\n与漏作业\n概率",
        loop="否：在更大的基准规划上重新校准",
        b1="数据处理：实际轨迹 → 覆盖分数", b2="裕量校准：覆盖分数 → 作业行距",
        gap="漏缝"),
}


def block_arrow(ax, x0, x1, y, h=2.6):
    """Grey chevron block arrow from x0 to x1 centred at y."""
    head = min(1.3, (x1 - x0) * 0.55)
    pts = [(x0, y - h / 4), (x1 - head, y - h / 4), (x1 - head, y - h / 2), (x1, y),
           (x1 - head, y + h / 2), (x1 - head, y + h / 4), (x0, y + h / 4)]
    ax.add_patch(Polygon(pts, closed=True, fc=ARROW, ec="none", zorder=2))


def brace(ax, x0, x1, y, depth=1.4):
    """Horizontal curly brace opening upward, tip pointing down at the centre."""
    t = np.linspace(0, 1, 200)
    xm = (x0 + x1) / 2
    for a, b, s in ((x0, xm, 1), (xm, x1, -1)):
        xs = a + (b - a) * t
        q = t if s == 1 else 1 - t                       # 0 at the outer end, 1 at the tip
        ys = y - depth * (0.5 * (1 - np.cos(np.pi * np.clip(q * 4, 0, 1)))
                          * 0.5 + 0.5 * (1 - np.cos(np.pi * np.clip((q - 0.75) * 4, 0, 1))) * 0.5)
        ax.plot(xs, ys, color=INK, lw=0.9, solid_capstyle="round", zorder=3)


def icon_runs(ax, x, y, w, h, rng):
    """Straight planned passes (dashed) with wavy executed trajectories."""
    xs = np.linspace(x, x + w, 80)
    for i in range(3):
        y0 = y + h * (0.2 + 0.3 * i)
        ax.plot([x, x + w], [y0, y0], color=INK2, lw=0.6, ls=(0, (2, 1.5)), zorder=4)
        e = np.cumsum(rng.normal(0, 1, 80)); e = (e - e.mean()) / (np.abs(e).max() + 1e-9)
        ax.plot(xs, y0 + 0.11 * h * e + 0.05 * h * np.sin(xs * 2.1 + i), color=BLUE, lw=1.1, zorder=5)


def icon_score(ax, x, y, w, h, gap_lbl):
    """Cross-section: executed swaths as bars along the lateral axis, one gap in red."""
    bars = [(0.00, 0.36), (0.30, 0.64), (0.69, 1.00)]
    for i, (a, b) in enumerate(bars):
        yy = y + h * (0.62 - 0.22 * (i % 2))
        ax.add_patch(Rectangle((x + w * a, yy), w * (b - a), h * 0.16, fc="#c9d9ef", ec=BLUE, lw=0.8, zorder=4))
    ax.add_patch(Rectangle((x + w * 0.64, y + h * 0.05), w * 0.05, h * 0.9, fc=RED, ec="none", alpha=0.85, zorder=5))
    ax.plot([x, x + w], [y + h * 0.05, y + h * 0.05], color=INK, lw=0.8, zorder=5)
    ax.text(x + w * 0.665, y + h * 0.98, gap_lbl, ha="center", va="bottom", fontsize=7.5, color=RED)


def icon_sorted(ax, x, y, w, h):
    """Sorted coverage scores; the k*-th order statistic highlighted."""
    n = 9
    v = np.sort(np.array([0.28, 0.35, 0.40, 0.47, 0.52, 0.60, 0.68, 0.80, 0.97]))
    bw = w / n
    for i in range(n):
        c = ORANGE if i == n - 2 else "#c9d9ef"
        ax.add_patch(Rectangle((x + i * bw + 0.08 * bw, y), 0.84 * bw, h * v[i], fc=c,
                               ec=BLUE if i != n - 2 else "#a35a00", lw=0.6, zorder=4))
    yk = y + h * v[n - 2]
    ax.plot([x - 0.2, x + w + 0.2], [yk, yk], color=ORANGE, lw=0.9, ls=(0, (2, 1.2)), zorder=5)
    ax.plot([x, x + w], [y, y], color=INK, lw=0.8, zorder=5)


def icon_decision(ax, cx, cy, s, txt, yes, no, exits=True):
    """Decision diamond with yes (down) and no (up) exits."""
    ax.add_patch(Polygon([(cx - s, cy), (cx, cy + s * 0.75), (cx + s, cy), (cx, cy - s * 0.75)],
                         closed=True, fc="#fff4e5", ec=ORANGE, lw=1.0, zorder=4))
    ax.text(cx, cy, txt, ha="center", va="center", fontsize=8, zorder=5)
    if not exits:
        return
    ax.annotate("", xy=(cx, cy - s * 0.75 - 2.1), xytext=(cx, cy - s * 0.75),
                arrowprops=dict(arrowstyle="-|>", color=GREEN, lw=1.0, mutation_scale=7), zorder=5)
    ax.text(cx + 0.35, cy - s * 0.75 - 1.0, yes, ha="left", va="center", fontsize=7.5, color=GREEN)
    ax.annotate("", xy=(cx, cy + s * 0.75 + 2.1), xytext=(cx, cy + s * 0.75),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.0, mutation_scale=7), zorder=5)
    ax.text(cx + 0.35, cy + s * 0.75 + 1.0, no, ha="left", va="center", fontsize=7.5, color=RED)


def icon_field(ax, x, y, w, h, n=5, overlap=True):
    """Field outline with parallel swaths and overlap bands."""
    ax.add_patch(Rectangle((x, y), w, h, fc="white", ec=INK, lw=0.9, zorder=4))
    sw = w / n
    for i in range(n):
        ax.add_patch(Rectangle((x + i * sw, y), sw, h, fc="#c9d9ef" if i % 2 == 0 else "#dfe8f5",
                               ec="none", zorder=4))
        if overlap and i:
            ax.add_patch(Rectangle((x + i * sw - sw * 0.12, y), sw * 0.24, h, fc="#7fa3d1", ec="none", zorder=5))
        ax.plot([x + (i + 0.5) * sw] * 2, [y + 0.06 * h, y + 0.94 * h], color=BLUE_D, lw=0.6, zorder=6)
    ax.add_patch(Rectangle((x, y), w, h, fc="none", ec=INK, lw=0.9, zorder=7))


def register_cjk_font():
    """Register the Simplified-Chinese face of Noto Sans CJK (matplotlib only reads face 0 of a .ttc)."""
    from matplotlib import font_manager as fm
    cache = os.path.join(os.path.expanduser("~"), ".cache", "cjk_fonts")
    os.makedirs(cache, exist_ok=True)
    for w in ("Regular", "Bold"):
        dst = os.path.join(cache, f"NotoSansCJKsc-{w}.otf")
        if not os.path.exists(dst):
            from fontTools.ttLib import TTCollection
            for f in TTCollection(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{w}.ttc").fonts:
                if f["name"].getDebugName(1) == "Noto Sans CJK SC":
                    f.save(dst)
                    break
        fm.fontManager.addfont(dst)


def draw(lang):
    T = TXT[lang]
    if lang == "zh":
        register_cjk_font()
        plt.rcParams.update({"font.family": "sans-serif",
                             "font.sans-serif": ["Noto Sans CJK SC", "Noto Sans CJK JP", "DejaVu Sans"],
                             "mathtext.fontset": "custom", "mathtext.rm": "Noto Sans CJK SC",
                             "mathtext.it": "DejaVu Sans:italic", "mathtext.bf": "Noto Sans CJK SC:bold",
                             "mathtext.sf": "Noto Sans CJK SC", "axes.unicode_minus": False})
    else:
        plt.rcParams.update({"font.family": "sans-serif",
                             "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"],
                             "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans",
                             "mathtext.it": "Liberation Sans:italic", "mathtext.bf": "Liberation Sans:bold"})
    rng = np.random.default_rng(3)
    fig = plt.figure(figsize=(7.48, 3.15))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 113.5), ax.set_ylim(0, 47.5), ax.axis("off")

    ybot, ytop = 10.5, 39.5                     # stage column extent
    hdr = 30.0                                  # header / inner-panel split
    cw, gapc = 13.2, 3.3
    x0s = [16.6 + i * (cw + gapc) for i in range(5)]
    hd = dict(color="white", ha="center", va="center", fontweight="bold", fontsize=9, linespacing=1.15)

    # input / output headings
    ax.text(7.2, 44.3, T["inp"], ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(x0s[-1] + cw + gapc + 6.6, 44.3, T["out"], ha="center", va="center", fontsize=11, fontweight="bold")

    # input boxes
    for (yb, yt, lab, kind) in ((26.0, 39.5, T["in1"], "runs"), (10.5, 24.0, T["in2"], "field")):
        ax.add_patch(Rectangle((1.0, yb), 12.4, yt - yb, fc=BLUE, ec=BLUE_D, lw=1.2, zorder=2))
        ax.add_patch(Rectangle((2.2, yb + 5.3), 10.0, yt - yb - 6.4, fc="white", ec="none", zorder=3))
        if kind == "runs":
            icon_runs(ax, 2.9, yb + 5.9, 8.6, yt - yb - 7.6, rng)
        else:
            px = [2.9, 9.8, 11.4, 7.6, 3.6]
            py = [yb + 6.2, yb + 5.8, yb + 10.0, yb + 12.2, yb + 10.8]
            ax.add_patch(Polygon(list(zip(px, py)), closed=True, fc="#e6efd9", ec=GREEN, lw=1.0, zorder=4))
            for k in range(3):
                xs = np.linspace(3.6, 10.6, 30)
                ax.plot(xs, yb + 7.4 + 1.5 * k + 0.35 * np.sin(xs * 1.3 + k), color="#7a9a4a", lw=0.5, zorder=5)
        ax.text(7.2, yb + 2.6, lab, ha="center", va="center", color="white", fontweight="bold",
                fontsize=8.5, linespacing=1.1, zorder=4)
        block_arrow(ax, 13.6, x0s[0] - 0.2, (yb + yt) / 2)

    # stage columns
    for i, x0 in enumerate(x0s):
        ax.add_patch(Rectangle((x0, ybot), cw, ytop - ybot, fc=BLUE, ec=BLUE_D, lw=1.2, zorder=2))
        ax.add_patch(Rectangle((x0 + 0.7, ybot + 0.7), cw - 1.4, hdr - ybot - 0.7, fc="white", ec="none", zorder=3))
        ax.text(x0 + cw / 2, (hdr + ytop) / 2 + 0.2, T["st"][i], **hd, zorder=4)
        if i < 4:
            block_arrow(ax, x0 + cw + 0.2, x0s[i + 1] - 0.2, (ybot + hdr) / 2 + 1.0)
    cx = [x + cw / 2 for x in x0s]
    fs = 7.6

    # stage 1: reference runs
    icon_runs(ax, x0s[0] + 1.6, 18.5, cw - 3.2, 9.0, rng)
    ax.text(cx[0], 14.6, T["s1"], ha="center", va="center", fontsize=fs, linespacing=1.35, zorder=5)
    # stage 2: coverage score
    icon_score(ax, x0s[1] + 1.5, 18.8, cw - 3.0, 7.0, T["gap"])
    ax.text(cx[1], 14.2, T["s2"], ha="center", va="center", fontsize=fs, linespacing=1.5, zorder=5)
    # stage 3: conformal calibration
    icon_sorted(ax, x0s[2] + 1.6, 21.3, cw - 3.2, 7.0)
    ax.text(cx[2], 19.3, T["s3a"], ha="center", va="center", fontsize=fs, zorder=5)
    ax.text(cx[2], 16.9, T["s3b"], ha="center", va="center", fontsize=fs - 0.6, zorder=5)
    ax.text(cx[2], 13.3, T["s3c"], ha="center", va="center", fontsize=fs - 0.6, color=INK2,
            linespacing=1.25, zorder=5)
    # stage 4: transfer check
    icon_decision(ax, cx[3], 20.0, 5.2, T["s4"], T["yes"], T["no"])
    # stage 5: deployed plan
    icon_field(ax, x0s[4] + 2.2, 18.6, cw - 4.4, 8.6)
    ax.text(cx[4], 15.6, T["s5a"], ha="center", va="center", fontsize=fs, zorder=5)
    ax.text(cx[4], 12.9, T["s5b"], ha="center", va="center", fontsize=fs, zorder=5)

    # recalibration loop from stage 4 back to stage 1 (above the columns)
    yl = 42.3
    ax.add_patch(FancyArrowPatch((cx[3], ytop + 0.1), (cx[3], yl), arrowstyle="-", color=RED, lw=1.0, zorder=3))
    ax.plot([cx[0], cx[3]], [yl, yl], color=RED, lw=1.0, ls=(0, (3, 1.6)), zorder=3)
    ax.annotate("", xy=(cx[0], ytop + 0.1), xytext=(cx[0], yl),
                arrowprops=dict(arrowstyle="-|>", color=RED, lw=1.0, mutation_scale=8), zorder=3)
    ax.text((cx[0] + cx[3]) / 2, yl + 0.5, T["loop"], ha="center", va="bottom", fontsize=7.8, color=RED)

    # output box
    xo = x0s[-1] + cw + gapc
    block_arrow(ax, x0s[-1] + cw + 0.2, xo - 0.2, (ybot + hdr) / 2 + 1.0)
    ax.add_patch(Rectangle((xo, 16.0), 13.2, 23.5, fc=BLUE, ec=BLUE_D, lw=1.2, zorder=2))
    ax.text(xo + 6.6, 34.2, T["o1"], color="white", ha="center", va="center", fontweight="bold",
            fontsize=8.5, linespacing=1.15, zorder=4)
    ax.add_patch(Rectangle((xo + 1.2, 17.2), 10.8, 11.0, fc="white", ec="none", zorder=3))
    icon_field(ax, xo + 2.0, 18.2, 9.2, 9.0, n=4)
    # spacing dimension line
    sw = 9.2 / 4
    ax.annotate("", xy=(xo + 2.0 + 0.5 * sw, 26.4), xytext=(xo + 2.0 + 1.5 * sw, 26.4),
                arrowprops=dict(arrowstyle="<->", color=RED, lw=0.9, mutation_scale=6), zorder=8)

    # grouping braces and captions
    brace(ax, x0s[0], x0s[1] + cw, ybot - 0.6)
    brace(ax, x0s[2], x0s[4] + cw, ybot - 0.6)
    ax.text((x0s[0] + x0s[1] + cw) / 2, ybot - 3.4, T["b1"], ha="center", va="top", fontsize=8.5)
    ax.text((x0s[2] + x0s[4] + cw) / 2, ybot - 3.4, T["b2"], ha="center", va="top", fontsize=8.5)

    name = "fig_workflow" + ("_zh" if lang == "zh" else "")
    os.makedirs(OUT, exist_ok=True)
    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}), ("tif", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), bbox_inches="tight", pad_inches=0.03,
                    facecolor="white", **kw)
    plt.close(fig)
    print("wrote", name)


FW = {
    "zh": dict(
        inp="输入层", in_runs="多田块作业记录\n（独立定位轨迹）", in_attr="田块边界、地形\nGNSS等级、控制参数",
        m=["模块1：\n覆盖分数构造", "模块2：\n模型尺度归一化", "模块3：\n共形校准", "模块4：\n推广检查与实施"],
        m1b="覆盖半径" + r" $r^\star(x)$", m1c=r"$S_i=\lambda_\mathrm{ref}+\max_x\,[r^\star(x)-\frac{w}{2}]$",
        m1d="撒施作业：" + r"$S_g$" + "（伸缩落量分布）",
        l1="层1：线性化协方差递推", l1f=r"$\mathbf{P}_{t+1}=\mathbf{A}_t\mathbf{P}_t\mathbf{A}_t^{\top}+\mathbf{B}_t\mathbf{B}_t^{\top}$",
        l2="层2：Kac–Rice超限概率", l2f=r"$\mu_j\leq\bar\Phi(u_0)+\Sigma_i[\Phi(u_i)-\Phi_2(u_i,u_{i+1})]$",
        l3="层3：行对合成与求逆", l3f=r"$\hat q_f=F_\pi^{-1}(1-\varepsilon)$",
        mc="或：蒙特卡洛数字孪生",
        m3b=r"$V_i=S_i/\hat q_{f_i}$", m3c="边际：" + r"$k_\star=\lceil(n+1)(1-\varepsilon)\rceil$",
        m3d="PAC：" + r"$F_{\mathrm{Bin}}(k_\star-1)\geq1-\delta$",
        m3e=r"$\hat\lambda=\hat q_g\,V_{(k_\star)}$",
        m4a=r"$\hat\lambda\leq\lambda_\mathrm{ref}$?", m4b="实施规划" + r"$\ \pi(\hat\lambda)$",
        m4c="漏作业概率" + r"$\ \leq\kappa\,\varepsilon$", m4d="作业行距" + r"$\ w-2\hat\lambda$",
        out="输出", outv="作业行距\n漏作业概率",
        a1=r"$\{S_i\}$", a2=r"$\{V_i\}$", a3=r"$\hat\lambda$",
        attr="田块属性（不用作业数据）",
        loop="推广检查未通过：加大" + r"$\lambda_\mathrm{ref}$" + "，在更大的基准规划上重新校准",
        fb1="否", yes="是", fb2="新作业记录持续加入校准集"),
    "en": dict(
        inp="Input", in_runs="Logged runs\n(independent\npositioning)", in_attr="Field boundary,\nterrain, GNSS\ngrade, controller",
        m=["Module 1:\nCoverage score", "Module 2:\nModel-scale\nnormalisation", "Module 3:\nConformal\ncalibration",
           "Module 4:\nTransfer check\nand deployment"],
        m1b="Covering radius " + r"$r^\star(x)$", m1c=r"$S_i=\lambda_\mathrm{ref}+\max_x\,[r^\star(x)-\frac{w}{2}]$",
        m1d="Spreading: " + r"$S_g$" + " (stretched pattern)",
        l1="L1: linearised covariance", l1f=r"$\mathbf{P}_{t+1}=\mathbf{A}_t\mathbf{P}_t\mathbf{A}_t^{\top}+\mathbf{B}_t\mathbf{B}_t^{\top}$",
        l2="L2: Kac–Rice exceedance", l2f=r"$\mu_j\leq\bar\Phi(u_0)+\Sigma_i[\Phi(u_i)-\Phi_2(u_i,u_{i+1})]$",
        l3="L3: pair product, inversion", l3f=r"$\hat q_f=F_\pi^{-1}(1-\varepsilon)$",
        mc="or: Monte Carlo twin",
        m3b=r"$V_i=S_i/\hat q_{f_i}$", m3c="marg.: " + r"$k_\star=\lceil(n+1)(1-\varepsilon)\rceil$",
        m3d="PAC: " + r"$F_{\mathrm{Bin}}(k_\star-1)\geq1-\delta$",
        m3e=r"$\hat\lambda=\hat q_g\,V_{(k_\star)}$",
        m4a=r"$\hat\lambda\leq\lambda_\mathrm{ref}$?", m4b="deployed plan " + r"$\pi(\hat\lambda)$",
        m4c=r"$\Pr[\mathrm{miss}]\leq\kappa\,\varepsilon$", m4d="line spacing " + r"$w-2\hat\lambda$",
        out="Output", outv="Line spacing,\nmiss\nprobability",
        a1=r"$\{S_i\}$", a2=r"$\{V_i\}$", a3=r"$\hat\lambda$",
        attr="field attributes (no run data)",
        loop="transfer check failed: enlarge " + r"$\lambda_\mathrm{ref}$" + " and recalibrate on a larger reference plan",
        fb1="no", yes="yes", fb2="new logged runs join the calibration set"),
}


def draw_framework(lang):
    """Module-style framework figure: four coloured modules, data arrows (black) and feedback loops (red dashed)."""
    from matplotlib.patches import FancyBboxPatch
    T = FW[lang]
    if lang == "zh":
        register_cjk_font()
        plt.rcParams.update({"font.family": "sans-serif",
                             "font.sans-serif": ["Noto Sans CJK SC", "DejaVu Sans"],
                             "mathtext.fontset": "custom", "mathtext.rm": "Noto Sans CJK SC",
                             "mathtext.it": "DejaVu Sans:italic", "mathtext.bf": "DejaVu Sans:bold",
                             "mathtext.sf": "Noto Sans CJK SC", "axes.unicode_minus": False})
    else:
        plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "DejaVu Sans"],
                             "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans",
                             "mathtext.it": "Liberation Sans:italic", "mathtext.bf": "Liberation Sans:bold"})
    rng = np.random.default_rng(5)
    fig = plt.figure(figsize=(7.48, 4.05))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 121), ax.set_ylim(0, 65.5), ax.axis("off")

    def rbox(x, y, w, h, fc, ec, lw=1.0, r=1.2, z=2, ls="-"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw,
                                    zorder=z, ls=ls))

    def arrow(p0, p1, col=INK, ls="-", lw=1.0, ms=8, z=6):
        ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, ls=ls,
                                                          mutation_scale=ms, shrinkA=0, shrinkB=0), zorder=z)

    fs, fsm = 7.6, 7.2
    yb, yt = 15.0, 56.0
    cols = [("#dbe7f6", "#5b8fd1"), ("#e2f0dc", "#6aaa5c"), ("#fde6cf", "#e09a4f"), ("#ebe0f3", "#9d7cc0")]
    xs = [19.0, 43.0, 70.0, 94.5]
    ws = [21.0, 24.0, 21.5, 19.0]
    # input layer
    rbox(1.0, yb, 15.0, yt - yb, "#f3f3f3", "#9a9a9a")
    ax.text(8.5, yt - 3.0, T["inp"], ha="center", va="center", fontsize=8.5, fontweight="bold")
    for k in range(4):                                     # stacked run thumbnails
        x0, y0 = 2.6 + 0.7 * k, 30.5 + 3.4 * (3 - k)
        rbox(x0, y0, 10.6, 6.2, "white", "#7a7a7a", lw=0.6, r=0.5, z=3 + k)
        xx = np.linspace(x0 + 0.8, x0 + 9.8, 40)
        for j in range(2):
            e = np.cumsum(rng.normal(0, 1, 40)); e = (e - e.mean()) / (np.abs(e).max() + 1e-9)
            ax.plot(xx, y0 + 2.0 + 2.3 * j + 0.55 * e, color=BLUE, lw=0.7, zorder=3 + k)
    ax.text(8.5, 27.2, T["in_runs"], ha="center", va="center", fontsize=fsm, linespacing=1.15)
    ax.text(8.5, 19.0, T["in_attr"], ha="center", va="center", fontsize=fsm - 0.4, color=INK2, linespacing=1.15)
    # modules
    for i in range(4):
        rbox(xs[i], yb, ws[i], yt - yb, cols[i][0], cols[i][1], lw=1.1)
        ax.text(xs[i] + ws[i] / 2, yt - 4.6, T["m"][i], ha="center", va="center", fontsize=8.2, fontweight="bold",
                linespacing=1.15)
    cx = [xs[i] + ws[i] / 2 for i in range(4)]
    # module 1
    x0 = xs[0] + 1.5
    rbox(x0, 33.5, ws[0] - 3, 11.0, "white", cols[0][1], lw=0.7, r=0.8, z=3)
    icon_score(ax, x0 + 1.4, 35.2, ws[0] - 5.8, 6.0, "")
    rbox(x0, 27.0, ws[0] - 3, 4.6, "white", cols[0][1], lw=0.7, r=0.8, z=3)
    ax.text(cx[0], 29.3, T["m1b"], ha="center", va="center", fontsize=fsm, zorder=5)
    rbox(x0, 20.5, ws[0] - 3, 4.6, "white", cols[0][1], lw=0.7, r=0.8, z=3)
    ax.text(cx[0], 22.8, T["m1c"], ha="center", va="center", fontsize=fsm - 0.6, zorder=5)
    ax.text(cx[0], 17.4, T["m1d"], ha="center", va="center", fontsize=fsm - 0.9, color=INK2, zorder=5)
    arrow((cx[0], 33.5), (cx[0], 31.6), col=cols[0][1], ms=6)
    arrow((cx[0], 27.0), (cx[0], 25.1), col=cols[0][1], ms=6)
    # module 2: three levels
    x0 = xs[1] + 1.3
    for k, (lt, lf) in enumerate(((T["l1"], T["l1f"]), (T["l2"], T["l2f"]), (T["l3"], T["l3f"]))):
        y0 = 39.0 - 9.3 * k
        rbox(x0, y0, ws[1] - 2.6, 7.4, "white", cols[1][1], lw=0.7, r=0.8, z=3)
        ax.text(cx[1], y0 + 5.2, lt, ha="center", va="center", fontsize=fsm - 0.3, fontweight="bold", zorder=5)
        ax.text(cx[1], y0 + 2.2, lf, ha="center", va="center", fontsize=fsm - (1.6 if k == 1 else 0.9), zorder=5)
        if k < 2:
            arrow((cx[1], y0), (cx[1], y0 - 1.9), col=cols[1][1], ms=6)
    ax.text(cx[1], 17.4, T["mc"], ha="center", va="center", fontsize=fsm - 0.9, color=INK2, zorder=5)
    # module 3
    x0 = xs[2] + 1.5
    rbox(x0, 37.0, ws[2] - 3, 9.0, "white", cols[2][1], lw=0.7, r=0.8, z=3)
    icon_sorted(ax, x0 + 1.6, 38.0, ws[2] - 6.2, 7.0)
    for k, key in enumerate(("m3b", "m3c", "m3d")):
        y0 = 31.0 - 4.9 * k
        rbox(x0, y0, ws[2] - 3, 4.1, "white", cols[2][1], lw=0.7, r=0.8, z=3)
        ax.text(cx[2], y0 + 2.05, T[key], ha="center", va="center", fontsize=fsm - (0.9 if k == 2 else 0.4), zorder=5)
    ax.text(cx[2], 18.0, T["m3e"], ha="center", va="center", fontsize=fsm + 0.4, zorder=5, color="#a35a00")
    # module 4
    cd = xs[3] + 1.0 + (ws[3] - 4.2) / 2
    icon_decision(ax, cd, 39.5, 5.6, T["m4a"], "", "", exits=False)
    arrow((cd, 39.5 - 4.2), (cd, 32.1), col=GREEN, ms=6)
    ax.text(cd + 0.6, 33.6, T["yes"], ha="left", va="center", fontsize=fsm - 0.4, color=GREEN)
    for k, key in enumerate(("m4b", "m4c", "m4d")):
        y0 = 28.0 - 5.0 * k
        rbox(xs[3] + 1.0, y0, ws[3] - 4.2, 4.1, "white", cols[3][1], lw=0.7, r=0.8, z=3)
        ax.text(xs[3] + 1.0 + (ws[3] - 4.2) / 2, y0 + 2.05, T[key], ha="center", va="center", fontsize=fsm - 0.4, zorder=5)
    # data arrows between modules
    ym = 35.5
    arrow((16.0, ym), (xs[0], ym))
    for i, lab in enumerate((T["a1"], T["a2"], T["a3"])):
        arrow((xs[i] + ws[i], ym), (xs[i + 1], ym))
        ax.text((xs[i] + ws[i] + xs[i + 1]) / 2, ym + 1.0, lab, ha="center", va="bottom", fontsize=fsm)
    # field attributes go straight to module 2 (over module 1)
    ax.plot([8.5, 8.5, cx[1]], [yt, 60.5, 60.5], color=INK, lw=1.0, zorder=4)
    arrow((cx[1], 60.5), (cx[1], yt))
    ax.text((8.5 + cx[1]) / 2, 61.2, T["attr"], ha="center", va="bottom", fontsize=fsm)
    # output
    arrow((xs[3] + ws[3], ym), (121.0 - 4.5, ym))
    ax.text(118.7, ym + 7.5, T["out"], ha="center", va="center", fontsize=8.5, fontweight="bold")
    ax.text(118.7, ym - 5.5, T["outv"], ha="center", va="center", fontsize=fsm - 0.4, linespacing=1.15)
    # feedback loops (red dashed): failed transfer check -> recalibrate; new runs -> calibration set
    red = "#c62828"
    yl = 7.0
    lb_x0, lb_x1 = 31.0, 89.0
    rbox(lb_x0, yl - 3.0, lb_x1 - lb_x0, 6.0, "#f4f4f4", "#8a8a8a", lw=0.8, r=1.0, z=3)
    ax.text((lb_x0 + lb_x1) / 2, yl, T["loop"], ha="center", va="center", fontsize=fsm, zorder=5)
    ax.plot([cd + 5.6, xs[3] + ws[3] - 1.7, xs[3] + ws[3] - 1.7], [39.5, 39.5, yb], color=red, lw=1.0, ls=(0, (3, 2)), zorder=6)
    ax.text(cd + 6.6, 40.6, T["fb1"], ha="center", va="bottom", fontsize=fsm - 0.4, color=red)
    ax.plot([xs[3] + ws[3] - 1.7, xs[3] + ws[3] - 1.7], [yb, yl], color=red, lw=1.0, ls=(0, (3, 2)), zorder=6)
    arrow((xs[3] + ws[3] - 1.7, yl), (lb_x1, yl), col=red, ls=(0, (3, 2)))
    ax.plot([lb_x0, 8.5], [yl, yl], color=red, lw=1.0, ls=(0, (3, 2)), zorder=6)
    arrow((8.5, yl), (8.5, yb), col=red, ls=(0, (3, 2)))
    ax.plot([118.7, 118.7], [ym - 9.8, 1.2], color=red, lw=1.0, ls=(0, (3, 2)), zorder=6)
    ax.plot([118.7, 4.0], [1.2, 1.2], color=red, lw=1.0, ls=(0, (3, 2)), zorder=6)
    arrow((4.0, 1.2), (4.0, yb), col=red, ls=(0, (3, 2)))
    ax.text(104.0, 1.9, T["fb2"], ha="center", va="bottom", fontsize=fsm - 0.4, color=red)

    name = "fig_framework" + ("_zh" if lang == "zh" else "")
    for ext, kw in (("pdf", {}), ("png", {"dpi": 600}), ("tif", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), bbox_inches="tight", pad_inches=0.03, facecolor="white", **kw)
    plt.close(fig)
    print("wrote", name)


if __name__ == "__main__":
    plt.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42})
    draw("en")
    draw("zh")
    draw_framework("en")
    draw_framework("zh")
