# Review R14: field robotics deployment

**Manuscript:** Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations
**Reviewer expertise:** autonomous agricultural vehicles in production, lidar/GNSS localisation, teach-and-repeat, operator workflows, logging, field failure modes
**Material read:** `docs/paper/manuscript.md` (full), `docs/paper/supplementary.md` (Appendix C, E and headings), `tools/feedcar/README.md`, `ce_logger.py`, `ce_certify.py`, `ce_core.py` (run segmentation)

---

## 1 Summary

The paper treats the overlap between adjacent passes as a decision variable with a stated reliability. The authors show that "no missed area" is equivalent to an exact scalar run score (the covering radius of the executed passes, including field-edge terms). They calibrate that score with split or PAC conformal prediction on a reference plan that has at least as many passes as the deployed one (CE, CE+). For fields with no history (CE-EVT-R), a five-layer Gaussian extreme-value theory predicts each field's 0.9 score quantile from controller, DEM and GNSS statistics, and that prediction is used as a ratio pivot for cross-field conformal calibration. All quantitative evidence comes from a closed-loop simulator. The simulator is driven by real field polygons (Chinese harvester trajectories), Copernicus DEM and RTKLIB-processed static CORS baselines. Results:
- CE+ uses 4–55% less overlap than two conformal planners at equal guarantee class on 90 fresh simulated fields.
- A pre-registered resampling check confirms the coverage guarantee in 26/26 cells.
- The theory pivot cuts excess overlap from about 30 pp to 3 pp on a simulated mixed fleet.

Real-vehicle validation (Section 6.7) is a TODO. The "passive logger and offline certification tools" mentioned there are, in the repository, a ROS Kinetic tool for an indoor/barn feed-delivery robot (`tools/feedcar/`) that follows a taught route. They do not target a tractor doing parallel-pass coverage.

The statistical work is careful and unusually honest about failed and post hoc claims. From a deployment standpoint, however, the paper has not yet established three things: that a practitioner can obtain the score it calibrates, that the exchangeability assumption survives real operations, or that the certificate maps onto a decision an operator or a guidance console can act on.

## 2 Recommendation

**Major revision.** For Computers and Electronics in Agriculture, I would not accept the paper without at least a modest real-vehicle data set. That data set must contain independent ground truth and test the main operational assumptions listed below. The theory and simulation contribution is substantial; the deployment claims in the Abstract, Highlights and Section 7.4 currently go beyond the evidence.

| Criterion | Score (1–10) |
|---|---|
| Novelty | 7 |
| Soundness (statistics 8; field-realism of the evaluation 4) | 6 |
| Practical relevance (as currently evidenced) | 4 |
| Clarity | 6 |

## 3 Strengths

1. **The right quantity.** The paper targets pass-to-pass (relative) error and the field edge rather than absolute accuracy. The point that common-mode DGPS error cancels in interior gaps but not at boundary passes (Theorem 3b, Section 6.2) is physically correct and operationally useful.
2. **The guarantee is decoupled from the theory.** It does not depend on the theory being accurate (Proposition 5). A practitioner can therefore use a crude pivot and still keep validity. This is the right architecture for deployment.
3. **Realistic GNSS tails.** The GNSS error model uses real RTK wrong-fixes and float drift (Table 1) rather than Gaussian noise. The authors correctly note that it is a lower bound for moving vehicles.
4. **Transparent reporting.** The status labels (pre-registered, exploratory, post hoc) and the reporting of failed claims (E-low v1, C3, C4) are exemplary.
5. **A refusal path is defined.** The deployment rules include refusal (`+inf` rule; refuse when `lam_hat > lam0`). A system that can say "not enough evidence" is what a field operator needs.
6. **Practical guidance.** Section 7.4 is concrete and mostly sensible. In particular: calibrate on a plan with at least as many passes as you deploy, record the exact score, and do not trust "2 × spec".

## 4 Major issues

### M1. The calibrated score cannot be computed from the logs a practitioner has (Sections 3, 4.2, 6.7, 7.4)

**Why it matters.** $S$ is defined on the *true* executed footprint. That footprint includes GNSS error, the dominant component under DGPS and the heavy tail under RTK (Table 1). A farm's records come from the guidance receiver itself: ISOBUS/TC logs, the as-applied map, or the console's coverage map. The guidance receiver cannot see its own error. A score computed from those logs measures only control error relative to the reported position. In the simulator's terms, that is $S$ with the GNSS term removed, which is exactly the part that sets the margin in R3. The feedcar tool has the same issue: `e` is the map→base_link pose relative to the taught route. The README itself warns that "real physical deviation must add localisation error", yet `ce_certify.py` certifies the pose deviation as if it were the physical one. CE-EVT-R's "one historical run per field" therefore presupposes ground truth that farms do not have.

**Fix.**
- State explicitly which inputs each variant needs and where they come from:
  - an executed implement-reference trajectory with independent cm-level truth (PPK from a second receiver against a different base, a total station, or post-hoc imagery of the wheel/boom tracks);
  - the AB lines or plan;
  - the field boundary used for $W$;
  - implement geometry and offsets;
  - fix status and timestamps;
  - for CE+, the probe-line XTE.
- Quantify how much of $S$ is invisible to the self-logged receiver in each regime. The simulator can do this directly: compute $S$ with and without the GNSS term.
- Either propose a certification that is valid with self-logged data (for example, a separately characterised and calibrated GNSS-error component), or restrict the claims to settings where truth is available.

### M2. Machine position is not implement footprint (Sections 3, 6.1; Supplementary C.1)

**Why it matters.** The simulator moves the antenna/vehicle reference and places a rigid footprint of width $w$ about it, with only a static per-run mounting bias (1.5 cm). In practice, misses come from several sources the model leaves out:
- passive drift of trailed implements on side slopes, and hitch side-play;
- boom yaw and oscillation on 24–36 m sprayers;
- spreader pattern asymmetry (wind, product);
- section-control latency;
- seeder drift between tractor and drill.

Under RTK these effects are often larger than the tractor's own XTE. R2 (1.5 m implement, hilly-wet terrain) is precisely the case where implement drift dominates.

**Fix.**
- Add an implement model (a trailed-implement kinematic model with slope-induced drift, or at minimum a stochastic implement-to-tractor lateral offset with its own dynamics), and repeat at least the CE+ and theory-accuracy results.
- Make the evaluation point explicit: the implement footprint edge, not the antenna.
- In the field study, put the truth receiver on the implement.

### M3. Exchangeability across operations versus real operation structure: interruptions, multi-day jobs, refills (Sections 3, 4.2, 5.4)

**Why it matters.** The simulator runs every field as one continuous job at constant 2 m/s, so adjacent passes are "one pass duration apart". Real jobs are interrupted:
- tank or hopper refills, typically every few hectares for sprayers;
- operator breaks, weather, and breakdowns;
- jobs finished the next day.

After a break, pass $k$ and pass $k+1$ are separated by minutes to 24 h, and the relevant error becomes long-term RTK repeatability. That includes base-station re-set, a datum or network-RTK correction change, and re-initialisation. This is much larger and less common-mode than the 1-pass-duration error modelled. Interior gaps then behave like edge gaps.

Exchangeability across operations is also broken by events that are routine in practice: steering recalibration, firmware updates, tyre pressure and ballast changes, a different operator's tuning, and a correction-service change. The paper lists these only generically ("a new configuration").

**Fix.**
- Model resumption gaps: insert breaks at realistic intervals (refill frequency × tank size), with a long-lag GNSS error drawn from different days or sessions of the same station pair.
- Report how the certified margin and validity change.
- Define the exchangeable unit operationally, as a checklist of what invalidates a calibration set: hardware, firmware, receiver, base or network, implement, controller gains, operator, and season.
- Report coverage when calibration and test come from different seasons. The CORS data already span four seasons, so this costs only analysis.

### M4. Unmodelled field failure modes are silently excluded or censored (Sections 3, 6.1; tools/feedcar)

**Why it matters.** The paper's failure model is Gaussian closed-loop noise plus a real GNSS error series. What actually breaks in the field is different:
- **Localisation dropouts.** RTK loss under tree lines, near buildings, or from radio-link loss with a local base. Fallback to float/DGPS/dead reckoning, and the guidance console's own behaviour on fix loss (pause, degrade, or continue).
- **Obstacles and avoidance.** Poles, wet patches, and stones that force a pass to deviate or be skipped and redone.
- **Stops and restarts mid-pass**, with line re-acquisition transients.
- **Actuator faults.** Steering-motor slip on the wheel, hydraulic valve dead-band drift, wheel-angle sensor offset.
- **Manual takeover.**
- **Speed changes.** Real operating speeds are 1.5–5 m/s for spraying and slower on headlands. Higher speed lengthens the line-acquisition transient after a turn, which may extend beyond the 2w inset used to define $W$.

None of these is in the simulator. The feedcar tooling handles them in ways that bias the certificate optimistically:
- (a) `README.md` §3 says obstacle stops and manual takeovers "do not matter, record as usual". A takeover replaces the controller with a human, so such runs are neither from the deployed system's distribution nor excluded.
- (b) Runs covering less than 95% of the route are dropped as `_partial` (`ce_core.py`, `min_cover=0.95`). If interruptions correlate with bad runs, this is survivorship bias. Also, a run missing up to 5% of the route counts as complete, and its maximum is taken over the part that was logged.
- (c) Pose jumps larger than 2 m (`max_jump`) are treated as relocalisation and re-matched rather than counted as excursions. The worst localisation events are censored from $S$, and `n_lost` is only logged as a warning, not attached to the run.

**Fix.**
- In the paper, add an explicit taxonomy of field failure modes, and state for each whether it is (i) inside the score and covered by the guarantee, (ii) excluded by a declared rule, or (iii) out of scope.
- Exclusion rules must be fixed before data collection and applied without looking at outcomes. Otherwise the guarantee is void.
- Add at least fix-loss episodes (a fix-status time series is available from RTKLIB) and line re-acquisition after turns to the simulator.
- In the tools, flag every run with `n_lost`, takeover, stop and coverage fraction. Never drop runs silently. Report the certificate both with and without flagged runs.

### M5. How the certificate is used operationally is unspecified, and partly conflicts with practice (Sections 4.2, 7.4)

**Why it matters.**
- **Fixed pass spacing.** In established crops (spraying and fertilising after drilling), pass spacing is fixed by tramlines or controlled-traffic lanes set at seeding. The deployed $\lambda$ cannot change per operation. CE+'s "new $\lambda$ from today's probe line" is therefore meaningful only for primary operations (tillage, drilling, broadcast spreading) or for section-control overlap settings.
- **Guidance-console mapping.** Consoles take an implement width and an overlap or skip value, sometimes with separate left and right offsets. They do not take a covering-radius-based plan. The paper should state how $\lambda$ maps to those inputs. It should also state the effect of rounding to whatever resolution the console accepts (often 1 cm, not 2 mm).
- **Refusal workflow.** What does the operator do on refusal: fall back to a fixed overlap, collect more runs, or not work the field?
- **Who runs it, and when.** Does the probe-line reading happen in the cab before each job, and on which hardware? Section 4.4 gives up to 353 s per field offline; that is fine, but the online step must be specified.
- **Miss definition.** The metric is "any miss on a 1 m grid". A 1 cm × 1 m skip is agronomically irrelevant for spraying (drift and boom overlap) but matters for seeding. A deployable certificate needs a minimum gap width or area, or a missed-area tolerance per operation type.

**Fix.**
- Add a short "operational protocol" subsection, ideally with a flowchart: inputs, decision, console setting, refusal handling, and recalibration triggers.
- Restrict CE+ claims to operations where spacing is free.
- Evaluate a tolerance-based variant $\Pr[M\le m_0]\ge1-\varepsilon$, or a minimum gap width, which is a simple change to the score.

### M6. The real-run requirements are not stated and are probably underestimated (Sections 4.3, 6.7, 7.4)

**Why it matters.** Operation counts per field:
- CE+ needs ≥ 9 (marginal) or ≥ 22 (PAC) recorded operations per field, per configuration.
- A field sees one to five operations of a given type per year, and each implement or receiver is a different configuration. At realistic rates this is 5–20 years of data, and exchangeability would fail long before that (M3).
- The 22-run PAC requirement equals the per-field minimum, so it gives the tightest possible but very noisy bound.

For CE-EVT-R, at least 25–29 calibration fields with ground-truthed runs are needed (M1).

The planned validation (6.7(b): one operation on each of 20–40 fields) cannot check the guarantee with useful power:
- With 30 test fields, the binomial standard error of realised coverage near 0.9 is about 0.055.
- On top of that, the calibration-draw variability of Beta($k$, $n+1-k$) has standard deviation about 0.054 (the paper's own number).
- To distinguish true coverage of 0.9 from 0.8 (one-sided α = 0.05, power 0.8), a normal-approximation sample size gives about 70 independent test operations *in addition to* the calibration set. Detecting a 0.85 shortfall needs roughly 250.
- Zero-miss events at the 0.9 level are 10% events, so roughly 3 misses are expected among 30 test fields. Each must be detected with cm-level truth on the implement edge.

**Fix.**
- Add a power analysis for the field study.
- Specify the study's unit (field-operation), the calibration/test split, the ground-truth method and its own error budget (PPK roughly 1–2 cm; it must be well below the tolerance being certified), and the pre-registered criteria, as was done for the simulations.
- A realistic minimum is about 25 calibration plus 70 or more test field-operations. Alternatively, report the field study as "consistent with" rather than "confirms".
- Also report $\varepsilon=0.2$ and $\varepsilon=0.05$, and how run requirements scale.

### M7. Real-world realism of the simulation inputs (Section 6.1, Tables 1–2)

**Why it matters.**
- **GNSS mismatch.** Field geometries are Chinese harvester tracks, but GNSS errors come from US Midwest CORS baselines. Static geodetic antennas under open sky lack vehicle multipath, canopy and tree-line obstruction, and RTK radio-link outages. The authors acknowledge this as a "lower bound", but every certified margin and every efficiency number inherits it.
- **Interpolation.** 30 s epochs interpolated to 1 Hz smooth exactly the fast jumps (fix/float transitions, wrong-fix onset) that cause single-pass excursions. Adding i2Nav residuals does not restore the correlation between those jumps and fix-state changes.
- **Speed and wheelbase.** One speed (2 m/s) and one wheelbase are used throughout.
- **Implement widths.** Widths of 1.5, 3 and 6 m are narrow for spraying and spreading (18–36 m), where boom-end behaviour and section control matter. A 1.5 m implement is unusual for autosteer coverage.

**Fix.**
- Use native 1 Hz RTK logs from at least one moving vehicle as a stress test. The CitrusFarm logs mentioned in 6.7(a) and Supplementary C.1 are suitable, as are public tractor logs.
- Add a speed sweep and one wide-implement regime.
- Report sensitivity of $\lambda^\star$ and of validity to these choices.

### M8. The repository's deployment tool does not match the paper's problem (Section 6.7; tools/feedcar)

**Why it matters.** Section 6.7 implies that the passive logger and certification tools are ready for the planned tractor study. They are not suited to it:
- `tools/feedcar` targets a ROS Kinetic feed-delivery vehicle repeating one closed taught route (teach-and-repeat). It certifies a tube score, max |e| about one route.
- It computes no pass-to-pass covering radius, no adjacent-pass relation, and no field-edge term.
- It reads the localisation pose (no independent truth; the lidar side-distance check is relative to a leave-one-out median profile, so it detects run-to-run variation but not a common bias).
- Its exchangeable unit is a lap within a few days of collection ("30 laps ≈ 4 h"). That is far narrower than the "operating conditions" population the guarantee is supposed to cover.

The README is also in Chinese only, and it tells operators that stops and takeovers are fine to include (see M4). The tool is a reasonable engineering artefact, but citing it as evidence of deployability misleads.

**Fix.**
- Either remove the reference, or present the feed car explicitly as a separate, simpler teach-and-repeat case study, with real data and the caveats above.
- Provide a tractor-side logger specification: required signals and rates, the ISOBUS/proprietary sources for XTE and fix status, the truth receiver setup, and a file format.

## 5 Minor issues

1. **Abstract and Highlights.** "Fields without history are certified" and "4–55% less overlap" should be qualified by "in simulation" in the Highlights themselves; readers of CEA scan Highlights only.
2. **Section 3.** The main area $W$ = $P$ inset by $2w$ excludes the headland, but the line-acquisition transient after a turn scales with speed and controller bandwidth, not with $w$. For $w=1.5$ m the inset is 3 m, about 1.5 s at 2 m/s. Show that the transient has settled within the inset, or include it in $W$.
3. **Section 4.2.** The probe-line XTE is "a noisy reading of the day's roughness and slip". A headland probe line is driven on compacted headland soil, often on a different slope. State whether it should be driven on an infield line, and how long it must be.
4. **Section 4.2.** A 2 mm rounding grid is finer than any guidance console setting; use the console's resolution.
5. **Section 6.1.** The roll-compensation factor $0.85\pm0.05$ and the 2.6 m antenna height should be justified against terrain-compensation specifications of commercial systems; residual roll error dominates R2.
6. **Table 1.** Give the fix rate and the duration distribution of float episodes. Practitioners judge RTK quality by these, not by RMS.
7. **Section 6.3.** The vendor rule "2 × pass-to-pass spec" is a straw man. Vendors specify pass-to-pass accuracy at about 95% over a 15 min window, and operators commonly set a few cm of overlap based on implement behaviour. Describe the farmer-tuned baseline more fully in the main text; it is the realistic comparator.
8. **Section 6.7.** CitrusFarm (123 rows) is an orchard robot dataset without parallel coverage passes in the sense of Section 3; clarify what would be replayed.
9. **Section 7.4.** Give the guidance as a table indexed by the data the user actually has (no history, one or two runs on many fields, 22 or more runs on one field), with required inputs per row.
10. **`ce_certify.py`.** The 3σ comparison uses $|\text{mean}| + 3\,\text{sd}$ of pooled points across runs, which mixes between-run bias. Report it per run as well, or state this.
11. **`ce_certify.py`.** The left/right one-sided bounds and the two-sided bound are each certified at level ε. If the operator reads all three, a multiplicity note is needed.
12. **README.** Assumes the `route_follow` parameters never change. Record a hash of the controller parameter file in each CSV, so mixing parameter sets is caught automatically rather than relying on the operator changing directories.
13. **Data availability.** The RTKLIB demo5 commit "was not recorded". For a GNSS-error-driven paper this matters; rebuild from a pinned commit and re-verify Table 1.
14. **Supplementary Appendix E.** These author notes (remove before submission) and the "28 vs 26 cells" note must be removed.

## 6 Questions to the authors

1. What fraction of the R1/R2/R3 exact score $S$ (at the 0.9 quantile) would be visible to a practitioner who logs only the guidance receiver's own positions?
2. How do certified margins and validity change if each field's operation is split into two or three sessions separated by hours or days, as with refills and multi-day jobs, using long-lag CORS error?
3. For operations constrained by tramlines or CTF lanes, what decision does CE+ inform? Is it the section-control overlap only?
4. Which ground-truth method will the field study use on the *implement*, what is its error budget relative to the certified margins (about 3–10 cm under RTK), and how will a "miss" be adjudicated?
5. What exclusion rules (fix loss, obstacle avoidance, takeover, re-driven passes) will be applied to field runs? Will they be registered before data collection?
6. How many field-operations do you plan for calibration and for test, and what is the power to detect coverage of 0.8 when 0.9 is claimed?
7. How sensitive is the theory's $\hat q_f$ to an implement-drift term and to speed? Can the L1 model absorb a trailed-implement state without breaking Proposition 4?
8. Under RTK, a single wrong fix of 0.3–0.6 m during one pass produces a miss regardless of margin. Is the certified margin under RTK effectively the probability of no wrong fix in the job? If so, would a fix-integrity monitor (pausing application) be a better lever than overlap?
9. Is the feed-car tool intended as part of this paper's evidence? If so, will real feed-car data be reported, with independent truth rather than the localisation pose?
