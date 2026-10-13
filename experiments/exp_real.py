"""E8: trace-driven validation on REAL agricultural-robot execution errors
(CitrusFarm, 106 RTK-measured row passes, 3 orchard blocks, 2 days).

No simulator is involved. An "operation" is a window of K consecutive real
passes (time order, so the real direction alternation and pass-to-pass
correlation are kept). With an implement of width w and erosion lam the
passes are planned at spacing w - 2*lam; the executed lateral offsets are the
recorded profiles, so the missed area is computed exactly from the real data.

Splits (calibration -> test):
  random  : random 50/50 split of sequences' windows, 300 repeats
  LOBO    : leave-one-orchard-block-out (13B, 13D, 14B)
  LODO    : leave-one-day-out (2023-07-16 vs 2023-07-18)
Calibration windows are non-overlapping (stride K); test windows use stride 1.
Outputs: results/real.csv
"""
import argparse
import math
import os

import numpy as np
import pandas as pd

import core
import exp_lib as L

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
DAY = {"01": "07-18", "02": "07-18", "03": "07-16", "04": "07-18", "05": "07-16", "06": "07-18", "07": "07-16"}


SEG = 10.0  # along-track length of one operation strip (m)


def windows(P, K, stride):
    out = []
    seqs = sorted({p["seq"] for p in P})
    for sq in seqs:
        ps = sorted([p for p in P if p["seq"] == sq], key=lambda p: p["t0"])
        for i in range(0, len(ps) - K + 1, stride):
            g = ps[i:i + K]
            lo = max(p["x"][0] for p in g)
            hi = min(p["x"][-1] for p in g)
            nseg = int((hi - lo) // SEG)
            for j in range(nseg):
                xg = np.arange(lo + j * SEG, lo + (j + 1) * SEG + 1e-9, 1.0)
                E = np.stack([np.interp(xg, p["x"], p["e"]) for p in g])  # (K, nx)
                out.append(dict(seq=sq, block=g[0]["block"], day=DAY[sq[:2]], start=i, seg=j, E=E))
    return out


def score(E):
    """Run-level pass-to-pass score (Lemma 1 / Theorem 1, uniform scale)."""
    pair = ((E[1:] - E[:-1]) / 2).max(axis=1)
    return float(max(pair.max(), E[0].max(), (-E[-1]).max())), pair, E[0].max(), (-E[-1]).max()


def missed(E, w, lam):
    """Exact missed fraction of a K-pass operation planned at spacing w-2*lam."""
    K, nx = E.shape
    h = w / 2 - lam
    yk = h + np.arange(K) * 2 * h
    width = K * 2 * h
    left = yk[:, None] + E - w / 2
    right = yk[:, None] + E + w / 2
    o = np.argsort(left, axis=0)
    left, right = np.take_along_axis(left, o, 0), np.take_along_axis(right, o, 0)
    left, right = np.clip(left, 0, width), np.clip(right, 0, width)
    reach = np.maximum.accumulate(right, axis=0)
    gaps = np.clip(left[1:] - reach[:-1], 0, None).sum(0) + np.clip(left[0], 0, None) + np.clip(width - reach[-1], 0, None)
    return float(gaps.mean() / width)


def methods(cal, eps, w, n_terms):
    S = np.array([score(c["E"])[0] for c in cal])
    diffs = np.concatenate([((c["E"][1:] - c["E"][:-1])).ravel() for c in cal])
    pairs = np.concatenate([np.r_[score(c["E"])[1], score(c["E"])[2], score(c["E"])[3]] for c in cal])
    return {
        "Nominal (no margin)": 0.0,
        "Fixed overlap 10 cm": 0.05,
        "Fixed overlap 30 cm": 0.15,
        "Gaussian pointwise": L.gaussian_pointwise_lambda(diffs, eps),
        "Empirical pointwise quantile": L.empirical_pointwise_lambda(diffs, eps),
        "Pointwise conformal": L.pointwise_conformal_lambda(diffs, eps),
        "Gaussian on score": L.gaussian_score_lambda(S, eps),
        "Cantelli bound on score": L.cantelli_score_lambda(S, eps),
        "Scenario (Campi-Garatti)": L.scenario_lambda(S, eps),
        "CVaR (empirical)": L.cvar_lambda(S, eps),
        "Wasserstein DRO-CVaR": L.dro_cvar_lambda(S, eps),
        "Worst-case (max score)": float(S.max()),
        "CE-U (ours, uniform)": float(core.conformal_quantile(S, eps)),
        "CE-pair (ours, union bound)": L.pair_union_lambda(pairs, eps, n_terms),
    }


def evaluate(cal, test, eps, w, split, rep, K):
    rows = []
    for m, lam in methods(cal, eps, w, K + 1).items():
        if not np.isfinite(lam) or lam >= 0.8 * w / 2:
            rows.append(dict(split=split, rep=rep, method=m, lam=lam, p_nomiss=np.nan, e_miss=np.nan,
                             overlap=np.nan, infeasible=True, n_cal=len(cal), n_test=len(test), K=K, w=w, eps=eps))
            continue
        ms = np.array([missed(t["E"], w, lam) for t in test])
        rows.append(dict(split=split, rep=rep, method=m, lam=lam, p_nomiss=float(np.mean(ms == 0)),
                         e_miss=float(ms.mean()), overlap=w / (w - 2 * lam) - 1, infeasible=False,
                         n_cal=len(cal), n_test=len(test), K=K, w=w, eps=eps))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", type=float, default=6.0)
    ap.add_argument("--repeats", type=int, default=300)
    args = ap.parse_args()
    P = list(np.load(os.path.join(HERE, "data", "citrus_passes.npy"), allow_pickle=True))
    rows = []
    for K in (3, 5):
        for eps in (0.1, 0.2):
            cal_all = windows(P, K, K)
            tst_all = windows(P, K, 1)
            rng = np.random.default_rng(K * 100 + int(eps * 10))
            seqs = sorted({c["seq"] for c in cal_all})
            # random split over sequences x windows
            for rep in range(args.repeats):
                idx = rng.permutation(len(cal_all))
                cal = [cal_all[i] for i in idx[: len(idx) // 2]]
                used = {(cal_all[i]["seq"], cal_all[i]["start"], cal_all[i]["seg"]) for i in idx[: len(idx) // 2]}
                # test strips must not share any pass segment with a calibration strip
                test = [t for t in tst_all if not any(t["seq"] == s and t["seg"] == sg and abs(t["start"] - st) < K
                                                      for s, st, sg in used)]
                if len(test) < 5:
                    continue
                rows += evaluate(cal, test, eps, args.w, "random", rep, K)
            for b in ("13B", "13D", "14B"):
                cal = [c for c in cal_all if c["block"] != b]
                test = [t for t in tst_all if t["block"] == b]
                rows += evaluate(cal, test, eps, args.w, f"LOBO:{b}", 0, K)
            for d in ("07-16", "07-18"):
                cal = [c for c in cal_all if c["day"] != d]
                test = [t for t in tst_all if t["day"] == d]
                rows += evaluate(cal, test, eps, args.w, f"LODO:{d}", 0, K)
            print(f"K={K} eps={eps}: {len(cal_all)} calibration windows, {len(tst_all)} test windows", flush=True)
    # online deployment on the real chronological stream (ACI, Gibbs & Candes 2021)
    aci_rows = []
    for K in (3, 5):
        stream = windows(P, K, K)
        order = sorted(range(len(stream)), key=lambda i: (stream[i]["day"], stream[i]["seq"], stream[i]["start"],
                                                          stream[i]["seg"]))
        stream = [stream[i] for i in order]
        for method in ("static (first day)", "ACI (ours, online)"):
            n0 = sum(1 for s_ in stream if s_["day"] == stream[0]["day"])
            hist = [score(s_["E"])[0] for s_ in stream[:n0]]
            q_static = core.conformal_quantile(hist, 0.1)
            eps_t, gamma = 0.1, 0.02
            for t, s_ in enumerate(stream[n0:]):
                if method.startswith("static"):
                    q = q_static
                else:
                    q = core.conformal_quantile(hist, float(np.clip(eps_t, 1e-3, 0.999))) if eps_t > 0 else max(hist) * 1.1
                q = min(q, 0.8 * args.w / 2)
                ms = missed(s_["E"], args.w, q)
                err = float(ms > 0)
                hist.append(score(s_["E"])[0])
                eps_t += gamma * (0.1 - err)
                aci_rows.append(dict(K=K, method=method, t=t, q=q, err=err, miss=ms, overlap=args.w / (args.w - 2 * q) - 1))
    pd.DataFrame(aci_rows).to_csv(os.path.join(RES, "real_aci.csv"), index=False)
    a = pd.DataFrame(aci_rows)
    print(a.groupby(["K", "method"])[["err", "overlap"]].mean().round(3))

    os.makedirs(RES, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(RES, "real.csv"), index=False)
    pd.set_option("display.width", 200)
    print(df[(df.split == "random") & (df.eps == 0.1)].groupby(["K", "method"])[["p_nomiss", "e_miss", "overlap"]]
          .mean().round(3))


if __name__ == "__main__":
    main()
