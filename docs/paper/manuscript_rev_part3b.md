### 6.3 Experiment A: fields with operation history

**A1, pre-registered comparison on 90 fresh fields.** The registration fixed two claims on fields 50–79 of each configuration: **V** (validity), CE+ pooled P(no miss) not significantly below 0.9 and CE+ PAC failing the meet test on fewer than 9 of 30 fields; **E** (efficiency within the guarantee class), CE+ has lower main-area overlap than conformal predictive programming (CPrP; Zhao et al., 2024) and union-bound conformal planning at pair level (UBCP; Lindemann et al., 2023), in both classes, by one-sided paired Wilcoxon tests with Holm correction over 12 comparisons. All methods used 100 calibration runs per field and the BCD + LQR-I stack. Both claims were met in every configuration (Table 4). Table 4 also shows the two practice rules, which the registration did not include as comparators.

<!-- source: results/v8/summary.txt; results/revision/rv1_v8_reanalysis.txt -->
| Config. | Method | P(no miss) | Meet rate | Missed area % | Overlap % | Regret pp |
|---|---|---|---|---|---|---|
| R1 | CE+ / CE+ PAC | 0.903 / 0.941 | 0.93 / 1.00 | 0.001 / 0.001 | **8.39** / **9.04** | −0.26 / +0.38 |
| | CPrP / CPrP PAC | 0.944 / 0.967 | 1.00 / 1.00 | 0.001 / 0.000 | 10.35 / 11.47 | +1.69 / +2.82 |
| | UBCP / UBCP PAC | 0.959 / 0.988 | 1.00 / 1.00 | 0.001 / 0.000 | 10.86 / 13.76 | +2.20 / +5.10 |
| | Vendor rule; farmer-tuned | 0.000; 0.897 | 0.00; 0.70 | 0.216; 0.001 | 1.75; 9.22 | −6.90; +0.57 |
| R2 | CE+ / CE+ PAC | 0.911 / 0.944 | 0.90 / 1.00 | 0.001 / 0.001 | **25.62** / **28.14** | +0.70 / +3.22 |
| | CPrP / CPrP PAC | 0.923 / 0.956 | 0.97 / 1.00 | 0.001 / 0.001 | 26.72 / 29.32 | +1.80 / +4.40 |
| | UBCP / UBCP PAC | 0.944 / 0.991 | 0.97 / 1.00 | 0.001 / 0.000 | 28.38 / 44.80 | +3.46 / +19.87 |
| | Vendor rule; farmer-tuned | 0.000; 0.834 | 0.00; 0.20 | 0.642; 0.001 | 3.46; 23.00 | −21.46; −1.92 |
| R3 | CE+ / CE+ PAC | 0.896 / 0.933 | 0.90 / 1.00 | 0.027 / 0.020 | **15.73** / **19.30** | +0.45 / +4.02 |
| | CPrP / CPrP PAC | 0.946 / 0.969 | 1.00 / 1.00 | 0.017 / 0.013 | 20.63 / 25.89 | +5.35 / +10.61 |
| | UBCP / UBCP PAC | 0.960 / 0.983 | 1.00 / 1.00 | 0.014 / 0.006 | 24.22 / 42.61 | +8.94 / +27.33 |
| | Vendor rule; farmer-tuned | 0.403; 0.834 | 0.00; 0.47 | 0.120; 0.036 | 7.59; 13.53 | −7.69; −1.75 |

*Table 4. Experiment A1 (pre-registered; 30 fresh fields per configuration). Overlap reductions of CE+ against CPrP and UBCP, within the guarantee class: 18.9% and 22.7% (R1 marginal), 21.2% and 34.3% (R1 PAC), 4.1% and 9.7% (R2 marginal), 4.0% and 37.2% (R2 PAC), 23.8% and 35.1% (R3 marginal), 25.5% and 54.7% (R3 PAC); all 12 Holm-significant (largest Holm p 0.0225). CE+ marginal is not significantly below 0.9 (field-clustered p 0.70, 0.98, 0.29); CE+ PAC fails the meet test on 0 of 30 fields in every configuration. Practice rules, missed area and regret are descriptive. The vendor rule is twice the nominal pass-to-pass accuracy; the farmer-tuned margin was tuned once on the five training fields.*

![](../../figures/paper/fig_v8_regret.png)

**Fig. 3.** Regret (overlap above the per-field oracle, pp) in Experiment A1 for the marginal (a) and PAC (b) guarantee classes; bars are means over 30 fields with 95% intervals, and numbers above bars are pooled P(no miss).

*What the gain is made of.* All compared methods deploy plans from the same family $\pi(\lambda)$ and differ only in how $\lambda$ is chosen, so at equal realised coverage they would deploy the same plan. The gain is calibration tightness: the comparators calibrate pair or per-constraint scores on the nominal plan or through a union bound and over-cover (P 0.92–0.99 at a nominal 0.9), which is what their extra overlap buys; CE+ reaches its target (Fig. 3). Most of the gain comes from the exact score and the reference plan, not from the probe-line normalisation: CE-q, which has neither the normalisation nor the training-field reference plan, reached 8.82%, 25.51% and 16.19% overlap in R1–R3 against 10.35%, 26.72% and 20.63% for CPrP. Measured as regret, CE+ was 27–95% below the comparators in the cells where its regret is positive. The applied overlap including the headland gave the same direction in all 12 comparisons (reductions 2.8–29.3%, all Holm-significant; Table S22).

*Transfer check.* The transfer argument needs the deployed margin to be at most the reference margin. In R1 and R2 this held on every field. In R3 the mean deployed CE+ margin exceeded $\lambda_\mathrm{ref}$ on 9 of 30 fields (marginal) and 19 of 30 (PAC); on those fields the guarantee rests on no theorem, although the measured coverage held (pooled P 0.896 and 0.933, meet rate 0.90 and 1.00). With the transfer check of Section 4.2, these fields fall back to the assumption-free CE, which in R3 deployed 17.77% overlap at P 0.928.

*Other stacks.* Applied on six planner–controller stacks, CE and CE+ met the design meet rate except in one case: CE+ on follow-previous-pass guidance in R2 reached P 0.850 with a meet rate of 0.70 (PAC 0.941 and 0.87). Follow-previous-pass guidance steers each pass relative to the previous executed pass, which couples passes and violates the transfer assumption; the assumption-free CE on the same stack met its target (P 0.945). The full table is in Supplementary Table S23.

*Practice rules.* The vendor rule (twice the nominal pass-to-pass accuracy) missed some strip on almost every run (P 0.000 under RTK, 0.403 under DGPS), but the missed area was small: 0.22%, 0.64% and 0.12% of the main area. The farmer-tuned margin met the target on 70% (R1), 20% (R2) and 47% (R3) of fields; it used 0.8 pp more overlap than CE+ in R1 and 2.6 pp (R2) and 2.2 pp (R3) less. Whether CE+'s extra overlap is worth its smaller miss probability is a question of cost (Section 6.6).

**A2, few runs per field (revision, pre-registered).** A2 replaces the 100 calibration runs by $n=9$–100 runs drawn from 200-run banks on 45 fields per configuration (2000 replicates per field; CE-q, the variant CE+ reduces to under constant normalisation; deployed plans evaluated on independent test runs). Both registered predictions were met: marginal mean coverage was 0.896–0.943, never below 0.895, and in line with the exact value $k_\star/(n+1)$ (0.900, 0.938, 0.913, 0.902, 0.901 for $n=9$, 15, 22, 40, 100); the PAC fraction of replicates with coverage at least 0.9 was 0.890–0.951 against a required 0.88 (Table S24). The price of few runs is overlap. With 9 runs the marginal rule cost 1.3, 4.0 and 8.3 pp above the oracle in R1–R3; the PAC rule needs at least 22 runs and then cost 3.4, 10.0 and 18.7 pp, falling to 1.1, 3.2 and 4.3 pp with 100 runs. With fewer than about 20 logged operations per field, cross-field calibration (Experiment B) is the practical route.

### 6.4 Experiment B: fields without operation history

**B1–B3, pre-registered zero-data experiments.** Three experiments were registered in sequence, each designed from the previous one's results and run on fields that no earlier zero-data analysis had used (Table 5; details in Supplementary D.3–D.6).

<!-- source: results/lowdata/summary.txt; results/lowdata_v2/summary.txt; results/lowdata_v2/matched_coverage.txt; results/lowdata_v3/summary.txt -->
| Experiment | Method; test fields; $n$ | Registered claims | Outcome |
|---|---|---|---|
| B1 | probability-integral-transform pivot; 148 fields; 30 | valid and ≥ 10% less excess overlap than the strongest valid comparator, every configuration | **Not met** in R1–R3 (+5.35, +3.98, +5.70 pp vs +3.22, +3.26, +1.31 pp) |
| B2 | XCE-T; 90 fields; 29 | C1: R1 PAC, and C2: R3 marginal, ≥ 10% better than raw pooling | **Both met** (Holm p 0.0002, 0.0012), but mostly through realised coverage at one calibration draw: at matched coverage all pivots of a configuration lay within 0.42 pp |
| B3 | XCE-T and a gated variant; 45 fields + mixed fleet; 25 | C3: mixed fleet, ≥ 10% better than every comparator, both classes; C4: gated variant never worse than the best comparator | **Partly met.** C3: 5 of 8 comparisons met; C4: 1 of 6 cells |

*Table 5. The pre-registered zero-data sequence (all with the model without field-edge terms). Excess overlap is the deployed overlap minus the per-field oracle overlap.*

B1 failed because the probability-integral-transform pivot amplifies tail errors and a numerical error in an early version of the model produced one non-finite prediction (Appendix B.4). B2 met both claims, but a post hoc matched-coverage analysis showed that within one machine configuration the pivots differ by tenths of a percentage point; B2 does not show that the model pivot is more efficient than raw pooling within a configuration. In B3 one cell failed its registered validity criterion: XCE-T in R1 under the marginal rule realised 0.877 against a criterion of 0.89 over 400 calibration subsets drawn from one fixed set of logged runs. B4 below checks whether such a value is a draw of the calibration data or a failure of the guarantee.

**B4, does the guarantee hold? (pre-registered).** B4 tests Proposition 3 over both sources of randomness. Each of the 45 fields per configuration (135 in the mixed fleet) received a bank of 200 independent logged runs at its reference plan; each of 4000 replicates per scenario, pivot and rule drew 25 calibration fields at random, one logged run per calibration field from its bank, and deployed on every other field. All 26 cells met their criteria (marginal mean coverage ≥ 0.895; PAC fraction of replicates with coverage ≥ 0.9 at least 0.88; Table S16). The exact targets are 0.923 for the marginal mean ($k_\star/(n+1)$), 0.729 for the marginal fraction and 0.928 for the PAC fraction (Beta distributions of Section 5.3); the observed 0.919–0.929, 0.689–0.767 and 0.911–0.949 agree with them. The sub-0.9 realised coverages of B2 (0.844) and B3 (0.877) are therefore draws of the calibration data, not failures of the guarantee. B4 confirms the guarantee and its implementation; it cannot detect a failure of exchangeability, because it splits a fixed set of fields at random. One implementation detail differs from the method: when a threshold was infinite, B4 deployed the planner cap instead of refusing; this occurred only for Mondrian pivots in B5 and is reported there.

**B5, configuration-aware baselines and per-configuration coverage (revision, pre-registered).** The mixed fleet pools three machine configurations. The registered B3 and B4 compared the model pivot mainly with configuration-blind pooling, which a contractor would not use. B5 adds per-configuration (Mondrian) pooling, an empirical per-configuration scale, a configuration-aware learned scale (CQR, trained on separate fields) and the Monte Carlo twin, and reports coverage per configuration (Table 6, Fig. 5).

<!-- source: results/revision/rv2_resampling.txt -->
| Pivot | $n=25$: coverage R1 / R2 / R3 (marginal) | $n=25$ excess, marginal / PAC | $n=60$ excess, marginal / PAC |
|---|---|---|---|
| Raw pooling | 0.999 / 0.998 / **0.779** | +29.19 / +63.97 | +17.12 / +37.98 |
| Spec. × scale law | 0.944 / **0.840** / 0.993 | +12.95 / +23.09 | +9.93 / +14.98 |
| Mondrian (per configuration) | 0.958 / 0.960 / 0.957 | refuses on 56% / 100% of fields | +4.35 / refuses on 74% |
| Per-configuration scale | 0.939 / 0.958 / 0.842 | +4.57 / +19.94 | +1.29 / +6.42 |
| CQR (configuration-aware) | 0.961 / 0.942 / 0.866 | +4.09 / +18.86 | +1.20 / +6.19 |
| **XCE-T** (analytic model) | 0.931 / 0.936 / 0.904 | **+2.89** / +14.56 | **+0.57** / +4.37 |
| **XCE-MC** (Monte Carlo twin) | 0.924 / 0.929 / 0.913 | **+2.68** / **+13.76** | **+0.55** / **+4.19** |

*Table 6. Experiment B5 (revision, pre-registered): mixed fleet of 135 fields, 4000 replicates. Overall validity held for every non-refusing pivot (marginal mean coverage 0.896–0.925; PAC fraction 0.892–0.955). Per-configuration coverage is not guaranteed by the theorem; values below 0.88 are in bold. Mondrian excess is over deployed fields; refused fields need another rule.*

All four registered predictions were met. (i) Every non-refusing pivot was valid overall. (ii) Raw pooling covered the DGPS configuration at only 0.779 (marginal; 0.582 of replicates under PAC) while over-covering the RTK fields at 0.999: the overall guarantee averages over configurations and can hide a configuration that is badly served. The model pivots covered every configuration at 0.904–0.936 ($n=25$) and 0.885–0.915 ($n=60$). (iii) Mondrian pooling, which is valid per configuration, needs at least 9 (marginal) or 22 (PAC) calibration fields per configuration; with 25 calibration fields shared by three configurations it refused on 56% of new fields under the marginal rule and on all under PAC. (iv) With 60 calibration fields, the model pivots cost 0.57 and 0.55 pp of excess overlap (marginal) against 4.35 (Mondrian, deployed fields only), 1.29 (per-configuration scale) and 1.20 pp (CQR), and 4.2–4.4 pp under PAC against 6.2–6.4 pp (per-configuration scale, CQR) and 12.2 pp (Mondrian, deployed fields only). The analytic model and the Monte Carlo twin were equivalent (within 0.8 pp in every cell). The empirical and learned configuration-aware scales also left the DGPS configuration under-covered (0.82–0.87 marginal at $n=25$–60), because a scale learned from one run per field or a median of a few runs does not capture its heavier tail.

![](../../figures/paper/fig_mixed_fleet.png)

**Fig. 5.** Experiment B5: mean excess overlap of the scale pivots on the mixed fleet with 60 calibration fields, marginal (a) and PAC (b) rule (excess over deployed fields; a pale bar marks a pivot that refuses on part of the fields), and mean coverage of the DGPS fields under the marginal rule with 25 calibration fields (c; dashed line 0.9).

**B6, model accuracy against learned predictors (post hoc).** Trained on the one run per field that this setting provides, cross-validated ridge regression and gradient boosting on field features did not reach the model's accuracy within the available pools (standard deviation of log(prediction / $\lambda^\star_f$) at the largest pool: 0.070 and 0.109 vs 0.029 in R1; 0.043 and 0.049 vs 0.029 in R2; 0.148 and 0.190 vs 0.056 in R3; Table S25). A feature correction of the model with a cross-validated penalty matched the model in R2 (0.029) and did not improve on it elsewhere. Trained on oracle targets, which need hundreds of runs per field, ridge regression beat the model under RTK (0.021 in R1 and R2) but not under DGPS (0.079). The Monte Carlo twin with 1000 runs was slightly more accurate than the analytic model (0.025, 0.026, 0.047), as expected for an exact simulation of the same model.
