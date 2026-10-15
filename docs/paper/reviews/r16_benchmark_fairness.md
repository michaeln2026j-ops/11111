# Review R16: Benchmarking fairness and experimental design

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)
**Reviewer focus:** whether the algorithm comparisons are fair, which covers data, tuning effort, guarantee level, metrics, oracle and regret definitions, and whether the reported numbers match the raw results.
**Material inspected:** `docs/paper/manuscript.md`, `docs/paper/supplementary.md`, `docs/theory_v8.md` §6 (the v8 pre-registration), `experiments/exp_system.py`, `experiments/ceplus.py`, `experiments/exp_lowdata.py`, `experiments/exp_lib.py`, `experiments/evt_theory.py` (`predict_cdf`), `experiments/baselines/uncertainty.py`, `results/v8/{summary.txt,regret_table.txt,system_v8.csv}`, `results/lowdata_v2/*.txt`, `results/lowdata_v3/*.txt`. All re-analyses below use the existing CSV and text files only. No simulation was run.

---

## 1. Summary

The paper casts zero-miss coverage under execution error as a scalar run score: the exact covering radius of the executed passes. It calibrates this score conformally on a reference plan with at least as many passes as the deployed plan (CE, CE-q, CE+). For fields with no history it also offers a cross-field ratio pivot built on a five-layer extreme-value theory (CE-EVT-R). There are two kinds of evidence:

- **With target-field data (v8).** A pre-registered comparison on 90 fresh fields tests CE+ against two conformal planners, CPP (Zhao et al.) and the pair-level Lindemann et al. planner, in a marginal class and a PAC class.
- **Without target-field data (E-low v1 to v3 and a resampling check).** A pre-registered sequence compares scale pivots.

The bookkeeping is unusually honest. Failed claims are reported, and post hoc analyses are labelled as such. The E-low pivots share calibration runs and test seeds exactly. The resampling check of the guarantee is well designed.

The fairness of the **efficiency** comparisons is weaker than the presentation suggests. My concerns, in order of importance:

1. The confirmatory comparator set is narrow, and its two members are the authors' own adaptations. Each adaptation contains exactly the defects the method was built to fix.
2. Efficiency is compared at unequal realised coverage in v8, although the paper applies matched coverage to its own E-low results.
3. CE+ uses side information and data that the baselines do not get: the probe-line XTE and training-field runs.
4. The theory pivot is evaluated inside the very generative model it encodes.
5. Pre-registered secondary analyses are missing, and one CE+ validity failure in the v8 raw data is not reported.
6. The oracle is not an upper bound for the CE+ class, and relative-regret ratios are unstable.
7. One reported range does not match its source file.

## 2. Recommendation and scores

**Recommendation: major revision.** The validity results are solid. The efficiency claims need a fairer comparator set, coverage-matched reporting in v8, and a misspecification test of the theory pivot before the headline numbers can be accepted as stated.

| Criterion | Score (1–10) |
|---|---|
| Novelty | 7 |
| Soundness (of the benchmarking) | 5 |
| Practical relevance | 5 |
| Clarity | 6 |

## 3. Strengths

1. **Pre-registration and status labelling.** Claims, comparators and tests were committed before the runs (git history, `docs/theory_v8.md` §6, `docs/prereg_lowdata_v*.md`). Every result carries a status label (Table S20). Failed claims (E-low v1, C3, C4) are reported in full.
2. **Guarantee-class discipline.** The paper states that comparisons must be within a class (marginal vs marginal, PAC vs PAC). For v8 it added PAC versions of the comparators instead of comparing CE+ PAC with marginal baselines.
3. **Common evaluation infrastructure.** All systems share one simulator, field set, evaluator and test seed per field (`exp_system.evaluate`, seed `seed+1`). CE+'s run-adaptive evaluation reuses the same `Condition` draws (`ceplus.deploy_eval`).
4. **E-low pivots are compared on identical data.** In `exp_lowdata.phase_b` every pivot uses the same calibration fields, the same single historical run per field (`S_hist`) and the same test seed. This is the cleanest comparison in the paper.
5. **The resampling check (Table 7) is the right test** of Proposition 5. It averages over both sources of randomness, has explicit criteria, and correctly treats the check as a test of the guarantee rather than of the methods.
6. **The paper limits its own claims.** It gives the matched-coverage caveat on E-low v2, uses the information limit (Proposition 8) to explain null results, and reports the applied-overlap secondary metric.

## 4. Major issues

### M1. The confirmatory comparators are the authors' adaptations, and they contain exactly the defects the contribution removes

**Location:** Section 6.3, Table 5; Supplementary C.3; `experiments/baselines/uncertainty.py` (`cpp_lambda`, `lindemann_cp_lambda`).

**What the code does:**

- **CPP** (`cpp_lambda`) calibrates the *pair score* (`core.pair_scores`, not the exact score) on the *nominal plan* π(0) (`lam_ref=None → 0`).
- **Lindemann pair-level** splits ε over T constraints (union bound) on the nominal plan.
- **The PAC versions of both** were constructed by the authors (`pac_delta`, "v8 fairness control"). The Lindemann PAC version also splits δ over T (`dT = pac_delta / T_used`). Neither paper defines a PAC variant.

**Why this matters:**

- Each design choice (nominal reference, looser score, union bound) is precisely what Sections 5.1–5.2 show to be suboptimal. The comparison therefore mostly confirms that the authors' own lemmas hold. It does not show superiority over a competently engineered conformal baseline.
- The upper end of the headline "4.0–54.7%" (abstract, highlights, conclusion) comes entirely from the authors' δ/T-split Lindemann PAC construction. In R3 PAC its main-area overlap is 42.61% against 19.30% for CE+ PAC.
- The decomposition in the raw data shows where the gain comes from. Main-area overlap on BCD + LQR-I:

| Regime | CPP | CE-q (exact score, reference plan) | CE+ |
|---|---|---|---|
| R1 | 10.35% | 8.82% | 8.39% |
| R2 | 26.72% | 25.51% | 25.62% |
| R3 | 20.63% | 16.19% | 15.73% |

- So almost all of the gain over CPP comes from score plus reference plan. That component is exactly what a careful practitioner applying CPP to this problem could also use. Section 5.1 itself says "the scenario approach applied to S* is the PAC version of CE".

**Concrete fix:**

- (a) Add, as pre-specified secondary comparators, the *strongest reasonable* adaptations of the published methods:
  - CPP with the exact score on a training-derived reference plan;
  - Lindemann with a pooled (not union-bound) quantile on the exact score;
  - the scenario approach on S* at β = δ = 0.1 (currently β = 0.01, see M4).
- (b) State in the abstract that the comparators are the authors' adaptations. Note that the PAC variants are the authors' constructions.
- (c) Report the headline range separately for published-variant (marginal) comparisons, which give 4.1–35.1%, and for authors' PAC constructions.

### M2. Efficiency in v8 is compared at unequal realised coverage, while E-low gains were discounted for the same reason

**Location:** Table 5, Fig. 3, Section 6.3 ("Two qualifications"); compare with Section 6.4 (E-low v2, "mostly through realised coverage").

**Why it matters.** Within the "same guarantee class", CE+ realises P(no miss) 0.903/0.911/0.896 (marginal), while CPP realises 0.944/0.923/0.946 and Lindemann 0.959/0.944/0.960.

- For E-low v2 the paper correctly concluded that gains which are "mostly differences in realised coverage" do not show greater efficiency. It then rescaled to matched coverage.
- For v8 the same logic is not applied. Instead, over-coverage is presented as a defect of the comparators.
- That argument is legitimate for the *guarantee design*. But it should be stated as such, separately from an efficiency claim at equal reliability.

**My approximate check.** CE+ PAC and CPP marginal have similar realised coverage, so comparing them approximates a coverage-matched comparison (paired Wilcoxon on `system_v8.csv`):

| Regime | CE+ PAC overlap (P) | CPP marginal overlap (P) | Result |
|---|---|---|---|
| R1 | 9.04% (0.941) | 10.35% (0.944) | CE+ better, p = 0.001 |
| R2 | 28.14% (0.944) | 26.72% (0.923) | CE+ **worse**, p = 0.007 |
| R3 | 19.30% (0.933) | 20.63% (0.946) | p = 0.11 |

At roughly equal reliability, the advantage survives in R1, is unclear in R3, and vanishes in R2.

**Concrete fix:**

- Report an overlap-vs-coverage frontier for each v8 method. Each method's margin can be scaled by a common factor, as in `scripts/matched_coverage.py`. Alternatively, report overlap at matched pooled P(no miss) = 0.9 and 0.95.
- Label it post hoc. State plainly how much of the 4–55% is a coverage difference.

### M3. CE+ uses information and data the baselines do not get

**Location:** Section 4.2; `ceplus.py` (`probe_xte`, `fit_training`); `exp_system.add_ceplus`.

- **(a) Side information per operation.** CE+ uses the probe-line XTE *at deployment* (`deploy_eval` draws `z` for each test run). No baseline receives this covariate.
  - In R1 the gate selected adaptive σ (`scale_b` = 17.2). There the side information is responsible for the extra gain of CE+ over CE-q (8.39% vs 8.82%; paired p = 0.011, 22 of 30 fields).
  - The probe line's driving time and overlap are not charged in any metric.
- **(b) Extra data.** CE+ uses 5 training fields × 40 runs (200 runs) to set λ₀ and σ(z), on top of the 100 target-field runs. The code comment "same calibration budget as the baselines" is true only for target-field runs. CPP and Lindemann could have used the same training fields to choose a reference plan, but were fixed to π(0).
- **(c) Uneven tuning effort.** CE+ went through versions v1–v8 with tuned constants: REF_INFLATE 1.25, SIG_FLOOR 0.3, GATE 3%, LAM_GRID 2 mm and the pilot MARGIN 1.10, refined on v7 (exploratory, Section 6.3). The baselines were run at one default configuration. The v8 fields are fresh, which protects against overfitting to fields but not against asymmetric development effort.
  - The sensitivity analysis of GATE, REF_INFLATE and SIG_FLOOR was pre-registered as secondary (`theory_v8.md` §6) but is not reported.
- **(d) CE (two-stage)** uses pilot batches. `pilot_iters` averages 2.9 / 2.5 / 4.7 and reaches up to 10 batches of 100 runs. CE still appears alongside 100-run baselines in Tables S1–S3. The scenario, Gaussian and DRO rules inherit CE's pilot-selected reference plan.

**Concrete fix:**

- Add a "CPP + training-field reference plan" baseline and a "CE+ without probe" baseline (that is, CE-q on λ₀) to Table 5.
- Report the pre-registered sensitivity analysis.
- Charge the probe line in the path-length and applied-overlap metrics.
- Mark data budgets (target-field runs, training runs, pilot runs) in a column of every comparison table.

### M4. Guarantee levels are not matched for several baselines

**Location:** Tables S1–S3; `exp_lib.scenario_lambda` and `dro_cvar_lambda` (β = 0.01); Section 5.2, Proposition 1.

- **Scenario approach and DRO-CVaR.** These are run with confidence β = 0.01, ten times stricter than CE+ PAC's δ = 0.1. They are nevertheless listed next to CE+ PAC and declared "dominated".
- **CPP and Lindemann.** By the paper's own Proposition 1, nominal-plan calibration has *no* distribution-free guarantee on the deployed plan. Calling them "at the same guarantee level" (abstract, highlights) is therefore inaccurate.
- **CE+ itself.** CE+ deploys π(λ̂) ≠ π(λ₀), so its guarantee relies on the transfer assumption of Theorems 2/5. Only CE is assumption-free.
- **The guarantee is not "the same" for either side**, and the wording should say so.

**Concrete fix:**

- Re-run the scenario approach and DRO at β = 0.1 from the existing scores. This is cheap: `c_bcd["S"]` can be re-derived. If it is not stored, flag the run as needed.
- Replace "at the same guarantee level" with "in the same nominal guarantee class (marginal or PAC order statistic)".
- Add a column to Table 5 stating each method's assumption: assumption-free, transfer (Theorem 5), or none (Proposition 1).

### M5. Pre-registered secondary analyses are omitted, and a CE+ validity failure in the v8 raw data is not reported

**Location:** `docs/theory_v8.md` §6 ("secondary analyses": scenario/DRO/Lindemann-union vs CE+ PAC, full-system ranking, validity description of methods without a guarantee, parameter sensitivity); Section 6.3; Table S20.

`results/v8/system_v8.csv` contains 51 systems on 7 stacks. The manuscript reports only 4 systems for v8 plus the applied-overlap metric. My recomputation, using the paper's meet test (one-sided binomial at 0.05, 200 runs), shows three things the reader should see.

**(a) CE+ fails on one v8 stack.** "Follow-previous-pass + LQR-I + CE+ (ours, v8)" in R2 has:

- pooled P(no miss) 0.850;
- meet rate 0.724 (8 of 29 feasible fields fail);
- one infeasible field;
- mean regret +15.25 pp.

This is a clear validity failure, plausibly because the sequential planner violates the shift-equivariance used by Theorem 2. In R2, "Follow-previous-pass + Lenain + CE+" also reaches only P 0.886 (meet 0.80). The paper calls CE a planner-agnostic certification layer (Section 6.1, v7 Table S4 highlights a follow-previous-pass stack as best in R1). This failure is therefore directly relevant and must be reported.

**(b) Parametric baselines without a guarantee are competitive.** The "Gaussian chance constraint" on the same exact scores has:

- in R2: lower overlap than CE+ (25.30% vs 25.62%, P 0.897, meet 0.83; paired difference n.s., p = 0.34);
- in R1: P 0.909 and meet 0.967 at 9.01%.

CE-q, the authors' own method, also has lower R2 overlap than CE+ (25.51%). This does not undermine the guarantee argument, but readers should see the full ranking that was promised.

**(c) The sensitivity analysis is missing** (see M3c).

**Concrete fix:**

- Add the full v8 table (all systems, all stacks) to the Supplementary, as the v7 tables already are.
- Report the follow-previous-pass failure in Sections 6.3 and 7.3 (as a limitation of the transfer assumption).
- Report the pre-registered sensitivity analysis.
- Make the planner-agnostic claim conditional on shift-equivariant stacks.

### M6. Cross-stack "best system" claims compare a maximum over many CE stacks with baselines on a single stack

**Location:** Section 6.3 ("the lowest-regret certified system on every regime was a CE variant, on stacks with better controllers than the default"); Table S4.

- CE variants were run on 6–7 planner and controller stacks. CPP, Lindemann, GP, scenario and the other baselines were run only on BCD + LQR-I (`systems_for`).
- Picking the best of many CE stacks and comparing it with single-stack baselines is selection over unequal opportunities, with a winner's-curse bias, since the same 30 fields are used for selection and reporting.
- Regret in Table S4 is relative to the BCD + LQR-I oracle, so better controllers produce negative regret unrelated to the certification layer.

**Concrete fix:** Either run the conformal baselines on the same stacks (at least the Lenain and offset-free MPC controllers), or drop the cross-stack ranking claim and state that it is not a like-for-like comparison. Compute stack-specific oracles if cross-stack regrets are reported.

### M7. The oracle is neither attainable-bounding nor at the target level, and relative-regret ratios are unstable

**Location:** Section 6.1 ("The oracle … is not attainable by any method"); Table 5 and Fig. 3; Section 6.3 ("27–92% below"); `exp_system.oracle_lambda`.

- **The oracle under-covers on fresh runs.** The oracle is a fixed point of `np.quantile(·, 0.9)` (an interpolated, non-conformal quantile) over 600 runs at a single fixed plan. On its own 200-run check (`oracle_p`) it averages 0.893 / 0.889 / 0.891 and is below 0.9 on 57–60% of fields (minimum 0.815).
- **The oracle is beaten.** CE+ marginal has negative regret on 63% of R1 fields. On 47% of R1 fields CE+ has both higher P and lower overlap than the oracle. This is possible because CE+ is run-adaptive (a different plan for each operation through σ(z)) while the oracle is restricted to one plan. The statement that the oracle "is not attainable by any method" is therefore false as written.
- **Ratios of regrets depend on the oracle's offset.** For example, in R2 marginal CE+ 0.70 pp vs CPP 1.80 pp gives "61% less regret". Shifting the oracle by 0.3 pp changes this to 73%. Ratios of small differences relative to a noisy, biased zero point should not be headline quantities.
- **The oracle is defined only for BCD + LQR-I**, yet it is used as the zero point for all stacks (see M6).

**Concrete fix:**

- Define the oracle with a conservative order statistic or a larger number of runs, so that its own P ≥ 0.9 on fresh runs. Report its fresh-run P in Table 5.
- Add a run-adaptive oracle, or state explicitly that the oracle is a fixed-plan reference.
- Report regret in absolute pp only and drop "x% less regret".
- Keep "excess overlap at matched coverage" as the efficiency metric throughout.

### M8. The theory pivot is evaluated inside its own generative model; learned comparators get coarser inputs

**Location:** Sections 4.3, 6.4–6.6, Table 9, Fig. 6; `evt_theory.predict_cdf`.

**What `predict_cdf` uses.** It draws operating conditions with the *simulator's own* `exp_system.make_cond`. That function covers the regime's moisture law, roll-compensation distribution, mounting-bias law and the GNSS error bank used for test runs. It then runs the *simulator itself* noise-free (`core.simulate(..., ZeroRNG(), trace=...)`) to obtain mean trajectories.

**Why this is a fairness problem.** The "zero-data theory" therefore has privileged, exact access to the data-generating process, including the true operating-condition distribution. In practice that distribution is unknown and the model is misspecified. By contrast:

- the CQR and ridge comparators receive six geometric features plus log width and log p2p;
- they receive no GNSS statistics, controller model or roll features.

Two further indicators of the model-match advantage:

- The non-conformal "theory only" deployment in E-low v2 is nearly oracle-efficient: excess +0.05 / +0.17 / −0.59 pp at P 0.904 / 0.906 / 0.881.
- The 1.7–3.7× accuracy advantage (abstract) and the mixed-fleet gains are upper bounds for a well-specified model.

**Concrete fix:**

- (a) Run a misspecification study. Evaluate the theory with perturbed controller gains, slip and roll parameters, a GNSS bank from different stations or days than the test runs, and a moisture law different from the test law. Report the pivot's log error and excess overlap.
- (b) Give the learned predictors the same physical inputs the theory consumes (GNSS RMS/PSD summary, controller bandwidth, DEM roll statistics), or the theory's intermediate outputs.
- (c) State in the abstract that the theory and the simulator share the vehicle model.

### M9. The mixed-fleet headline uses the weakest comparator; the strongest one is missing from the resampling check

**Location:** Abstract ("reduced excess overlap from 29.8 to 3.0 percentage points relative to pooled calibration"); highlights; Section 7.1; Table 8; `results/lowdata_v3/validity_resample_extended_curves.txt`.

- **The headline comparator is a strawman.** "Raw pooling" of scores from a 6 m DGPS machine and a 1.5 m RTK machine is something no practitioner would do. The configuration is known, so at a minimum the scores would be normalised by width or p2p.
- **The strongest comparator is CQR,** which is configuration-aware. The theory's gain over it is:

| CQR comparison | Result |
|---|---|
| Marginal, registered | +1.87 vs +3.16 pp (40.9%, significant) |
| PAC, registered | +7.91 vs +9.01 pp (not significant, Holm p 0.065) |
| PAC, matched coverage | CQR better (+2.54 vs +2.64 pp) |

- **CQR is absent from the resampling check** (Table 7 and the source file have no CQR rows), which is the basis of the abstract's numbers.
- **Data budget is not stated.** Per-configuration (stratified) raw pooling with 25 calibration fields *per configuration* would average about +3.10 pp marginal and +12.27 pp PAC (mean of the within-regime raw cells in Table 7), close to the theory's mixed-fleet +2.96 / +14.69 pp. Stratification at the same total budget (about 8 fields per configuration) is infeasible for ε = 0.1. That is a genuine argument *for* the pivot and should be made explicitly rather than through a raw-pooling headline.

**Concrete fix:**

- Headline the comparison against the strongest valid comparator (CQR, and spec × scale law).
- Add CQR to the resampling check.
- Add a stratified-by-configuration baseline with its data budget stated.

### M10. Spot-check of reported numbers against raw files: 13 matches, 1 mismatch, 1 unsupported statement

| # | Manuscript location | Reported | Raw file | Result |
|---|---|---|---|---|
| 1 | Table 5, R1 marginal | CE+ 8.39% (P 0.903), CPP 10.35% (0.944), Lindemann 10.86% (0.959); 18.9% / 22.7% | `results/v8/summary.txt`; recomputed from `system_v8.csv` | Match |
| 2 | Table 5 caption | largest Holm p 0.0225; field-clustered p 0.70 / 0.98 / 0.29; 0/30 PAC failures | `summary.txt` | Match (0/30 also reproduced with binomial test on the CSV) |
| 3 | Table 5, R3 PAC regret | +4.02 / +10.61 / +27.33; oracle 8.65 / 24.92 / 15.28% | `regret_table.txt`; CSV recomputation | Match |
| 4 | **Section 6.3**: "CE+ is **27–92%** below the comparators in the ten comparisons where its regret is positive" | 27–92% | `regret_table.txt`: R3 marginal vs Lindemann is +0.45 vs +8.94 pp, i.e. **95%** less (commit 170c4f3 itself says "27–95%") | **Mismatch**: the range should be 27–95% |
| 5 | Table S22 (applied overlap) | 30.05 / 31.04 / 31.46 … ; 2.8–29.3% | `summary.txt` | Match |
| 6 | Table 6 / S9, C1 and C2 | +0.27 vs +1.56 (Holm p 0.0002); −0.38 vs +1.10 (0.0012) | `lowdata_v2/summary.txt` | Match |
| 7 | Section 6.4, matched coverage | +0.06 vs +0.41; +0.46 vs +0.66 | `lowdata_v2/matched_coverage.txt` (R1 PAC theory +0.06, raw +0.41) | Match |
| 8 | Table 7, mixed fleet | theory 0.9243 / 0.747 / +2.96; raw +29.80; PAC theory +14.69 | `validity_resample_extended_curves.txt` | Match (all 26 cells PASS) |
| 9 | Table 8, matched coverage | +15.54 / +20.55 / +10.68 / +1.41 / +0.73; PAC CQR +2.54, theory +2.64 | `summary_extended_curves.txt` | Match |
| 10 | Table 9, lower block | features 0.095 / 0.049 / 0.206; theory 0.029 / 0.029 / 0.056; oracle-trained 0.020 / 0.021 / 0.080 | `feature_learning_curve.txt` | Match |
| 11 | Table 4 | R3 −0.040 / 0.108 → +0.008 / 0.106; R1, R2 rows | `check_boundary_R3.txt`, `check_boundary_R1_R2.txt` | Match |
| 12 | Supplementary D.2 | R2 erosion CE+ 0.153, CPP 0.158, oracle 0.149 m | CSV `lam_mean`, `param`, `oracle_lam` | Match (0.1527 / 0.1579 / 0.1493) |
| 13 | Section 6.4, C3 | 5 of 8 met; CQR PAC 12.3%, Holm p 0.0648; spec × scale law p 0.1805 / 0.9555 | `lowdata_v3/summary.txt` | Match |
| 14 | Section 4.4 runtimes | 133–187 / 287–353 / 16–51 s | `theory_runtime.txt` | Match |
| 15 | Section 4.4: "The cost scales with total pass length" | — | Within R1, the longest field (3519 m) took 150 s and the 2415 m field took 187 s. Within R2, the shortest field (5225 m) took the longest (353 s). | **Not supported** within a regime; holds only across regimes |

**Fix:** Correct "27–92%" to "27–95%", or better drop relative regret (M7). Qualify the runtime-scaling sentence.

## 5. Minor issues

1. **Exploratory figures cited where confirmatory data exist.** Introduction and Section 6.3 quote v7 (exploratory) farmer-tuned meet rates of 0.733 / 0.27 / 0.700. The confirmatory v8 data give 0.700 / 0.200 / 0.467 with the paper's binomial meet test. Use v8, or report both.
2. **The relative overlap reduction inflates practical impact.** "4.0–54.7% less overlap" is relative to an overlap ratio. In terms of total swath over the main area (1 + J), the savings are about 0.9% (R2 vs CPP) to about 16% (R3 PAC vs Lindemann PAC). In applied-input terms including the headland, R2 vs CPP is about 0.8%. Report input savings in absolute terms (e.g. litres or kg per ha) alongside the relative numbers.
3. **Calibration runs are not shared across methods.** In `systems_for`, every baseline calls `collect` with the shared `rng`, so each method gets its own independent 100 calibration runs, and CE+ uses yet another seed. `CalData` sharing exists (`cal=`) but is unused. Where reference plans coincide (CPP, Lindemann, GP on π(0)), share the runs. Elsewhere, share the operating conditions C to reduce paired-comparison noise.
4. **The "about 25 baselines" count includes weak adaptations:**
   - Pointwise Gaussian belief and GP without Bonferroni are per-point chance constraints and achieve P ≈ 0.
   - Tube-MPC uses its W99 radius as a per-side margin (P = 1.000, regret +35 to +164 pp; the Wmax variant is infeasible in all 90 fields).
   - Spec overlap appears on 9 stacks.

   They are valid reference points, but they should not count towards the breadth of the benchmark. Report how many distinct, competent baselines there are.
5. **The farmer-tuned baseline is tuned on only 5 training fields to pooled P ≥ 0.9**, at a level of effort much lower than CE+. A per-regime grid-searched fixed margin tuned on the 30 v7 fields (the same fields used to refine CE+) would be a fairer "industry best practice" baseline.
6. **The validity claim V (marginal) is a non-rejection test** ("not significantly below 0.9"). It has low power with 30 clustered fields. Report the one-sided lower confidence bound on pooled P(no miss) per regime instead of only the p-value.
7. **Table 5 lacks per-method meet rates and infeasibility counts.** They are available in the CSV (e.g. CE+ marginal meet 0.933 / 0.900 / 0.900, consistent with Proposition 7). Add them.
8. **Table S19 note contradicts its claim.** The note says the extended curves change "only the raw and scale-law mixed-fleet cells", but it also changes the R3 raw marginal cell. The note mentions this, so just reword "only".
9. **The secondary metric is described loosely.** Section 6.3 says applied overlap "gave the same direction in all 12 comparisons (reductions 2.8–29.3%)". Note that the R2 reductions vs CPP are 2.8% at Holm p 0.0345, near the threshold.
10. **The matched-coverage factor is fitted on the test fields themselves** (`scripts/matched_coverage.py`), so it is an oracle-style diagnostic. State this explicitly in Section 6.1.
11. **The resampling check was announced with the wrong cell count.** Appendix E notes that the commit announcing it says "28 cells". Remove Appendix E before submission, as the authors intend.

## 6. Questions to the authors

1. What is the v8 overlap of CPP when it is given (i) the exact score, (ii) the training-derived reference plan λ₀, and (iii) both? Same question for Lindemann pair-level with a pooled quantile.
2. What is the gain of CE+ in R1 without the probe-line covariate (constant σ, same λ₀)? How long is the probe line, and what does it cost in time and overlap per operation?
3. Why does nominal-plan CPP *over*-cover (P 0.944 / 0.923 / 0.946) when Proposition 1 predicts that nominal-plan calibration under-covers? Is the over-coverage entirely due to the looser pair score?
4. Can you report the pre-registered secondary analyses of `theory_v8.md` §6: the full ranking, scenario/DRO/Lindemann-union vs CE+ PAC, and sensitivity to GATE, REF_INFLATE and SIG_FLOOR?
5. How do you explain the R2 failure of "Follow-previous-pass + LQR-I + CE+" (P 0.850, meet 0.72)? Which assumption is violated, and how would a practitioner detect it before deployment?
6. How does the theory pivot's log error change when the theory's operating-condition distribution or GNSS bank differs from the test distribution (for example, different CORS stations or days, or a wrong moisture range)?
7. Why was CQR excluded from the resampling check, given that it was the strongest comparator in E-low v3?
8. Can the oracle be computed with a conformal or conservative order statistic, so that its fresh-run P(no miss) is at least 0.9? How do Table 5's regrets change?
9. Why are the scenario approach and DRO run at β = 0.01 rather than at δ = 0.1?
