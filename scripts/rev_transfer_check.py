"""Experiment A1 with the transfer check applied (descriptive, post hoc; reviewer request, round 2).

On every field whose mean deployed CE+ margin exceeds the reference margin, the CE+ result is replaced by the
assumption-free CE result of the same field (fall back to CE). The registered runs drew z per operation, so the
operation-level check would refuse only some operations; the field-level replacement is therefore a conservative
reading (more fallbacks than the operation-level check). Output: results/revision/rv8_transfer_check.txt
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
d = pd.read_csv(os.path.join(ROOT, "results", "v8", "system_v8.csv"))
CE = "BCD + LQR-I + CE (ours)"
COMP = {"marginal": ("BCD + LQR-I + CE+ (ours, v8)", "Conformal predictive programming (Zhao et al.)",
                     "Conformal planning, pair-level union bound (Lindemann et al.)"),
        "PAC": ("BCD + LQR-I + CE+ PAC (ours, v8)", "Conformal predictive programming, PAC delta=0.1",
                "Conformal planning, pair-level union bound, PAC delta=0.1")}
out = [__doc__.strip(), ""]
for reg in sorted(d.regime.unique()):
    dr = d[d.regime == reg]
    ce = dr[dr.system == CE].set_index("field")
    out.append(f"== {reg}")
    for cls, (cep, cprp, ubcp) in COMP.items():
        v = dr[dr.system == cep].set_index("field").copy()
        fb = v.lam_mean > v.lam_ref + 1e-9
        w = v.copy()
        for c in ("overlap", "p_nomiss", "regret_pp", "e_miss"):
            w.loc[fb, c] = ce.loc[w.index[fb], c]
        o_c = dr[dr.system == cprp].set_index("field").overlap.reindex(w.index)
        o_u = dr[dr.system == ubcp].set_index("field").overlap.reindex(w.index)
        out.append(f"  {cls}: fields falling back to CE {int(fb.sum())}/30")
        for lab, x in (("CE+ as registered", v), ("CE+ with transfer check", w)):
            out.append(f"    {lab:26s} pooled P(no miss) {x.p_nomiss.mean():.3f}  overlap {100 * x.overlap.mean():.2f}%  "
                       f"regret {x.regret_pp.mean():+.2f} pp  missed area {100 * x.e_miss.mean():.3f}%  "
                       f"reduction vs CPrP {100 * (1 - x.overlap.mean() / o_c.mean()):.1f}%  vs UBCP {100 * (1 - x.overlap.mean() / o_u.mean()):.1f}%")
        out.append(f"    CPrP overlap {100 * o_c.mean():.2f}%  UBCP overlap {100 * o_u.mean():.2f}%")
txt = "\n".join(out)
open(os.path.join(ROOT, "results", "revision", "rv8_transfer_check.txt"), "w").write(txt + "\n")
print(txt)
