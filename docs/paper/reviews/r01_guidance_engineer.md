# Review R01: agricultural machinery guidance and auto-steer engineering

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (submitted to *Computers and Electronics in Agriculture*)

**Reviewer expertise:** GNSS auto-guidance and auto-steer systems, pass-to-pass accuracy specification and testing (ISO 12188-2), implement offsets and drift, headland management and section control, OEM practice.

**What I checked beyond the text:** the simulator (`experiments/core.py`: `Field`, `Condition`, `simulate`, `plan`, `evaluate`, `exact_scores`), the vendor and farmer baselines (`experiments/baselines/vendor.py`), the v8 per-field results (`results/v8/system_v8.csv`, `results/v8/summary.txt`), the GNSS summary (`experiments/data/cors_summary.csv`), the field metadata (`experiments/data/fields.json`) and Supplementary C–E. I ran only small read-only checks and no simulations.

---

## 1. Summary of the paper

The paper treats the lateral overlap between adjacent passes as a margin that should carry a stated probability of leaving no unworked strip. It shows that "zero missed area in the main field area" is equivalent to a scalar run score, the covering radius of the executed pass centres. It then calibrates that score with split-conformal or PAC quantiles computed on a more conservative reference plan (CE / CE+). CE+ also normalises the score by the cross-track-error RMS of a headland probe line. For fields with no history of their own, a five-layer Gaussian extreme-value model of the closed-loop vehicle predicts each field's 0.9-quantile margin, and this prediction is used only as a ratio pivot for conformal calibration across fields (CE-EVT-R), with one run on each calibration field. All evidence comes from simulation. Field outlines are real (Chinese harvester tracks), terrain comes from GLO-30, and GNSS error comes from US CORS baselines processed with RTKLIB. A pre-registered comparison on 90 fields reports 4–55% less main-area overlap than two academic conformal planners. A resampling check confirms the coverage guarantee, and the theory pivot greatly beats raw pooling in a mixed fleet of three machine configurations.

## 2. Recommendation

**Major revision.**

| Criterion | Score (1–10) |
|---|---|
| (a) Novelty | 6 |
| (b) Technical soundness | 5 |
| (c) Practical relevance | 4 |
| (d) Clarity | 5 |

The statistics are careful, and the pre-registration and reporting of failed claims are unusually honest. As guidance engineering, however, the work has three main problems:

- **Wrong objective for agronomy and economics.** It certifies "no gap of any width anywhere", which is not what operators or agronomists need, and it ends up recommending overlaps that no RTK user would accept.
- **Simulation does not model the mechanisms that cause real pass-to-pass and edge errors.** Headland passes, implement dynamics, the RTK integrity behaviour of commercial receivers, and paddy terrain are missing or unrealistic, so the headline physical finding (DGPS misses concentrate at field edges) is likely an artefact.
- **No real-vehicle data at all, and no account of how the calibration data could be obtained.** Section 6.7 is a TODO, and the paper does not explain how a real machine would produce the exact run score.

---

## 3. Strengths

- **A sound and useful reduction.** The zero-miss event is reduced exactly to a covering-radius score (Lemma 1), and this score is shown to be the smallest valid one (Lemma 2 / Theorem 1). The observation that calibrating on the nominal plan and deploying a plan with more passes reverses the dominance direction (Proposition 1) is correct, and the conformal-planning literature has largely ignored it.
- **Honest separation of evidence status.** Results are labelled pre-registered, exploratory, developmental or post hoc, and failed claims are reported (E-low v1, C3, C4, Table S20). The authors also downgrade their own E-low v2 "wins" after the matched-coverage analysis. Few papers in this journal show this level of transparency.
- **A real attempt at realistic inputs.** Real field polygons, a real DEM and real multi-season GNSS error series are used instead of Gaussian noise. Table 1 correctly points out that the RTK tail is heavy and non-Gaussian. The mounting bias, which flips sign in the field frame between up- and down-field passes, reproduces the familiar "skip every other pass" symptom.
- **Careful vendor terrain-compensation baseline.** The baseline is documented against patents and OEM help screens (`baselines/vendor.py`) and correctly avoids double compensation.
- **Correct separation of validity and efficiency in CE-EVT-R.** The guarantee does not rest on the physics model; the model affects only efficiency. The direct resampling check over both sources of randomness (Table 7) is the right test.
- **An actionable planning tool in Proposition 8.** It makes the useful point that per-field normalisation cannot remove within-field tail randomness, so PAC margins with one run per field are bounded below.

---

## 4. Major issues

### M1. The zero-miss objective does not match what an operator or agronomist needs, and the paper hides the resulting trade-off
**Location:** Section 3 (Objective), Section 6.1 (Metrics), Section 6.3, Section 7.4, Abstract, Highlights.

**Problem.** The constraint is P(M = 0) ≥ 0.9, where M counts any gap of positive width on any 1 m section (`core.evaluate` clips gaps at 0 with no tolerance). A 1 mm skip over 1 m of a 30 ha field therefore counts as a failure exactly like a 1 m skip over the whole field. No real operation is judged this way:

- A sprayer boom's pattern has overlapping nozzle fans at the swath edge.
- Broadcast spreaders are designed for 50–100% overlap.
- For a seeder, a "gap" is a slightly wide guess row.
- For tillage, a few centimetres of unworked soil are agronomically irrelevant.

**Evidence from the authors' own v8 file** (`results/v8/system_v8.csv`, column `e_miss`, mean expected missed fraction of the main area):

| Regime | 2 × vendor p2p rule: main-area overlap | 2 × vendor p2p rule: expected missed area | CE+: main-area overlap | CE+: expected missed area |
|---|---|---|---|---|
| R1 | 1.75% | 0.22% | 8.39% | 0.001% |
| R2 | 3.46% | 0.64% | 25.6% | 0.001% |
| R3 | 7.59% | 0.12% | 15.7% | 0.027% |

So in R2, CE+ applies roughly 22 pp more product over the whole main area to avoid about 0.6% under-application. For any input with a flat or concave yield response, this trade is strongly negative. The Introduction's argument (pesticide tonnage, nitrogen-use efficiency) actually argues *against* it.

The paper reports none of this. Statements such as "the vendor rule never met a 0.9 zero-miss target" and "left a gap on essentially every run" (Section 1, Section 7.4) are true only under this extreme criterion. The R1 oracle margin of 11.9 cm under RTK (4.7 times the 2.5 cm spec) makes the same point: certified zero-miss is driven by rare tail events, not by typical pass-to-pass performance.

**Fix.**
1. For every system, report the distribution of missed-area fraction and of maximum gap width alongside P(no miss).
2. Define and evaluate a tolerance-based score that counts as a miss only a gap wider than τ over a length of at least ℓ (for example τ = 5 cm, ℓ = 5 m, or values chosen per operation). The covering-radius machinery extends directly to this.
3. Add a cost-based analysis, with a cost per pp of overlap and a cost per % of missed area, per operation type. Use conformal risk control on missed-area fraction, which the paper cites but does not use (Appendix E admits this), as a comparator.
4. Remove or qualify the claims that the vendor rule fails.

### M2. The vendor baseline is a straw man and is mis-described as "current practice"
**Location:** Section 1, paragraph 2; Section 6.3 (v7 paragraph); Section 7.4, first bullet; Table 2.

**Problem.** The vendor specification (Deere StarFire, ±2.5 cm) is a one-dimensional, 15-minute, 95% statistic of the *pointwise* relative error between passes, under open sky on level ground. The paper sets the overlap to twice this value (a total of 5 cm, i.e. λ = 2.5 cm) and asks it to bound the *maximum* gap over the whole field at the 90% run level. That fails by construction; it says nothing about the specification or about practice.

The authors' own code header states that this is "the study's design rule ... NOT a manufacturer recommendation". The manuscript instead calls it "current practice" and "the vendor rule".

Real practice also includes things the paper never mentions:
- operator-set implement overlap in the display, typically 0–10 cm;
- automatic section control at boom or row-unit level;
- implement-width calibration;
- guess-row checks at planting.

**Fix.**
1. Describe the rule accurately as the authors' heuristic.
2. Add practice-representative baselines: common console overlap settings (0, 5, 10, 15 cm) evaluated on the full missed-area distribution (see M1), and a "95% / 99% p2p quantile" rule computed from the same logs.
3. State clearly that the vendor specification is not a whole-field maximum statistic.

### M3. Headland and field-edge modelling: the edge-miss mechanism and the "DGPS misses concentrate at field edges" finding are probably artefacts
**Location:** Section 3 (main area W = P inset by 2w), Fig. 1, Theorem 3(b), Section 6.2 (Table 4 and the paragraph after it), Section 7.1, Section 7.4 ("pay particular attention to boundary passes"), Conclusion.

**Problem.** The evaluated area is `M = P.buffer(-2w)`, so every boundary of W, including the two long sides parallel to the passes, borders the headland band. On a real field, headland passes driven around the perimeter cover that band.

The edge term in Lemma 1 and Theorem 3(b) treats the edge of W as a fixed line that the outermost infield pass alone must reach. This is equivalent to assuming either that no headland passes exist or that they are executed perfectly. Under DGPS, both assumptions are wrong:
- A real "edge" gap is a gap between the outermost infield pass and the innermost headland pass.
- These two passes are typically driven many minutes, sometimes hours, apart (headlands first or last).
- The relevant error is therefore a *time-separated pass-to-pass* difference, not a single-pass absolute error against a fixed boundary.

The physical explanation the paper gives ("no neighbour to cancel it") does not hold on a real field. The neighbour exists; it is merely driven at a different time. Fig. 1 makes this worse by labelling the region beyond the edge "outside the field".

The paper also ignores where most real overlap occurs:
- On small, irregular fields (the paddy fields here are 0.2–3.4 ha), most double application happens at headlands and point rows.
- Section control, and its latency and look-ahead, manages this zone.
- The authors' own secondary metric shows applied overlap of 30–49% in v8 (`results/v8/summary.txt`), against 8–26% in the main area.

The headline efficiency metric thus excludes the part of the field where most input is wasted.

**Fix.**
1. Simulate the headland passes, with the same vehicle and GNSS model and a realistic order (headlands first or last), and evaluate coverage over the whole field.
2. Recompute the edge terms as pairs of infield and headland passes with realistic time separation.
3. Either restrict all statements about the main area to "relative to an ideal headland", or remove the edge-concentration claim and the related practical guidance.
4. Correct Fig. 1.
5. Discuss section control and point-row coverage, at least qualitatively, and state that the method addresses only the lateral overlap of parallel infield passes.

### M4. The calibration data that the method requires cannot be obtained from machine logs, and the sample sizes used are unrealistic
**Location:** Section 4 (Algorithms 1–3), Section 6.1 (protocol: "calibrated on 100 runs per field"), Section 7.4, Section 6.7.

**(a) Observability.** The exact score is computed from the *true* executed implement position.

- An auto-steer log records the *GNSS-estimated* position, which already contains the GNSS error that dominates the score.
- In the simulator, `meas` contains `eps_y`, while the footprint is evaluated at the true position `d`.
- A logged run therefore cannot yield S. Every calibration run, including the "one historical run per field" of CE-EVT-R, would need independent ground truth (PPK with a separate base, or as-applied sensing of the worked strip).

The paper says this only in passing, in the TODO of Section 6.7. Yet the Abstract, Section 4.3 and Section 7.4 speak of "logged runs" and "historical operations" as if they were freely available.

**(b) Sample size.** The confirmatory v8 comparison uses n_cal = 100 runs per field (`exp_system.py --n-cal 100`). The paper itself says a field "is worked a few times per year" and that n ≥ 9 (marginal) or n ≥ 22 (PAC) is the minimum. No experiment evaluates CE+ at n = 9–25 runs on the target field. In addition, these calibration operations must be driven at the conservative reference plan π(λ0), and that overlap cost is never counted.

**(c) Exchangeability across operations.** Successive operations on a field differ in season, soil state, implement, crop height, receiver firmware and correction service. Persistent machine biases (implement offset, TCM calibration, antenna offset) are constant until someone recalibrates. The simulator instead redraws `mount` i.i.d. for every run (`Condition.mount`), which gives exchangeability by construction.

**Fix.**
1. State explicitly what instrumentation is needed to observe S, and estimate its cost.
2. Add CE+ results at n ∈ {9, 15, 25} on the target field, including the cost of the calibration operations.
3. Add a sensitivity study with persistent per-machine biases and seasonal drift, or a weighted or non-exchangeable conformal variant (Barber et al., 2023, already cited).

### M5. The vehicle–implement model omits the main real sources of pass-to-pass error
**Location:** Section 6.1 (Simulator), Supplementary C.1, `core.simulate`.

The footprint is attached rigidly to the vehicle reference point, and several other simplifications follow:

1. **No implement dynamics.** There is no trailed or semi-mounted implement model, no implement side-hill drift, no hitch lateral offset and no active or passive implement steering. On slopes, implement drift relative to the tractor is often *the* dominant pass-to-pass error, and it differs between up- and down-slope passes.
2. **One speed.** A single 2 m/s (7.2 km/h) is used, while sprayers run at 10–25 km/h and seeders at 8–15 km/h. Speed changes closed-loop bandwidth, the time between adjacent passes (and so GNSS decorrelation) and the slip dynamics.
3. **Idealised steering actuator.** Only a first-order lag with saturation and rate limit is modelled. There is no hydraulic deadband, hysteresis or valve nonlinearity, and no steering-wheel-motor slip for retrofit kits.
4. **Fixed pass order and turn geometry.** The order is strictly back-and-forth with a semicircular turn of r = 4.5 m regardless of w. For w = 1.5 m and 3 m the turning diameter exceeds the pass spacing, so real machines use bulb or keyhole turns or skip patterns (lands, alternation). Those patterns greatly increase the time between *adjacent* passes, which removes the common-mode cancellation of DGPS error that drives the paper's DGPS conclusions.
5. **Headland too narrow to turn in.** The headland width is fixed at 2w. For R2 that is 3 m, less than the 9 m turning diameter the simulator itself assumes.
6. **Idealised line acquisition.** After each turn, line acquisition is a Gaussian residual (σ = 3 cm, 0.5°). In practice the line-entry transient is a main source of skips at the start of passes. With a 3 m headland in R2 it would fall inside W.

**Fix.**
- Add a two-body tractor–implement model with implement side-slip on slopes.
- Add a speed sweep.
- Add pass-order patterns (back-and-forth, skip-1, lands) and turn types consistent with w and the minimum turning radius.
- Add a sensitivity table showing how λ* and the CE+ advantage change.
- At minimum, scope the claims to "rigidly mounted implements, sequential back-and-forth passes at 2 m/s".

### M6. GNSS error model: the tail that sets the certified margin may be a processing artefact, and the data come from another continent
**Location:** Section 6.1 (Data), Table 1, `core.gnss_bank`.

**Problem.** The certified margin is a high quantile of a field-wide maximum, so it is governed almost entirely by the error tail. That tail comes from:

1. static CORS antennas on 5–30 km baselines, post-processed in RTKLIB demo5 at **30 s epochs**, then linearly interpolated to 1 Hz;
2. a high-frequency residual taken from a *single* 1615 s vehicle record (i2Nav), tiled with random shifts and reversals.

**Wrong fixes.** "Wrong fixes" of 0.3–0.6 m and float drift lasting minutes, at 30 s epochs on 20–30 km baselines, are characteristic of RTKLIB's ambiguity resolution in this configuration. They are not what a commercial dual-frequency auto-steer receiver produces on a 1 Hz real-time link with integrity monitoring. Commercial systems also flag float or low-quality solutions and alert the operator or disengage, and that behaviour is not modelled.

**Fixed versus float.** In Table 1, "RTK fixed" and "RTK float" have *identical* 99.9% (24 cm) and maximum (1.39 m) values. This suggests that the "fixed" bank contains non-fixed epochs, or that both share the same outlier events. The CORS summary shows daily fix rates as low as about 0.91 in the "rtk_fix" grade.

**Lower bound claim.** The caption's claim that these RTK errors are "a lower bound on machine errors" is not justified for the tail. Vehicle multipath raises the body of the distribution, but processing artefacts may *inflate* the tail relative to a commercial receiver.

**Geographic mismatch.** The error series come from US Midwest stations, while the fields are in southern China and the North China Plain. Constellation (BeiDou availability), ionospheric latitude and correction-network geometry all differ.

**Fix.**
1. Show λ* and the CE+ results with wrong-fix and float epochs removed, or replaced by an "operator stops / system disengages" model.
2. Validate the 1 Hz short-lag relative error (the quantity that matters for adjacent passes about 30–150 s apart) against a real 1 Hz rover record, with its lag structure (Allan deviation or structure function).
3. Tone down the "lower bound" statement.
4. Explain the identical fixed and float tail statistics.

### M7. Terrain on paddy fields is not physically plausible
**Location:** Section 6.1 (Data), Table 2 (R2 "hilly-wet", R3 "hilly"), `Field._load_dem`.

**Problem.** Paddy fields are, by design, levelled terraces enclosed by bunds; their working surface has essentially no side slope. A 30 m GLO-30 DEM cannot resolve terraces and returns the *hillside* gradient.

In the v8 data the mean slope of the R2 paddy fields reaches 7.9° (median about 0.8°, so the 7.9° is an extreme case). In R1, the "flat" North China Plain wheat fields show slopes up to 3.3°, which is plausibly DEM noise: GLO-30 has metre-level vertical noise at 30 m posting. These gradients drive the simulated slip (β = −0.35 k_s g) and the roll-induced antenna error. The R2 "hilly-wet" regime, with its 25% oracle overlap on a 1.5 m implement under RTK, may therefore be largely an artefact of the DEM.

**Machine configurations.** R3 assumes a DGPS 6 m machine with auto-steer on paddies of 0.2–2.5 ha; some fields have only 7 passes and 324 m of total pass length. This is not a configuration with practical relevance.

**Fix.**
- Report the distribution of slopes per regime.
- Use levelled terraces for paddies, or a sub-metre DEM, or move the hilly regimes to genuinely sloping dryland fields (hilly wheat, vineyards, orchards).
- Filter DEM noise on the flat regime.
- Justify each machine configuration with a reference to real equipment, for example a 6-row rice transplanter with RTK, or a 6 m boom with sub-metre DGPS on dryland.

### M8. Over-claiming in the Abstract, Highlights and Conclusion, and a missing obvious comparator for the mixed fleet
**Location:** Abstract, Highlights 2, 4 and 5; Section 6.3; Section 6.6; Table 8; Section 8.

1. **"4.0–54.7% less overlap than two conformal planners at the same guarantee level".**
   - The comparators are two academic methods, re-implemented by the authors, that were not designed for this problem and that over-cover (P 0.92–0.99).
   - The comparison uses n = 100 calibration runs.
   - The 54.7% figure is against a PAC union-bound method.
   - On the applied-overlap metric the reductions are 2.8–29.3%.

   Neither the Abstract nor the Highlights say that the gain is against over-covering academic baselines rather than against practice. The farmer-tuned baseline is the practice-relevant one, and in v8 R1 it has 9.22% overlap against 8.39% for CE+, at comparable P. It is not reported in the main tables.
2. **"Fields without history are certified".** This holds only in simulation. It also needs one ground-truthed run on each of about 25 other fields of the same population (M4), and an exchangeable field population.
3. **Missing mixed-fleet comparator.** "Across a mixed fleet the theory pivot cut excess overlap from 29.8 to 3.0 pp." Raw pooling of a 1.5 m RTK, a 3 m RTK and a 6 m DGPS machine is a comparator nobody would use. The obvious practical baseline is **pooling stratified by machine configuration**: each configuration is known exactly, and Proposition 5 holds within each stratum. Section 7.2 itself says that within one configuration raw pooling is as good as the theory pivot to within tenths of a point, so stratified pooling may remove most of the theory's advantage. Any remaining advantage would come from the smaller per-stratum sample (about 8 fields per configuration), which is a legitimate but much narrower claim. This comparator must be added. The spec × scale-law pivot was also not significantly worse (Holm p 0.18 / 0.96), and CQR was comparable under PAC.
4. **"Theory predicts the required margin" (Highlight 3; Section 6.2).** The accuracy figures are against the authors' own simulator, which shares all modelling assumptions with the theory (linear closed loop, the same slip and roll model). Agreement with a simulator built on the same model is a consistency check, not a prediction of real machine behaviour. Say so explicitly.

**Fix.**
- Rewrite the Abstract and Highlights to state the comparator class, n_cal = 100 and simulation-only evidence.
- Add the farmer-tuned baseline to Table 5.
- Add configuration-stratified pooling to Tables 7–8 and Fig. 5.
- Reword "predicts" as "matches the simulator it was derived from".

### M9. There is no real-machine evidence, and a key observable is never validated
**Location:** Section 6.7 (TODO), Section 7.3 item 1, CE+ Section 4.2.

**Problem.** For a CEA paper whose stated application is guidance and auto-steer, a manuscript with zero machine data and a TODO section is not complete. CE+ also rests on the assumption that the XTE RMS reported on the headland probe line carries information about the day's pass-to-pass error.

- Commercial displays report XTE relative to the system's *own* GNSS solution, often filtered.
- XTE is structurally blind to GNSS error, the dominant term under DGPS and in RTK wrong fixes.
- It is unclear whether any commercial system exposes the probe-line XTE needed.

The repository contains CitrusFarm logs (123 rows) that have not been summarised.

**Fix.** At least one of the following:
- An offline replay of real logged data with an independent truth reference, demonstrating that the score can be computed and that the predicted margin is reasonable.
- A small field test: one RTK auto-steer tractor, PPK truth, 10–20 fields or repeated passes, measuring real gap-width distributions and probe XTE against pass-to-pass error.

Without this, the paper is better suited to a methods venue, or the claims must be scoped strictly to simulation.

### M10. Presentation is not ready for a CEA readership
**Location:** whole manuscript; Supplementary Appendix E; Data availability.

**Problems.**
- **Internal labels.** The text is organised around internal experiment versions (v7, v8, E-low v1/v2/v3, C1–C5, gates, "extended curves", "registered grid floor"). Readers need the development history only to judge pre-registration; it obscures the engineering message.
- **Notation.** Five theory layers, eight propositions, six theorems and four lemmas sit in a 24-page main text, and some notation is unclear (for example $\Gamma^{-1}$ in Section 5.5 is undefined).
- **Unfinished material.**
  - Supplementary Appendix E ("Notes for the authors, remove before submission") is still present.
  - The Data availability statement contains "TODO: archive with a DOI".
  - The RTKLIB commit "was not recorded".
  - Section 6.7 is a placeholder.

**Fix.**
- Restructure around three questions: what margin is needed, how to certify it with field data, and how to certify it without.
- Move the version history to a single supplementary table.
- Cut the main-text theory to the results used.
- Remove the internal notes and complete the archival and reproducibility details.

---

## 5. Minor issues

- **Section 1, paragraph 2.** "twice the nominal pass-to-pass accuracy" is ambiguous. State that this means a total overlap of 2 × p2p (λ = p2p = 2.5 cm), and that the specification is a 95%, 15-minute, pointwise statistic.
- **Section 1.** The Global Market Insights report on autonomous tractors is weak grey literature for a scientific claim. Also, the claim that autonomy "removes the operator who used to correct visible gaps by eye" is debatable for auto-steer, where operators rarely correct gaps.
- **Section 3, Lemma 1.** "Passes relevant to the chord" should be defined in the text. The code uses passes whose centres lie within w of the chord.
- **Section 3 / Section 6.1.** The 1 m along-track evaluation grid cannot see gaps shorter than 1 m along the pass (for example a GNSS jump lasting less than 0.5 s at 2 m/s). State this resolution limit.
- **Fig. 1.** The region below the edge is labelled "outside the field", but in the model it is the headland band (see M3).
- **Table 1.** The fixed and float tail statistics are identical (see M6). The source comment points to `docs/experiments_report.md` rather than to a results file.
- **Table 2.** Give a source for the 20 cm DGPS pass-to-pass specification and for the implement and receiver pairings.
- **Section 6.1.** The 2.6 m antenna height and the 2.6 m wheelbase are equal; confirm that this is intentional. A 2.6 m antenna on a 2.6 m-wheelbase tractor is plausible but high.
- **Section 6.1.** The mounting bias (σ = 1.5 cm) is redrawn on every run. In reality it is persistent per machine (see M4c).
- **Section 6.3, Table 5.** Add the farmer-tuned baseline and the vendor rule with their missed-area fractions. Negative regret in R1 marginal (−0.26 pp) needs a one-line explanation: it reflects under-coverage on some fields.
- **Section 6.3.** "CE+ also chose constant normalisation in R2" means the probe-line mechanism was inactive in one of three regimes. Report how often the gate switched the adaptive σ(z) on, per regime.
- **Proposition 2.** Show the arithmetic for "λ0 − λ̂ ≈ 5 cm ⇒ ≤ 0.7%" and state the K and θ values used.
- **Section 5.5.** $\Gamma^{-1}$ is undefined; presumably $G^{-1}$ of the normalised shape is meant.
- **Section 4.4.** The runtime of 16–353 s per field is fine offline. State the hardware.
- **Section 6.6, Table 9.** The comparison "ridge regression trained with one run on each of 147 fields" mixes configurations. Also report it per configuration.
- **Section 7.4.** "With at least 22 recorded operations on a field" does not match how farms work, and no result supports it at that n (see M4b).
- **Highlights.** Highlight 4 ("the guarantee held in 26 of 26 checks") should say "in simulation".
- **References.** The Zhao et al. (2024) arXiv entry should be updated if it has since been published. Add the ISO 12188-2 standard and the Rounsaville et al. (2016) relative-XTE paper; the code cites both and they are directly relevant to pass-to-pass definitions.
- **Supplementary C.3.** "About 25 systems" should be an exact count, with a table giving the configuration and parameters of each.
- **Units.** The figures use m while the tables use cm or %. Harmonise them.

---

## 6. Questions to the authors

1. For CE+, farmer-tuned and the 2 × spec rule in v8, what are the distributions of missed-area fraction and of maximum gap width per run? How do the conclusions change if a miss is defined as a gap wider than 2, 5 or 10 cm?
2. On a real machine, how would you obtain the exact run score of a calibration run? Which ground-truth instrumentation do you assume, and at what cost per operation?
3. How does CE+ perform with 9, 15 and 25 calibration runs on the target field, and what overlap is spent on those calibration operations at π(λ0)?
4. In the mixed fleet, how does CE-EVT-R compare with conformal pooling stratified by machine configuration (raw pooling within each configuration)?
5. Does the DGPS edge-concentration effect survive when headland passes are simulated with the same GNSS error series and a realistic headland-first or headland-last order?
6. How sensitive is λ* to the RTK tail? Please recompute the R1 oracle margin with wrong-fix and float epochs removed, or with an alert/disengage model.
7. What are the per-regime slope distributions? How many R2 and R3 fields have a mean DEM slope above 2°, and are these terraced paddies?
8. How do the results change with speed (for example 3, 5 and 7 m/s), with skip-pass or lands patterns, and with a trailed implement that drifts on side slopes?
9. Can a commercial auto-steer system export the probe-line XTE you use? Is that XTE computed from a filtered or a raw cross-track estimate?
10. How do you expect the method to interact with section control and with implement spread patterns (for example a spreader designed for 100% overlap)? Is it intended for all operations or only for those with sharp swath edges?
11. Given that fields are worked by the same machine and receiver over several years, how would persistent biases and their occasional recalibration affect exchangeability, and therefore the PAC guarantee?
