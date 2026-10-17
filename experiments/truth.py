"""Model-mismatch "truth" variants for the revision experiment RV4 (docs/prereg_revision.md).

The nominal simulator, theory and MC twin are untouched; a variant only attaches switches to a Condition built
exactly as the nominal one (same random draws), with its own random stream for the extra disturbances.
"""
import numpy as np

import exp_system as E

VARIANTS = {
    "nominal": {},
    "T1 wet patches": dict(patches=dict(rate=1 / 50.0, len=(5.0, 20.0), scale=0.02)),
    "T2 trailed implement": dict(implement=dict(hitch=5.0, crab=1.0)),
    "T3 speed and actuation": dict(speed=(1.5, 3.0), latency=0.15, deadband=float(np.radians(0.3))),
    "T4 degraded GNSS": dict(gnss_scale=1.5),
    "T5 levelled terrain": dict(terrain=0.25),
    "T6 combined": dict(patches=dict(rate=1 / 50.0, len=(5.0, 20.0), scale=0.02), implement=dict(hitch=5.0, crab=1.0),
                        speed=(1.5, 3.0), latency=0.15, deadband=float(np.radians(0.3)), gnss_scale=1.5),
}
SHORT = {k: k.split()[0] for k in VARIANTS}


def make_cond(rng, n, reg, variant, seed):
    cond = E.make_cond(rng, n, reg)
    tr = dict(VARIANTS[variant])
    if not tr:
        return cond
    cond.truth_rng = np.random.default_rng([seed, 7919])
    if "gnss_scale" in tr:
        cond.rtk_scale = tr.pop("gnss_scale")
    if "speed" in tr:
        cond.truth_speed = cond.truth_rng.uniform(*tr["speed"], n)
    cond.truth = tr if tr else None
    return cond
