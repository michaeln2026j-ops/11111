# Review R09: Simulation-based evaluation and sim-to-real transfer

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)
**Reviewer expertise:** vehicle and terrain-interaction models, slip, simulator validation against field data, sim-to-real transfer.
**Material inspected:** manuscript.md, supplementary.md (Appendices B, C, E), `experiments/core.py` (simulator), `experiments/evt_theory.py` (interfaces only), `experiments/exp_real.py`, `results/real.csv`, `results/real_aci.csv`.

---

## 1. Summary

The paper treats the probability of leaving an unworked strip between parallel passes as a chance constraint and reduces the zero-miss event to a scalar run score, the covering radius of the executed passes (Lemma 1). It then sets the footprint margin by split-conformal or PAC calibration of that score on a reference plan with at least as many passes as the deployed plan (CE, CE+). For fields with no history it builds a five-layer Gaussian extreme-value theory from the linearised closed loop (L1 covariance, L2 Kac–Rice pair and edge exceedance, L3 Bonferroni product, L4 mixture over operating conditions, L5 Gumbel law). It uses the theory's predicted 0.9 quantile only as a ratio pivot for cross-field conformal calibration (CE-EVT-R). All quantitative evidence comes from one closed-loop kinematic simulator. Field boundaries come from harvester trajectories, terrain from Copernicus GLO-30, and GNSS error from static NOAA CORS baselines processed with RTKLIB. The pre-registration and the reporting of failed claims are exemplary. However, Section 6.7, "Field validation on a real vehicle", is a TODO. An offline replay on CitrusFarm robot logs is present in the repository (`results/real.csv`) but is not reported, and in that replay the method under-covers its target.

## 2. Recommendation

**Major revision**, close to reject-and-resubmit for this journal. The statistical part (exact score, dominating reference plan, Proposition 5 validity) is sound and does not depend on the simulator. The headline efficiency results and the "theory predicts the margin without run data" claim are a different matter. They are statements about how well an analytical model agrees with a simulator that shares its structure, parameters and condition distribution. With no real-vehicle evidence, CEA readers cannot judge the practical claims, for example "the theory pivot cut excess overlap from 29.8 to 3.0 pp" or "misses under DGPS concentrate at field edges".

| Criterion | Score (1–10) |
|---|---|
| Novelty | 7 |
| Soundness (statistical core / simulation-based claims) | 7 / 4 → overall 5 |
| Practical relevance (as submitted, no real data) | 4 |
| Clarity | 6 |

## 3. Strengths

1. **The guarantee is distribution-free.** CE, CE+ and Proposition 5 give finite-sample guarantees that do not depend on the theory or the simulator being right. Section 4.3 states this clearly. This is the part most likely to survive transfer to real machines.
2. **Real error inputs where it matters most.** Using real CORS GNSS error series (including wrong fixes and float drift, Table 1) and executing passes in real time order, so that adjacent passes read the same error series one pass duration apart, is much better than i.i.d. Gaussian GNSS noise. It is the right way to expose the common-mode versus pass-to-pass distinction.
3. **Transparent protocol.** Pre-registration by commit, labels for developmental, post hoc and pre-registered results, failed claims reported (E-low v1, C3, C4), and an explicit admission that within-configuration pivots are equivalent (Sections 6.4, 7.2).
4. **A physically interpretable mechanism.** Theorem 3(b): common-mode DGPS error cancels in interior gaps but not at field edges. This prediction can be tested on real data.
5. **Fair comparator construction.** Shared simulator, fields, evaluator and common random numbers across systems, about 25 baselines, and comparisons within a guarantee class.

## 4. Major issues

### M1. Circularity: the theory is verified against the simulator it was built from, not validated
**Location.** Sections 5.3, 6.2, 6.6 (Tables 3, 4, 8, 9, Fig. 2, Fig. 6); `experiments/evt_theory.py`.
**Why it matters.**
- L1 linearises exactly the model coded in `core.simulate`: kinematic bicycle, 0.25 s lag, the same saturation and rate limits, the same LQR-I gains, the same OU slip with 2 s correlation, the same roll-antenna term with $h=2.6$ m, and the same integrator clamp at 0.3.
- `predict_cdf` calls `core.simulate(..., ZeroRNG(), trace=...)` to get the noise-free trajectory around which it quasi-linearises.
- L4 averages over `make_cond`, which is the simulator's own condition sampler: moisture ~ Beta(2,3) or U(0.6, 0.9), $k_s = 0.15+0.85\,m\cdot\mathrm{LN}(0,0.25)$, roughness lognormal, $c\sim N(0.85,0.05)$, mount ~ $N(0,1.5\text{ cm})$, and the same CORS bank.
- The theory therefore knows the true generative distribution of every nuisance parameter. A log error of 0.029 (Table 9) measures numerical consistency between two implementations of the same model, that is, verification.
- Several layers were also modified because they disagreed with the simulator (Section 6.2: "introduced because earlier checks failed"; the edge terms were derived after observing DGPS bias; Supplementary B.3 lists two earlier edge-term versions that were rejected). The theory has been tuned against the simulator.

**Consequences.**
- (a) The claim that the theory predicts margins "1.7–3.7 times more accurately than data-driven regressors" (Abstract, Table 9, Fig. 6) is an unfair comparison. The ridge regression has to learn from one noisy run per field. The theory receives the exact parametric model and the exact condition distribution for free.
- (b) The mixed-fleet gain (Table 8, Fig. 5) depends on the theory capturing between-configuration scale. In practice that requires knowing slip gains, roll-compensation quality, controller gains and the moisture distribution for each machine and field. None of these is available "without run data".
- (c) Proposition 8's "prediction from the theory alone" (Fig. 7) inherits the same issue.

**Concrete fix.**
1. Rename the evidence in Section 6.2 and Table 9 as model verification, and say so in the abstract.
2. Run a mismatch study. Perturb the simulator, but not the theory, in ways that matter physically, and report the theory's log error and CE-EVT-R excess overlap as a function of each mismatch:
   - a dynamic tyre model (cornering stiffness, relaxation length) instead of kinematic side-slip;
   - slip nonlinear in slope, with soil-dependent saturation;
   - roll from a vehicle suspension model and micro-terrain, not from DEM gradient;
   - a trailed or three-point implement with its own lateral dynamics;
   - speed variation;
   - a controller other than LQR-I without telling the theory;
   - a moisture distribution different from the assumed Beta(2,3).
3. Give the theory only quantities that are identifiable in practice: nominal controller gains from the vendor, slope from the DEM, and a moisture prior that is deliberately misspecified. Show what remains of the 29.8 → 3.0 pp advantage.
4. Compare the theory with a regression that is given the same physical inputs the theory consumes, such as slope statistics, pass length, GNSS grade, width and controller bandwidth. Currently the regressor's features differ from the theory's inputs.

### M2. No real-vehicle evidence; the real-data replay that exists is unreported and adverse
**Location.** Section 6.7 (TODO), Section 7.3(1), Supplementary C.1 ("not summarised"), `results/real.csv`, `results/real_aci.csv`, `experiments/exp_real.py`.
**Why it matters.**
- CEA is an applied journal. Every number in the paper comes from simulated execution.
- The repository contains a trace-driven replay on CitrusFarm RTK robot passes: 106 passes in `exp_real.py`, versus "123 rows" in the manuscript, which is inconsistent. No simulator is involved, which makes it the only sim-free evidence the authors have.
- My aggregation of `results/real.csv` gives the following pooled P(no miss) at $\varepsilon=0.1$ for "CE-U (ours, uniform)":
  - 0.856 under the random 50/50 split;
  - 0.807–0.854 under leave-one-sequence-out;
  - 0.814–0.878 under leave-one-block-out;
  - 0.826 and 0.838 under leave-one-day-out.
- So the method under-covers in every split, including the random split, where exchangeability should hold most nearly.
- Overlap is about 28% at a margin of about 0.65 m for $w=6$ m and $K=3$. That suggests the replayed "error" is dominated by orchard row-geometry irregularity rather than tracking error.
- Whatever the cause (dependence between overlapping test windows, splits that are not exchangeable, the older CE-U variant, or a bug), this is exactly the sim-to-real signal a reader needs. Leaving it out while claiming "the guarantee held in 26 of 26 checks" is not acceptable.

**Concrete fix.**
1. Report the replay in full, with the current method (CE+ or CE marginal and PAC rather than CE-U), and explain the under-coverage.
2. Clarify what the ground truth is. If the offsets are the RTK-reported position relative to a fitted row line, GNSS error is invisible in them and the data test row geometry, not pass-to-pass accuracy.
3. Use non-overlapping test windows, or account for their dependence, when testing marginal coverage.
4. Reconcile 106 versus 123 rows.

### M3. Simulator fidelity is low for the terrain and slip claims the paper relies on
**Location.** Section 6.1 "Simulator", Supplementary C.1, `core.py` lines 1–25 and 275–388.
**Specific concerns.**
- **Kinematic model with a heuristic side-slip.** $\beta=-0.35\,k_s\,g_{lat}+\mathrm{OU}$ is a slope-proportional slip angle with no tyre or soil mechanics: no cornering stiffness, no load transfer on side slopes, no dependence on speed, ballast or tyre pressure, no wheel–soil sinkage, no implement draft. The constant 0.35 and the $k_s$ and moisture mapping are not referenced or identified from data. R2 "hilly-wet" is the regime where slip matters most, yet slip is the least grounded component.
- **Terrain resolution and paddy geometry.** GLO-30 has 30 m posting and is a DSM in places. Lateral gradient is looked up by nearest neighbour on a 1 m resampled grid (`Field.gy`), which produces step discontinuities, as the authors' own "jup/jdn" statistical linearisation acknowledges. More fundamentally, R2 and R3 use paddy fields in hilly southern China. Individual paddies are laser-levelled or terraced basins, so the in-field cross-slope is near zero, and a 30 m DEM spreads inter-terrace relief across the field. The simulator may therefore attribute large side-slopes, roll offsets and slip to fields that are in reality flat. The terrain-driven between-field variation that the theory pivot exploits may be partly a DEM artifact.
- **Roll from DEM only.** `roll = arctan(g_v)` ignores suspension and tyre compliance and the micro-relief (ruts, bunds, clods) that dominates roll-induced antenna error at 2.6 m height on real tractors. That error is high-frequency and non-Gaussian, which is exactly what L1 would not capture.
- **Implement = vehicle reference point.** The footprint is centred on the vehicle trajectory `d`. Real sprayers and drills are often trailed or three-point mounted, with their own lateral offset dynamics and a slope-dependent dog-tracking offset. For drills and spreaders the effective working width is not a hard interval either.
- **Speed 2 m/s, constant.** This is slow for spraying (typically 3–8 m/s). Speed changes the closed-loop bandwidth, the along-track correlation length (hence $N$ in Theorem 6) and the time between adjacent passes (hence GNSS common-mode cancellation). Headland turns have a fixed duration (`t_turn`), and line acquisition is modelled as a 3 cm Gaussian residual.
- **GNSS.** The CORS antennas are static geodetic antennas on long baselines (5–30 km). Interpolating 30 s epochs to 1 Hz and adding i2Nav high-frequency residuals is a plausible patch. However, it misses vehicle-specific multipath, canopy and tree-line masking at field edges, which bear directly on the edge-miss claim, and correction-link outages. The authors concede that RTK is "a lower bound". That makes the validity results optimistic for target-field-free calibration, whose scale is set by the simulated error.
- **No validation of the simulator itself.** No figure compares simulated pass-to-pass error, XTE spectra or slope-induced offsets with any published field measurement. ISO 12188-1/-2 style pass-to-pass tests, or published autosteer accuracy trials on slopes, could serve.

**Concrete fix.**
1. Add a simulator-validation subsection that compares simulated pass-to-pass error distributions (RMS, 95%, 99.9% and the 15-min pass-to-pass statistic) with published autosteer trials or vendor test reports for each GNSS grade, on flat and sloped ground.
2. Report a sensitivity analysis of the key outcomes (theory accuracy, CE+ overlap reduction, mixed-fleet gain) to the slip constant, roll-compensation level, speed, DEM resolution (for example LiDAR-derived 1–5 m DEMs where available, or synthetic terraced fields) and implement type.
3. Justify, or drop, the claim that R2 represents "hilly-wet" operation on paddy.

### M4. The probe-line normalisation of CE+ is a simulator artifact until shown otherwise
**Location.** Section 4.2, Algorithm 2, Section 7.3(1).
**Why it matters.** CE+ normalises by the headland probe-line XTE RMS. In the simulator the measured XTE contains the antenna position error, including GNSS, and comes from the same per-run condition (moisture, $k_s$, roughness) that drives the infield passes, so they are correlated by construction. On a real vehicle the probe line runs on the headland, which has different compaction, slope and canopy masking from the infield, and the autosteer-reported XTE is blind to GNSS error, the dominant term under DGPS. The authors acknowledge that the relation is unverified. CE+ is the headline method of the confirmatory comparison.
**Concrete fix.** Report the simulated correlation between probe XTE and run score per regime. Repeat the v8 comparison with a probe-line condition that is independent of, or only partially correlated with, the infield condition. Validity still holds by exchangeability, but this shows how much of the efficiency gain survives. The gate may then turn the normalisation off; say so.

### M5. Efficiency claims inherit simulator fidelity, and the comparators may be handicapped by it
**Location.** Table 5, Section 6.3, abstract ("4.0–54.7% less overlap").
**Why it matters.** Part of the gain over CPP and Lindemann is attributed to their over-coverage when calibrated on the nominal plan. The size of that over-coverage depends on how strongly the score distribution changes with pass count. In the simulator that is driven by the plan-dependent terrain features and the time-alignment of GNSS error, both of which are modelled rather than measured. Different slip or terrain models could change the reductions materially, especially in R2, where the gain is already only about 4%.
**Concrete fix.** Report the CE+ vs CPP and Lindemann overlap reductions under at least two alternative simulator configurations (see M3). Better, replay real multi-pass logs, where the "decision dependence" can be emulated by re-spacing recorded passes as in `exp_real.py`.

### M6. Exchangeability and the "population of fields" in practice
**Location.** Proposition 5, Section 7.3(4).
**Why it matters.** In simulation, fields are i.i.d. draws from a curated list and each historical run is a fresh i.i.d. draw from the simulator's condition distribution. Real historical operations differ in season, operator, firmware, receiver, correction source and implement, and are not i.i.d. across fields. The adverse leave-one-day-out and leave-one-block-out results in `real.csv` are consistent with this concern.
**Concrete fix.** Add a simulated drift or shift experiment, for example calibration runs from a different season's moisture distribution or a firmware change to the controller. Discuss weighted or non-exchangeable conformal options (Barber et al., 2023, cited) for practitioners.

### M7. What minimal real-data validation would convince me
I would accept a revised paper that includes **both** of the following, even at modest scale.

**(A) Pass-level ground truth on a real machine.**
- **Fields and runs.** At least 10 to 15 fields (ideally 20 to 40, as planned), with one or two operations each, on a commercial RTK autosteer tractor. Ideally include a second receiver grade, using DGPS/SBAS on the same machine as a second configuration, so the mixed-fleet claim can be tested on real data.
- **Independent ground truth.** Use a PPK solution from a separate antenna on the implement, not the steering antenna. This captures implement offset and GNSS error.
- **Logging.** Log the autosteer XTE, including a headland probe line.
- **Analyses:**
  - (i) the exact run score of each operation versus the CE-EVT-R prediction, as the real analogue of Fig. 2, with the theory parameterised only from vendor data, DEM and a stated moisture prior;
  - (ii) leave-one-field-out coverage of CE-EVT-R with the registered rule;
  - (iii) the probe-XTE versus score correlation;
  - (iv) whether real DGPS misses concentrate at field edges (Theorem 3(b)).
- **Pre-registration.** Pre-register these analyses as the authors did for the simulations.

**(B) A simulator-to-field calibration check.** On a subset of passes, for example a few slope transects with a known cross-slope, compare measured lateral offsets and their spectra with simulator output under the identified parameters. This shows that the slip and roll model is in the right range.

A lighter fallback, acceptable only if machine access is impossible, has two parts. First, a correct, fully reported trace-driven replay on public agricultural-machine logs with independent ground truth. Second, the mismatch study of M1 showing robustness of efficiency to structural model error. Even then, the title and abstract should state that the efficiency evidence is simulation-only.

## 5. Minor issues

1. `core.py` docstring lists a "drift" term in $\dot d$ that does not appear in the code. Align the documentation with the implementation.
2. Section 6.1 should list the actual simulator constants: slip factor 0.35, $k_s$ mapping, roughness law, OU time constant 2 s, line-acquisition residual 3 cm, heading noise 0.15°, integrator clamp 0.3, and the turn model. Give a source or rationale for each.
3. Table 1: state whether the 1.39 m RTK-fixed maximum and 0.3–0.6 m wrong fixes survive the 30 s → 1 Hz interpolation unchanged, and how often an actual vehicle receiver would flag them, since autosteer systems typically disengage on fix loss.
4. Nearest-neighbour terrain lookup (`Field.gy`) introduces artificial gradient steps at 1 m cell boundaries. Use bilinear interpolation, or show that this is immaterial.
5. A constant speed of 2 m/s should be justified for the operations listed (spraying, seeding, tillage), or varied.
6. Harvester-derived field boundaries and working directions are combined with 1.5–6 m implements. Discuss whether these boundaries (and the main-area inset of 2w) are representative of the operations simulated.
7. Main-area overlap excludes headland swath. For CEA readers, also report input-cost-weighted or applied overlap in the main tables, not only in Supplementary S22.
8. Runtime (Section 4.4) is reported for a predictor that needs the full nonlinear noise-free simulation. Say so, because it means the "theory" requires the simulator at deployment time.
9. Section 6.7 and Appendix E (author notes, "remove before submission") must not appear in a submitted version. The data DOI is also still a TODO.
10. The RTKLIB demo5 commit was "not recorded". This harms reproducibility of the GNSS error bank. Archive the processed series themselves.
11. Fig. 2 should also show the 200-run reference uncertainty (bootstrap interval) for each point, especially under DGPS, where Table 4 notes that about 0.066 of the log-sd is reference noise.
12. The abstract should state "simulated execution" explicitly in the headline efficiency sentence. It currently says "In simulations driven by real field boundaries…" once, and the highlights do not say it at all.

## 6. Questions to the authors

1. Which inputs does `EVT_predict_cdf` receive that a farmer could not obtain? In particular, does it use the simulator's exact moisture, slip-gain and roll-compensation distributions, and the same CORS bank used to generate runs? What happens to Table 9 when these are misspecified by ±50%?
2. In `results/real.csv`, why does CE-U reach only 0.856 mean P(no miss) under the random split, where exchangeability should approximately hold? Are test windows (stride 1) overlapping and dependent? What is the ground-truth reference for the CitrusFarm offsets?
3. How large is the in-field lateral slope on the paddy fields from GLO-30 compared with the slope expected for levelled paddies? How much of the R2/R3 between-field variation in $\lambda^\star_f$ comes from terrain rather than field length or GNSS?
4. How do results change with a dynamic (tyre-force) vehicle model and a trailed implement? Did you try any alternative vehicle model at all?
5. Is the time alignment of GNSS error between adjacent passes (one pass duration plus a fixed turn time) preserved at realistic speeds of 3–5 m/s, and how sensitive is the DGPS edge-miss mechanism to it?
6. For the planned tractor campaign: what ground-truth accuracy do you expect from PPK on the implement, and how will you separate implement offset from GNSS error in the run score?
7. Would you be willing to pre-register the real-vehicle analyses (M7) with the same rigour as E-low v2/v3, including a claim that could fail, such as the theory's log error on real fields being below a stated value?
