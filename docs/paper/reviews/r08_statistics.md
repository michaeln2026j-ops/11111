# Review R08: Statistical methodology and research transparency

**Manuscript:** Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations (Computers and Electronics in Agriculture)

**Reviewer focus:** pre-registration fidelity, multiple testing (Holm), Wilcoxon and clustered inference, validity checks, analytic flexibility (garden of forking paths)

**Material checked:** `docs/paper/manuscript.md`, `docs/paper/supplementary.md`; pre-registrations `docs/theory_v8.md` §6, `docs/prereg_lowdata.md` (v1), `docs/prereg_lowdata_v2.md`, `docs/prereg_lowdata_v3.md`, `docs/prereg_validity.md`; results `results/v8/summary.txt`, `results/lowdata/summary.txt`, `results/lowdata_v2/{summary,matched_coverage}.txt`, `results/lowdata_v2/lowdata_R*.csv`, `results/lowdata_v3/{summary,summary_extended_curves,validity_resample,validity_resample_extended_curves}.txt`; git history and file timestamps of registrations, run logs and outputs.

---

## 1 Summary

The paper proposes conformal erosion (CE/CE+), which calibrates an exact covering-radius run score on a dominating reference plan, and CE-EVT-R, which certifies fields that have no history by cross-field split conformal calibration. CE-EVT-R pivots each field's single historical score by a theory-predicted 0.9 quantile. The empirical programme is unusually transparent. It consists of:

- **v8:** one pre-registered confirmatory comparison with target-field data, on fields 50–79.
- **E-low v1–v3:** three sequential pre-registered zero-data experiments.
  - v1: fields 80+, failed.
  - v2: fields 50–79, both narrow claims met.
  - v3: fields 5–19 plus a mixed fleet, met in part (C3 5/8 comparisons, C4 1/6 cells).
- **Resampling check:** a pre-registered two-level check of the coverage guarantee, which passed all 26 cells.

Post hoc analyses support the main narrative: matched coverage, learning curves of feature predictors, the information-limit prediction, the field-edge terms and the extended margin curves.

**Timing of registrations.** I checked commit times against result commit times and against the modification times of untracked intermediate files. Every registration predates the outputs it governs:

| Experiment | Registration committed | First output |
|---|---|---|
| v1 | 05:27 | Phase A from about 09:08 |
| v2 | 14:49 | Phase A pickles from 14:56; summary 16:38 |
| v3 | 17:04 | Phase A logs from 17:08; summary 18:55 |
| Resampling check | 19:04 | History banks 19:46–19:48; summary 19:50 |
| v8 | 02:57 | Run outputs 17:06–21:33 |

Between the v8 registration and the v8 run, the only simulator change I found adds optional tracing that draws no random numbers, plus shard-resume logic. Nothing changes v8 results.

**How the reported tests map onto the registrations:**

| Experiment | Registered analysis | Implemented | Reported faithfully? |
|---|---|---|---|
| v8 V/E | Field-level validity; Wilcoxon + Holm over 12 | Yes (Holm over 12; field-clustered binomial; 0/30 PAC fails) | Yes |
| E-low v1 | Field-clustered validity; ≥10% vs strongest valid comparator; Holm over regime × comparator | Yes (3 rows) | Yes, but Table 6 omits that CE-EVT itself was invalid in 3 cells |
| E-low v2 | Beta-quantile validity; Holm over regime × class × comparator; C1, C2 | Yes (Holm over 15 rows) | Yes; predictions vs scale law reported only in S10 |
| E-low v3 | Validity ≥0.89 / ≥0.85; Holm over all comparisons; C3–C5 | Yes (Holm over 14) | Partly: the method's own failure of the v3 validity criterion (R1 marginal 0.877) is not stated in the main text |
| Resampling check | 4000 replicates, thresholds 0.895 / 0.88 | Yes; numbers in the registered reading (S19) | Main Table 7 uses a post hoc re-reading (extended curves) |

The headline confirmatory claims are therefore genuinely pre-registered and were run as registered. I have no evidence of p-hacking within any experiment.

My concerns are at a different level:

1. **Validity is "shown" by non-rejection or by deliberately lenient thresholds.**
2. **The E-low efficiency p-values are conditional on one shared calibration realisation.** The authors themselves diagnosed this flaw for validity, but they did not carry the diagnosis over to efficiency.
3. **Validity criteria were redesigned after each failure,** and the main text does not state these failures plainly.
4. **The abstract and highlights foreground descriptive or post hoc numbers.**

None of these invalidates the theory, but each changes how strongly the empirical claims can be stated.

---

## 2 Recommendation

**Major revision.**

| Criterion | Score (1–10) | Comment |
|---|---|---|
| Novelty | 7 | Exact score, decision-dependent calibration and theory-pivoted cross-field conformal calibration are new for agricultural CPP. |
| Soundness (statistical) | 5 | Confirmatory designs are registered and honoured, but validity criteria lack power, efficiency inference ignores the shared-calibration dependence, and some post hoc numbers are promoted. |
| Practical relevance | 6 | Clear for multi-configuration fleets. Within one configuration the paper itself finds no efficiency difference. All evidence is simulated. |
| Clarity / transparency | 7 | Status labelling (Table S20) is exemplary. Main-text tables and the abstract are less disciplined than the supplement. |

---

## 3 Strengths

1. **A real pre-registration chain, verifiable in git.** Each registration predates its outputs (Section 1), states fixed criteria, and is followed by a result file that prints MET or NOT MET verbatim. Failed claims are reported: E-low v1 in all three regimes, C3 as registered, C4 in 5 of 6 cells. This is rare and commendable.
2. **Explicit status labels.** Table S20 labels every result as pre-registered, developmental, exploratory or post hoc. Section 6.1 also states that all registered results used the theory without field-edge terms.
3. **Multiplicity handled within each experiment.** Holm is applied as registered: 12 comparisons in v8, 15 rows in E-low v2 (all regime × class × comparator rows, not only the two claims) and 14 in v3. The secondary v8 metric gets its own Holm family and is not used as confirmatory evidence.
4. **Self-correction of the validity test.** The authors recognised that test fields share one calibration pool, so realised coverage is a draw from Beta(k, n+1−k), and they designed a two-level resampling check that varies both the field split and the historical run (`prereg_validity.md`). That is the correct check of Proposition 5.
5. **The matched-coverage analysis was run and reported even though it weakens the authors' own registered wins.** It shows that C1 and C2 were mostly realised-coverage luck (Section 6.4, Table S11).
6. **Practical choices are made in advance, and comparisons stay within one guarantee class.** These include the +∞ rule, the training-only gate, deployment caps and common random numbers, and comparisons are always marginal vs marginal and PAC vs PAC.

---

## 4 Major issues

### M1. Validity is "established" by non-rejection or by thresholds with little power

**Where:**
- Abstract ("met every validity … claim").
- Section 6.3 and Table 5 (v8 claim V).
- Section 6.4 (E-low v2 Beta check).
- Section 6.5 and Table 7 (resampling criteria).
- Proposition 7.

**Why it matters:**

- **v8 V, marginal.** "Not significantly below 0.9" is a failure to reject, not evidence of validity. The registration (`theory_v8.md` §6) does not even name the test; the field-clustered one-sided test was chosen at analysis time.
  - With 30 fields, per-field coverage SD ≈ 0.036 (Beta(91,10) sd ≈ 0.030 combined with binomial sd ≈ 0.021 over 200 runs), the clustered SE is about 0.0066.
  - A true pooled coverage of about 0.884 would therefore be missed roughly 20% of the time.
  - The R3 value of 0.896 (p = 0.29) is uninformative in either direction.
- **v8 V, PAC.** "Fewer than 9 of 30 failing fields" has size about 2% under Bin(30, 0.143). It is almost powerless against a method that is merely marginally valid:
  - P(X ≥ 9 | p = 0.20) = 0.13, so such a method passes 87% of the time.
  - P(X ≥ 9 | p = 0.25) = 0.33, so it passes 67% of the time.
  - The criterion cannot distinguish PAC validity from marginal validity, which is exactly what the PAC claim is about. The observed 0/30 is informative descriptively but is not what was tested.
- **E-low v2.** The criterion "pooled P(no miss) ≥ Beta 5% quantile" (0.798 marginal) is passed by CE-EVT-R at a realised 0.844. It would be passed by many methods whose true coverage is well below 0.9. It is a sanity bound, not a validity test.
- **Resampling check.**
  - For n = 25 and ε = 0.1, the exact marginal coverage of split conformal with continuous scores is k/(n+1) = 24/26 = 0.9231. The registered threshold of 0.895 sits 0.028 below that, about 35 Monte Carlo SEs. It would accept a systematic implementation bias of two to three percentage points.
  - Observed R1 marginal coverage (0.9193–0.9205, SE 0.0008) is about 3–5 SEs below 0.9231. This is not a validity failure, since it is still above 0.9, but it is a detectable deviation that a sharper reference would reveal (see Q3).

**Fix:**

1. Re-express every validity statement as an estimate with a one-sided confidence bound, for example "pooled coverage 0.896, lower 95% bound 0.885". Add a statement of the smallest coverage shortfall each criterion could detect with 80% power.
2. For PAC in v8, report the number of failing fields together with an exact upper bound on the per-field failure rate. State plainly that the criterion does not distinguish PAC from marginal validity.
3. In Section 6.5, report deviations from the exact reference values: 24/26 for marginal, and the PAC-implied probability for the PAC rule. The 0.895 and 0.88 thresholds are too loose to serve as the only reference.
4. Remove the word "confirmed" where only non-rejection was obtained.

### M2. E-low efficiency tests treat fields as independent although all test fields share one calibration realisation

**Where:**
- Section 6.4 and Table 6 (C1 Holm p 0.0002, C2 0.0012).
- Supplementary Tables S9 and S16 (C3).
- Section 7.2.

**Why it matters:**

- **v2.** In leave-one-field-out with n_cal = 29, any two test fields share 28 of their 29 calibration scores. Each calibration score is a single fixed historical run.
  - The per-field paired differences therefore share a common random component, the realised calibration quantile.
  - The Wilcoxon signed-rank test over 30 fields measures how consistently that single draw moves all fields in the same direction (24 of 30 positive for C1 and for C2, from `lowdata_R*.csv`). It does not measure what would happen with a new set of historical runs.
- **v3.** Same problem: 400 subsets of one fixed 30-field (or 90-field) pool, each field with one fixed run.
- **The authors made this argument themselves for validity.** In Section 6.4 and S10 they say v1's field-clustered validity test "ignored that all test fields share almost the same calibration pool". In S10 and `prereg_validity.md` §1 they say v3's 400 subsets do not average out "the luck of those runs". The same reasoning applies to the efficiency p-values, but they are reported without qualification.
- **The data confirm it.** In `results/lowdata_v2/matched_coverage.txt`, the R3 marginal comparison at ε = 0.1, n_cal = 25, averaged over 400 subsets, reverses the C2 direction: theory +5.26 pp versus raw +1.34 pp, against the registered −0.38 vs +1.10. Over the two-level resampling (Table 7) the two are equal (+5.06 vs +5.20). C2's p = 0.0012 is therefore a statement about one draw of historical runs, not about the method.

**Fix:**

1. State explicitly that the v2 and v3 p-values are conditional on the realised historical runs and do not support population-level efficiency claims.
2. Base any efficiency inference on the two-level resampling design, using paired per-replicate differences with percentile intervals. Alternatively, use a hierarchical bootstrap that resamples fields and redraws each calibration field's run from its 200-run bank.
3. Report these intervals for the mixed-fleet comparisons in particular, since they are the paper's main efficiency message.

### M3. Validity criteria were redesigned after each failure; the main text does not list the proposed method's registered validity failures

**Where:**
- Table 6.
- Section 6.4 (v1 and v3 paragraphs).
- Section 6.5 ("the sub-0.9 realised coverages … were such draws").
- Abstract and highlights ("held in 26 of 26 checks").

**Why it matters (forking paths):** every redesign is statistically defensible on its own, but the sequence is: registered validity test → failure → test declared misspecified → new test.

- **v1.** CE-EVT marginal was invalid under the registered test in R1 (p 0.018) and R2 (p 0.000). CE-EVT PAC could not deploy on any of 31 R3 fields.
  - Table 6 reports only excess-overlap numbers. Its columns also mix guarantee classes without labels: +5.35 and +3.98 are PAC (R1, R2) and +5.70 is marginal (R3).
- **v3.**
  - Under the registered criterion (mean ≥ 0.89), CE-EVT-R failed validity in R1 marginal (0.877). This appears only in the supplement (S17, "C4 details").
  - The main text mentions only that the best comparator was invalid, and later reframes the 0.877 as a "draw".
  - `prereg_validity.md` was committed at 19:04, nine minutes after the v3 results (18:55). Its §1 explicitly motivates itself by the v3 R1 value.
- **The resampling check largely verifies exchangeability by construction.** It randomly splits a finite pool of simulated fields and redraws runs from the same simulator, so exchangeability holds by design. It therefore checks the implementation, the deployment cap and the reference → deployed plan transfer. It cannot test the substantive assumption that real fields of a farm are exchangeable (time trends, unseen field types, operator effects).
  - The 26 cells are also strongly dependent: they use the same fields, the same evaluation curves and four pivots that share one conformal machinery. "26 of 26" overstates the amount of independent evidence.

**Fix:**

1. Add a "validity" column to Table 6 that lists every registered validity outcome for the proposed method:
   - v1: invalid in R1 and R2 marginal; no deployment in R3 PAC.
   - v2: passed a lenient Beta bound.
   - v3: failed in R1 marginal.
   - Resampling: passed.
2. State in Section 6.5 that the resampling check was registered after, and in response to, the v3 validity failure.
3. Describe the check as a verification of the implementation and of the transfer step under exchangeability, not as an empirical confirmation of exchangeability.
4. In the abstract and highlights, replace "26 of 26 checks" with a formulation that conveys this, for example "a pre-registered resampling check found mean coverage 0.919–0.929 (nominal 0.923) in all regimes and pivots".

### M4. The abstract and highlights foreground descriptive or post hoc numbers and the weakest comparator

**Where:** Abstract, highlights, Section 8.

**Why it matters:**

- **"Across a mixed machine fleet the theory pivot reduced excess overlap from 29.8 to 3.0 percentage points relative to pooled calibration."**
  - This figure comes from the resampling check, whose efficiency outputs were registered as descriptive and outside the criterion (`prereg_validity.md` §2, "不参与判据" [not part of the pass criterion]).
  - It is compared against raw pooling, the weakest comparator.
  - The registered mixed-fleet claim C3 was not met: against spec × scale law, mean +1.87 vs +13.18 pp, Holm p 0.18; against CQR (PAC), Holm p 0.065.
- **"With one run per field it predicted margins 1.7–3.7 times more accurately than data-driven regressors"** is post hoc (Table 9 lower block, Fig. 6). The abstract does not say so. The ratios are 0.049/0.029, 0.095/0.029 and 0.206/0.056 against regressors trained on 30–60 fields.
- **Missing from the abstract:** v1 failed; C3 and C4 were not met; and within one configuration the v2 "wins" are, by the authors' own analysis, differences in realised coverage.

**Fix:**

1. Rewrite the abstract so that each number carries its status (pre-registered confirmatory, pre-registered descriptive, post hoc).
2. Quote the mixed-fleet result against the strongest comparator (CQR and spec × scale law), with the registered outcome.
3. Include one sentence on the claims that were not met.
4. Apply the same discipline to the highlights.

### M5. Estimand–test mismatch: "≥ 10% relative reduction in mean" tested by a signed-rank test of zero shift

**Where:**
- v1 and v3 registrations.
- Section 6.4.
- Tables 6, S9 and S16.
- Supplementary "C3 details".

**Why it matters:**

- The claims are defined on a ratio of means, (mean_comp − mean_ours) / mean_comp ≥ 10%. Significance is assessed by a one-sided Wilcoxon signed-rank test of H0: zero location shift.
  - The 10% margin is applied only to the point estimate and is never tested.
  - The Wilcoxon test targets the pseudo-median of paired differences, not the difference of means.
- **The mismatch has consequences.** In C3 against spec × scale law, the mean reduction is 85.8% but Holm p is 0.18. Mean and rank answers diverge because of heterogeneity across the three machine configurations in the 45-field mixed fleet. The authors acknowledge that per-field differences "are not tabulated".
- **The relative metric is ill-defined when "ours" is negative.** S9 reports "+134.7%". Negative excess means deploying below the oracle margin, which in R1 marginal coincides with under-coverage (0.844). Such values reward under-coverage.
- **Recommendation for the registered analyses:** they must stand as registered, but they need a mean-based companion analysis.

**Fix:**

1. Add a companion analysis that tests the registered margin directly on the registered estimand: a paired bootstrap or t-interval on mean_comp − mean_ours − 0.1·mean_comp, or equivalently a ratio-of-means CI.
2. Tabulate per-field (or at least per-configuration) differences for the mixed fleet.
3. Report a test stratified by configuration (e.g., van Elteren) or per-configuration results.
4. Drop relative improvements above 100% in favour of absolute pp differences with CIs.

### M6. The central "equivalence within one configuration" conclusion is never tested and rests on in-sample matched coverage

**Where:**
- Contribution 5.
- Section 6.4 (v2 paragraph: "within 0.30 / 0.35 / 0.08–0.10 / 0.34–0.42 pp").
- Section 7.2.
- Section 7.4 ("choose the simplest").
- Table S11.

**Why it matters:**

- **The matched-coverage analysis is post hoc for v2 and secondary for v3.** The common factor c is tuned on the same test fields whose outcomes are then reported, and no uncertainty is attached.
- **"All pivots within ≤ 0.42 pp" is an equivalence statement made by failing to find differences.** With 15–30 fields that share a calibration realisation (M2), the power to find a 0.2–0.4 pp difference is unknown.
- **The range depends on an unregistered exclusion.** "Excluding a one-run-trained CQR scale" changes the R1 marginal range from 0.40 to 0.30 pp.
- **The equivalence holds only within some cells.** R3 marginal in v3 shows the theory pivot clearly worse at matched coverage (+1.64 vs +0.56 pp). Under 400 subsets of the v2 pool it is also worse (+5.26 vs +1.34 pp).
- **The practical recommendation in Section 7.4 is therefore not statistically supported.**

**Fix:**

1. Either perform a formal equivalence analysis (TOST with a stated margin, e.g. 0.25 pp, using the two-level resampling replicates and a field bootstrap for intervals), or soften the language to "no difference larger than X could be detected".
2. Report all pivots without exclusions, flagging CQR separately.
3. Label every matched-coverage number as in-sample.

### M7. Reuse of fields across experiments

Reused field ranges: 50–79 in v8, E-low v2 test, v3 calibration pool and the resampling check; 5–19 in system experiments v3–v6, E-low v3 test and the resampling check.

**Where:**
- Section 6.1 (field splits).
- Supplementary C.2 and Appendix E.
- Abstract ("90 fresh fields").

**What I verified:**

- **No v8 → v2 leakage.**
  - The v8 method was frozen at 02:57.
  - v8 outputs on fields 50–79 were first written at 17:06, after the v2 registration (14:49) and the v2 summary (16:38). The run logs suggest the v8 shards ran from about 16:40 after a resume patch (commit `269ec2e`, 16:43).
  - Neither experiment could have informed the other's method choice.
- **No change to v8 results from code edits.** Code changes to `core.py` between the v8 registration and the run are additive (an optional `trace` argument that draws no random numbers, and a new `exact_pair_scores` function).

**Remaining concerns:**

- **The experiments are not independent samples.** v8 and E-low v2 draw the same 30 fields per regime. Field-level idiosyncrasies (an atypical boundary, terrain or GNSS draw) are shared, so the two experiments are not independent samples of the field population. The abstract's "90 fresh fields" is true for each experiment separately but invites a reading of independent replication.
- **The v3 design used data that later entered v3.** The v3 calibration pool is the v2 test set. The v3 design probe (Table 9 upper block, the gate's candidates, the decision to target the mixed fleet) was built from v1 and v2 data, including per-field λ* of these very calibration fields. Validity is unaffected, but the efficiency comparison in v3 is not as "untouched" as the phrase "fields not seen by the analyses that designed it" suggests.
- **The resampling check is not independent of v2 and v3.** It reuses the v2/v3 fields and the same per-field evaluation curves (same seeds). Its coverage numbers therefore share Monte Carlo noise with the v2 and v3 readings.
- **Fields 5–19 were not unseen.** They were used in system experiments v3–v6 while the CE method was being developed. It is not stated whether any of the "development fields" used to correct the theory (Table 3, Supplementary B) lie in 5–19.

**Fix:**

1. Add a field-usage matrix to the supplement: field index range × experiment × role (train / calibration / test / development) × date of first use. Also state which fields served as theory development fields.
2. Replace "90 fresh fields" with "90 fields not used by any earlier system comparison".
3. State that v8 and E-low v2 share fields and are not independent replications.

### M8. No prospective power or sample-size justification; C4 "best comparator" selected on test data

**Where:** all registrations; Section 6.4 (v3); Table S16.

**Why it matters:**

- **No power analysis anywhere.** None of the five registrations contains a power or sample-size argument.
- **v3 could not have resolved its own non-inferiority claim.** It used 15 test fields per regime with a 0.25 pp non-inferiority margin. The authors' own v2 analysis (registered before v3) had already shown between-pivot differences of 0.1–0.4 pp at matched coverage. The design therefore had little chance of resolving C4, a fact the authors note only after the result ("of the same order as the 0.25 pp margin").
- **The "best comparator" was chosen on the test fields.** C4 compares the gated method against the minimum of three noisy means (raw, scale law, CQR), and the registration does not say whether that minimum is taken on test fields or whether invalid comparators qualify.
  - This is a winner's-curse comparison that biases against the method.
  - In R1 marginal it selected CQR, which was itself invalid (coverage 0.861) and whose low excess (−0.29 pp) reflects under-coverage.
  - The v1 registration specified "valid" comparators; v3 did not. This is an unregistered analyst choice, although it went against the authors.

**Fix:**

1. Report post hoc power or minimum detectable differences for each registered efficiency test (from the observed paired SDs).
2. Report C4 against each comparator separately and restricted to valid comparators, alongside the registered reading.
3. In the limitations, state that v3 was underpowered for C4 by design.

### M9. Post hoc re-readings appear as the primary numbers in main tables

**Where:** Table 7 (resampling) and Table 8 (mixed fleet, matched-coverage column).

**Why it matters:**

- **The re-reading was not part of any registration.** The extended curves (0.25 λ\*) were computed on 2026-10-15 02:17, after all registered results. The registered handling of deployments below the grid (read at 0.6 λ\*) was not specified in `prereg_lowdata_v3.md`; it was an implementation choice.
- **The numbers in Table 8 change materially, in the direction that favours the theory pivot:**

  | Mixed-fleet matched-coverage excess | Registered reading | Extended reading |
  |---|---|---|
  | Raw pooling, marginal | +12.89 | +15.54 pp |
  | Raw pooling, PAC | +13.47 | +18.61 pp |
  | Scale law, marginal | +17.22 | +20.55 pp |
  | Scale law, PAC | +17.07 | +21.46 pp |
  | CE-EVT-R | essentially unchanged | essentially unchanged |

  The re-reading is technically justified, since it removes readings at the grid floor that overstated both coverage and overlap. It should still not displace the registered values.
- **Table 7.** The differences are small (S19), but the registered reading should still be the one reported in the main table.

**Fix:**

1. Show the registered reading in the main tables and the extended reading as a labelled sensitivity column, or the reverse with an explicit "post hoc" label in the column header rather than only in the caption.
2. In Table 8 the matched-coverage column currently mixes a registered secondary analysis with a post hoc re-reading. Label it accordingly.

---

## 5 Minor issues

1. **Table 6, v1 row.** Label the class of each number (R1 and R2 are PAC comparisons, R3 is marginal). State that the proposed method was registered-invalid in R1/R2 marginal and could not deploy in R3 PAC.
2. **Section 6.4, "5 of 6 registered predictions borne out".** This counts only the "vs pooled raw" column of the v2 registration. Against the scale law, the predictions were wrong or only partly right in R1 PAC, R2 marginal and R3 marginal (Table S10). Report both columns in the main text.
3. **Number of cells.** The commit message of the resampling result (`63de5f6`) says "all 28 cells PASS", while the result files and the registration imply 26 (3 × 3 × 2 + 4 × 2). Appendix E notes the discrepancy but does not explain it. Explain it, or confirm that no cells were dropped.
4. **Unreported grids.** `results/lowdata_v2/matched_coverage.txt` contains additional ε ∈ {0.05, 0.2} and n_cal ∈ {10, 20, 25} grids over 400 subsets that the manuscript does not report. Some cut against the narrative (R3 at ε = 0.05: theory +14.18 pp vs scale law +8.25 pp). Report them in the supplement as exploratory, or state why they were omitted.
5. **v8 registration wording.** It says fields 50–79 were "never used by v1–v7". The manuscript's "fresh" is consistent, but the v8 validity test (field-clustered one-sided binomial) is not named in the registration. Say that the test was fixed at analysis time.
6. **Proposition 7 vs the registration.** Proposition 7 (manuscript) is "Proposition 4" in `theory_v8.md`. The registration refers to the latter. Add the mapping in the main text or Supplementary C, not only in Appendix E, which is marked for removal.
7. **No family-wise control across experiments.** Holm families are per experiment. This is acceptable for separately registered studies, but state it. The sequential design (v1 failed → v2 claims chosen from v1 exploratory data → v3) is itself a source of implicit multiplicity, and the reader should be told that C1 and C2 were selected because exploratory analysis indicated those cells would win.
8. **Fig. 7 / Proposition 8.** Each observation lies "within one predicted standard deviation", but the predicted SDs are 0.33–0.74 around means of 1.26–1.85. This is a weak test with essentially no power, and R1 (observed 1.018 vs 1.30 ± 0.35) is at the low edge. Calling it a prediction "borne out" overstates it. Present it as consistency, not confirmation.
9. **Monte Carlo SEs.** Table 7 reports Monte Carlo SEs for mean coverage only. Add SEs for the PAC fractions (binomial, about 0.004 at 4000 replicates) and for the mean excess.
10. **Fig. 3 intervals.** The "95% intervals" are not defined (t-interval over fields? bootstrap?). Specify.
11. **Reporting conventions.**
    - Report Holm p-values that print as 0.0000 as < 1e-4.
    - Give raw p-values alongside the adjusted ones in Tables S9 and S16.
12. **Registration language and permanence.**
    - All registrations are in Chinese. Provide verified English translations in the supplement so that reviewers and readers can check fidelity themselves.
    - Registration rests on git timestamps alone, which the authors control. Intermediate files (`*.pkl`, the curve and history banks) are not version-controlled, so only their file system modification times support the ordering; I found them consistent.
    - Deposit a frozen snapshot with content hashes (OSF or Zenodo) before publication, as `theory_v8.md` §7 itself recommends.
13. **v3 calibration pool size.** The registration says "about 89 valid fields"; the results say 90. Clarify.
14. **Appendix E.** "Notes for the authors (remove before submission)" is still in the supplementary file.
15. **Exact marginal coverage.** Section 6.5 says marginal coverage lies "between 1−ε and the upper bound 1−ε+1/(n+1)". Also give the exact value k/(n+1) = 0.923 for continuous scores and comment on R2 (0.928, above it) and R1 (0.919, below it).
16. **"Theory only" row in Table S8.** It is (correctly) flagged as having no guarantee, but `summary.txt` labels it "valid=yes". Remove the label from the generated output to avoid misquotation.

---

## 6 Questions to the authors

1. **v8 launch.** When was the v8 confirmatory run first launched? Commit `269ec2e` adds shard resumption "after an interruption" at 16:43. Did any partial v8 output on fields 50–79 exist before the E-low v2 registration at 14:49?
2. **Cell count.** Why does commit `63de5f6` report 28 cells while the files contain 26? Was any method or class computed and later dropped?
3. **R1 coverage deficit.** In the resampling check, R1 marginal mean coverage (0.9193–0.9205, SE 0.0008) lies 3–5 SEs below the exact split-conformal value 24/26 = 0.9231. Is this due to the reference → deployed transfer (κ of Theorem 5), the deployment cap, curve interpolation, or the 2 mm rounding? A decomposition would make the check a real implementation test.
4. **Mixed-fleet breakdown.** Can you tabulate per-configuration (RTK 3 m / RTK 1.5 m / DGPS 6 m) mean differences and signed-rank results for C3 against spec × scale law and against CQR? Which configuration drives the 85.8% mean gain that is not significant?
5. **Non-inferiority test.** How exactly were the non-inferiority tests in v2 and v3 implemented: a Wilcoxon on d + 0.25 pp, or something else? Is this documented in the analysis scripts?
6. **Development fields.** Which field indices were the "development fields" used for the theory corrections (Table 3, Supplementary B)? Do any lie in 5–79?
7. **v3 design probe.** Did the probe (Table 9 upper block) use λ\* of the fields that later formed the v3 calibration pool? If so, what was the probe's role in choosing the mixed-fleet comparators and C3's 10% threshold?
8. **Unreported analyses.** Were further analyses on the v2/v3 test fields run but not reported (other ε, n_cal, pivots, metrics), beyond those visible in `matched_coverage.txt`?
9. **Extended curves.** Would you accept reporting the registered readings as primary in Tables 7 and 8, with the extended-curve readings as sensitivity analyses?
10. **Real-vehicle registration.** For the planned real-vehicle validation (Section 6.7), will the analysis plan specify a power calculation and an equivalence or non-inferiority formulation of the coverage claim, rather than "not significantly below"?
