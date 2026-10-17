# Pre-registration: revision experiments (RV1–RV6)

Written and committed **before** any of the computations below were run. It responds to the 20 internal expert
reviews in `docs/paper/reviews/`. Real-vehicle validation is out of scope here.

General rules (all experiments):
- $\varepsilon=\delta=0.1$; marginal and PAC rules as in the manuscript (Section 4).
- No existing registered result is overwritten. New outputs go to `results/revision/`.
- Every number reported in the revised manuscript from these experiments is labelled *revision (pre-registered)* or
  *revision (descriptive)* as stated below. Outcomes are reported whatever they are.
- When a cross-field rule gives $+\infty$ (k > n), the field is counted as **refused**; refusal rates are reported,
  and coverage/overlap are reported (i) over deployed fields and (ii) with the registered fallback of the earlier
  resampling check (deploy the planner cap $0.4w$). The fallback is a practical rule, not part of the guarantee.

Fields: the 135 fields that already have theory predictions, run banks and margin curves (E-low v2 fields
50–79 and E-low v3 fields 5–19 of each regime). The CQR learner is trained only on the E-low v1 fields (indices 80+,
one run each), never on these 135.

---

## RV1 — Re-analysis of the v8 confirmatory runs (descriptive)

Source: `results/v8/system_v8.csv` (no new simulation). For every system of the BCD + LQR-I stack, per regime:
mean missed area fraction, 95th percentile of missed area, P(no miss), overlap, regret; meet rate per Proposition 7
for every CE/CE+ row of every stack (including stacks not in the main table); the fraction of fields on which CE+ had
`dominated = False`. Practice baselines (vendor-spec overlap, farmer-tuned overlap) are reported next to CE+ and the
two conformal planners.

**Expected-cost comparison.** For a cost ratio $r$ = (cost of 1% of the area missed) / (cost of 1% of the area
over-applied), expected cost per system $= \text{overlap} + r\cdot\text{mean missed area}$ (both in % of the main
area). Report, per regime, the break-even $r^\*$ above which CE+ is cheaper than each practice baseline, and the
literature-plausible range of $r$ for several operations (stated with its sources or as an explicit assumption).

## RV2 — Cross-field calibration: stronger baselines and per-configuration coverage (pre-registered)

Resampling exactly as `scripts/validity_resample.py` (random calibration split, one run per calibration field redrawn
from its 200-run bank, deployment read from the field's margin curve), 4000 replicates, mixed fleet of 135 fields,
$n_\mathrm{cal}\in\{25, 60\}$. Pivots:
1. raw pooling; 2. spec × scale law; 3. theory (registered CE-EVT-R scale; R3 additionally with field-edge terms,
   see RV6); 4. **Mondrian** (per-configuration conformal: the calibration fields of the target's own configuration
   only, raw scores); 5. **per-configuration scale** (pivot $q_f$ = median of the single-run scores of the calibration
   fields of $f$'s configuration, all fields then pooled; the median is computed on the calibration fields only);
   6. **CQR** (ridge on field + configuration features, trained on E-low v1 fields only, as in E-low v3);
   7. **MC twin** (pivot $q_f$ = 0.9 quantile of $m=1000$ independent runs of the *nominal* simulator on $f$'s reference
   plan, seeds disjoint from all banks and curves).

Outputs per pivot × class × $n_\mathrm{cal}$: overall mean coverage; **coverage per configuration** (mean over replicates
of the mean coverage of that configuration's target fields; PAC: fraction of replicates in which that configuration's
mean coverage ≥ 0.9); refusal rate; mean excess overlap (pp) over deployed fields and with the cap fallback.

Predictions (each is reported as met / not met):
- P2.1 (validity, guaranteed by Proposition 5): overall marginal mean coverage ≥ 0.895 and PAC fraction ≥ 0.88 for
  every pivot that refuses on < 1% of target fields.
- P2.2 (per-configuration coverage, not guaranteed): with raw pooling, the DGPS configuration's marginal coverage is
  below 0.85; with the theory pivot it is ≥ 0.88 in every configuration.
- P2.3 (Mondrian at $n_\mathrm{cal}=25$): refuses on more than 20% of target fields under the marginal rule and on
  essentially all (> 95%) under the PAC rule (about 8 fields per configuration < 22).
- P2.4 (efficiency at $n_\mathrm{cal}=60$, marginal, cap fallback): theory pivot mean excess ≤ Mondrian, per-config
  scale and CQR mean excess + 0.5 pp (i.e. not materially worse than the configuration-aware baselines), and MC twin
  within 0.5 pp of the theory pivot.

## RV3 — Target-field calibration with few runs (pre-registered)

CE-q (constant normalisation; the variant CE+ reduces to when the gate chooses constant σ) on each of the 135
fields: draw $n\in\{9, 15, 22, 40, 100\}$ runs from the field's bank (with replacement across replicates, without within),
2000 replicates per field and $n$; marginal for all $n$, PAC for $n\ge22$; deploy $\min(\hat\lambda,\text{cap})$ and read
P(no miss) and overlap from the margin curve. Also the farmer-tuned and vendor margins (the per-regime values used in
v8) read from the same curves. Report mean coverage, fraction of field × replicate cells with coverage ≥ 0.9, mean
excess overlap. Prediction P3.1: marginal mean coverage ≥ 0.895 for every $n$; P3.2: PAC fraction ≥ 0.88.

## RV4 — Model mismatch: the theory is not told how reality differs (pre-registered)

"Truth" simulator variants (theory, MC twin and all pivots keep the **nominal** model; calibration runs and test
runs come from the truth):
- **T1 wet patches:** per pass, Poisson patches (rate 1 per 50 m, length uniform 5–20 m) adding a slip angle
  $a\sim$ Student-$t_3$ scaled to 0.02 rad, sign random (heavy-tailed, spatially intermittent).
- **T2 trailed implement:** the footprint follows the implement, a first-order lag of the tractor offset over a
  hitch length of 5 m, plus a downhill crab of 1.0 m per unit lateral gradient.
- **T3 speed and actuation:** per-run speed uniform 1.5–3.0 m/s (controller gains designed at 2 m/s), 0.15 s
  steering latency, 0.3° deadband.
- **T4 degraded GNSS:** GNSS error × 1.5 (vehicle multipath, poorer sky view).
- **T5 levelled terrain:** lateral terrain gradient × 0.25 (terraced, levelled basins).
- **T6 combined:** T1 + T2 + T3 + T4 (terrain as DEM).

Per field and variant: a 200-run truth bank at the reference plan and a truth margin curve (28 geometric points from
$0.25\,\hat q$ to the cap, 200 runs each, common random numbers; truth $\lambda^\star$ = smallest grid λ with P ≥ 0.9,
interpolated). Analyses:
- A4.1 theory and MC-twin accuracy: mean and sd of $\log(\hat q/q_\mathrm{truth})$ per regime and variant.
- A4.2 cross-field resampling as RV2 (mixed fleet, $n_\mathrm{cal}=25$ and 60) per variant: coverage (overall and per
  configuration), refusal rate and excess overlap for raw pooling, spec × scale law, Mondrian, theory and MC twin.
- A4.3 target-field CE-q with $n\in\{22, 100\}$ per variant.

Predictions: P4.1 (guaranteed): overall validity of every non-refusing pivot in every variant (criteria as RV2).
P4.2: theory log-error sd stays below 0.15 in every regime and variant (i.e. well below the 0.39 between-configuration
spread that makes the pivot useful). P4.3: in the mixed fleet, the theory pivot's marginal mean excess (cap fallback,
$n_\mathrm{cal}=25$) is below 50% of raw pooling's and below that of spec × scale law in every variant.
P4.4: CE-q marginal mean coverage ≥ 0.895 in every variant.

## RV5 — Headland laps (pre-registered)

The registered evaluation treats the main-area boundary as a hard edge reached only by the outermost pass. Variant
**L**: one headland lap along each lateral side, planned so that its inner footprint edge reaches λ into the main area
(nominal overlap 2λ with the outermost pass, like an interior pair), driven after all infield passes (time-separated
GNSS error), simulated as a straight pass in the headland band and projected onto the boundary through its local
angle. Score and missed area are computed with the lap footprints included (exactness of Lemma 1 preserved).

Per field (135, nominal model): bank and margin curve with laps. Report: share of runs whose binding term (maximum of
the pair decomposition) is a boundary term, with and without laps, at the reference plan; truth $\lambda^\star$ with and
without laps; CE-q ($n=22, 100$) validity and excess with laps. Prediction P5.1: with laps, the boundary share under
DGPS falls below 50%; P5.2: CE-q validity holds (as RV3).

## RV6 — Theory with field-edge terms on all R3 fields; equal-budget Monte Carlo (descriptive)

Recompute the R3 theory with the field-edge terms (Theorem 3(b)) on all 45 R3 fields (15 already done), and the MC
twin on all 135 fields. Report accuracy against the bank quantile, and CPU time of each per field. No claim is made in
advance about which is more accurate; both are reported.

## RV7 — Tuned learned predictors (descriptive, post hoc)

Re-run the learning curves of Table 9 with cross-validated ridge (penalty by 5-fold CV on the training fields),
gradient boosting (sklearn, depth 2, 200 trees, CV over learning rate) and a theory + features hybrid with CV penalty
(which can shrink to the theory), trained on one run per field and on oracle targets.
