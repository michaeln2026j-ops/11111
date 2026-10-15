# Response to the 20 internal reviews

All 20 reviews recommended major revision. This document lists, for every recurring issue and every reviewer, what was changed and where. New experiments were pre-registered in `docs/prereg_revision.md` (committed before any of them was run); their outcomes are reported whether or not the registered predictions were met. Section numbers refer to the revised manuscript (`docs/paper/manuscript.md`); the previous version is `docs/paper/archive/manuscript_v1.md`.

**Not addressed in this revision: real-vehicle validation.** Every reviewer asked for field data with independent ground truth. This is the one item left open by decision of the authors; the revision states "simulation study" in the abstract and graphical abstract, removes the placeholder section, and lists the need for independent ground truth among the limitations (Section 7.4).

## A. Issues raised by several reviewers

| # | Issue (reviewers) | Change |
|---|---|---|
| A1 | The model is validated against the simulator it is built from (r04, r05, r09, r11, r12, r15, r19) | Stated in Sections 5.4 and 6.2. New pre-registered Experiment C1 (Section 6.5, Table 7): six "truth" variants the model is not told about. Result: the model pivot keeps its advantage under a trailed implement, degraded GNSS and levelled terrain, loses it under heavy-tailed slip, unstable steering and the combination; reported as such in abstract, discussion and conclusion. |
| A2 | Monte Carlo of the same simulator would do as well as the analytic model (r05, r11) | Added the Monte Carlo twin as a pivot everywhere (XCE-MC). It is as accurate and as efficient as the analytic model (Sections 4.3, 6.2, 6.4); the paper now presents the pivot as "a model, analytic or Monte Carlo". |
| A3 | Zero-miss objective ignores the size and cost of a miss (r01, r02, r07, r12, r19, r20) | Missed area reported for every system (Table 4). New cost analysis (Section 6.6, Table 8, Fig. 5): break-even cost ratio against the vendor rule 31–117; the cost-optimal margin under RTK accepts frequent sliver misses. Gap-tolerance certificate added (Section 4.4) with overlap savings. Abstract, highlights, discussion and guidance now say when a zero-miss margin is not worth it. |
| A4 | Comparators over-cover; comparison not at equal coverage (r10, r16) | Section 6.3 explains that all methods deploy the same plan family, so at equal realised coverage they coincide; the gain is calibration tightness, and most of it comes from the score and the reference plan (CE-q vs CPrP numbers). |
| A5 | Farmer-tuned and vendor rules missing from the confirmatory table (r01, r02, r19, r20) | Added to Table 4 with missed area; discussed in Section 6.3 and the cost analysis. |
| A6 | Mixed-fleet headline compared with configuration-blind pooling (r01, r03, r11, r12, r19) | New pre-registered Experiment B5 (Table 6, Fig. 4): Mondrian (per-configuration) pooling, per-configuration empirical scale, CQR, Monte Carlo twin, and coverage per configuration. All four predictions met; the headline in abstract and graphical abstract now uses these baselines (0.6 vs 1.2–4.4 pp). |
| A7 | Per-configuration coverage hidden by the averaged guarantee (r03, r04) | Reported for every pivot (Table 6, Table 7); raw pooling covers DGPS at 0.78. |
| A8 | "Distribution-free" overclaimed for plans other than the reference plan; κ never reported (r03, r04, r10, r15, r19) | Table 2 states the guarantee of every variant; only CE is assumption-free; Theorem 2 restated under an explicit superposition hypothesis with the correct marginal bound $\sup\kappa\cdot\varepsilon$ (Section 5.2, Appendix A.15). |
| A9 | CE+ deployed margins above the reference margin; `dominated` flag unused (r03, r10, r15) | Reported (Section 6.3: 9 and 19 of 30 R3 fields); CE+ now has a transfer check with fallback to CE (Section 4.2). C1 shows that the only validity shortfall arose exactly in this situation. |
| A10 | "DGPS misses concentrate at field edges" may be an artefact of the hard-edge evaluation; headland not simulated (r01, r02, r04, r05, r06) | New pre-registered Experiment C2 (headland laps). Edges bind in only 1% (RTK) and 10% (DGPS) of runs even with a hard edge, and 0.1–1.9% with laps; the claim is removed and replaced by these numbers (Sections 5.4, 6.5). The "common-mode" explanation is corrected with measured GNSS correlations. |
| A11 | Few runs per field never tested (r01, r03, r14, r20) | New pre-registered Experiment A2 ($n=9$–100): valid at every $n$, with the overlap price reported. |
| A12 | Calibration needs ground truth that machine logs cannot provide (r01, r12, r14, r19, r20) | Stated in Limitations 2 and in the practical guidance. |
| A13 | Learned baselines weak and untuned (r11) | Cross-validated ridge, gradient boosting and a penalised hybrid added (Table S25); the accuracy ratio is now 1.5–2.6× instead of 1.7–3.7×. |
| A14 | Readability for CEA readers; internal names; notation clashes; length (r12, r17) | Theory moved to Appendix A with a verbal summary (Section 5.4); nomenclature table; method table (Table 2); experiments renamed A/B/C with a mapping to repository names; comparator acronyms CPrP and UBCP (CPP now only means coverage path planning); notation unified ($\lambda_\mathrm{ref}$, $\nu_0$, $k_\star$, $R(a)$, $Y(x)$); main text about 8,600 words. |
| A15 | Draft leftovers: TODO, empty DOI, Appendix E, file paths in captions (r01, r12, r17, r19) | Removed; data availability rewritten; captions without paths (sources remain as HTML comments). |
| A16 | Reproducibility: ignored cache files, no README, overwritten registered outputs, Table 1 not reproducible (r18) | All cached inputs committed; README with a paper-item → script map; pinned versions (`requirements-lock.txt`); Table 1 regenerated by `scripts/table_gnss.py` (values corrected); the extended-curve re-readings are kept separate from the registered files and the difference is documented. |
| A17 | Simulator realism: implement, speed, latency, GNSS on static antennas, paddy slopes from 30 m DEM (r01, r05, r06, r09, r13) | Tested as truth variants T2–T5 in C1 and as headland laps in C2; remaining limits stated in Section 7.4 and Table 1/3 captions. |

## B. Theory (r04, r15)

| Item | Change |
|---|---|
| Theorem 1 relied on undefined "shift-equivariant transfer" | Validity defined through a virtual erosion of the executed reference plan; Theorem 1 then holds with no assumption (Appendix A.3). |
| Theorem 4 error bound vacuous at the operating point | Full $\eta$ reported (≈ 0.10, of the order of $\varepsilon$); accuracy of the product form stated as empirical (A.13, Section 5.4). |
| Theorem 5 "exact" but hypotheses violated by the refined model | Restated under a superposition hypothesis on (pair, section) pairing, Gaussianity not needed; exact for the linear model, approximate for the simulator (A.15, Section 5.2). |
| Random κ in the deployment bound | $\sup_{t\le\lambda_\mathrm{ref}}\kappa(t)\,\varepsilon$ (A.7, A.15). |
| Theorem 6 overclaimed; "15%" | Relabelled a heuristic remark; 11% (A.16). |
| Lemma 4 extremal-index reasoning | Corrected ($\theta<1$ even for constant $\Lambda$; Jensen gives an upper bound) (A.14). |
| Proposition 4 independence across passes | Assumption A3 (state reset or part of $C$) added; plan-independence limited to the time-invariant model; edge variance $\nu_0$ (A.10). |
| Theorem 3(b) "iff" | Inclusion (conservative bound) (A.12). |
| Proposition 6 cited but not stated | Relabelled a heuristic remark (A.18, B.4). |
| Proposition 8 called an information limit | Renamed "margin inflation under the ideal scale" (Proposition 4), stated as an identity for the ideal pivot, not a lower bound (Section 5.5, A.20). |
| CE semantics | $P(\text{deploy and miss})\le\varepsilon$ for the marginal rule; conditional statement only under PAC (A.4). |
| Proposition 1 heuristic | Counterexample given (A.6). |
| Proposition 2 constants | $a/|J(\pi_0)|$, $w-2\lambda_\mathrm{ref}$, range for the measured $\theta$ (A.8). |
| Cap in the resampling check not covered by Proposition 5 | Stated; refusal rates reported in B5 (A.17, Table 6). |

## C. Reviewer by reviewer (major points not covered above)

- **r01 guidance engineer.** Practice rules framed as the authors' own rules of thumb (Table 4 caption). Headland-turn diameter vs R2 headland width: noted in Limitations (simulated kinematics).
- **r02 coverage planning.** Headland and field-edge issues: C2. Fields2Cover heading gains: unchanged; the method is planner-agnostic (Table S23). Hameed baseline built from secondary descriptions: now disclosed (Supplementary C.3).
- **r03 conformal.** 26/26 check cannot detect exchangeability failures: stated (Section 6.4, B4). Theorem 1 definitions: A.3. +∞ rule: unchanged, with refusals reported.
- **r04 extreme value.** See B; Chen–Stein bound not attempted, product-form accuracy reported as empirical.
- **r05 control.** "Under-damped" corrected to integral action (A.13); integrator clamp and saturation limits stated (Appendix B.1); theory restricted to the modelled controller (Section 5.4).
- **r06 GNSS.** Table 1 recomputed; RTK grade described as continuous ambiguity resolution with 16% float epochs; common-mode claim replaced by measured correlations; degraded-GNSS variant T4; US stations vs Chinese fields stated (Table 1 caption).
- **r07 agronomy.** Cost analysis and tolerance (A3); suitability depends on the cost ratio $r$ (Section 6.6, 7.5).
- **r08 statistics.** All registered outcomes reported, including the B3 R1 marginal failure (Section 6.4) and the C1 predictions (Table S27); field-usage matrix (Supplementary C.6); post hoc labels kept (Table S20). Power analyses were not added retrospectively.
- **r09 simulation.** C1 and C2; circularity stated.
- **r10 safe planning.** UBCP pooling and its PAC construction disclosed; scenario and DRO baselines at a different confidence level disclosed (Supplementary C.3).
- **r11 ML baselines.** A13 and B5 (CQR in the resampling check; Mondrian).
- **r12 associate editor.** A14, A15; Section 6.7 removed; "simulation study" stated.
- **r13 terramechanics.** Wet patches (T1), trailed implement (T2), levelled terrain (T5); spatial soil fields not modelled (Limitations).
- **r14 field robotics.** Ground truth (Limitations 2); operational use via the transfer check and practical guidance; the feed-vehicle tools are no longer cited as evidence of deployability.
- **r16 benchmark fairness.** Regret range corrected to 27–95%; follow-previous-pass failure reported (Section 6.3); oracle described as a reference point that a method can fall below; runtime claim about pass length removed.
- **r17 clarity.** A14; abstract and highlights rewritten without layer names.
- **r18 reproducibility.** A16; licence of the code remains for the authors to choose.
- **r19 devil's advocate.** A3, A5, A6, A8; the abstract now reports where the method does not help.
- **r20 economics.** Cost analysis with an illustrative, not estimated, cost ratio; calibration cost (ground-truth runs) stated.
