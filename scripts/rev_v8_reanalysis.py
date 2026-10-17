"""RV1 (docs/prereg_revision.md): descriptive re-analysis of the v8 confirmatory runs, results/v8/system_v8.csv.

    python3 scripts/rev_v8_reanalysis.py   # -> results/revision/rv1_v8_reanalysis.txt
"""
import os

import numpy as np
import pandas as pd
from scipy.stats import binom

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
N_TEST = 200
# a field "meets" the 0.9 target unless its 200-run P(no miss) is significantly below 0.9 (one-sided 0.05)
K_MIN = int(min(k for k in range(N_TEST + 1) if binom.cdf(k, N_TEST, 0.9) >= 0.05))

MAIN = [("CE+ (ours)", "BCD + LQR-I + CE+ (ours, v8)"), ("CE+ PAC (ours)", "BCD + LQR-I + CE+ PAC (ours, v8)"),
        ("CE (ours, assumption-free)", "BCD + LQR-I + CE (ours)"), ("CE-q (ours)", "BCD + LQR-I + CE-q (ours, Thm 2)"),
        ("Conformal pred. programming", "Conformal predictive programming (Zhao et al.)"),
        ("Conformal pred. programming PAC", "Conformal predictive programming, PAC delta=0.1"),
        ("Pair-level conformal", "Conformal planning, pair-level union bound (Lindemann et al.)"),
        ("Pair-level conformal PAC", "Conformal planning, pair-level union bound, PAC delta=0.1"),
        ("Vendor spec overlap (2x p2p)", "BCD + LQR-I + spec overlap (2x vendor p2p)"),
        ("Farmer-tuned overlap", "BCD + LQR-I + farmer-tuned global overlap")]


def main():
    d = pd.read_csv(os.path.join(RES, "v8", "system_v8.csv"))
    d["reg"] = d.regime.str[:2]
    out = [f"RV1 re-analysis of results/v8/system_v8.csv (descriptive). Meet: >= {K_MIN}/200 runs miss-free."]
    for key in ("R1", "R2", "R3"):
        dr = d[d.reg == key]
        out.append(f"\n== {key}: oracle overlap {100 * dr.oracle_overlap.mean():.2f}%")
        out.append(f"  {'system':34s} {'P(no miss)':>10s} {'meet':>6s} {'miss %':>7s} {'miss p95 %':>10s} "
                   f"{'overlap %':>9s} {'applied %':>9s} {'regret pp':>9s}")
        rows = {}
        for lab, nm in MAIN:
            v = dr[dr.system == nm]
            if v.empty:
                continue
            meet = np.mean(np.rint(v.p_nomiss * N_TEST) >= K_MIN)
            rows[lab] = dict(P=v.p_nomiss.mean(), miss=100 * v.e_miss.mean(), ov=100 * v.overlap.mean(),
                             ap=100 * v.overlap_applied.mean())
            out.append(f"  {lab:34s} {v.p_nomiss.mean():10.3f} {meet:6.2f} {100 * v.e_miss.mean():7.3f} "
                       f"{100 * v.p95_miss.mean():10.3f} {100 * v.overlap.mean():9.2f} {100 * v.overlap_applied.mean():9.2f} "
                       f"{v.regret_pp.mean():+9.2f}")
        out.append("  break-even cost ratio r* (cost of 1% missed / cost of 1% over-applied) above which CE+ is cheaper:")
        for ce in ("CE+ (ours)", "CE+ PAC (ours)"):
            for b in ("Vendor spec overlap (2x p2p)", "Farmer-tuned overlap"):
                if ce in rows and b in rows:
                    dov, dm = rows[ce]["ov"] - rows[b]["ov"], rows[b]["miss"] - rows[ce]["miss"]
                    rs = dov / dm if dm > 0 else np.inf
                    out.append(f"    {ce:16s} vs {b:30s}: +{dov:.2f} pp overlap buys -{dm:.3f} pp missed  -> r* = {rs:.1f}")
        for lab, nm in (("CE+", "BCD + LQR-I + CE+ (ours, v8)"), ("CE+ PAC", "BCD + LQR-I + CE+ PAC (ours, v8)")):
            v = dr[dr.system == nm]
            out.append(f"  {lab}: lam0 (reference) {v.lam_ref.mean():.3f}; mean deployed lam {v.lam_mean.mean():.3f}; "
                       f"fields with mean deployed lam > lam0: {int((v.lam_mean > v.lam_ref + 1e-9).sum())}/30; "
                       f"flag dominated=False: {int((v.dominated.astype(str) == 'False').sum())}/30")
    out.append("\n== Meet rate and pooled P(no miss) of every CE / CE+ row on every stack")
    ce = d[d.system.str.contains(r"\(ours")]
    for (key, nm), v in ce.groupby(["reg", "system"]):
        meet = np.mean(np.rint(v.p_nomiss * N_TEST) >= K_MIN)
        flag = "  <-- below design (marginal ~0.85 expected; PAC ~0.99)" if ("PAC" in nm and meet < 0.9) or meet < 0.75 else ""
        out.append(f"  {key} {nm:55s} P {v.p_nomiss.mean():.3f}  meet {meet:.2f}{flag}")
    out.append("\n== Regret reduction of CE+ vs the two conformal planners (cells where CE+ regret > 0)")
    red = []
    for key in ("R1", "R2", "R3"):
        dr = d[d.reg == key]
        for cls, ce_nm, comps in (("marginal", "BCD + LQR-I + CE+ (ours, v8)", MAIN[4][1:] + MAIN[6][1:]),
                                  ("PAC", "BCD + LQR-I + CE+ PAC (ours, v8)", MAIN[5][1:] + MAIN[7][1:])):
            r0 = dr[dr.system == ce_nm].regret_pp.mean()
            for c in comps:
                rc = dr[dr.system == c].regret_pp.mean()
                if r0 > 0:
                    red.append(1 - r0 / rc)
                out.append(f"  {key} {cls:8s} CE+ {r0:+.2f} vs {c[:45]:45s} {rc:+.2f} -> {100 * (1 - r0 / rc):.1f}%")
    out.append(f"  range over cells with positive CE+ regret: {100 * min(red):.1f}-{100 * max(red):.1f}%")
    txt = "\n".join(out)
    os.makedirs(os.path.join(RES, "revision"), exist_ok=True)
    open(os.path.join(RES, "revision", "rv1_v8_reanalysis.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
