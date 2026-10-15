"""RV5 (docs/prereg_revision.md): headland laps. Share of runs whose binding term is a boundary term with and without
laps (same infield runs), required margins with laps vs the hard edge, and target-field CE-q validity with laps.

    python3 scripts/rev_laps.py     # -> results/revision/rv5_laps.txt
"""
import glob
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import ceplus as CP  # noqa: E402

REV = os.path.join(HERE, "..", "results", "revision")
EPS, DELTA = 0.1, 0.1


def oracle(c, p=0.9):
    if not len(c["lam"]) or c["P"].max() < p:
        return np.nan
    i = int(np.argmax(c["P"] >= p))
    return c["lam"][i] if i == 0 else float(np.interp(p, c["P"][i - 1:i + 1], c["lam"][i - 1:i + 1]))


def main():
    out = ["RV5 (pre-registered): headland laps. Binding share = fraction of runs at the reference plan whose largest "
           "term is a boundary term (field edge, or a gap between a lap and an infield pass)."]
    rng = np.random.default_rng(5)
    for key in ("R1", "R2", "R3"):
        L = [pickle.load(open(f, "rb")) for f in sorted(glob.glob(os.path.join(REV, f"lap_{key}_*.pkl")))]
        if not L:
            continue
        hb = np.mean([np.mean(r["hard_b"] >= r["hard_i"]) for r in L])
        lb = np.mean([np.mean(r["bank_b"] >= r["bank_i"]) for r in L])
        qh = np.array([np.quantile(r["hard"], 0.9) for r in L])
        ql = np.array([np.quantile(r["bank"], 0.9) for r in L])
        out.append(f"\n== {key}: {len(L)} fields")
        out.append(f"  binding term is a boundary term: hard edge {hb:.3f}, with laps {lb:.3f}")
        out.append(f"  0.9 score quantile at the reference plan: hard edge {qh.mean():.3f} m, with laps {ql.mean():.3f} m "
                   f"(mean ratio laps/hard {np.mean(ql / qh):.3f})")
        nom = {}
        for f in glob.glob(os.path.join(REV, f"mm_nominal_{key}_*.pkl")):
            m = pickle.load(open(f, "rb"))
            nom[m["fi"]] = m
        pairs = [(oracle(r["cur"]), oracle(nom[r["fi"]]["cur"]), np.interp(oracle(r["cur"]), r["cur"]["lam"], r["cur"]["ov"]),
                  np.interp(oracle(nom[r["fi"]]["cur"]), nom[r["fi"]]["cur"]["lam"], nom[r["fi"]]["cur"]["ov"]))
                 for r in L if r["fi"] in nom]
        pairs = np.array([p for p in pairs if np.all(np.isfinite(p))])
        if len(pairs):
            out.append(f"  oracle margin (P 0.9): with laps {pairs[:, 0].mean():.3f} m vs hard edge {pairs[:, 1].mean():.3f} m; "
                       f"main-area overlap {100 * pairs[:, 2].mean():.2f}% vs {100 * pairs[:, 3].mean():.2f}% ({len(pairs)} fields "
                       f"with both curves)")
        for n, dl, cls in ((22, DELTA, "PAC"), (100, None, "marginal"), (9, None, "marginal")):
            P = []
            for r in L:
                b, c = np.asarray(r["bank"]), r["cur"]
                if not len(c["lam"]):
                    continue
                k = CP.order_index(n, EPS, dl)
                idx = rng.random((500, len(b))).argsort(axis=1)[:, :n]
                lam = np.minimum(np.sort(b[idx], axis=1)[:, k - 1], r["cap"])
                P.append(np.interp(lam, c["lam"], c["P"]))
            P = np.concatenate(P)
            out.append(f"  CE-q with laps, n={n:3d} {cls:8s}: mean coverage {P.mean():.4f}, fraction >= 0.9 {np.mean(P >= 0.9):.3f}")
    txt = "\n".join(out)
    open(os.path.join(REV, "rv5_laps.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
