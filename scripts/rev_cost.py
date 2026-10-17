"""Cost analysis (descriptive; docs/prereg_revision.md RV1, extended with the nominal margin curves of
scripts/rev_sims.py): expected cost of a margin = overlap + r * missed area (both in % of the main area), for cost
ratios r = cost of a missed unit area / cost of an over-applied unit area.

Policies per field: vendor (2x pass-to-pass), farmer-tuned (v8 values), the field's 0.9-oracle (what an ideally
calibrated eps = 0.1 certificate deploys), CE-q from 100 / 22 bank runs (marginal / PAC), and the cost-optimal
margin for each r (a reference that needs the test distribution). Also the overlap saved by a gap tolerance tau.

    python3 scripts/rev_cost.py     # -> results/revision/rv_cost.txt
"""
import glob
import os
import pickle
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import ceplus as CP  # noqa: E402

REV = os.path.join(HERE, "..", "results", "revision")
FARMER = {"R1": 0.12, "R2": 0.14, "R3": 0.35}
VENDOR = {"R1": 0.025, "R2": 0.025, "R3": 0.20}
RS = (1, 3, 10, 30, 100, 300)


def at(c, key, lam):
    lam = np.clip(lam, c["lam"][0], c["lam"][-1])
    return (float(np.interp(lam, c["lam"], c["P_raw"])), 100 * float(np.interp(lam, c["lam"], c["ov"])),
            100 * float(np.interp(lam, c["lam"], c["emiss"])))


def oracle(c, p=0.9):
    i = int(np.argmax(c["P"] >= p))
    return c["lam"][i] if i == 0 else float(np.interp(p, c["P"][i - 1:i + 1], c["lam"][i - 1:i + 1]))


def main():
    out = ["Cost analysis (descriptive). cost = overlap % + r x missed-area %. Nominal model, hard edge, "
           "margin curves of results/revision/mm_nominal_*.pkl (200 test runs per grid point)."]
    for key in ("R1", "R2", "R3"):
        recs = [pickle.load(open(f, "rb")) for f in sorted(glob.glob(os.path.join(REV, f"mm_nominal_{key}_*.pkl")))]
        recs = [r for r in recs if len(r["cur"]["lam"]) and r["cur"]["P"].max() >= 0.9 and "emiss" in r["cur"]]
        if not recs:
            continue
        out.append(f"\n== {key}: {len(recs)} fields")
        pol = {}
        for r in recs:
            c = r["cur"]
            lam = {"vendor 2x p2p": VENDOR[key], "farmer-tuned": FARMER[key], "0.9-oracle (ideal eps=0.1)": oracle(c),
                   "CE-q n=100 marginal": CP.quantile(r["bank"][:100], 0.1),
                   "CE-q n=22 PAC": CP.quantile(r["bank"][:22], 0.1, 0.1)}
            for nm, l in lam.items():
                pol.setdefault(nm, []).append(at(c, key, l))
            grid = np.linspace(c["lam"][0], c["lam"][-1], 400)
            P = np.interp(grid, c["lam"], c["P_raw"])
            ov, em = 100 * np.interp(grid, c["lam"], c["ov"]), 100 * np.interp(grid, c["lam"], c["emiss"])
            for rr in RS:
                i = int(np.argmin(ov + rr * em))
                pol.setdefault(f"cost-optimal r={rr}", []).append((P[i], ov[i], em[i]))
        out.append(f"  {'policy':28s} {'P(no miss)':>10s} {'overlap %':>9s} {'missed %':>9s} " +
                   " ".join(f"{'cost r=' + str(rr):>10s}" for rr in RS))
        for nm, v in pol.items():
            v = np.array(v)
            out.append(f"  {nm:28s} {v[:, 0].mean():10.3f} {v[:, 1].mean():9.2f} {v[:, 2].mean():9.3f} " +
                       " ".join(f"{v[:, 1].mean() + rr * v[:, 2].mean():10.2f}" for rr in RS))
        o = np.array(pol["0.9-oracle (ideal eps=0.1)"]); vd = np.array(pol["vendor 2x p2p"]); fm = np.array(pol["farmer-tuned"])
        for nm, b in (("vendor", vd), ("farmer-tuned", fm)):
            dm = b[:, 2].mean() - o[:, 2].mean()
            dov = o[:, 1].mean() - b[:, 1].mean()
            out.append(f"  break-even r (0.9-oracle vs {nm}): {dov / dm:.1f}" if dm > 0 else
                       f"  break-even r (0.9-oracle vs {nm}): none (no fewer misses)")
        for tau in (0.02, 0.05, 0.10):
            sav = [at(r["cur"], key, oracle(r["cur"]))[1] - at(r["cur"], key, max(oracle(r["cur"]) - tau / 2, r["cur"]["lam"][0]))[1]
                   for r in recs]
            out.append(f"  gap tolerance tau = {100 * tau:.0f} cm: overlap saved {np.mean(sav):.2f} pp (margin lowered by tau/2)")
    txt = "\n".join(out)
    open(os.path.join(REV, "rv_cost.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
