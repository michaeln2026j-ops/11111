# Review R05: control theory for vehicle path tracking

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (submitted to *Computers and Electronics in Agriculture*)

**Reviewer expertise:** path-tracking control (LQR with integral action, Lyapunov covariance propagation, quasi-linearisation and describing functions, saturation and anti-windup, sideslip).

**Material examined:** manuscript, Supplementary Material (Appendices A–D), the theory notes `docs/theory_evt.md`, the simulator `experiments/core.py` and the theory predictor `experiments/evt_theory.py`. I ran only small checks: the LQR-I gains, closed-loop poles, complementary sensitivity, and the steady-state Lyapunov variance of the leaky-integrator surrogate. Each took a few seconds. I did not run any simulation campaigns.

---

## 1. Summary of the paper

The paper treats the overlap between adjacent passes of a field operation as a margin to be certified, so that the plan leaves no unworked strip with probability at least 1−ε. It shows that the zero-miss event equals a scalar "covering-radius" run score. Calibrating that score by split-conformal or PAC quantiles on a reference plan with at least as many passes gives distribution-free certificates (CE, CE+). For fields with no operation history, a five-layer theory predicts each field's required margin from the controller, terrain and GNSS statistics. The layers are Lyapunov covariance of the closed loop, Kac–Rice exceedance, a Bonferroni-bounded product over pass pairs, a mixture over operating conditions, and a Gumbel scale law. The prediction is used only as a ratio pivot for cross-field conformal calibration with one run per field (CE-EVT-R), so validity does not depend on the theory. All quantitative evidence comes from a closed-loop simulator, driven by real field boundaries, DEMs and CORS GNSS error series, using a kinematic vehicle with an LQR-I controller. The results include a pre-registered comparison against two conformal planners, a pre-registered sequence of zero-data experiments, and a resampling check of the coverage guarantee.

## 2. Recommendation

**Major revision.**

| Criterion | Score (1–10) |
|---|---|
| (a) Novelty | 7 |
| (b) Technical soundness | 5 |
| (c) Practical relevance | 5 |
| (d) Clarity | 6 |

The conformal part is sound and carefully done: the exact score, the dominating reference plan, and the guarantee that does not depend on the theory. The statistical reporting is unusually honest. My concerns are about the control-theoretic layer (L1) and what the paper claims from it:

- L1 is presented as a "theory derived from the closed-loop vehicle model" that needs "no run data". In the code, however, it runs the simulator itself (noise set to zero) to get the conditional mean trajectory. It is then validated against that same simulator, with the same plant, gains, actuator limits, condition distribution and GNSS bank.
- Several structural statements do not hold for the model that is actually used:
  - plan-independent covariance;
  - Gaussianity given C;
  - the "safe upper bound" of the unclamped model.
- The integrator clamp that the authors had to model is a simulator design choice. Its level is low enough to limit slip compensation on the very slopes the hilly regime is about.

None of this threatens the coverage guarantee, which the authors correctly decouple from the theory. It does threaten the efficiency claims that rest on the theory: the mixed fleet, "1.7–3.7 times more accurate than regressors", and the DGPS field-edge mechanism. It also limits how general the method is beyond the specific simulated LQR-I loop.

## 3. Strengths

- **Correct separation of validity from model accuracy.** The theory enters CE-EVT-R only through a field-measurable scale. Proposition 5 then holds for any pivot, and the resampling check (Table 7, 26/26 cells) tests the guarantee over both sources of randomness. This is the right way to use an imperfect physics model inside a certificate.
- **The exact covering-radius score (Lemma 1) and the dominance argument (Lemma 2, Corollary 1).** These are clean and useful, and the decision-dependence point (Proposition 1) is real and often overlooked.
- **The L1 analysis is competent.** It includes:
  - LQR-I designed on the actuator-lag-augmented model;
  - time-varying quasi-linearisation along the mean trajectory;
  - random-input describing functions with Booton self-consistency;
  - an explicit observation operator for the 1 m interpolation grid;
  - a Kazakov-type equivalent gain for the clamped integrator.

  The authors also found and fixed several of their own errors: the A2 sign assumption, the wrong adjacent-pair correlation, and e^{-M} versus the product form.
- **Physical insight into common-mode GNSS error.** It cancels in interior gaps but not at single-pass boundaries. This is a useful message for practitioners using sub-metre GNSS, although it needs real-vehicle confirmation (see Major issue 7).
- **Transparent reporting.** Results are labelled pre-registered, exploratory, developmental or post hoc. Failed claims (E-low v1, C3, C4) are reported, and negative findings are reported too (within one configuration all pivots are equivalent).
- **Tracking error expressed as a certified agronomic quantity.** Connecting the controller's closed-loop statistics to a certified overlap is a valuable link for the precision-agriculture community.

## 4. Major issues

### 1. L1 is a Rao–Blackwellised Monte Carlo of the simulator, not an independent "theory"; the validation is therefore largely self-consistency

**Location:** Section 5.3 (L1, Proposition 4), Section 4.3 ("without run data"), Section 6.2, Fig. 2, Table 9, Section 6.6 ("as a zero-data predictor"); `evt_theory.predict_cdf`.

**What the code does.** `predict_cdf` samples `n_cond = 200–300` operating conditions from the *same* `make_cond` the simulator uses. That distribution covers soil moisture, slip gain k_s, roughness, roll compensation, mounting bias and the real CORS error segment. For each condition it calls `core.simulate(..., ZeroRNG(), trace=...)`, which is the full nonlinear simulator with every Gaussian draw set to zero. The result is the conditional mean trajectory, including:
- steering saturation;
- rate limits;
- the integrator clamp;
- the nearest-neighbour terrain lookup;
- the GNSS trajectory.

The linear covariance machinery then adds only the small within-run noise (OU slip, heading noise, initial transient) around that mean.

**Why this matters.** Under DGPS, and largely under RTK too, the GNSS term sits in C and therefore in the mean. So the dominant part of the "prediction" is a deterministic run of the simulator. The theory knows the true plant, the true controller gains, the true actuator limits and the true condition distribution. The 0.029–0.056 log-error (Table 9) and the diagonal in Fig. 2 are therefore checks of the inner Gaussian/Kac–Rice approximation around a perfectly known model. They do not show that a closed-loop model predicts real execution. They also make the comparison with ridge regressors trained on one run per field (Fig. 6, Table 9; "1.7–3.7 times more accurate") structurally unfair: one competitor has an exact digital twin and the other has one noisy sample per field.

**Fix.**
- **(a)** Describe L1–L4 honestly as "a semi-analytic (Rao–Blackwellised) evaluation of a digital-twin model". Monte Carlo is over the run-level condition C, with the within-run Gaussian part integrated analytically. Drop "derived from controller, terrain and GNSS statistics" wherever it implies no simulator is needed.
- **(b)** Add the natural baseline: a plain Monte Carlo of the same digital twin with a matched CPU budget. The theory takes 16–353 s per field (Table S21), so report how many noisy simulator runs fit in that time and what log-error their empirical 0.9 quantile reaches. If brute-force simulation with 200 runs is as accurate and similarly fast, the five-layer machinery is not needed for the pivot. Its value would then lie in interpretability (scale law, edge mechanism, κ), and the paper should say so.
- **(c)** Report a **model-mismatch experiment**. Evaluate the theory with nominal parameters against a simulator with perturbed or higher-fidelity dynamics, for example:
  - τ ±50 %;
  - wheelbase and antenna height errors;
  - k_s and roughness scaled ×0.5 and ×2;
  - a dynamic bicycle model with cornering stiffness;
  - a hydraulic steering deadband;
  - 50–100 ms GNSS latency;
  - a GNSS bank from other stations or years.

  Without this, the mixed-fleet gain (29.8 → 3.0 pp) is shown only for a perfectly specified model.

### 2. Proposition 4 and Theorem 5 assume plan-independent, conditionally Gaussian gap processes, but the model actually used is time-varying, plan-dependent and non-Gaussian

**Location:** Proposition 4 (gap variance "independent of the plan"), Theorem 5 (equal covariance), Section 5.3 "Three refinements", Supplementary A.10, A.15, B.1(b).

**The inconsistency.** Proposition 4 is stated for the stationary LTI loop. The refinements that were *needed* to match simulation make the loop time-varying, with A_t depending on:
- the terrain gradient along the actual pass (Jacobian of β and of the roll term with respect to d);
- the describing-function gains N_u and N_r, which depend on the mean command μ_u(t), and hence on the GNSS trajectory and the terrain under that pass;
- a leak rate fitted per (condition, pass).

Moving a pass laterally (π₀ → π₁) changes all three, so the covariances of paired gap processes differ. The coupling proof of Theorem 5 ("realised with a common centred Gaussian part") then fails. With unequal covariances, Z⁽¹⁾ = Z⁽⁰⁾ + Δm does not hold. Theorem 5 is "exact" only for the LTI, unclamped, unsaturated model that the paper itself shows to be inaccurate on hilly or DGPS fields. Gaussianity given C is also only approximate once saturation (in about 96 % of DGPS conditions per the theory notes) or the clamp is active.

**Fix.**
- **(a)** State Proposition 4 and Theorem 5 explicitly under A1 with constant terrain gradient and an inactive clamp. Present the refinements as approximations outside that scope.
- **(b)** Alternatively, extend Theorem 5 to unequal covariances. One route is to bound sup_x |σ⁽¹⁾(x)/σ⁽⁰⁾(x) − 1| ≤ γ and use a scaled coupling Z⁽¹⁾ ≤ (1+γ)Z̃⁽⁰⁾ + Δ, which gives 1−F_{π₁}(t) ≤ 1−F_{π₀}((t−Δ̄)/(1+γ)). Then report γ computed from L1 on the test fields.
- **(c)** Report how often, and how far, the deployed plans violate the equal-covariance condition in R2 and R3.

Section 6.2's "coverage after a plan change predicted to 0.007" is an empirical check, not a proof. It should be presented as such.

### 3. The integrator clamp: an arbitrary, low clamp level; an ad-hoc equivalent-gain model; an unsupported "safe upper bound"

**Location:** Section 5.3 (third refinement), Table 3 ("the unclamped linear model, which can only overstate variance"), Section 7.3(3), Supplementary B.1(c), B.2; `core.simulate` (`np.clip(integ + meas*dt, -0.3, 0.3)` with conditional integration); `evt_theory.leak_rates`.

**(i) The clamp limits slip compensation on the slopes the hilly regime is about.** From the gains in `core._lqr_gains`, K_lqri = [1.386, 3.326, 0.520, 0.300]. In steady state with constant slip β, ψ = −β, so the integrator must hold I = (K_ψ/K_I)·β ≈ 11.1·β. The clamp |I| ≤ 0.3 therefore caps compensable slip at |β| ≈ 0.027 rad (1.55°), which is a steering authority of only about 5.2° from the integral path. With β = 0.35·k_s·g_y, k_s ≈ 1–1.2 in the wet R2 regime, and paddy cross-slopes at the 90th/99th percentile of 0.05/0.15 (computed from the DEM maps of the paddy fields), the integrator saturates *on its mean* on a non-trivial share of R2 terrain. The vehicle then holds a steady downhill offset, which neither real autosteer nor the linear theory would show.

The noise-driven integrator standard deviation is also comparable to the clamp. The authors quote about 0.145 against 0.3. My Lyapunov check of the unclamped loop gives sd(I) ≈ 0.07 at roughness 0.01 and ≈ 0.25 at roughness 0.0365. So for high-roughness runs the clamp is active most of the time.

Both effects make the hilly-wet results depend on a simulator constant with no stated physical basis. The theory then had to be tuned to that constant.

**(ii) The Kazakov-type leaky integrator matches the wrong quantity.** The leak rate is set so that Var(I) of a linear leaky loop equals the variance of a clipped Gaussian. Two problems:
- What matters for the score is the offset d and its spectrum, not the integrator state.
- The leak is fixed once per (condition, pass) from the *median* of the noise-free integrator trace. The clamp's activity, however, varies along the pass with the cross-slope.

This is a heuristic with three validation conditions (B.1(c)). It should be described as such.

**(iii) The "safe upper bound" is not established.** The justification "clamping only reduces variance" concerns the *integrator state*. It says nothing monotone about Var(d). A clamped or leaky integrator weakens low-frequency disturbance rejection, which can increase offset variance. I checked this with the authors' own linear model (`evt_theory`, steady-state Lyapunov, OU plus heading noise). The offset standard deviation is **non-monotone** in the leak rate:
- roughness 0.01: sd(d) = 2.170, 2.079, 1.974, 1.961, 2.007, 2.070 and 2.136 cm for leak 0, 0.05, 0.2, 0.5, 1, 2 and 5 s⁻¹;
- roughness 0.0365: the same U-shape, 7.91 → 7.15 → 7.79 cm.

It tends back towards the unclamped value as the integral action vanishes. In this particular gain set the unclamped value happens to stay at or above the leaky values, which is why the bound held in three conditions. With a different Q/R tuning, a stiffer integrator, or a clamp that bites on the mean (point i), there is no reason it should hold. Moreover, the true clamp with conditional integration is a hard nonlinearity with memory. It can hold the integrator at a wrong value during a GNSS jump and produce a post-saturation overshoot that no leaky linear model reproduces.

**Fix.**
- Either prove the bound (for example, show that sup over leak rates of Var(d) is attained at zero leak for the given gains, plus an argument that the hard clamp is dominated by some leaky surrogate), or relabel it as an empirical envelope and report its coverage over many conditions.
- Report the clamp's duty cycle (fraction of time clamped, and whether clamped on the mean) per regime.
- Repeat at least the R2 theory-vs-simulation comparison with a realistic anti-windup instead of a 0.3 m·s clamp. Back-calculation, or a clamp sized to the steering authority (for example, integrator authority equal to δ_max), would both be appropriate. This shows whether the leaky-integrator layer is needed at all.

### 4. Plant, sideslip and actuator models are minimal, and the paper's generality claims exceed them

**Location:** Section 6.1 "Simulator", Supplementary C.1, Section 7.3(1, 3), Abstract ("predicts each field's required margin from controller, terrain and GNSS statistics").

The vehicle is a kinematic bicycle at a fixed 2 m/s, with these simplifications:
- **Slip.** Slip is an exogenous kinematic angle β = −0.35 k_s g_y + OU. It enters ḋ but not ψ̇, and it does not depend on speed, lateral acceleration, normal load, cornering stiffness or implement draft.
- **Roll.** Roll is the static terrain cross-slope, with no suspension or tyre compliance and no roll dynamics.
- **Actuator.** The actuator is a first-order lag with saturation and rate limit. There is no deadband, backlash, hysteresis or valve dynamics, and no measurement or computation latency.
- **Heading.** The heading measurement is white and independent of the position error.
- **Implement.** The implement footprint is rigidly centred on the vehicle reference point. A towed implement is a low-pass filter plus a slope-dependent drift. Its lateral error is not the tractor's, and it is the implement that leaves the gap.

Each omission matters for the extremes the paper targets:
- **Deadband plus integral action** is the textbook source of limit cycles, the classical describing-function case. A Gaussian model cannot represent it.
- **Latency** reduces phase margin. It also moves the peak of the noise-to-offset transfer, which is already 1.32 at about 0.1 Hz in my computation of the complementary sensitivity of the given LQR-I loop.
- **Speed.** Speed sets both the spatial bandwidth and the effective N of the scale law. 2 m/s (7.2 km/h) is low for spraying and fertilising, which often run at 8–20 km/h.
- **Towed implements** dominate tillage and seeding.

**Fix.**
- Restrict the claims in the Abstract, Introduction and Conclusion to "a kinematic tractor with a rigidly mounted implement under LQR-I at fixed speed", or add at least the following:
  - one dynamic-bicycle run with cornering stiffness and slip-dependent yaw;
  - an actuator deadband or backlash case;
  - a latency case;
  - a towed-implement case (a hitch-point model, e.g. a trailer kinematic chain).

  For each, show both the effect on λ* and the theory's error.
- Report a speed sweep, for example 2, 3 and 5 m/s, for one regime.

### 5. Controller assumptions limit where the theory can be used

**Location:** Section 4.3, Section 6.1 (controllers), Section 6.6, Section 7.4 (practical guidance).

L1 needs the controller's state-feedback gains, the actuator model, the noise covariances and the condition distribution. Commercial autosteer controllers are proprietary and frequently nonlinear (gain scheduling with speed, pure-pursuit-like look-ahead, curvature feed-forward). The theory is implemented only for LQR-I (`evt_theory.step` hard-codes K_lqri). The paper evaluates CE layers on six stacks (pure pursuit, Stanley, Lenain observer, offset-free MPC), but CE-EVT-R and all theory results use only BCD + LQR-I. A practitioner with a John Deere, Trimble or Topcon receiver cannot evaluate L1 as written.

A related point concerns the XTE probe. The headland-probe XTE in CE+ is the *measured* cross-track error, which an integral controller drives to zero. Sensor (GNSS) error is therefore invisible in XTE: the loop tracks it, and it appears only in the true offset through the complementary sensitivity. This is the control-theoretic reason why b ≈ 0 under GNSS-dominated error. The paper should state this explicitly, because it bounds the usefulness of XTE-based normalisation under float or DGPS.

**Fix.**
- **(a)** State the scope as a known linear controller.
- **(b)** Either give a procedure to identify the needed closed-loop quantities from logged data, or show the predictor's accuracy for a second controller family. The needed quantities are the transfer functions from slip and from measurement error to true offset, plus the noise intensities. For identification, the spectra of the logged XTE and of steering-angle residuals could serve. For a second controller, pure pursuit with its look-ahead dynamics would be an option, via quasi-linearisation of the look-ahead law.
- **(c)** Show the effect of controller tuning on λ*, since the paper's own analysis implies that the certified margin is a functional of T(jω) and the GNSS error spectrum. The LQR-I weights Q4 = diag(4, 1, 0.1, 0.4), R4 = 4 are not justified. They produce noise amplification above 1 between about 0.02 and 0.15 Hz. Reporting sensitivity to the tuning, and noting the opportunity to tune the controller to minimise the certified margin, would add real value for this audience.

### 6. The GNSS band that the loop amplifies is largely synthetic

**Location:** Section 6.1 "Data", `core.gnss_bank`.

The CORS series are 30 s epochs, linearly interpolated to 1 Hz, so they carry essentially no content above about 1/60 Hz. Content above that comes from a single 1615 s vehicle record (i2Nav), winsorised and tiled with random shifts, reversals and sign flips. The LQR-I loop amplifies measurement error most in roughly 0.02–0.15 Hz: |T| = 1.07, 1.24, 1.32 and 0.97 at 0.02, 0.05, 0.1 and 0.2 Hz in my check. That band is exactly where the GNSS model is a splice of interpolation and one re-used 27-minute record.

Because adjacent passes are one pass duration apart (minutes), their gap depends on GNSS content at periods from seconds to minutes. The pass-to-pass statistic, and hence λ*, is sensitive to precisely this synthetic part.

**Fix.**
- Provide a sensitivity analysis: scale the HF residual by 0.5 and 2, or replace it with an alternative (for example, a 1 Hz CORS or kinematic dataset).
- Report how λ* in R1 and R3 changes.
- At minimum, state that the mid-band spectrum is modelled, not measured.

### 7. Two physical mechanisms are claimed from the simulator and depend on its modelling choices

**Location:** Section 6.2 ("the physical mechanism of Theorem 3(b)"), Section 7.4 ("Under DGPS … boundary passes … set the certified margin"), Highlights and Conclusion.

**(a) Field-edge mechanism.** The DGPS field-edge result follows from evaluating coverage on W (P inset by 2w) with the main-area passes only. In a real operation, the headland passes border W. The "edge" is then an interior gap between the innermost headland pass and the first or last infield pass. These are driven at very different times (the start or end of the operation), so GNSS common mode does *not* cancel, but the gap is still a two-pass quantity, not a single-pass one. The practical recommendation should be re-derived with headland passes included in coverage, or limited to the modelling assumption.

**(b) Spatial correlation of slip.** Within-run slip roughness is an OU process in *time*, independent across passes (Proposition 4). Real soil and slip variation is a *spatial* random field: passes 1.5–6 m apart cross correlated soil. This both introduces cross-pass dependence given C and changes the gap variance (positively correlated slip cancels in gaps). It also breaks Theorem 4's independence of non-adjacent pairs.

**Fix.** Discuss both mechanisms and, ideally, test one case with spatially correlated slip.

### 8. The "under-damped" explanation of negative autocorrelation is incorrect; the right explanation strengthens the paper

**Location:** Section 5.3 L3 ("because the under-damped closed loop has single-pass autocorrelation about −0.24 at 10 m"), Supplementary A.13.

The LQR-I closed loop I computed has poles at about −4.51, −0.86 ± 0.88j (ζ ≈ 0.70, ω_n ≈ 1.23 rad/s) and −0.32 rad/s. It is well damped. The negative lobe (I reproduce ρ(10 m) ≈ −0.234) comes mainly from **integral action**. The transfer from slip to offset then has a zero at s = 0, so the offset spectral density vanishes at zero frequency. That forces ∫ r(τ) dτ = 0, so the autocorrelation *must* become negative.

This is a structural property of any offset-free controller, not of the damping. It means the sign-indefinite correlation, and hence the need for the Bonferroni argument, is generic rather than incidental. Please correct the text and state this.

## 5. Minor issues

- **Section 5.3, L1 assumptions** list a "locally constant terrain gradient". The code (`TERRAIN_SL`) instead statistically linearises the simulator's *nearest-neighbour* gradient lookup (a step map), which is a simulator artefact rather than physics. Supplementary B.1 still states assumption A1′ (smooth terrain) and the non-Gaussian explanation. The theory notes (§6.2) retract both and attribute the residual bias to the integrator clamp. Please reconcile all three and use bilinear terrain interpolation in the simulator.
- **Linearisation point.** Linearising about the noise-free trajectory gives f(E x), not E f(x). The 0.07–0.20 cm RMS check (Table S5) is reassuring. Please also report it for conditions with active saturation or clamping, where the difference is largest.
- **Rate limiter.** The rate limiter is treated by a static random-input describing function on the rate (N_r). A rate limiter is a dynamic nonlinearity that introduces phase lag, the classical PIO mechanism. A static gain captures only the amplitude effect. Please state this or use a phase-aware describing function.
- **Table 3 versus theory notes.** Table 3's R3 "first version" reads 36.0 / 37.3 (−3.5 %). The theory notes (§6.2) say the reference was unified to 37.09 (−2.9 %). Use one reference throughout.
- **Proposition 4 wording.** Proposition 4 states that the stationary covariance solves P = APA' + BΣB'. With initial line-acquisition transients (d₀ ~ N(0, 3 cm), ψ₀ ~ N(0, 0.5°)) and a slow closed-loop pole (−0.32 rad/s, about 3.2 s or 6.3 m at 2 m/s), the main area starts only 2w = 3 m into each pass in R2. The pass is therefore not stationary on the evaluated section. Say that the time-varying recursion from the acquisition state is used. Also justify the acquisition-transient magnitudes: real headland-turn line acquisition often leaves decimetre errors.
- **Mean shift Δ.** The mean-shift bound in Theorem 5 (A.15) is "dominated by the roll-induced antenna offset … under integral action". This assumes the integrator removes the slip mean, which fails where the clamp binds (Major issue 3). There, slip also contributes to Δ.
- **Heading noise.** It is white at 20 Hz and independent of the position error. With dual-antenna GNSS or GNSS/INS, heading and position errors are correlated. Please state this.
- **Units and notation.** "Spectral moments λ₀, λ₂" collide with the erosion λ and λ₀ (the reference erosion). Rename the spectral moments (for example m₀, m₂).
- **Kac–Rice regularity.** Theorem 3(a) is stated for a C¹ process. Z' = (ψ+β) differences include OU slip, which is continuous but not differentiable. That is fine for Kac–Rice on Z, but Theorem 6's Cramér–Leadbetter conditions (local behaviour of the covariance at 0) should be checked and stated.
- **Edge terms over sections.** In Theorem 3(b), the product of single-pass probabilities is exact per section, but combining across sections by a union bound is loose for long overlap bands. Please state that this is an upper bound.
- **Fig. 2.** Report the between-field spread of log λ* per regime next to the theory's log-error, so readers can judge the 0.029 figure. The R2 range is narrow (about 0.14–0.17 m).
- **Section 4.4 / Table S21.** Report the runtime of an equivalent noisy Monte Carlo with 200 runs for comparison (see Major issue 1).
- **Clean-up before submission.** Appendix E ("remove before submission") and the TODO in Section 6.7 must be removed or resolved. A paper whose main claim concerns execution error needs at least the CitrusFarm replay of Section 6.7(a).

## 6. Questions to the authors

1. With your CPU budget per field (16–353 s), how many noisy simulator runs can be executed, and what log-error against λ*_f does their empirical 0.9 quantile reach? In what sense does the five-layer predictor outperform direct simulation of the same model?
2. What is the fraction of time that the integrator is clamped, per regime? On how much of the R2 area is it clamped *on its mean* (i.e., required |β| > 0.027 rad)? How does λ* in R2 change if the clamp is raised to match the steering authority, or replaced by back-calculation anti-windup?
3. Can you prove, for the given LQR-I gains, that Var(d) of the leaky-integrator loop is maximised at zero leak, and that the hard clamp is dominated by it? If not, will you relabel the "safe upper bound" as an empirical envelope?
4. How large is the covariance difference between paired gap processes of π(λ₀) and π(λ̂) under the time-varying model in R2 and R3? Does Theorem 5 still hold with a computable correction?
5. How accurate is the theory when its plant or condition model is misspecified? Cases to test: τ, k_s and roughness off by a factor of 2; a dynamic-bicycle or deadband actuator; 100 ms latency; a GNSS bank from different stations or years.
6. Can L1 be applied to a commercial autosteer of unknown structure, for example by identifying the slip-to-offset and measurement-error-to-offset transfer functions from logged XTE and steering data? What data would a farm need?
7. How do λ* and the field-edge conclusion change when the headland passes are included in the coverage evaluation, and when slip roughness is a spatial rather than temporal process?
8. How sensitive are the R1 and R3 margins to the synthetic 1/60–0.5 Hz GNSS content (the i2Nav tiles)?
9. Would a towed implement (hitch-point kinematics) change the qualitative conclusions, in particular the cancellation of common-mode error in interior gaps?
10. Have you considered using the L1–L4 machinery inversely, choosing the LQR-I weights to minimise the certified margin? This seems a natural and practically valuable contribution of the closed-loop view.
