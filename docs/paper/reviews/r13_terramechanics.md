# Review R13 — Terramechanics and off-road vehicle dynamics

**Manuscript:** "Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations" (Computers and Electronics in Agriculture)
**Reviewer expertise:** terramechanics, slip on slopes, lateral drift, soil–tyre interaction, tractor–implement dynamics, trailed-implement offset.
**Material examined:** `docs/paper/manuscript.md`, `docs/paper/supplementary.md` (Appendix A, B, C), and the vehicle, terrain and slip model in `experiments/core.py` (`Field._load_dem`, `Field.gy`, `Condition`, `simulate`).

---

## 1. Summary

The authors reduce the zero-miss event of a parallel-swath coverage plan to a scalar run score: the covering radius of the executed pass centrelines, measured against the implement half-width. They calibrate this score with split conformal prediction (marginal and PAC) on a reference plan that has at least as many passes as the deployed one (CE, CE+). They also build a five-layer extreme-value theory from a linearised closed-loop vehicle model (Lyapunov covariance, then Kac–Rice exceedance, a Bonferroni-bounded product, a mixture over operating conditions, and a Gumbel scale law). This theory predicts each field's required margin without run data and serves as a ratio pivot for cross-field conformal calibration (CE-EVT-R). All quantitative evidence comes from a closed-loop simulator. The simulator uses real field polygons, Copernicus GLO-30 elevation and real CORS GNSS error series. Its vehicle model is a kinematic bicycle with a first-order steering lag. Terrain enters as a side-slip angle β = −0.35·k_s·g_lat plus an Ornstein–Uhlenbeck (OU) term, where k_s and the OU intensity are set by a per-run scalar soil moisture. Roll enters as an antenna offset with partial compensation.

The statistical contribution is careful and honestly reported. From my disciplinary standpoint, though, the physical execution model rests on two assumptions that the paper does not support with terramechanics or validate against vehicle data: (i) the implement footprint is centred rigidly on the tractor reference point, and (ii) all soil and terrain disturbances are Gaussian, temporally (not spatially) correlated, and independent between passes. The theory layer (L1–L5) and its reported accuracy (log-error sd 0.029–0.056) inherit these assumptions directly. The conformal guarantee does not. The paper is clear that validity is distribution-free. It is much less clear that the theory's accuracy, the "decisive" mixed-fleet gains and the practical guidance about where misses occur may be artefacts of a simulator whose disturbance model was built to match the theory.

## 2. Recommendation

**Major revision.**

| Criterion | Score (1–10) |
|---|---|
| Novelty | 7 |
| Soundness (vehicle–terrain modelling and the physical assumptions behind the theory) | 4 |
| Practical relevance | 6 |
| Clarity | 6 |

The conformal machinery (Sections 3–5.2, 5.4) is sound and would be valuable to the community. The vehicle–soil–implement model needs either physical justification and sensitivity analyses, or a much narrower framing of the theory-based claims.

## 3. Strengths

1. **Correct target quantity.** Framing the problem around pass-to-pass (relative) error, with the explicit distinction between interior gaps and field-edge misses, is physically right. The common-mode cancellation argument for DGPS (Section 6.2) is a useful insight for practitioners.
2. **Real GNSS tails.** The GNSS tails are real (wrong fixes, float drift; Table 1) and are not Gaussianised. The theory handles them correctly by conditioning on the run-level operating condition C rather than forcing them into L1.
3. **Classic slope offsets are represented.** The model includes the "skip every other pass" signature. The roll-induced antenna offset and the vehicle-frame mounting bias both flip sign between up- and down-field passes (`core.py`, `meas = d − h·sin(roll)(1−c) + sgn·ε + mount`). Many coverage papers ignore this.
4. **Steering actuator realism.** Steering lag, saturation and rate limits are included, and the integrator anti-windup is modelled explicitly in the theory, with a safe upper bound.
5. **Validity is decoupled from the theory.** The paper states repeatedly that validity does not depend on the theory (Proposition 5), and it reports pre-registered and failed claims transparently (Table 6, Section 7.2).
6. **Limitations are partly admitted.** The authors acknowledge that the simulator samples slope by nearest neighbour, which breaks Gaussianity at high slip (Supplementary B, "Assumption on terrain", A1′).

## 4. Major issues

### M1. The slope-induced slip model is ad hoc, uncalibrated and physically incomplete

**Location:** Section 6.1 "Simulator"; Supplementary C; `core.py`, `Condition.__init__` (`k_s = 0.15 + 0.85·m·LogN(0, 0.25)`) and `simulate` (`beta = −k_s·g_v·0.35 + ou`).

**Why it matters:**
- **No physical basis.** The side-slip angle is linear in the lateral gradient (tan of the cross-slope), with a constant 0.35 and a moisture-dependent gain. No terramechanics reference, no field measurement and no sensitivity analysis supports either constant.
- **The real relation is nonlinear.** Measured crab angles of tractors on side slopes are nonlinear in slope. They depend on:
  - lateral load transfer to the downhill tyres;
  - tyre cornering stiffness, inflation pressure and lug pattern;
  - the soil's shear strength parameters (c, φ, Janosi–Hanamoto shear deformation modulus K);
  - drawbar pull, because the combined longitudinal and lateral slip interact through the friction ellipse;
  - forward speed.

  The relation saturates, and the vehicle slides, as the lateral force demand approaches the soil's shear capacity (Bekker; Wong, *Theory of Ground Vehicles*; Pacejka; Lenain et al. 2006 and later work by the same group on slip-angle observers).
- **Slip and roughness are coupled through one scalar.** Moisture drives both through the same per-run variable, so the model cannot represent dry-but-steep or wet-but-flat conditions independently.
- **Consequences for the paper.** The required margins in R2 ("hilly-wet") and the scaling of λ* with terrain both depend on these two unvalidated constants. The theory reproduces the simulator, so its excellent agreement in Table 3 and Fig. 2 says nothing about real slip.

**Concrete fix:**
- **(a)** Justify the slip law with literature or measurements. At minimum, report the crab angle the model produces at 5, 10 and 15% cross-slope in each moisture class, and compare it with published values.
- **(b)** Replace or bracket the linear law with a saturating slip model, for example lateral force from a Pacejka- or Dugoff-type tyre with soil-dependent peak friction, or a Janosi–Hanamoto shear-stress law with load transfer. Rerun Table 3 / Fig. 2 and the v8 validity check with this model.
- **(c)** Provide a one-at-a-time sensitivity analysis of λ* and of theory accuracy to the slip constant (0.35 ×{0.5, 2}) and to the k_s distribution.
- **(d)** Decouple the slip gain from roughness intensity, or justify the coupling.

### M2. Implement dynamics are absent: the footprint is the tractor's path

**Location:** Section 3 "Execution model"; Fig. 1; `core.py`, where `rec = sgn·d` (the vehicle reference point) is used directly as the footprint centre.

**Why it matters:** The coverage that matters is the implement's, not the tractor's. On side slopes the dominant real source of pass-to-pass error for drawn implements is that the implement does not track the tractor, through several mechanisms:
1. **Trailed implement offset.** A tractor that crabs uphill to hold its line drags a trailed implement whose drawbar is misaligned by the crab angle. The implement also generates its own downhill side force (soil-engaging tools, gravity on a heavy sprayer tank). A 2–3° crab with a 4–6 m hitch-to-axle distance already shifts the implement 15–30 cm. That is an order of magnitude above the RTK margins certified in R1 and R2 (about 10–15 cm). Commercial passive and active implement guidance systems exist precisely for this reason.
2. **Off-tracking and transients.** The implement filters the tractor path with a lag that depends on hitch geometry and speed. Changes in slope along the pass therefore produce implement transients that the tractor's integrator does not remove.
3. **Mounted implements on slopes.** Roll of a three-point-linkage implement displaces the soil-engaging point laterally by roughly tool height × roll angle. For sprayers, boom roll and yaw change the effective swath edge.
4. **Side draft.** Asymmetric tillage tools (ploughs, offset discs) generate a side draft that depends on soil.

In the simulator the LQR-I integrator drives the measured antenna offset to zero, so steady-state slip is largely compensated. The only residual slope effect is the roll term. As a result the simulator may substantially underestimate slope-induced pass-to-pass error for trailed implements. The finding that interior gaps under RTK are small and well predicted by a Gaussian theory may not survive the addition of an implement.

**Concrete fix:**
- **(a)** Add at least a single-axle trailed-implement model: hitch point, implement axle, implement cornering stiffness or soil side force, and implement side slip on the cross-slope. Treat the footprint as centred on the implement.
- **(b)** Report, per regime, the distribution of the tractor-to-implement lateral offset.
- **(c)** Rerun the theory accuracy check (Table 3, Fig. 2) and the v8 validity and efficiency claims with the implement model. If this is out of scope, state in the title, abstract and Section 7.3 that the footprint is that of a rigidly mounted implement with no lateral compliance, and remove "tillage" from the application list in Section 1.
- **(d)** Specify the implement type per regime. The same vehicle (2.6 m wheelbase, 2.6 m antenna height, 2 m/s) is used for a 1.5 m paddy implement and a 6 m DGPS implement, which is not physically plausible.

### M3. Soil variability is modelled as temporal noise, not as a spatial field; this conflicts with the independence assumptions of L1–L3

**Location:** Section 5.3 L1 and Proposition 4 ("Gaussian innovations independent across passes"); L3 ("non-adjacent pairs are independent given C"); `core.py` (OU slip with a 2 s time constant, drawn independently per pass; moisture is a per-run scalar).

**Why it matters:** Real soil variability (texture, moisture, compaction, organic matter) is a spatially correlated random field. Its variogram ranges are typically tens of metres, which spans several adjacent passes. Headlands, tramlines, dead furrows and former field boundaries add structured variability. A wet hollow or a compacted zone is crossed by all neighbouring passes at the same along-track position. The resulting slip is positively correlated across many passes and fixed in field coordinates. The simulator does the opposite: the OU slip is indexed by time and drawn independently for each pass, so two passes 3 m apart see unrelated soil.

This has three consequences:
- **(i)** Proposition 4's independence across passes and L3's independence of non-adjacent pairs given C both fail unless the soil map is part of C. If it is part of C, it is unknown at prediction time, and the theory pivot would need to integrate over it.
- **(ii)** At the boundary of a patch, adjacent passes experience different slip, which produces localised differential drift (a gap). This is a mechanism that the theory cannot represent.
- **(iii)** For CE+, the headland probe line samples headland soil, which is usually compacted and drier than infield soil. Its XTE is therefore a biased proxy of infield slip (Section 4.2).

**Concrete fix:**
- **(a)** Make the slip gain a spatial random field, for example a Gaussian or log-Gaussian field with ranges of 10–50 m and a nugget, fixed per field-season. Add a headland compaction contrast.
- **(b)** Re-examine L1–L3 under this structure. The cross-pass covariance becomes non-zero, the product form of Theorem 4 needs a dependence correction, and the extremal index changes.
- **(c)** Report theory accuracy and CE-EVT-R efficiency under it.
- **(d)** Discuss whether a soil or yield map (EM38, previous yield maps) could enter C.

### M4. Heavy-tailed, impulsive terrain disturbances are excluded, and the Gaussianity "validation" is circular

**Location:** Section 5.3 (L1 Gaussian innovations; L2 Kac–Rice; L5 Gumbel scale law); Supplementary B, line 104 (diagnostic "skewness −0.002, excess kurtosis −0.012"); Table 1 caption; Section 2 ("Parametric models misrepresent the heavy … tail").

**Why it matters:** In the field, the extreme lateral deviations that create misses are dominated by rare, impulsive or regime-switching events rather than by Gaussian roughness. Examples:
- wet patches and waterlogged spots, where slip jumps and the vehicle slides;
- stones, stumps and clods striking a wheel or a tool, producing yaw impulses;
- ruts, including wheels falling into the previous pass's ruts. This is relevant in R2, where the 1.5 m swath is about one tractor track width.
- ridge crossings, terrace bunds and drainage furrows;
- traction loss near the peak of the slip curve.

These disturbances are compound-Poisson or jump-diffusion with heavy (often power-law) amplitude distributions. For them:
- the Kac–Rice/Gumbel machinery does not apply;
- the margin's dependence on field length changes from √(2 log N) to a rate proportional to the expected number of events;
- the 1.0–1.4% quantile errors of Table 3 would not be expected to hold.

The manuscript treats GNSS heavy tails carefully: real data, carried in C. Terrain receives the opposite treatment, because the simulator injects only Gaussian OU noise. The reported near-Gaussian conditional marginals in R2 therefore confirm the simulator's construction, not the physics. The model's only non-Gaussianities (the slope-grid jumps of A1′ and saturation) are acknowledged, then either assumed away or linearised.

The conformal guarantee survives heavy tails when calibration runs sample them. Two parts of the paper, however, depend on Gaussian structure: the efficiency claims of CE-EVT-R, and Proposition 8's predicted PAC inflations (Fig. 7), which use theory CDFs as the run-score law. Rare events also interact badly with one run per calibration field. If wet patches occur on, say, 5% of field-seasons, a pool of 25 single runs will often contain none or one of them. The marginal guarantee is unaffected on average, but the realised coverage (Beta spread, Section 5.4) becomes much more variable. The theory pivot will then systematically under-predict on fields prone to such events, which are exactly the fields where certification matters.

**Concrete fix:**
- **(a)** Add an impulsive disturbance channel to the simulator: compound-Poisson yaw or lateral impulses with Pareto or lognormal amplitudes (stones, ruts), and a two-state Markov-modulated slip gain (wet-patch regime) tied to field positions.
- **(b)** Report, as a function of event rate and tail index:
  - theory accuracy (Table 3, Fig. 2);
  - the validity resampling check (Table 7);
  - mixed-fleet excess overlap (Table 8).
- **(c)** Either extend L2/L5 with a jump term (Rice formula for a Gaussian-plus-Poisson process, or a peaks-over-threshold/GPD layer for the terrain component), or state explicitly that the theory applies only to Gaussian terrain disturbances.
- **(d)** Remove or qualify the sentence suggesting that the diagnostic in Supplementary B validates Gaussianity.

### M5. Terrain input: a 30 m surface model applied to levelled paddy fields

**Location:** Section 6.1 "Data"; Table 2 (R2 and R3 "paddy (hilly)"); `Field._load_dem` (GLO-30 gradient, bilinearly resampled to 1 m).

**Why it matters:**
- **Paddy basins are not sloped.** Paddy fields in the hilly south of China are terraced and levelled within their bunds, so the within-field cross-slope is close to zero by design. Copernicus GLO-30 is a 30 m X-band surface model that includes canopy and buildings. At 30 m it smooths across terrace steps and assigns the hillside slope to the levelled basin. The "hilly" slip and roll in R2 and R3 are therefore probably not physical for those fields.
- **The real paddy disturbances are absent.** In a puddled paddy the dominant lateral disturbances are hardpan unevenness, sinkage, floating and rut following, none of which the model includes.
- **30 m resolution misses the relevant scales.** It cannot resolve micro-topography (furrows, tramlines, field-scale undulation at 5–20 m) that excites the steering loop at the bandwidths relevant here (OU time constant 2 s, i.e. 4 m at 2 m/s).

**Concrete fix:**
- **(a)** Report the distribution of cross-slopes used in each regime (mean, 95th percentile, maximum), and state how terraces were handled.
- **(b)** For paddy fields, either use a levelled-basin assumption with a hardpan-roughness model, or choose genuinely sloping upland fields for the "hilly" regimes.
- **(c)** Add a sensitivity run with higher-resolution terrain or a synthetic microrelief spectrum (for example ISO 8608 class A–C ground profiles adapted to fields) to check whether the theory's spectral moments λ₀ and λ₂ remain accurate when the terrain excites the loop at higher frequencies.

### M6. The practical claims are stronger than the physical model supports

**Location:** Abstract; Highlights; Section 6.6; Section 7.1; Section 7.4 ("under DGPS, pay particular attention to boundary passes"; the theory "explains a physical effect").

**Why it matters:**
- **Where misses occur depends on the missing physics.** The edge-concentration result and the mixed-fleet gains (29.8 → 3.0 pp) are presented as physical findings. Both depend on the relative size of GNSS, slip and implement terms. Adding the implement offset (M2), spatial soil (M3) and impulsive events (M4) could change where misses concentrate, for example at slope transitions or wet patches rather than at field edges, and could change how much between-field variation a terrain-blind scale misses.
- **No vehicle data.** Section 6.7 is a TODO, so no vehicle data constrain any terramechanical parameter.

**Concrete fix:**
- Present Sections 6.2 and 6.6 as properties of the simulator ("in a simulator with linear slip and rigid implements …").
- Move the physical interpretation to a hypothesis to be tested in Section 6.7.
- Include at least the CitrusFarm replay, or any real autosteer log with ground truth, before publication. Even one season of logged tractor and implement data with PPK ground truth on 10–20 fields would turn the slip and implement parameters from assumptions into estimates.

## 5. Minor issues

1. **Undocumented slip parameters.** Supplementary C gives β = −0.35·k_s·g_lat. State the units (g is a tangent, β in rad), the resulting crab-angle range, and the source of the 0.35 constant and the lognormal(0, 0.25) and (0, 0.3) dispersions.
2. **Roll model.** Roll is set to arctan(g_lat), i.e. vehicle roll equals the terrain cross-slope. Real roll also includes tyre deflection, suspension and the asymmetric sinkage of downhill tyres in soft soil (larger in wet soil). Consider roll = arctan(g) + soil-dependent deflection.
3. **Roll compensation.** A roll-compensation factor of 0.85 ± 0.05 is low for current IMU-based terrain compensation (typically above 0.95). It is also time-invariant, with no roll-sensor bias drift. Justify the value or bracket it.
4. **Speed and acceleration.** Constant speed (2 m/s) for all regimes and operations rules out speed-dependent slip, dynamic load transfer and longitudinal–lateral slip coupling under drawbar load. State this.
5. **Line acquisition.** After a headland turn the residual is N(0, 3 cm) and is "excluded after 10 m" for the XTE statistic. Line acquisition on slopes is slip-dependent and often the source of misses near the headland boundary. Check how the 2w main-area inset interacts with it.
6. **Tramlines and rut following.** The follow-previous-pass baseline should interact with ruts from the previous pass. In R2 (1.5 m swath) the wheels may run in the neighbour's ruts, which couples adjacent passes and violates the per-pass independence ξ_k used in Theorem 5's coupling.
7. **Footprint width on slopes.** The footprint width w is horizontal. On a cross-slope, the slope-parallel working width of a mounted implement differs by cos(slope), and boom or tool height changes the effective edge for sprayers. Hameed et al. (2016) is cited as a baseline for this effect, so the simulator should either include it or explain why not.
8. **Field geometry from harvest tracks.** Field polygons come from combine harvester trajectories. The resulting boundaries are harvested-area hulls, not field edges. This matters for the edge-term findings (Theorem 3(b)).
9. **Moisture per run.** Beta(2, 3) moisture drawn i.i.d. per run ignores seasonal and day-to-day persistence. Calibration runs from one season deployed in another break exchangeability in practice. Discuss this as a deployment risk distinct from M3.
10. **Terminology.** "Wheel slip" is used in the Introduction, but only lateral side slip (sideslip angle) is modelled. Distinguish longitudinal slip from slip angle.
11. **Missing literature.** Cite tractor side-slope tracking and implement-guidance work. Examples include Lenain/Thuilot/Cariou slip-angle observers beyond 2006; Bevly et al. on GPS-based sideslip estimation; Karkee and Steward on tractor–implement kinematic models; Backman et al. on trailed-implement path control. Also cite terramechanics references for lateral soil–tyre forces (Wong; Schwanghart; Crolla and El-Razaz).

## 6. Questions to the authors

1. What crab angle does the model produce at 10% cross-slope for the median and the 95th-percentile k_s in R2? How does it compare with published measurements for tractors on cultivated soil?
2. What is the distribution of within-field lateral gradients in the R2 and R3 paddy fields as sampled from GLO-30? How many fields have mean cross-slope above 5%, given that paddy basins are levelled?
3. How large is the steady-state true lateral offset of the vehicle (not the antenna) on a constant cross-slope once the LQR-I integrator has converged? Is the roll term then the only steady slope contribution?
4. If a trailed implement with a 5 m hitch length were added, would interior gaps under RTK remain Gaussian and well predicted by L1–L2? Would the edge-concentration finding under DGPS survive?
5. How would the theory and Proposition 8's predicted PAC inflation change if 2% of runs contained a wet-patch slide of 0.3–0.5 m lasting 10–20 m? Is the √(2 log N) scaling still appropriate?
6. Does the probe-line XTE on the compacted headland correlate with infield slip when the infield slip gain is spatially variable? Has this relation been checked in any real log?
7. Why do all three regimes share one vehicle (2.6 m wheelbase, 2.6 m antenna height, 0.25 s steering lag) despite implements of 1.5–6 m and very different soil conditions (puddled paddy versus wheat on the North China Plain)?
8. Can the main results (Tables 5, 7 and 8) be stratified by field slope class, to show whether certified margins and the theory's accuracy degrade with cross-slope?
