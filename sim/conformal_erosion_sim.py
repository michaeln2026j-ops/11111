"""Numerical sanity check for conformal-erosion coverage certificates.

Setting: boustrophedon coverage of a rectangular field [0, L] x [0, S] with an
implement of width w. Executed cross-track error along each swath is a smooth
random field e(y, s) whose amplitude depends on terrain (sigma(y)) and on a
per-run condition factor (soil moisture etc.). We check:

  Thm 1 (zero-miss certificate): split conformal on the per-run score
         "minimal erosion that would have avoided every gap" gives
         P(no missed area) >= 1 - eps.
  Thm 2 (missed-area risk control): conformal risk control on the monotone
         loss "missed-area fraction" gives E[missed fraction] <= alpha.
  Thm 3 (spatially adaptive): normalized scores e / sigma_hat(y) give the
         same guarantee with fewer swaths (less overlap).

Usage: python3 sim/conformal_erosion_sim.py [--fig out.png]
"""
import argparse

import numpy as np

L, S, W = 60.0, 100.0, 3.0  # field width, length (m), implement width (m)
NS = 200  # arc-length samples per swath
S_GRID = np.linspace(0.0, S, NS)
J = 40  # random Fourier features


def sigma_true(y):
    """Terrain-dependent error scale: flat part + a slope band around y=40 m."""
    return 0.05 + 0.20 * np.exp(-(((y - 40.0) / 8.0) ** 2))


K_MAX = 120  # max swaths per run (bank of independent per-pass processes)
RHO = 0.5  # share of error that is common to adjacent passes


def _rff(rng, n, ls):
    w = rng.normal(0.0, 1.0 / ls, (n, J))
    ph = rng.uniform(0.0, 2 * np.pi, (n, J))
    a = rng.normal(0.0, 1.0, (n, J)) * np.sqrt(2.0 / J)
    return (a[:, None, :] * np.cos(S_GRID[None, :, None] * w[:, None, :] + ph[:, None, :])).sum(-1)


def sample_run(rng):
    """One execution run: returns e(y, k) -> lateral error profile (m) of the
    k-th pass driven at planned centre y.

    e = cond * sigma(y) * (RHO * common(y, s) + sqrt(1-RHO^2) * indep_k(s)):
    a field-wide component correlated across passes (slope drift, GNSS bias)
    plus a pass-specific component (time-varying GNSS drift, controller
    transients). Only the pass-to-pass difference creates gaps.
    """
    wy = rng.normal(0.0, 1.0 / 15.0, J)
    ws = rng.normal(0.0, 1.0 / 10.0, J)
    ph = rng.uniform(0.0, 2 * np.pi, J)
    amp = rng.normal(0.0, 1.0, J) * np.sqrt(2.0 / J)
    indep = _rff(rng, K_MAX, 10.0)
    cond = rng.lognormal(0.0, 0.25)

    def e(y, k):
        common = (amp[None, :] * np.cos(np.outer(S_GRID, ws) + wy[None, :] * y + ph[None, :])).sum(1)
        return cond * sigma_true(y) * (RHO * common + np.sqrt(1 - RHO**2) * indep[k])

    return e


def plan(half_width_fn):
    """Greedy swath placement: next centre y' satisfies y' - h(y') = y + h(y).

    For the uniform case this reduces to spacing 2h; greedy is optimal for the
    1-D interval-covering problem when y + h(y) is increasing.
    """
    ys = np.linspace(0.0, L, 6001)
    h = half_width_fn(ys)
    if h.min() < 0.25 * W / 2:  # erosion beyond 75% of the implement: infeasible
        raise ValueError("erosion exceeds implement half-width")
    lo = ys - h
    centres, reach = [], 0.0
    while reach < L:
        ok = np.nonzero(lo <= reach + 1e-12)[0]
        y = ys[ok[-1]]
        centres.append(y)
        reach = y + half_width_fn(np.array([y]))[0]
        if y >= L:
            break
    return np.array(centres)


def missed_fraction(centres, e):
    """Fraction of field area left uncovered when executing `centres` under e."""
    off = np.stack([e(y, k) for k, y in enumerate(centres)])  # (N, NS)
    left = centres[:, None] + off - W / 2
    right = centres[:, None] + off + W / 2
    order = np.argsort(left, axis=0)
    left = np.take_along_axis(left, order, 0)
    right = np.take_along_axis(right, order, 0)
    reach = np.maximum.accumulate(right, axis=0)
    gaps = np.clip(left[1:] - reach[:-1], 0, None).sum(0)
    gaps += np.clip(left[0] - 0.0, 0, None) + np.clip(L - reach[-1], 0, None)
    return gaps.mean() / L


def run_score(e, sig_hat):
    """Per-run nonconformity: smallest normalized erosion with zero miss."""
    lo, hi = 0.0, 20.0
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        try:
            c = plan(lambda y: W / 2 - mid * sig_hat(y))
        except ValueError:
            hi = mid
            continue
        if missed_fraction(c, e) > 0:
            lo = mid
        else:
            hi = mid
    return hi


def crc_lambda(runs, sig_hat, alpha, hi=20.0, iters=18):
    """Conformal risk control (loss bound B=1): smallest lambda with
    (n R_n(lambda) + 1)/(n+1) <= alpha, found by bisection (R_n is monotone)."""
    n = len(runs)

    def ok(lam):
        try:
            c = plan(lambda y: W / 2 - lam * sig_hat(y))
        except ValueError:
            return True, None
        risk = np.mean([missed_fraction(c, e) for e in runs])
        return (n * risk + 1.0) / (n + 1) <= alpha, c

    if (n * 0 + 1.0) / (n + 1) > alpha:
        raise RuntimeError("alpha < 1/(n+1): need more calibration runs")
    lo = 0.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        good, _ = ok(mid)
        lo, hi = (lo, mid) if good else (mid, hi)
    return hi, plan(lambda y: W / 2 - hi * sig_hat(y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-cal", type=int, default=400)
    ap.add_argument("--n-test", type=int, default=1000)
    ap.add_argument("--eps", type=float, default=0.1)
    ap.add_argument("--alpha", type=float, default=0.003)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    cal = [sample_run(rng) for _ in range(args.n_cal)]
    test = [sample_run(rng) for _ in range(args.n_test)]
    n, eps = args.n_cal, args.eps
    k = int(np.ceil((n + 1) * (1 - eps)))

    variants = {
        "uniform (sigma_hat = const)": lambda y: np.full(np.shape(y), 0.15),
        "adaptive (sigma_hat = terrain)": sigma_true,
    }

    print(f"field {L}x{S} m, implement {W} m, n_cal={n}, n_test={args.n_test}\n")
    print("baseline: no erosion")
    c0 = plan(lambda y: np.full(np.shape(y), W / 2))
    m0 = np.array([missed_fraction(c0, e) for e in test])
    print(f"  swaths={len(c0)}  P(miss>0)={np.mean(m0 > 0):.3f}  E[miss]={m0.mean():.4f}\n")

    for name, sh in variants.items():
        scores = np.sort([run_score(e, sh) for e in cal])
        q = scores[k - 1]
        c = plan(lambda y: W / 2 - q * sh(y))
        m = np.array([missed_fraction(c, e) for e in test])
        print(f"[Thm1/3 zero-miss, eps={eps}] {name}")
        print(f"  q={q:.3f}  swaths={len(c)}  P(no miss)={np.mean(m == 0):.3f}  (target >= {1 - eps})")

        lam, c2 = crc_lambda(cal, sh, args.alpha)
        m2 = np.array([missed_fraction(c2, e) for e in test])
        print(f"[Thm2 risk control, alpha={args.alpha}] {name}")
        print(f"  lambda={lam:.3f}  swaths={len(c2)}  E[miss]={m2.mean():.4f}  (target <= {args.alpha})\n")


if __name__ == "__main__":
    main()
