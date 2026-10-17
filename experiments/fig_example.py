"""Qualitative example + runtime benchmark (E7).

fig_example.png: one real hilly paddy field, executed coverage of the nominal
plan vs. the conformal-erosion plan for the same operating condition; missed
area in red.  results/runtime.csv: wall-clock of calibration / planning.
"""
import os
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import core
import exp_lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
RES = os.path.join(HERE, "..", "results")
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


def draw(ax, F, ys, X, D, r, w, title):
    xs, ys_ = F.M.exterior.xy
    ax.fill(*F.P.exterior.xy, color="#f2f1ed", zorder=0)
    ax.plot(xs, ys_, color="#52514e", lw=0.8, zorder=4)
    for k, y in enumerate(ys):
        xk = X[k]
        d = D[k][r]
        ax.fill_between(xk, y + d - w / 2, y + d + w / 2, color=C[0] if k % 2 == 0 else C[2],
                        alpha=0.35, lw=0, zorder=1)
    # missed cells on a fine raster inside M
    minx, miny, maxx, maxy = F.M.bounds
    gx = np.arange(minx, maxx, 0.5)
    gy = np.arange(miny, maxy, 0.02)
    cov = np.zeros((len(gy), len(gx)), bool)
    for k, y in enumerate(ys):
        o = core.pass_offsets(X[k], D[k][r:r + 1], gx)[0]
        lo, hi = y + o - w / 2, y + o + w / 2
        cov |= (gy[:, None] >= lo[None, :]) & (gy[:, None] <= hi[None, :])
    GX, GY = np.meshgrid(gx, gy)
    from shapely import contains_xy
    inside = contains_xy(F.M, GX, GY)
    miss = inside & ~cov
    jj, ii = np.nonzero(miss.T)
    ax.scatter(gx[jj], gy[ii], s=1.5, color="#e34948", zorder=3, lw=0)
    ax.set_aspect("equal")
    bx0, by0, bx1, by1 = F.P.bounds
    ax.set_xlim(bx0 - 2, bx1 + 2)
    ax.set_ylim(by0 - 2, by1 + 2)
    ax.set_title(title, fontsize=7.5, loc="left")
    ax.set_xticks([])
    ax.set_yticks([])


def main():
    rng = np.random.default_rng(7)
    fields = core.load_fields("paddy", seed=0)
    F = max(fields[20:60], key=lambda f: f.z_mean_slope)
    w = 3.0
    const = L.ConstSigma(1.0)
    q, hist, _ = L.calibrate_conformal(lambda n: [(F, np.arange(n))], const, 0.1, w, rng, lam0=0.03, n_cal=100)
    cond = core.Condition(np.random.default_rng(11), 1, moisture=0.6)
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 4.2))
    for ax, lam, name in [(axs[0], 0.0, "Nominal plan (no margin)"),
                          (axs[1], q, f"Conformal erosion, q = {q*100:.1f} cm")]:
        ys = core.plan(F, w, lam, const)
        X, D = core.simulate(F, ys, cond, np.random.default_rng(5))
        m = core.evaluate(F, ys, X, D, w)[0]
        st = L.evaluate_plan(F, ys, 300, np.random.default_rng(3), w=w)
        draw(ax, F, ys, X, D, 0, w, f"{name}\n{len(ys)} passes, overlap {st['overlap']*100:.1f}%\n"
             f"this run: missed {m*1e4:.1f}‱ | 300 runs: P(no miss)={st['p_nomiss']:.2f}")
    fig.suptitle(f"Real paddy field #{F.fid} (mean slope {F.z_mean_slope:.1f}°); red = missed area",
                 fontsize=8, x=0.01, ha="left", y=1.04)
    fig.savefig(os.path.join(FIG, "fig_example.png"))
    plt.close(fig)

    rows = []
    for Fi in ([] if os.environ.get("SKIP_RUNTIME") else fields[20:35]):
        t0 = time.time()
        q, hist, _ = L.calibrate_conformal(lambda n: [(Fi, np.arange(n))], const, 0.1, w, rng, lam0=0.03, n_cal=100)
        t1 = time.time()
        ys = core.plan(Fi, w, q, const)
        t2 = time.time()
        rows.append(dict(field=Fi.fid, area_ha=Fi.M.area / 1e4, passes=len(ys),
                         calib_s_including_sim=t1 - t0, fp_iters=len(hist), plan_ms=(t2 - t1) * 1e3))
    if os.environ.get("SKIP_RUNTIME"):
        return
    pd.DataFrame(rows).to_csv(os.path.join(RES, "runtime.csv"), index=False)
    print(pd.DataFrame(rows).describe().round(3))


if __name__ == "__main__":
    main()
