# Review r19 (Reviewer 2, devil's advocate)

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations"
**Journal:** Computers and Electronics in Agriculture
**Material read:** manuscript.md, supplementary.md, cover_letter.md. Spot checks of results/v8/summary.txt, Supplementary D.1 (v7 tables), experiments/evt_theory.py, experiments/exp_system.py, and the git history of the pre-registrations.

---

## 1. Summary

The paper treats the overlap between adjacent passes as a certified safety margin. The authors define an "exact run score": the covering radius of the executed passes minus half the implement width. They show that zero missed area is equivalent to this score being at most the margin, and that no other valid score is smaller. They then calibrate the score with split-conformal or PAC order statistics on a reference plan that has at least as many passes as the deployed plan (CE, CE-q, CE+). For fields with no operating history, a five-layer Gaussian extreme-value theory predicts each field's 0.9 quantile, and this prediction serves as a ratio pivot for cross-field conformal calibration with one run per field (CE-EVT-R).

All evidence comes from simulation. The simulator uses real field boundaries (Chinese harvester trajectories), the GLO-30 DEM and US CORS GNSS error series processed with RTKLIB. The paper reports:

- a pre-registered comparison on 90 fields against two conformal planners, with all claims met;
- three pre-registered zero-data experiments: v1 failed, v2 was met but mostly through realised coverage, v3 was partly met;
- a pre-registered resampling check of validity, with 26 of 26 cells passing;
- post hoc analyses of field-edge terms, learning curves and an "information limit".

The paper is unusually candid about negative results. That candour makes the case against it easy to build, because the paper says much of it itself.

## 2. Recommendation and scores

**Recommendation: Major revision, bordering on reject.** In its current form the paper is not acceptable for COMPAG. The decisive gaps are:

- there is no real-vehicle evidence (Section 6.7 is a TODO placeholder);
- the confirmatory comparison leaves out the strongest practical baseline, a simple fixed margin tuned on training fields;
- the theory's accuracy is measured against the same simulator whose model and condition sampler it calls;
- the method assumes that executed pass positions are observable from logs, which is not true for GNSS-dominated error.

| Criterion | Score (1-10) |
|---|---|
| Novelty | 5 |
| Soundness (theory and statistics) | 6 |
| Soundness (evidence for the practical claims) | 3 |
| Practical relevance | 3 |
| Clarity | 5 |
| **Overall** | **4** |

## 3. Strengths (brief)

- **Clean core reduction.** Zero miss is equivalent to S ≤ λ (Lemma 1). The point about decision dependence, that calibrating on the nominal plan does not transfer to a plan with more passes (Proposition 1), is correct and useful to the conformal-planning community.
- **Transparent reporting.** Pre-registration, a status table for every result (Table S20), failed claims reported in the main text, and matched-coverage re-analyses that weaken the authors' own v2 claims.
- **Correct validity check.** The resampling check over both sources of randomness (Table 7) is the right test of Proposition 5.
- **Real data as simulator inputs.** Real boundaries, DEM and GNSS error series are better than purely synthetic inputs.
- **Physically interpretable result.** Field-edge misses dominate under DGPS because the error is common-mode across adjacent passes.

## 4. Major issues: the strongest case against the paper

### M1. Is the problem real for farmers? RTK, section control, and a "zero-miss" target that has no agronomic meaning

**Location:** Abstract; Introduction paragraphs 1-2; Section 3 (Objective); Section 7.4 (bullet 1); cover letter, "Why it fits the journal".

- **The target is an event, not an area.** The event {M = 0} counts any gap of any width on any 1 m section of the field as a failure. A 2 mm sliver over 1 m in a 30 ha field has no agronomic consequence. Sprayer nozzle patterns taper and overlap, spreader patterns are designed to overlap, and seed-drill spacing tolerances exceed these gaps.
- **The paper never reports missed area or missed-area fraction**, only P(no miss). The headline statement that the vendor rule "left a gap on essentially every run" under RTK (Introduction; Section 7.4) is therefore an artefact of the criterion, not evidence of a farm problem. Under RTK with a 2.5 cm pass-to-pass specification, the expected missed area is presumably tiny.
- **The paper does not show that RTK falls short.** It does not quantify, in hectares, kg of input or currency, what a farmer loses with RTK plus the vendor overlap, nor what CE+ saves.
- **In the main-area metric the gains are about 1-2 pp of a 3 m swath.** In the headland-inclusive applied metric (Table S22) the reduction against CPP is 2.8-10.8%, on top of 30-49% applied overlap that commercial automatic section control already removes in practice. Section control is not mentioned anywhere.
- **The cover letter overstates readiness.** It says the method "can be used directly with standard guidance hardware". Nothing in the paper supports this.

**What would change my mind:**
- report the missed-area distribution, both the mean and an upper quantile in m² per ha, for the vendor rule, the farmer-tuned rule and CE+ under RTK;
- add an agronomic or economic translation in input cost per ha;
- add a variant certified on a missed-area tolerance (for example P(M ≤ m₀) ≥ 1 − ε, or conformal risk control on M), and show that the ranking survives;
- justify zero-miss as the right specification with reference to implement patterns and section control.

### M2. Is the method's complexity justified against a simple fixed safety margin? The confirmatory test leaves out the obvious baseline

**Location:** Section 6.3 / Table 5 (v8); Supplementary D.1, Tables S1 and S3 (v7).

**The v8 confirmatory comparison only compares CE+ with two conformal planners** (CPP and Lindemann). These are methods from other domains, re-implemented by the authors in a nominal-plan configuration, and the manuscript itself says they over-cover by design (Fig. 3; "part of the gain is that the comparators … over-cover").

The farmer-tuned global overlap was dropped from the confirmatory test. In the exploratory v7 run it looked like this:

| Regime | Method | P(no miss) | Overlap % | Regret pp | Runs on target field |
|---|---|---|---|---|---|
| R1 | Farmer-tuned | 0.886 | 8.72 | −0.15 | 0 |
| R1 | CE+ v7 | 0.915 | 8.86 | — | 100 |
| R3 | Farmer-tuned | 0.868 | 13.82 | — | 0 |
| R3 | CE+ v7 | 0.910 | 16.00 | — | 100 |
| R3 | CE-q | — | 15.45 | — | 100 |

A fixed margin tuned once on five training fields, with zero runs on the target field, is therefore within about 0.3 pp of the oracle in R1. It misses the 0.9 target by only 1-3 points of pooled P(no miss). The obvious fix is to tune the fixed margin to a slightly stricter level on the training fields (for example 0.93-0.95, or a quantile with a safety factor). That fix would very likely meet 0.9 in R1 and R3 at overlap similar to CE+, without 100 calibration runs per field, a probe line, an XTE normaliser or a five-layer theory.

R2 is the only regime where the farmer rule clearly fails (meet rate 0.27). This is plausibly because 5 training fields are too few for the wet hilly configuration, not because the margin is fixed.

The same point applies to the zero-data setting.
- **Within one configuration:** raw pooling, a conformal quantile of pooled scores used as one fixed margin, is as good as the theory pivot at matched coverage (Section 6.4, "within tenths of a percentage point"; Section 7.2; Section 7.4, "choose the simplest"). The paper therefore concedes that a data-driven fixed margin is the right tool for a single machine.
- **Across configurations:** see M3.

**What would change my mind:** a confirmatory (or at least fully reported) comparison on the v8 fields against:
- (a) a fixed margin tuned on training fields at a stricter level so that it meets 0.9 pooled;
- (b) a conformal fixed margin pooled per configuration from the same 5 training fields.

Both should be evaluated on overlap at matched coverage. If CE+ still wins by more than about 1 pp of regret in at least two regimes, the complexity is justified.

### M3. The headline mixed-fleet result (29.8 → 3.0 pp) is won against a configuration-blind straw man

**Location:** Abstract ("reduced excess overlap from 29.8 to 3.0 percentage points"); Highlight 5; Section 6.6 / Table 8; Section 7.1.

- **"Raw pooling" and the "scale law" ignore the machine configuration.** No farmer or contractor would pool scores from a 6 m DGPS sprayer with those of a 1.5 m RTK implement. The obvious practical baseline is to stratify by configuration: pool raw scores within each configuration, or use a categorical scale per configuration. Section 7.3 item 4 already requires every configuration to be represented in the calibration pool, so stratification is always possible.
- **By the paper's own within-regime results, stratified raw pooling would match the theory pivot** to within tenths of a pp per configuration. So the 29.8 → 3.0 headline almost certainly measures the cost of ignoring a categorical variable, not the value of the EVT theory.
- **Stratification costs sample size.** With 25 calibration fields split across 3 configurations it uses roughly 8 per configuration, which affects the PAC rule. That trade-off should be shown, not avoided.
- **The vendor-specification × scale-law pivot comes closest to stratification, and there the theory's advantage was not significant** (Holm p 0.18 and 0.96; C3 not met).
- **The configuration-aware CQR was comparable to the theory in the PAC class** (+2.64 vs +2.54 pp at matched coverage).

**What would change my mind:**
- add stratified raw pooling, plus a stratified conformal method with shrinkage across configurations, to Table 8 and to the resampling check;
- if the theory still clearly wins, keep the headline;
- otherwise remove 29.8 → 3.0 from the abstract and highlights.

### M4. All evidence is simulation-only, and the theory is validated against its own model

**Location:** Section 6.2 (Table 3, Fig. 2, Table 9); Section 6.7 (TODO); Section 7.3 item 1; Abstract ("predicts each field's required margin"); Highlight 3.

**(a) There is no real vehicle data at all.** Section 6.7 is literally a TODO. CitrusFarm logs exist in results/real.csv but are "not summarised". For an applied journal, a certification method that has never been run on a machine is a serious weakness.

**(b) The theory reuses the simulator.** experiments/evt_theory.py:
- calls `core.simulate` for the noise-free closed-loop trajectory;
- imports the controller gains from `core._lqr_gains`;
- hard-codes the simulator's anti-windup clamp (`I_MAX = 0.3`, "core.simulate clips the state at 0.3");
- samples operating conditions with the simulator's own `exp_system.make_cond`.

The theory therefore has oracle knowledge of:
- the vehicle and controller model;
- the parameter values;
- the soil-moisture, slip, roll-compensation and mounting-bias distributions;
- the GNSS error population.

Consequences:
- **The reported accuracy is a self-consistency check, not evidence of predictive validity.** This covers the log-error standard deviations of 0.029 / 0.029 / 0.056, Table 3 and Fig. 2 ("on the diagonal").
- **The theory-vs-regression comparison (Table 9, Fig. 6; abstract "1.7–3.7 times more accurately than data-driven regressors") is structurally unfair.** One side knows the data-generating process. The other learns it from one noisy run per field.
- On a real farm, none of these distributions is known: moisture-dependent slip gain, OU roughness parameters, roll-compensation quality, mounting bias, the receiver's real error tail.

**(c) The GNSS model has weak points:**
- CORS series come from static geodetic antennas in the US Midwest, applied to Chinese paddy and wheat fields;
- 30 s epochs are interpolated to 1 Hz, which artificially smooths the error between adjacent passes, the very common-mode correlation on which the field-edge mechanism (Theorem 3(b)) depends;
- the speed is fixed at 2 m/s;
- one simulator family produces all "real" behaviour.

**What would change my mind:**
- (i) a misspecification study: run the theory with perturbed or estimated parameters (for example controller gains identified from a short log, moisture prior off by 30%, roll compensation unknown) and report the resulting log error and excess overlap;
- (ii) a cross-simulator test, with the theory derived from the linear model and the truth from a different dynamics model, for example a dynamic tyre model or a different steering actuator;
- (iii) at minimum, the CitrusFarm replay, plus a real-tractor pilot on even 10-20 fields with PPK ground truth.

Without (iii), the paper reads as a methods paper for a statistics or robotics venue, not COMPAG.

### M5. The calibration data are not observable in practice

**Location:** Abstract ("calibrates the footprint margin on logged runs"); Section 4.2 (probe-line XTE); Section 7.4; cover letter ("auto-steer logs").

- **The exact run score needs the true executed footprint of every pass.** Auto-steer logs record GNSS-estimated positions and XTE relative to that estimate.
- **The error the paper says dominates is invisible in those logs.** Under DGPS this is GNSS error, and under RTK it is wrong fixes and float drift (Table 1). A machine that follows its GNSS estimate perfectly logs XTE ≈ 0 while leaving real gaps.
- **Calibration therefore needs independent ground truth on every calibration run.** Examples are PPK on a second antenna, or as-applied imagery. Section 6.7 implicitly admits this ("PPK rover as ground truth").
- **The same applies to the XTE normaliser.** The authors note that under GNSS-dominated error the fit gives b ≈ 0, so CE+ reduces to CE-q.

The manuscript never addresses observability. The claims "logged runs" and "standard guidance hardware" are therefore overclaims.

**What would change my mind:** an explicit section on what must be measured and how, with the cost of a ground-truth sensor. Or a version of the score computable from observable quantities (for example as-applied coverage maps, or post-processed positions), with its validity proven or simulated under measurement error.

### M6. The confirmatory headline needs 100 calibration runs per field, which contradicts the paper's own motivation

**Location:** Section 6.1 ("Each system is calibrated on 100 runs per field"); Introduction (iii), "a field is worked a few times per year"; Abstract and Highlight 2 ("4–55% less overlap … same guarantee").

- **The 4.0-54.7% reduction requires 100 historical operations on the target field** with ground-truth positions (M5). That is decades of operations.
- **The introduction itself makes this the third objection to existing conformal planners.**
- **Small-n performance of CE+ is not reported.** With n = 9-22, the marginal and PAC quantiles are much noisier, and CE+'s advantage over CPP could shrink. The R2 erosion difference is already only 3% (0.153 vs 0.158 m, Supplementary D.2). The PAC rule at n = 22 takes the maximum score.
- **The baselines inherit the same 100-run budget,** so the comparison is internally fair. But it is not the regime a farm will see.

**What would change my mind:** a v8-style comparison at n ∈ {9, 15, 22, 30}, with the farmer-tuned fixed margin (M2) included.

### M7. Results are substantially negative or post hoc, but the abstract and highlights read as a clean success

**Location:** Abstract; Highlights 2-5; Conclusion; cover letter.

The abstract and highlights select:
- the v8 result (met);
- the validity check (met, but true for any pivot by construction);
- the mixed-fleet resampling mean (pre-registered only as descriptive);
- the regression comparison (post hoc).

Omitted from the abstract:

| Result | Status |
|---|---|
| E-low v1 | failed in all three regimes |
| E-low v2 | claims met, but "mostly through realised coverage" (matched-coverage gaps of 0.06 vs 0.41 pp) |
| E-low v3 C3 | not met as registered |
| E-low v3 C4 | 1 of 6 cells |
| Field-edge terms (Theorem 3(b)) | post hoc, never used in any pre-registered experiment |

Specific overclaims:
- **"Distribution-free zero-miss guarantees" (Abstract; Conclusion; cover letter, contribution 2)** applies only to the assumption-free CE variant, which deploys its own reference plan.
  - CE+, the method in the headline, and CE-q deploy a different plan, π(tσ(z_new)) or π(q*).
  - For those plans the guarantee rests on Theorem 5: Gaussian structure, equal covariance, mean-shift bound Δ̄, factor κ.
  - κ is never reported for the v8 fields, and Δ̄ needs a GNSS modulus of continuity that "may be large under DGPS" (Section 7.3 item 2).
  - Empirical P(no miss) in v8 (0.896-0.911) is reassuring, but it is not a distribution-free guarantee.
- **Highlight 4, "Fields without history are certified; the guarantee held in 26 of 26 checks", suggests the theory produces the certificate.**
  - Per Proposition 5 and Table 7, raw pooling with no theory is certified equally well. The check "tests the guarantee and its implementation, not the methods" (Section 6.5).
  - The guarantee also rests on fields being i.i.d. from one population. That is a strong assumption for one farm's fields, which share an operator, a machine and a season.
- **"Predicted margins 1.7–3.7 times more accurately than data-driven regressors" (Abstract)** is post hoc. It is computed against regressors with one run per field, against a theory with oracle model knowledge (M4). The oracle-trained regressor beats the theory in R1 and R2 (Table 9: 0.020 / 0.021 vs 0.029 / 0.029).
- **The 29.8 → 3.0 headline** is from the "extended curves" file, a post hoc re-reading committed after the pre-registered run. See also M3.
- **The cover letter states that the comparison was with "two recent conformal planners" with "every … efficiency claim met",** with no mention that the confirmatory set excluded the fixed-margin practice that the introduction criticises.
- **The cover letter calls the theory a "method [that] takes 0.3–6 min per field".** In fact the theory needs model parameters that a farmer does not have (M4).

**What would change my mind:**
- rewrite the abstract to state the limited validation (simulation only, oracle model);
- state that the distribution-free guarantee holds strictly for CE and under Theorem 5's assumptions for CE+;
- state that within one configuration the theory brings nothing over pooling;
- report the v1 failure and the partial v3 outcome in the abstract.

### M8. Is the theory needed at all?

**Location:** Section 5.3 (about 40% of the theory section); Sections 6.4-6.6; Section 7.2.

**By the paper's own account the five-layer EVT is:**
- not needed for validity (Proposition 5; Table 7);
- not useful within a configuration (Sections 6.4 and 7.2);
- not reliably selectable by a gate (C4 met in 1 of 6 cells);
- not more efficient than a configuration-aware CQR in the PAC class.

Its remaining benefit, across configurations, is probably available from stratification (M3). Its predictive accuracy is self-referential (M4).

**The layers themselves are mostly textbook tools assembled for one simulator:**
- the Lyapunov equation;
- the Kac-Rice upcrossing bound;
- a second-order Bonferroni sandwich;
- a mixture over conditions;
- the classical Gumbel law (Leadbetter et al.).

**The development history is also a warning sign.** The theory was repaired three times because validation checks failed:
- the observation operator;
- the anti-windup integrator model;
- two versions of the edge terms that overestimated the margin.

This is a classic garden-of-forking-paths risk, which the authors acknowledge by labelling the work "developmental".

Theorems 2, 5 and 6 and Lemma 4 are fine, but for a COMPAG reader they add length without a decision the reader could not make otherwise.

**What would change my mind:** evidence that the theory beats stratified pooling across configurations, beats CQR in both classes, and survives parameter misspecification (M4). Failing that, move Section 5.3 and most of Section 6.6 to the supplement and reframe the paper around CE / CE+.

### M9. The novelty over existing conformal planning is incremental

**Location:** Section 2; Section 5.1; Contributions 1-2.

- **The authors concede the point** (Section 5.1): "The contribution of CE is therefore not the quantile rule but the score and the reference plan". For a scalar decision, PAC CE is the scenario approach and CE-q is split conformal on a maximum score.
- **The "exact score" is close to a definition.** It is the needed erosion λ̄(e) under shift-equivariance. "Smallest valid score" (Lemma 2, Theorem 1, Corollary 1) follows in one line from the definition of validity and the monotonicity of order statistics. A sup-type run score is already standard in functional conformal bands (Lei et al., 2015; Diquigiovanni et al., 2022), which the paper cites.
- **Calibrating on a dominating, more conservative reference plan is a natural monotonicity argument.** Its exact form (Theorem 5) needs Gaussian assumptions.
- **CE-EVT-R is the one-sample-per-group setting of Dunn et al. (2023) with a scale normaliser.** Normalised (studentised) conformal scores are standard.
- **What is new is applying all of this to agricultural pass-to-pass coverage, plus the field-edge observation.** That is a legitimate application contribution for COMPAG, but it should be framed as such. Phrases like "exact reduction", "theory-pivoted" and "certified" suggest more methodological novelty than there is.

**What would change my mind:** a clearer statement of which results are new as mathematics and which are standard tools specialised here; a comparison with a scenario-approach baseline on the same exact score (which by Section 5.1 should equal CE PAC); and evidence that the CPP and Lindemann baselines are implemented as their authors would apply them to this problem, not only in the nominal-plan configuration CE was designed to beat.

### M10. Pre-registration weaknesses and readiness

**Location:** Section 6.1; Supplementary C.2 and Appendix E; Data availability.

**Pre-registration:**
- Pre-registrations are self-hosted git commits, sometimes about 1-2 hours before the results. For example, prereg_lowdata_v3 was committed at 17:04 and its results at 18:55 on 2026-10-14.
- Third-party registration (for example OSF) is acknowledged as missing in Appendix E.
- Field sets are reused across questions:
  - fields 50-79 are used for v8, E-low v2 and the v3 calibration pool;
  - fields 5-19 were used earlier in the v3-v6 system experiments.

**Readiness:**
- The supplementary still contains "Appendix E. Notes for the authors (remove before submission)", which includes a discrepancy between a commit message ("28 cells") and the paper's 26 cells.
- Section 6.7 and the DOI are TODO placeholders.
- The RTKLIB commit "was not recorded".
- The cover letter contains [Date] and name placeholders.

The manuscript is not submission-ready.

**What would change my mind:** remove the placeholders, archive code and data with a DOI, pin all tool versions, and either complete Section 6.7 or remove it and state the simulation-only scope in the title or abstract.

## 5. Minor issues

1. **Fields and GNSS from different continents** (Section 6.1): Chinese field boundaries combined with US CORS GNSS series (different constellation visibility, ionosphere and baselines). Justify, or use Chinese CORS / CMONOC data.
2. **Regime choices look arbitrary** (Table 2). A 1.5 m RTK implement on wet hilly paddy and a 6 m DGPS implement on hilly paddy are unusual. Explain which real operations they represent.
3. **Fixed speed** (Supplementary C.1): 2 m/s is slow for spraying (typically 3-7 m/s). Run a sensitivity check on speed, which changes the time between adjacent passes and so the common-mode GNSS correlation.
4. **Interpolating 30 s GNSS epochs to 1 Hz** (Section 6.1) removes 1-30 s error dynamics. Show sensitivity, or use 1 Hz CORS data, which are available for many stations.
5. **Main-area overlap of 25% in R2** (Table 5) even for the oracle. That suggests a planner and implement mismatch that inflates denominators and dilutes relative gains. The authors note this, but it should be reconsidered.
6. **Regret below the oracle** (Table 5, R1 marginal −0.26 pp) reflects under-coverage at a single draw. Report regret at matched coverage for v8 as well, as was done for E-low.
7. **Proposition 2** quotes a bound of about 0.7% using θ ≈ 0.5 without a source for θ in R1. Give the estimate.
8. **Section 4.4.** Runtime is reported for only three fields per regime. Report the distribution over all fields, and the scaling with field size for large farms (100+ ha).
9. **Prop. 6 is cited in the main text** (Section 4.3), but its statement appears only in Supplementary B.4, where it is labelled heuristic and motivated post hoc. Either state it in the main text or demote it.
10. **Table 6 mixes metrics.** Registered means at one draw appear next to matched-coverage values. Use one consistent primary metric per row.
11. **Abstract length and density.** The abstract is about 250 words of dense notation ("five-layer", "Lyapunov covariance, Kac–Rice…"). Rewrite it for agricultural engineers.
12. **Highlights exceed typical style** (for example "Zero-miss coverage reduces exactly to a scalar run score, the tightest valid one" is jargon-heavy). Also check them against the 85-character limit.
13. **References.** Several references are preprints (Zhao et al., 2024; Wang and Ning, 2025). Market-report citations (Global Market Insights, 2026) are weak support for an agronomic motivation.
14. **Fig. 1 is labelled "illustrative, not data".** Fine, but also add a real simulated example of a field-edge miss under DGPS.
15. **Terminology.** The paper uses "erosion", "margin", "overlap" and "λ" interchangeably. Define each once and use one term.

## 6. Questions to the authors

1. What is the expected missed area per ha, mean and 99th percentile, under RTK with the vendor rule, the farmer-tuned rule and CE+? Is it agronomically relevant?
2. How would a farmer obtain exact run scores in practice, given that auto-steer logs do not observe GNSS error? What ground-truth sensor do you assume, and at what cost?
3. Why was the farmer-tuned fixed margin removed from the v8 confirmatory comparison? What happens if it is tuned on the training fields to a stricter level (for example 0.95) so that it meets 0.9?
4. How does the theory pivot compare with raw pooling stratified by machine configuration in the mixed fleet, in the same 4000-replicate resampling check?
5. How large are κ(λ̂) and Δ̄ for the v8 CE+ deployments, especially in R2 (hilly) and R3 (DGPS)? Is the deployed guarantee κε rather than ε?
6. How much does the theory's log error grow when the controller parameters, slip and moisture distributions and GNSS error statistics are estimated rather than taken from the simulator?
7. What do CE+ results look like with n = 9-22 calibration runs per field, the range the introduction says is realistic?
8. Why were US CORS stations used for Chinese fields? Are the results sensitive to station choice and to the 30 s → 1 Hz interpolation?
9. Is the i.i.d.-fields assumption of Proposition 5 plausible for the fields of one farm, which share operator, machine, season and receiver? How would year-to-year drift (firmware, wear) affect it?
10. When will the CitrusFarm replay and the tractor study of Section 6.7 be available? Would you consider submitting after them?
