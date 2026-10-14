"""Is the theory pivot replaceable by a data-driven predictor? (secondary analysis, post hoc)

A field-feature regression  log lam*_f ~ features(f)  is trained per regime on the E-low v1 pool (fields 80+,
oracle lam* from many simulated runs: the best training signal such a predictor could get) and used as the
pivot scale q_f on the E-low v2 fields (50-79, disjoint), next to the theory quantile, the scale law and the
oracle (ideal). Reported per pivot: spread of lam_g / lam*_g over test fields (leave-one-field-out,
n_cal = 29, marginal and PAC) and the mean excess overlap of the resulting plans (deterministic in lam).

    python3 scripts/feature_pivot.py
"""
import glob
import math
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import ceplus as CP  # noqa: E402
import core  # noqa: E402
import exp_lib as L  # noqa: E402
import exp_lowdata as X  # noqa: E402
import exp_system as E  # noqa: E402

RES = os.path.join(HERE, "..", "results")


def features(F, r):
    lo, hi = F.lateral_range()
    return [math.log(max(r["N_len"], 2.0)), math.log(F.M.area), math.log(r["K0"]), F.z_mean_slope,
            float(np.mean([core.pass_feature(F, y) for y in np.linspace(lo, hi, 14)[1:-1]])), math.log(hi - lo)]


def load(key, d):
    rs = sorted([pickle.load(open(f, "rb")) for f in glob.glob(os.path.join(d, f"A_{key}_*.pkl"))], key=lambda r: r["fi"])
    return [r for r in rs if np.all(np.isfinite(r["Fhat"]))]


def main():
    out = []
    for key in ("R1", "R2", "R3"):
        rname, reg = X.regime(key)
        w = reg["w"]
        fields = core.load_fields(reg["kind"], w=w, seed=0)
        tr, te = load(key, os.path.join(RES, "lowdata")), load(key, os.path.join(RES, "lowdata_v2"))
        Xtr = np.array([features(fields[r["fi"]], r) for r in tr])
        ytr = np.log([r["oracle_lam"] for r in tr])
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-12
        A = np.c_[np.ones(len(tr)), (Xtr - mu) / sd]
        lam_ridge = 1.0
        beta = np.linalg.solve(A.T @ A + lam_ridge * np.diag([0] + [1] * (A.shape[1] - 1)), A.T @ ytr)
        r2_tr = 1 - np.var(ytr - A @ beta) / np.var(ytr)
        Xte = np.array([features(fields[r["fi"]], r) for r in te])
        q_feat = np.exp(np.c_[np.ones(len(te)), (Xte - mu) / sd] @ beta)
        orc = np.array([r["oracle_lam"] for r in te])
        q_th = np.array([X.inv_cdf(r["tgrid"], r["Fhat"], 0.9) for r in te])
        lg = np.array([math.sqrt(2 * math.log(max(r["N_len"], 2))) for r in te])
        S = np.array([r["S_hist"] for r in te])
        cor = lambda q: np.corrcoef(np.log(q), np.log(orc))[0, 1]  # noqa: E731
        out.append(f"\n{key}: train {len(tr)} fields (v1 pool), test {len(te)} (v2); feature model train R2 {r2_tr:.2f}; "
                   f"corr(log q, log lam*) on test: theory {cor(q_th):.2f}, features {cor(q_feat):.2f}, scale law {cor(lg):.2f}")
        out.append(f"   log-error sd on test: theory {np.std(np.log(q_th / orc)):.3f}, features {np.std(np.log(q_feat / orc)):.3f}")
        piv = {"raw (no pivot)": np.ones(len(te)), "scale law": lg, "learned features": q_feat,
               "theory (CE-EVT-R)": q_th, "oracle (ideal)": orc}
        ovc = {}

        def ov(i, lam):
            k = (i, round(float(lam), 4))
            if k not in ovc:
                Fg = fields[te[i]["fi"]]
                try:
                    ovc[k] = L.overlap_ratio(Fg, core.plan(Fg, w, float(lam), E.UNIT), w)
                except ValueError:
                    ovc[k] = np.nan
            return ovc[k]
        oo = np.array([ov(i, orc[i]) for i in range(len(te))])
        n = len(te)
        for tag, dl in (("marginal", None), ("PAC", 0.1)):
            for nm, q in piv.items():
                lam = np.array([q[g] * CP.quantile(np.delete(S / q, g), 0.1, dl) for g in range(n)])
                ex = np.array([100 * (ov(i, lam[i]) - oo[i]) for i in range(n)])
                out.append(f"   [{tag:8s}] {nm:20s} lam/lam* mean {np.mean(lam / orc):.3f} sd {np.std(lam / orc):.3f}  "
                           f"excess {np.nanmean(ex):+.2f} pp")
    txt = "\n".join(out)
    print(txt)
    with open(os.path.join(RES, "lowdata_v2", "feature_pivot.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()
