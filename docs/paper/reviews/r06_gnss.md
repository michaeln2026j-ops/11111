# Review R06 — GNSS positioning perspective

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)

**Reviewer expertise:** GNSS positioning (RTK fixed/float, DGPS, SPP, CORS networks, RTKLIB, temporal error correlation, multipath, convergence).

**Material examined:** `docs/paper/manuscript.md`, `docs/paper/supplementary.md`, `figures/paper/*.png`, `experiments/data_cors.py`, `experiments/data_rtk.py`, and `experiments/core.py` (`_hf_residual`, `gnss_bank`, `gnss_ne`, `Condition`, `simulate`). I ran a few small read-only checks on the shipped `experiments/data/cors_errors.npz` and `cors_summary.csv`. They are quoted below and marked "[reviewer check]".

---

## 1 Summary

The paper treats coverage planning as a chance constraint on missed area. It reduces the zero-miss event to an exact covering-radius run score and calibrates that score with conformal prediction on a dominating reference plan (CE/CE+). It adds a five-layer extreme-value theory, which serves as a ratio pivot for cross-field calibration when there are no target-field runs (CE-EVT-R). All quantitative evidence comes from a closed-loop simulator. Its GNSS error input is built from 12 NOAA CORS station pairs (5–30 km baselines, 8 days each), processed with RTKLIB demo5 at four receiver grades. The 30 s epochs are linearly interpolated to 1 Hz, and a high-frequency residual taken from one 27-min i2Nav vehicle RTK record is added. The error is projected on the field lateral axis at the true time of each pass. The GNSS-specific claims are:
(i) RTK-fixed errors have a heavy, temporally clustered tail that Gaussian models miss.
(ii) DGPS error is "largely common-mode across adjacent passes", so it cancels in interior gaps but not at field edges, and misses under DGPS concentrate at the field boundary (Theorem 3(b), Sections 5.3 and 6.2, Discussion, Practical guidance).
(iii) The vendor 2× pass-to-pass rule fails under RTK and DGPS.

My review focuses on whether the GNSS error model is realistic enough to support these claims and the regime-level efficiency numbers.

## 2 Recommendation and scores

**Recommendation: Major revision.**

The conformal parts (exact score, dominating reference plan, CE-EVT-R validity) are valid within the simulator, and validity does not depend on the GNSS model. However, every efficiency number, the theory-versus-simulation agreement, and in particular the physical claim about DGPS common-mode error and edge-concentrated misses depend on a GNSS error model with structural problems. These are: static geodetic antennas standing in for a moving vehicle, 30 s data linearly interpolated, an RTK-grade high-frequency residual added to every grade, an RTK "fixed" grade that contains float epochs, and a DGPS grade unlike what is used in agriculture. My own check of the shipped data contradicts the common-mode claim quantitatively (Major issue 3).

| Criterion | Score (1–10) |
|---|---|
| Novelty | 7 |
| Technical soundness (GNSS error model and its use) | 4 |
| Practical relevance | 6 |
| Clarity | 6 |

## 3 Strengths

1. **Real error series instead of white Gaussian noise.** Driving the simulator with real RTKLIB solutions keeps fix/float transitions, wrong fixes and slow multipath. Using the same series, in real time order, for successive passes is the right structural idea: pass-to-pass error is a time-lag difference of one error process. This is better than most CPP work.
2. **Transparent processing.** `data_cors.py` documents the configuration well: kinematic mode with `dynamics=off`, `est-stec` ionosphere for RTK, continuous AR without fix-and-hold, GLONASS AR off, ITRF2020 truth propagated with station velocities, and per-pair problems. The authors also openly flag a real truth problem and drop that pair (KAR4-ILUC).
3. **Honest caveat.** Both the code and the Table 1 caption say that static CORS antennas understate vehicle errors.
4. **Cold-start convergence is removed** (`CONVERGE_S` = 30 min) rather than mixed into the tail, and per-day biases are kept on purpose, with the correct remark that a constant bias cancels in interior gaps.
5. **Physically sensible frame.** The earth-fixed error is projected on the field lateral axis with the sign flip between up and down passes, and it is kept separate from the vehicle-frame mounting bias. Code and description agree (`core.simulate`).

## 4 Major issues

### M1. Static station-pair baselines are not a model of a moving agricultural vehicle, and the bias is not only "a lower bound"
*Location:* Section 6.1 "Data", Table 1 caption, Limitation 1, Abstract ("real ... GNSS error series"); `data_cors.py` (docstring CAVEAT).

*Why it matters.*
- **Missing error sources.** A choke-ring or geodetic antenna on a monument with open sky, processed with `dynamics=off`, has none of the main vehicle error sources:
  - near-field multipath from cab roof, ROPS and implement;
  - multipath that changes with heading and decorrelates within seconds in motion;
  - canopy and tree-line masking (relevant for the hilly paddy fields of R2 and R3);
  - cycle slips and loss of lock in headland turns, with RTK re-convergence after each one;
  - antenna tilt and vibration;
  - correction latency and data-link (radio/NTRIP) outages.

  These also change the **temporal structure**, not only the magnitude. Static-site multipath is slow and sidereal-repeating, so it appears common-mode across passes minutes apart. Vehicle multipath is fast, so it appears as independent per-pass error. Calling the static errors "a lower bound" therefore understates the problem. The **split between common-mode and differential error**, which drives both the interior/edge result and the R1/R2 conclusion that controller and terrain terms dominate under RTK, may be biased in a systematic direction.
- **Geographic mismatch.** The fields are in South China (paddy, hilly) and the North China Plain. The GNSS series are from the US Midwest and Great Plains (about 40–47° N). Low-latitude South China lies under the equatorial ionisation anomaly crest. Ionospheric gradients and scintillation are much stronger there, especially near the 2024–2025 solar maximum, and they directly affect RTK fix rates on 5–30 km baselines and DGPS residuals.
- **Constellation mismatch.** Processing is GPS+GLONASS only (`navsys=5`). Machines in China use BeiDou (and Galileo) as primary constellations, which gives different geometry and fix behaviour.
- **Unrepresentative baselines.** CORS-to-CORS baselines of 5–30 km do not match common farm practice: an own base under about 10 km, or network RTK/VRS.

*Concrete fix.*
1. Replace or augment the bank with **kinematic vehicle data that have an independent reference**. Options:
   - a PPK or navigation-grade GNSS/INS truth on a tractor or car, such as the multi-sequence i2Nav awesome-gins datasets beyond the single 27-min record now used;
   - agricultural robot datasets with RTK+PPK;
   - the authors' planned tractor campaign (Section 6.7).
2. If this cannot be done before resubmission, add a **parametric vehicle-error overlay** with literature-based magnitudes: heading-dependent multipath with a correlation time of a few seconds, slip-induced float episodes with realistic re-convergence (10–60 s at decimetre level), and link-outage episodes. Report sensitivity of λ*, the R1/R2/R3 regrets and the edge share to these terms. The code already has an `rtk_scale` knob; also scale the error variance and the correlation time separately.
3. Either use CORS or CMONOC/BDS stations at low latitude in China, or state explicitly that the GNSS climate does not match the fields, and remove "real GNSS errors" from the Abstract and Highlights without that qualification.

### M2. Linear interpolation of 30 s epochs plus a single RTK-grade residual gives an unrealistic sub-minute spectrum, which is exactly what the run score is sensitive to
*Location:* Section 6.1; `core.gnss_bank` and `core._hf_residual`; Supplementary C, l.158.

*Why it matters.* The run score is a **supremum over 1 m sections** along each pass. Its tail is governed by the sub-minute part of the lateral error, through the Kac–Rice slope variance λ₂ in L2 and the modulus of continuity in Theorem 5. The current pipeline distorts this band in four ways:
1. **Linear interpolation loses variance.** Between independent samples, the interpolated variance at fraction *a* is ((1−a)² + a²)σ², which is 2/3 σ² on average. The pooled DGPS series decorrelate fast: [reviewer check] the normalised structure function 1−ρ(lag) of the warm north error is **0.49 at 30 s, 0.60 at 60 s, 0.66 at 120 s, 0.69 at 240 s**, and for 8 of 12 DGPS pairs the 1/e correlation time is 28–70 s (`cors_summary.csv`, `tau_e_s_warm`). The fast component is therefore under-represented between epochs, and its 30 s samples are **aliased**: CORS RINEX at 30 s is decimated, not averaged.
2. **Within-pass GNSS error has almost no internal structure.** R3 fields have 7–13 passes and 324–1016 m of total pass length (Section 4.4, Supplementary Table S5b), so passes are about 40–100 m long, which is 20–50 s at 2 m/s. Each pass sees 1–3 real CORS samples, and its GNSS error inside the pass is close to a straight line.
3. **The added high-frequency residual is RTK-grade for every grade.** It comes from one 1615 s i2Nav RTK record and has a standard deviation of only **0.8 cm (N) and 1.0 cm (E)** [reviewer check]. It is added unchanged to DGPS and SPP. In the resulting 1 Hz DGPS bank the standard deviation of 1 s increments is **1.2 cm** [reviewer check], while over 30 s about half of a 23 cm standard deviation decorrelates. Real 1 Hz DGPS code solutions have decimetre-level epoch-to-epoch noise unless heavily carrier-smoothed. The DGPS high-frequency content is therefore underestimated by roughly an order of magnitude.
4. **The residual is a single, contaminated realisation.** One 27-min urban/suburban road record is tiled with random shifts, reversals and sign flips, with no taper at tile joins, and shared by all runs and grades. The residual also contains truth and lever-arm errors and GNSS/INS time-synchronisation errors (`data_rtk.py` applies a fixed lever arm), which correlate with vehicle dynamics. Using a 31-sample moving average as the high-pass filter leaves sidelobe leakage around the 30 s cut-off.

Consequences: the simulator and the theory share the same artificially smooth input. The excellent agreement in Fig. 2 and Tables 3–4 therefore shows internal consistency, not realism. Theorem 5's GNSS timing term (modulus of continuity) is also artificially small.

*Concrete fix.*
- Use genuine 1 Hz (or 5–10 Hz) observations. Options:
  - IGS/EUREF high-rate RINEX;
  - Chinese provincial CORS or other 1 Hz networks;
  - NGS 1 s raw files converted with the manufacturer's converter (for example, Trimble `convertToRINEX` for T02);
  - the 1 Hz kinematic data of M1.
- If only 30 s data are available, replace linear interpolation with a **conditional stochastic downscaling** that has the correct per-grade power spectral density (PSD): fit a sum of Gauss–Markov or power-law components to 1 Hz reference data per grade and simulate bridges between 30 s samples. Scale the high-frequency residual per grade, not one RTK record for all.
- Report the per-grade PSD or structure function of the final 1 Hz bank against a real 1 Hz reference.
- Report the sensitivity of λ*_f, the R3 regret and the edge share to the high-frequency level (×1, ×3, ×10).

### M3. The claim that "DGPS error is largely common-mode across adjacent passes" is not supported, and the edge-dominance result does not require it
*Location:* Abstract (last sentence), Section 3 after Lemma 1, Section 5.3 "Physical insight", Section 6.2 (paragraph after Table 4), Section 7.1, Section 7.4 bullet "Under DGPS ...", Conclusion.

*Why it matters.*
1. **Quantitatively it is the other way round in the authors' own data.** Adjacent passes at the same section are separated in time by between the turn time (about 13 s at the turn end, from `t_turn` = π·4.5/2 + 6 s) and 2L/v + 13 s at the far end. That is about 13–113 s for R3 fields and up to about 500 s for long fields. At these lags the pooled DGPS series keep only **about 34–51% of their variance as common-mode** (1−ρ = 0.49–0.66, M2) [reviewer check]. The "largely common-mode" part is concentrated in four pairs whose slow, 20–50 min components the authors themselves attribute to **static-site code multipath** (BAYR-MIBY, MNBV-ECSD, MNEY-MNSV, NEOM-IACB; `data_cors.py` docstring and `tau_e_s_warm` of 1400–3000 s). That is precisely the component a moving vehicle would not have (M1).
2. **Edge dominance follows from the score geometry alone.** The interior gap is Z = ½(e_{k+1} − e_k), with variance ½σ²(1 − ρ(Δt)) ≤ ½σ². The edge term carries the full single-pass error, with variance σ². So even with **fully independent** passes (ρ = 0), the edge term has √2 times the standard deviation of an interior gap. Under a heavy-tailed, decimetre-level DGPS error, which dominates the controller terms, an edge exceedance is therefore more likely per section regardless of common mode. Supplementary Table S5b reports that the edge terms matter most on fields with 7–13 passes. That fits a "share of boundary pseudo-pairs" explanation as well as a common-mode one.
3. The two edge-term versions that failed (Supplementary B, item 2) are explained by "common-mode error rarely produces" both passes moving apart. This is again asserted, not measured.

*Concrete fix.* Run a decomposition experiment on the R3 fields, with otherwise identical runs:
- (a) the current GNSS model;
- (b) the same marginal GNSS error but **independent per pass** (an independent segment and start for each pass);
- (c) a **fully common** constant offset per run;
- (d) the current model with the four slow-multipath pairs excluded.

For each, report λ*_f and the **fraction of misses located at the field edges versus the interior** (directly from the simulator; this statistic is never reported). Also report the empirical structure function D(Δt) = E[(e(t+Δt) − e(t))²]/(2σ²) of the lateral error at the actual adjacent-pass lags, per pair. Until this is done, rephrase the claim as: "under DGPS the single-pass error at the edge is not differenced, so edge terms must be modelled". Delete "because GNSS error is common-mode across adjacent passes" from the Abstract, Section 7.1 and the Conclusion.

### M4. The field-edge result depends on not simulating the headland and on an error-free boundary
*Location:* Section 3 ("main area W ... P inset by twice the implement width"), Theorem 3(b), Section 6.2, Section 7.4; `core.Field` (`self.M = self.P.buffer(-H)  # main area, perimeter headland passes excluded`).

*Why it matters.*
- **The headland ring is not simulated.** In practice, the lateral edges of W are adjacent to the headland ring, which the same machine works before or after the infield passes. A "field-edge miss" at W is in reality an interior gap between the outermost main pass and a headland pass. Under GNSS error these two passes are separated by the **whole operation duration**, so the gap behaves like a large-lag difference. It could be either larger or smaller than the current single-pass edge term, but it is not what is modelled.
- **The boundary carries no error of its own.** It is treated as exact in the error-free frame. Under DGPS, the boundary and A-B line are recorded in an earlier session, possibly with another correction source and datum (for example CGCS2000 versus ITRF/WGS84 realisations, which differ at the decimetre level), and they carry their own absolute error. The day-specific DGPS bias, which the bank keeps on purpose, then enters the edge term in full.

The recommendation "under DGPS, pay particular attention to boundary passes, which set the certified margin" is therefore not supported for real operations.

*Concrete fix.* Simulate the headland ring passes, with their real time order, and evaluate coverage on P, or at least on W plus the headland–infield interface. Add a boundary-record error, drawn from a different pair-day or session than the operation. Report how the edge share and λ* change.

### M5. RTK grade definitions are not those an autosteer user experiences
*Location:* Table 1, Table 2 (R1 and R2 "RTK fixed"), Section 2 ("heavy ... tail of RTK errors (wrong fixes, float drift; Table 1)"); `data_cors.py` `GRADE_OPTS`; `core.gnss_bank`.

*Why it matters.*
1. **The "RTK fixed" grade includes every float epoch** (Q = 2). [reviewer check] The warm-period fix rate has a median of 98% but goes down to **11%** on the worst pair-day (LINH-SC00, 706 m height difference; NLIB-IAMN, 28.8 km). Some runs in R1 and R2 are therefore driven on long float or nearly float periods. A commercial RTK autosteer would instead warn, degrade or stop on loss of fix. The tail attributed to "RTK" mixes true wrong fixes with float drift that a real system would flag.
2. **The "RTK float" grade is essentially indistinguishable from fixed.** Table 1 gives RMS 2.9 vs 2.7 cm, 95% 4.7 vs 4.2 cm, and **identical** 99.9% (24 cm) and maximum (1.39 m) values; the warm standard deviation is 1.5 vs 1.2 cm [reviewer check]. This is an artefact of a static antenna with ambiguities carried for hours in a continuous filter. On a moving vehicle, float solutions after cycle slips are typically at the decimetre level. Float is not used in any regime, but Table 1 presents it as a receiver grade and so implicitly validates it.
3. **Missing failure modes.** Correction age and outages are not modelled: post-processing uses complete base data, and `maxage = 30 s` never binds. RTK re-convergence after loss of lock in headland turns is also missing (only the daily cold start is removed). These are the dominant practical RTK failure modes in field operations.
4. **The pass-to-pass specification is not comparable as used.** The vendor figure (2.5 cm) is a 15-min, 95% (2σ) statistic. Section 6.3 compares it with run-level suprema over whole operations, and "twice the nominal pass-to-pass accuracy" is not defined against that standard.

*Concrete fix.*
- Define R1 and R2 as fixed-only, with an explicit loss-of-fix behaviour such as pausing or flagging, as commercial systems do. Add a separate regime with realistic float episodes, each with an onset, a decimetre-level magnitude and a re-convergence time.
- Report fix-rate-stratified results.
- Either drop the float and SPP rows from Table 1, or label them "static CORS, not used".
- State the definition of the pass-to-pass specification. ISO 12188-2 is the standard reference for pass-to-pass testing of guidance systems and should be cited. Compute the matching 15-min pass-to-pass statistic from the bank so readers can compare it with vendor values.

### M6. The DGPS grade and its diversity do not represent agricultural sub-metre GNSS, and R3 hinges on a few pairs and events
*Location:* Table 1, Table 2 (R3), Section 6.6 (R3 PAC information-limit results), Section 6.5.

*Why it matters.*
- **Not the DGPS that farms use.** Agricultural "DGPS" is mostly SBAS (WAAS/EGNOS/BDSBAS/MSAS) or L-band PPP services with carrier-smoothed receivers and published 15-min pass-to-pass specifications. Code-differential RTKLIB from a 5–30 km CORS (`posmode = dgps`, raw code) has a different noise level and temporal structure. That structure also depends strongly on the CORS receivers' internal code smoothing: BAYR-MIBY has σ_h ≈ 6 cm and slow correlation, while other pairs have 25–35 cm with correlation under a minute. R3 is therefore a mixture of very different error processes, chosen by which CORS receivers happen to be installed.
- **The tail rests on few independent units.** The bank has only 12 independent sites (96 pair-days). The R3 PAC margins sit at the sample maximum (Section 6.6), so they are driven by a handful of rare events. These events are **shared between calibration and test runs** because both draw from the same bank. This is fine for checking conformal validity inside the simulator. It says nothing about robustness to a GNSS distribution shift (another site, correction service or season), which is the realistic threat to a certificate.

*Concrete fix.*
1. Add a DGPS-like grade from SBAS or PPP series, or at least a carrier-smoothed code solution.
2. Report R3 results stratified by station pair.
3. Run a **leave-one-pair-out (or leave-site-out) validity check**: calibrate on runs that use 11 pairs and test on the twelfth. This tests coverage under GNSS shift and shows how fragile the certificate is.
4. Report how many distinct pair-days contribute to runs in the top 10% of scores.

### M7. The theory–simulation agreement is circular with respect to GNSS
*Location:* Sections 5.3 (L1 b_t(C)), 6.2, Fig. 2, Tables 3–4; Theorem 5 GNSS term.

*Why it matters.* L1 treats the GNSS trajectory as a deterministic input inside C, sampled from the **same** bank that drives the simulator. The agreement shown (log-error SD 0.029 for RTK) therefore validates the linear-Gaussian closed loop given a GNSS input. It does not validate the GNSS model, and it will not carry over to real receivers when the bank is wrong (M1, M2). Theorem 5's GNSS timing term is "bounded by the modulus of continuity of the error series", and this modulus is artificially small for an interpolated series (1 s increments with σ ≈ 1.2 cm under DGPS). The numerical value of $\bar\Delta$ and of κ used in practice is never reported.

*Concrete fix.* Report the GNSS part of $\bar\Delta$ and the resulting κ for each regime. Repeat the theory-versus-simulation check with a GNSS bank whose sub-minute content is realistic (M2). State in Section 6.2 that the check is conditional on the GNSS input model.

## 5 Minor issues

1. **Antenna calibration file.** `data_cors.py` uses `igs14.atx` with IGS20/ITRF2020 coordinates; `igs20.atx` is the consistent choice. The effect is millimetres, but it should be fixed or justified.
2. **Reproducibility.** The demo5 commit is "not recorded" (Reference list, Everett). Record it, and include the full RTKLIB configuration in the Supplement: elevation mask 15°, `arthres = 3`, `slipthres = 0.05`, `ionoopt`/`tropopt`, `dynamics = off`, continuous AR.
3. **Table 1 caption.** It does not say what the statistics are computed on: 30 s or the 1 Hz bank, warm or whole day, with or without the i2Nav residual, horizontal or lateral. The 1.39 m maximum appears identically in two grades; identify the event.
4. **Mirroring and time reversal.** `gnss_ne` mirrors the series at the segment end, and half of the runs (u ∈ [L, 2L)) read it backwards. Time reversal is not statistically neutral for GNSS (convergence, wrong-fix onset and slow recovery are asymmetric), and around a mirror point adjacent passes see artificially identical errors. Quantify how often a run crosses a mirror point, or remove the reflection.
5. **Speed.** It is fixed at 2 m/s, so the time lag between adjacent passes, and hence the GNSS common-mode share, scales with 1/v. Sprayers work at 4–8 m/s. Add a speed sensitivity.
6. **Heading measurement noise** is fixed at 0.15° for all grades (`psim`). With DGPS-only guidance, heading derived from GNSS or a low-cost IMU is much noisier. Make it grade-dependent or justify it.
7. **Along-track error** is ignored. Only the lateral projection is used. That is reasonable for straight passes, but it matters at the turn ends and for section control. State this explicitly.
8. **Vertical error** and its coupling with antenna height on slopes are not modelled; roll comes only from the 30 m DEM, which cannot represent micro-relief in paddy fields. Mention this in the Limitations.
9. **Section 6.1 wording.** "Each simulated run draws a station-pair-day and start time" should add that the draw is length-weighted over contiguous segments of at least 2 h, after 30 min convergence removal and splitting at gaps over 300 s.
10. **Abstract and Highlights.** "Real ... GNSS error series" should read "static CORS GNSS error series", given M1.
11. **Section 1, paragraph 2.** "The vendor rule ... under RTK left a gap on essentially every run." Clarify that the run score is an operation-level supremum, which a 15-min pass-to-pass specification is not designed to bound.
12. **The i2Nav residual** is winsorised at the 99.5th percentile to remove "its single 19 cm jump". Such jumps (wrong fixes, cycle slips) are genuine vehicle phenomena. Removing them while keeping the static-site tail is inconsistent; discuss why.
13. **Missing references.** ISO 12188-1/-2 (positioning and guidance test procedures for agricultural vehicles); literature on pass-to-pass error of agricultural GNSS receivers and on SBAS/PPP in agriculture; RTK performance at low latitudes during solar maximum.
14. **Section 7.3, limitation 1.** It should also state the 30 s→1 Hz interpolation and the RTK-grade high-frequency residual as GNSS-model limitations (M2).

## 6 Questions to the authors

1. In the simulator, what fraction of R3 (and R1/R2) miss events lie at the W edges versus interior gaps, overall and per station pair?
2. What is the distribution of the adjacent-pass time lag at the same section for the R1, R2 and R3 fields, and what is the corresponding lateral-error correlation ρ(Δt) in the bank?
3. How do λ*_f and the edge share change if GNSS errors are made independent across passes, or if the four slow-multipath DGPS pairs are excluded (M3)?
4. Why are the RTK-float and RTK-fixed tails identical (99.9% and maximum)? Is the 1.39 m event the same epoch in both?
5. How does the autosteer model behave on float or wrong-fix epochs? Does the controller simply follow the corrupted position, and is that realistic for the vendor systems used as baselines?
6. With the high-frequency residual scaled to realistic 1 Hz DGPS levels (M2), do the R3 theory-versus-simulation agreement (Table 4) and the R3 v8 efficiency results still hold?
7. Would a leave-one-pair-out evaluation keep the CE+ PAC meet rate in R3 (M6)?
8. Did you look for 1 Hz RINEX from other networks (IGS high-rate, Chinese CORS with BDS), which would avoid the interpolation and also match the field locations?
9. How would the headland ring and a boundary recorded in another session change the conclusion that "boundary passes set the certified margin" (M4)?
