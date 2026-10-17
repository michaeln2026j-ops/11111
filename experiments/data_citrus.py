"""Real execution-error traces from the CitrusFarm dataset (UC Riverside).

Teng et al., "Multimodal Dataset for Localization, Mapping and Crop Monitoring
in Citrus Tree Farms", ISVC 2023; data: s3://ucr-robotics/citrus-farm-dataset
(CC BY-SA 4.0). A Clearpath Jackal drove boustrophedon row passes in three
orchard blocks (13B, 13D, 14B) on two days; ground truth is 10 Hz RTK-GNSS.

Pipeline per sequence:
  1. rotate to the dominant row direction (axial mode of velocity headings);
  2. segment straight passes (|heading - row axis| < 12 deg, length > 60% of
     the block's median pass length), trim 3 m at both ends (turn transients);
  3. the planned lines are the orchard's regular row lattice y_k = a + k*D,
     fitted per block by least squares on pass means (rows are planted on a
     fixed spacing), so residuals include each pass's real offset;
  4. lateral error profile e(s) = y(s) - y_ref on a 1 m along-track grid.
Output: data/citrus_passes.npz  (lists of profiles with metadata)
"""
import glob
import os

import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "data", "citrus")


def load(f):
    d = np.loadtxt(f, delimiter=",", comments="#")
    return d[:, 0], d[:, 1], d[:, 2]


def axial_mode(ang):
    a = np.mod(ang, np.pi)
    h, e = np.histogram(a, bins=90, range=(0, np.pi))
    k = np.argmax(h)
    sel = (a >= e[k]) & (a < e[k + 1])
    return float(np.median(a[sel]))


def _smooth(a, n=21):
    k = np.ones(n) / n
    return np.convolve(np.pad(a, n // 2, mode="edge"), k, mode="valid")


def segment(t, x, y, min_frac=0.6, tol=np.radians(30), trim=3.0):
    vx, vy = _smooth(np.gradient(x, t)), _smooth(np.gradient(y, t))  # 2 s moving average
    sp = np.hypot(vx, vy)
    ang = np.arctan2(vy, vx)
    th = axial_mode(ang[sp > 0.5])
    c, s = np.cos(-th), np.sin(-th)
    X, Y = c * x - s * y, s * x + c * y  # rows along X
    hd = np.arctan2(_smooth(np.gradient(Y, t)), _smooth(np.gradient(X, t)))
    straight = ((np.abs(hd) < tol) | (np.abs(np.abs(hd) - np.pi) < tol)) & (sp > 0.3)
    passes = []
    i = 0
    n = len(t)
    while i < n:
        if not straight[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and straight[j + 1] and np.sign(np.cos(hd[j + 1])) == np.sign(np.cos(hd[i])):
            j += 1
        if j - i > 20:
            passes.append((i, j, int(np.sign(np.cos(hd[i])))))
        i = j + 1
    L = np.array([abs(X[b] - X[a]) for a, b, _ in passes])
    keep = [p for p, l in zip(passes, L) if l > min_frac * np.median(L[L > 10])] if len(L) else []
    out = []
    for a, b, dr in keep:
        xs, ys = X[a:b + 1], Y[a:b + 1]
        o = np.argsort(xs)
        xs, ys = xs[o], ys[o]
        lo, hi = xs[0] + trim, xs[-1] - trim
        grid = np.arange(np.ceil(lo), np.floor(hi) + 1, 1.0)
        if len(grid) < 15:
            continue
        out.append(dict(x=grid, y=np.interp(grid, xs, ys), dir=dr, t0=float(t[a])))
    return out, th


def lattice(passes, spacing_guess):
    """Fit y_ref = a + k*D to pass means; returns row index per pass and ref."""
    m = np.array([np.median(p["y"]) for p in passes])
    best = None
    for D in np.linspace(0.85 * spacing_guess, 1.15 * spacing_guess, 301):
        for a0 in np.linspace(0, D, 60, endpoint=False):
            k = np.round((m - a0) / D)
            r = m - (a0 + k * D)
            cost = np.sum(np.minimum(r ** 2, 1.0))
            if best is None or cost < best[0]:
                best = (cost, D, a0)
    _, D, a0 = best
    k = np.round((m - a0) / D)
    # refine by least squares
    A = np.c_[np.ones_like(k), k]
    a, D = np.linalg.lstsq(A, m, rcond=None)[0]
    return k.astype(int), a, D


def main():
    blocks = {}
    for f in sorted(glob.glob(os.path.join(SRC, "gt_*.csv"))):
        seq = os.path.basename(f)[3:-4]
        block = seq.split("_")[1]
        t, x, y = load(f)
        ps, th = segment(t, x, y)
        for p in ps:
            p["seq"] = seq
            p["block"] = block
        blocks.setdefault(block, []).extend(ps)
        print(f"{seq}: {len(ps)} passes, row axis {np.degrees(th):.1f} deg")
    profiles = []
    for block, ps in blocks.items():
        m = np.sort([np.median(p["y"]) for p in ps])
        dm = np.diff(m)
        guess = np.median(dm[dm > 2.0])
        k, a, D = lattice(ps, guess)
        res = []
        for p, kk in zip(ps, k):
            e = p["y"] - (a + kk * D)
            res.append(e)
            profiles.append(dict(block=block, seq=p["seq"], row=int(kk), dir=p["dir"], t0=p["t0"],
                                 x=p["x"], e=e, spacing=D))
        allr = np.concatenate(res)
        print(f"block {block}: {len(ps)} passes, row spacing D={D:.2f} m, lateral err sd={allr.std()*100:.1f} cm, "
              f"p95|e|={np.percentile(np.abs(allr),95)*100:.1f} cm")
    # merge time-consecutive fragments of the same row driven in the same direction
    profiles.sort(key=lambda p: (p["seq"], p["t0"]))
    merged = []
    for p in profiles:
        q = merged[-1] if merged else None
        if q is not None and q["seq"] == p["seq"] and q["row"] == p["row"] and q["dir"] == p["dir"]:
            x = np.r_[q["x"], p["x"]]
            e = np.r_[q["e"], p["e"]]
            o = np.argsort(x)
            x, e = x[o], e[o]
            keep = np.r_[True, np.diff(x) > 0]
            q["x"], q["e"] = x[keep], e[keep]
        else:
            merged.append(dict(p))
    profiles = merged
    print("after merging fragments:", len(profiles), "passes; median length",
          np.median([p["x"][-1] - p["x"][0] for p in profiles]), "m")
    np.save(os.path.join(ROOT, "data", "citrus_passes.npy"), np.array(profiles, dtype=object), allow_pickle=True)


if __name__ == "__main__":
    main()
