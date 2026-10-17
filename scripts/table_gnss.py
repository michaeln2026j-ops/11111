"""Table 1 of the manuscript: horizontal error of the processed NOAA CORS series per receiver grade (30 s epochs,
first 30 min after each daily cold start removed, as used by core.gnss_bank before interpolation to 1 Hz).

    python3 scripts/table_gnss.py     # -> results/table_gnss.txt
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "experiments"))
import core  # noqa: E402

z = np.load(os.path.join(core.DATA, "cors_errors.npz"), allow_pickle=True)
lines = ["Grade | station-pair-days | epochs | RMS (cm) | 95% (cm) | 99.9% (cm) | max (cm)"]
for g in ("rtk_fix", "rtk_float", "dgps", "spp"):
    H = []
    for s in z[g]:
        t = np.asarray(s["t"], float)
        keep = t >= t[0] + core.CONVERGE_S
        H.append(np.hypot(np.asarray(s["en"])[keep], np.asarray(s["ee"])[keep]))
    h = np.concatenate(H)
    lines.append(f"{g} | {len(z[g])} | {len(h)} | {100 * np.sqrt(np.mean(h ** 2)):.1f} | {100 * np.quantile(h, 0.95):.1f} | "
                 f"{100 * np.quantile(h, 0.999):.1f} | {100 * h.max():.0f}")
txt = "\n".join(lines)
print(txt)
open(os.path.join(HERE, "..", "results", "table_gnss.txt"), "w").write(txt + "\n")
