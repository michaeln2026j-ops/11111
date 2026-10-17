"""E-low v3 analysis, exactly as pre-registered (docs/prereg_lowdata_v3.md).

    python3 scripts/analyze_lowdata_v3.py

Pools: training = E-low v1 phase-A records (results/lowdata, fields 80+), calibration = E-low v2 records
(results/lowdata_v2, fields 50-79), test = E-low v3 records + curves (results/lowdata_v3, fields 5-19).
"""
import glob
import math
import os
import pickle
import sys

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import ceplus as CP  # noqa: E402
import core  # noqa: E402
import exp_lib as L  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402
from feature_pivot import features  # noqa: E402

RES = os.path.join(HERE, "..", "results")
EPS, DELTA, N_CAL, DRAWS, GATE_DRAWS, GATE_MARGIN = 0.1, 0.1, 25, 400, 200, 0.1
NI_MARGIN, LEVEL = 0.25, 0.05
KEYS = ("R1", "R2", "R3")
CLASSICAL = ("raw", "scale law", "spec x scale law")
FIELDS = {}


def fields(key):
    if key not in FIELDS:
        _, reg = X.regime(key)
        FIELDS[key] = core.load_fields(reg["kind"], w=reg["w"], seed=0)
    return FIELDS[key]


def load(d):
    out = []
    for key in KEYS:
        _, reg = X.regime(key)
        for f in sorted(glob.glob(os.path.join(d, f"A_{key}_*.pkl"))):
            r = pickle.load(open(f, "rb"))
            r["key"], r["reg"], r["cap"] = key, reg, 0.4 * reg["w"]
            r["ok"] = bool(np.all(np.isfinite(r["Fhat"])))
            out.append(r)
    return out


def config_features(r):
    return features(fields(r["key"])[r["fi"]], r) + [math.log(r["reg"]["w"]), math.log(r["reg"]["p2p"])]


class CQR:
    """Ridge model of log S on field + machine-configuration features, one run per training field."""

    def __init__(self, train):
        Xa = np.array([config_features(r) for r in train])
        y = np.log([max(r["S_hist"], 1e-3) for r in train])
        self.mu, self.sd = Xa.mean(0), Xa.std(0) + 1e-12
        A = np.c_[np.ones(len(y)), (Xa - self.mu) / self.sd]
        self.b = np.linalg.solve(A.T @ A + np.diag([0] + [1] * (A.shape[1] - 1)), A.T @ y)

    def __call__(self, r):
        z = (np.array(config_features(r)) - self.mu) / self.sd
        return float(np.exp(self.b[0] + z @ self.b[1:]))


def scales(r, cqr):
    lg = math.sqrt(2 * math.log(max(r["N_len"], 2.0)))
    th = X.inv_cdf(r["tgrid"], r["Fhat"], 1 - EPS) if r["ok"] else np.nan
    return {"raw": 1.0, "scale law": lg, "spec x scale law": r["reg"]["p2p"] * lg, "CQR": cqr(r), "theory": th}


def pivots(pool, name):
    """S / q for a calibration pool; a field with a non-finite theory CDF ranks last (+inf rule)."""
    out = []
    for r in pool:
        q = r["q"][name]
        out.append(np.inf if not np.isfinite(q) else r["S_hist"] / q)
    return np.array(out)


# ------------------------------------------------------------------ training-only gate (prereg section 2)
def overlap_curve(r):
    F = fields(r["key"])[r["fi"]]
    w = r["reg"]["w"]
    grid = np.geomspace(0.3 * r["oracle_lam"], min(8 * r["oracle_lam"], r["cap"]), 40)
    lam, ov = [], []
    for g in grid:
        try:
            ov.append(L.overlap_ratio(F, core.plan(F, w, float(g), E.UNIT), w))
            lam.append(float(g))
        except ValueError:
            pass
    return np.array(lam), np.array(ov)


def gate(train, cands, dl, rng):
    """Proxy-matched excess overlap per candidate pivot on the training pool."""
    res = {}
    n = len(train)
    for name in cands:
        V = pivots(train, name)
        lam_all, star_all, idx_all = [], [], []
        for _ in range(GATE_DRAWS):
            cal = rng.choice(n, size=min(N_CAL, n - 1), replace=False)
            tgt = np.setdiff1d(np.arange(n), cal)
            t = CP.quantile(V[cal], EPS, dl)
            for g in tgt:
                q = train[g]["q"][name]
                lam = min(q * t, train[g]["cap"]) if np.isfinite(q * t) else train[g]["cap"]
                lam_all.append(lam), star_all.append(train[g]["oracle_lam"]), idx_all.append(g)
        lam_all, star_all = np.array(lam_all), np.array(star_all)
        c = float(np.quantile(star_all / lam_all, 1 - EPS))  # mean 1[c lam >= lam*] = 1 - eps
        ex = [100 * (np.interp(min(c * l_, train[g]["cap"]), train[g]["ovc"][0], train[g]["ovc"][1])
                     - train[g]["oracle_overlap"]) for l_, g in zip(lam_all, idx_all)]
        res[name] = float(np.mean(ex))
    th = res["theory"]
    best_cl = min((k for k in res if k != "theory"), key=lambda k: res[k])
    return ("theory" if th < res[best_cl] - GATE_MARGIN else best_cl), res


# ------------------------------------------------------------------ evaluation on the test fields
def evaluate(cal_pool, tests, name_of, dl, rng):
    """name_of: pivot name used for the calibration pool and the targets (same name). Returns per-draw
    coverage, per-field mean excess, the lambda matrix (draws x tests) and clamp count."""
    V = pivots(cal_pool, name_of)
    n = len(cal_pool)
    lam = np.zeros((DRAWS, len(tests)))
    for d in range(DRAWS):
        cal = rng.choice(n, size=min(N_CAL, n), replace=False)
        t = CP.quantile(V[cal], EPS, dl)
        for j, r in enumerate(tests):
            q = r["q"][name_of]
            lam[d, j] = min(q * t, r["cap"]) if np.isfinite(q * t) else r["cap"]
    P = np.array([[np.interp(lam[d, j], tests[j]["cur"]["lam"], tests[j]["cur"]["P"]) for j in range(len(tests))]
                  for d in range(DRAWS)])
    OV = np.array([[100 * (np.interp(lam[d, j], tests[j]["cur"]["lam"], tests[j]["cur"]["ov"]) - tests[j]["oracle_overlap"])
                    for j in range(len(tests))] for d in range(DRAWS)])
    below = int(sum((lam[:, j] < tests[j]["cur"]["lam"][0]).sum() for j in range(len(tests))))
    return dict(cov=P.mean(1), excess=OV.mean(0), lam=lam, below=below)


def matched(tests, lam):
    lo, hi = 0.2, 5.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        cov = np.mean([np.interp(min(mid * lam[d, j], tests[j]["cap"]), tests[j]["cur"]["lam"], tests[j]["cur"]["P"])
                       for d in range(0, DRAWS, 8) for j in range(len(tests))])
        lo, hi = (mid, hi) if cov < 1 - EPS else (lo, mid)
    return float(np.mean([100 * (np.interp(min(hi * lam[d, j], tests[j]["cap"]), tests[j]["cur"]["lam"], tests[j]["cur"]["ov"])
                                  - tests[j]["oracle_overlap"]) for d in range(0, DRAWS, 8) for j in range(len(tests))]))


def valid(ev, cls):
    return (ev["cov"].mean() >= 0.89) if cls == "marginal" else (np.mean(ev["cov"] >= 1 - EPS) >= 0.85)


def main():
    rng = np.random.default_rng(0)
    train, calp, tests = load(os.path.join(RES, "lowdata")), load(os.path.join(RES, "lowdata_v2")), load(os.path.join(RES, "lowdata_v3"))
    train = [r for r in train if r["ok"]]
    for r in tests:
        r["cur"] = pickle.load(open(os.path.join(RES, "lowdata_v3", f"curve_{r['key']}_{r['fi']}.pkl"), "rb"))
    cqr = CQR(train)
    for r in train + calp + tests:
        r["q"] = scales(r, cqr)
    for r in train:
        r["ovc"] = overlap_curve(r)
    out, tests_rows = [], []
    scen = [(k, [r for r in train if r["key"] == k], [r for r in calp if r["key"] == k], [r for r in tests if r["key"] == k])
            for k in KEYS] + [("mixed", train, calp, tests)]
    for sc, tr, cp, te in scen:
        cands = ["theory", "raw", "scale law"] + (["spec x scale law"] if sc == "mixed" else [])
        out.append(f"\n== {sc}: train {len(tr)}, calibration pool {len(cp)}, test {len(te)} fields")
        for cls, dl in (("marginal", None), ("PAC", DELTA)):
            choice, gres = gate(tr, cands, dl, rng)
            out.append(f"  [{cls}] gate (training only, proxy-matched excess pp): "
                       + ", ".join(f"{k} {v:+.2f}" for k, v in gres.items()) + f"  -> chooses {choice}")
            evs = {}
            names = ["raw", "scale law", "CQR", "theory"] + (["spec x scale law"] if sc == "mixed" else [])
            for nm in names:
                evs[nm] = evaluate(cp, te, nm, dl, rng)
            evs["gated"] = evaluate(cp, te, choice, dl, rng)
            for nm, ev in evs.items():
                lab = {"theory": "CE-EVT-R (ours)", "gated": f"CE-EVT-R-G (ours, uses {choice})"}.get(nm, nm)
                cv = ev["cov"]
                out.append(f"    {lab:38s} coverage mean {cv.mean():.3f}  P(cov>=0.9) {np.mean(cv >= 0.9):.2f}  "
                           f"valid {'yes' if valid(ev, cls) else 'NO '}  excess {ev['excess'].mean():+.2f} pp  "
                           f"matched-coverage excess {matched(te, ev['lam']):+.2f} pp  below-grid {ev['below']}")
            comps = ["raw", "scale law", "CQR"] + (["spec x scale law"] if sc == "mixed" else [])
            if sc == "mixed":  # C3: theory >= 10% better than every comparator
                for c in comps:
                    a, b = evs["theory"]["excess"], evs[c]["excess"]
                    p = stats.wilcoxon(a, b, alternative="less").pvalue if np.any(a != b) else 1.0
                    rel = (b.mean() - a.mean()) / b.mean() if b.mean() > 0 else np.nan
                    tests_rows.append(dict(claim="C3", sc=sc, cls=cls, comp=c, rel=rel, p=p, ok_valid=valid(evs["theory"], cls),
                                           ours=a.mean(), them=b.mean(), kind="superiority"))
            else:  # C4: gated non-inferior to the best comparator
                best = min(comps, key=lambda c: evs[c]["excess"].mean())
                a, b = evs["gated"]["excess"], evs[best]["excess"]
                diff = a - b - NI_MARGIN
                p = stats.wilcoxon(diff, alternative="less").pvalue if np.any(diff != 0) else 1.0
                tests_rows.append(dict(claim="C4", sc=sc, cls=cls, comp=best, rel=np.nan, p=p, ok_valid=valid(evs["gated"], cls),
                                       ours=a.mean(), them=b.mean(), kind="non-inferiority"))
            # C5: prediction of where the theory helps (rel >= 10% over raw)
            rel_raw = (evs["raw"]["excess"].mean() - evs["theory"]["excess"].mean()) / evs["raw"]["excess"].mean() \
                if evs["raw"]["excess"].mean() > 0 else np.nan
            tests_rows.append(dict(claim="C5", sc=sc, cls=cls, comp="raw", rel=rel_raw, p=np.nan, ok_valid=True,
                                   ours=evs["theory"]["excess"].mean(), them=evs["raw"]["excess"].mean(),
                                   kind=f"gate predicts {'gain' if choice == 'theory' else 'no gain'}"))
    # Holm over C3 and C4
    idx = [i for i, t in enumerate(tests_rows) if t["claim"] in ("C3", "C4")]
    ps = np.array([tests_rows[i]["p"] for i in idx])
    order, run = np.argsort(ps), 0.0
    for rnk, k in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rnk) * ps[k]))
        tests_rows[idx[k]]["p_holm"] = run
    out.append("\n== claims")
    for t in tests_rows:
        if t["claim"] == "C3":
            ok = t["ok_valid"] and t["rel"] >= 0.10 and t["p_holm"] < LEVEL
            out.append(f"  C3 mixed [{t['cls']:8s}] vs {t['comp']:18s} ours {t['ours']:+.2f} vs {t['them']:+.2f}  rel {100 * t['rel']:+.1f}%  "
                       f"p_holm {t['p_holm']:.4f}  {'MET' if ok else 'NOT MET'}")
        elif t["claim"] == "C4":
            ok = t["ok_valid"] and t["p_holm"] < LEVEL
            out.append(f"  C4 {t['sc']} [{t['cls']:8s}] gated vs best ({t['comp']}) {t['ours']:+.2f} vs {t['them']:+.2f}  "
                       f"non-inferiority p_holm {t['p_holm']:.4f}  valid {t['ok_valid']}  {'MET' if ok else 'NOT MET'}")
    hits = 0
    c5 = [t for t in tests_rows if t["claim"] == "C5"]
    for t in c5:
        gain = (t["rel"] >= 0.10) if np.isfinite(t["rel"]) else False
        pred = t["kind"].endswith("predicts gain")
        hits += gain == pred
        out.append(f"  C5 {t['sc']:5s} [{t['cls']:8s}] {t['kind']:22s} actual theory vs raw rel {100 * t['rel']:+.1f}%  {'hit' if gain == pred else 'MISS'}")
    out.append(f"  C5 prediction hits {hits}/{len(c5)}")
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(RES, "lowdata_v3", "summary.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
