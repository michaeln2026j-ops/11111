"""E-low: certification from ONE historical run per calibration field and none on the target field
(pre-registered in docs/prereg_lowdata.md).

Phase A (per field, shardable):  theory-predicted CDF of the run score at the reference plan (evt_theory),
                                  one historical run at the reference plan, the per-field oracle.
Phase B (after merging A):        leave-one-field-out: calibrate every method on one run of each of n_cal
                                  other fields, deploy on the target field, evaluate on 200 fresh runs.

    python3 exp_lowdata.py --phase A --regime R1 --first 80 --count 60 --shard 0 --nshards 10
    python3 exp_lowdata.py --phase B --regime R1
"""
import argparse
import glob
import math
import os
import pickle
import time

import numpy as np

import ceplus as CP
import core
import evt_theory as T
import exp_lib as L
import exp_system as E

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "lowdata")
POOLS = {"R1": (80, 60), "R2": (80, 57), "R3": (80, 31)}  # (first index, count): fresh fields (prereg)
EPS, DELTA, N_TEST = 0.1, 0.1, 200


def regime(key):
    rname = [k for k in E.REGIMES if k.startswith(key)][0]
    return rname, E.REGIMES[rname]


def ref_erosion(rname, reg):
    """Reference erosion lam0 from the training fields only, exactly as CE+ (ceplus.fit_training)."""
    w = reg["w"]
    fields = core.load_fields(reg["kind"], w=w, seed=0)
    ctrl = lambda: "lqr_i"  # noqa: E731
    lam_train = 0.10 if reg["p2p"] < 0.05 else 0.40
    _, lam0 = CP.fit_training(fields[:5], w, reg, E.make_cond, lambda F: E.sim_core(F, ctrl, reg), ctrl, EPS,
                              lam_train, seed=E._seed(rname, "ceplus", "LQR-I", False), adaptive=False)
    return lam0


def phase_a(key, first, count, shard, nshards, n_cond):
    rname, reg = regime(key)
    w = reg["w"]
    fields = core.load_fields(reg["kind"], w=w, seed=0)
    lam0 = ref_erosion(rname, reg)
    idx = list(range(first, min(first + count, len(fields))))[shard::nshards]
    os.makedirs(OUT, exist_ok=True)
    for fi in idx:
        F = fields[fi]
        t0 = time.time()
        seed = E._seed(rname, "lowdata", F.fid)
        tgrid = lam0 * np.linspace(0.3, 2.2, 39)
        try:
            Fhat = T.predict_cdf(F, w, reg, lam0, tgrid, n_cond=n_cond, rng=np.random.default_rng(seed))
            ys0 = core.plan(F, w, lam0, E.UNIT)
        except ValueError:
            continue
        S_l = E.sim_core(F, lambda: "lqr_i", reg)
        rng = np.random.default_rng(seed + 1)
        cond = E.make_cond(rng, 1, reg)
        X, D = S_l(ys0, cond, rng)
        S_hist = float(core.exact_scores(F, ys0, X, D, w, lam0)[0])  # one historical operation
        lam_s, ov_s, p_s = E.oracle_lambda(F, w, S_l, reg, seed + 2, EPS)
        rec = dict(regime=rname, fi=fi, fid=F.fid, lam0=lam0, tgrid=tgrid, Fhat=Fhat, S_hist=S_hist,
                   oracle_lam=lam_s, oracle_overlap=ov_s, oracle_p=p_s, K0=len(ys0),
                   N_len=float(sum(F.chord(F.M, y)[1] - F.chord(F.M, y)[0] for y in ys0 if F.chord(F.M, y))))
        with open(os.path.join(OUT, f"A_{key}_{fi}.pkl"), "wb") as f:
            pickle.dump(rec, f)
        print(f"[A] {rname} field {F.fid} ({fi}): S_hist {S_hist:.3f}  Fhat(S_hist) {np.interp(S_hist, tgrid, Fhat):.3f}  "
              f"oracle lam {lam_s:.3f}  ({time.time() - t0:.0f}s)", flush=True)


def inv_cdf(tgrid, Fhat, v):
    """Smallest t on the grid (linear interpolation) with Fhat(t) >= v; beyond the grid: last point + slope."""
    Fm = np.maximum.accumulate(Fhat)
    if v <= Fm[0]:
        return float(tgrid[0])
    if v >= Fm[-1]:
        return float(tgrid[-1] * 1.25)  # outside the predicted range: conservative
    return float(np.interp(v, Fm, tgrid))


def phase_b(key, n_cal, seed=0):
    rname, reg = regime(key)
    w = reg["w"]
    fields = core.load_fields(reg["kind"], w=w, seed=0)
    recs = []
    for f in sorted(glob.glob(os.path.join(OUT, f"A_{key}_*.pkl"))):
        with open(f, "rb") as fh:
            recs.append(pickle.load(fh))
    recs.sort(key=lambda r: r["fi"])
    n = len(recs)
    print(f"[B] {rname}: {n} fields in the pool")
    V = np.array([np.interp(r["S_hist"], r["tgrid"], np.maximum.accumulate(r["Fhat"])) for r in recs])
    S = np.array([r["S_hist"] for r in recs])
    logN = np.array([math.sqrt(2 * math.log(max(r["N_len"], 2.0))) for r in recs])
    # farmer-tuned global overlap: industry practice, tuned once on the training fields (as v6-v8)
    big = reg["p2p"] > 0.05
    m_l = E.VEND.farmer_tuned_overlap(fields[:5], np.random.default_rng(E._seed(rname, "farmer_lqri")), ctrl="lqr_i",
                                      target=1 - EPS, w=w, grid=0.05 if big else 0.01, coarse=0.2 if big else 0.04,
                                      o_max=4.0 if big else 1.0, **E.cond_kw(reg))
    rows = []
    rng = np.random.default_rng(seed)
    for g, rg in enumerate(recs):
        others = [i for i in range(n) if i != g]
        cal = rng.choice(others, size=min(n_cal, len(others)), replace=False)
        lam = {}
        for tag, dl in (("", None), (" PAC", DELTA)):
            v_star = CP.quantile(V[cal], EPS, dl)
            lam[f"CE-EVT{tag} (ours)"] = inv_cdf(rg["tgrid"], rg["Fhat"], v_star) if np.isfinite(v_star) else np.inf
            lam[f"Pooled conformal, raw scores{tag}"] = CP.quantile(S[cal], EPS, dl)
            qn = CP.quantile(S[cal] / logN[cal], EPS, dl)
            lam[f"Ablation: pooled, scale-law normalised{tag}"] = qn * logN[g]
        lam["Ablation: theory only, no conformal"] = inv_cdf(rg["tgrid"], rg["Fhat"], 1 - EPS)
        lam["Farmer-tuned global overlap"] = m_l / 2
        lam["Spec overlap (2x p2p)"] = reg["p2p"]
        F = fields[rg["fi"]]
        S_l = E.sim_core(F, lambda: "lqr_i", reg)
        seed_t = E._seed(rname, "lowdata-test", F.fid)
        for name, lv in lam.items():
            base = dict(regime=rname, fid=F.fid, method=name, lam=lv, oracle_lam=rg["oracle_lam"],
                        oracle_overlap=rg["oracle_overlap"], oracle_p=rg["oracle_p"], n_cal=len(cal))
            try:
                if not np.isfinite(lv):
                    raise ValueError("infinite erosion")
                r = E.evaluate(F, w, core.plan(F, w, float(lv), E.UNIT), S_l, N_TEST, seed_t, reg)
                r["excess_pp"] = 100 * (r["overlap"] - rg["oracle_overlap"])
                rows.append(dict(base, **r))
            except ValueError:
                rows.append(dict(base, p_nomiss=np.nan, infeasible=True))
        print(f"[B] {rname} field {F.fid}: " + "  ".join(f"{k.split(' (')[0][:18]}={v:.3f}" for k, v in lam.items()
                                                        if np.isfinite(v)), flush=True)
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, f"lowdata_{key}.csv"), index=False)
    return df


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True)
    ap.add_argument("--regime", required=True)
    ap.add_argument("--first", type=int, default=None)
    ap.add_argument("--count", type=int, default=None)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--n-cond", type=int, default=300)
    ap.add_argument("--n-cal", type=int, default=30)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.out:
        OUT = a.out
    if a.phase == "A":
        first, count = POOLS[a.regime] if a.first is None else (a.first, a.count)
        phase_a(a.regime, first, count, a.shard, a.nshards, a.n_cond)
    else:
        phase_b(a.regime, a.n_cal)
