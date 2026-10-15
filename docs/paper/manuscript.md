# A calibration method for setting pass overlap with a guaranteed probability of no missed strips in agricultural coverage path planning

## Abstract

The overlap between adjacent passes needed to avoid unworked strips depends on GNSS grade, terrain, implement and controller, yet the fixed overlap used in practice carries no stated reliability. This paper proposes conformal erosion, a calibration method that sets the overlap margin of a coverage plan so that the probability of any missed strip stays below a chosen level. Each logged run is reduced to one coverage score, the widest gap or edge recession of the executed passes; an order statistic of these scores gives the margin. A field with operation history is calibrated on its own runs; a field without history is calibrated on one run from each of many other fields, put on a common scale by a vehicle–terrain–GNSS model (analytic, or a Monte Carlo digital twin) whose accuracy does not affect the guarantee. In a pre-registered simulation study driven by real field boundaries, terrain and GNSS error series, the method held its target miss probability in every check under the nominal simulator. With 100 logged runs per field it used 4–55% less overlap than two conformal planners at the same guarantee; across a mixed fleet without target-field data it exceeded the per-field optimum by 0.6 percentage points of overlap, against 1.2–4.4 for configuration-aware baselines, covering every machine configuration. This held under implement dynamics, degraded GNSS and levelled terrain, but not under heavy-tailed slip or unstable steering. A zero-miss margin paid off against the vendor rule only when a missed area cost 30–100 times an over-applied one.

**Keywords:** coverage path planning; pass-to-pass accuracy; overlap; GNSS guidance; conformal prediction; precision agriculture

### Highlights

- A method sets pass overlap so that missed strips occur with a chosen probability
- Each logged run is reduced to one coverage score that decides complete coverage
- Fields without history are calibrated across fields with a vehicle model
- Simulation: target held; 4–55% less overlap than conformal planners
- A zero-miss margin pays off only if a miss costs 30–100x an overlap

### Nomenclature

| Symbol / acronym | Meaning |
|---|---|
| $w$ | implement (swath) width |
| $W$ | main area: field inset by $2w$ (the rest is headland) |
| $\lambda$ | margin (erosion): planned overlap between adjacent passes is $2\lambda$ |
| $\pi(\lambda)$, $K(\lambda)$ | greedy plan with margin $\lambda$ and its number of passes |
| $J(\lambda)$ | main-area overlap ratio of $\pi(\lambda)$ |
| $e_k(x)$ | lateral offset of executed pass $k$ at along-pass position $x$ |
| $M(\lambda,e)$ | missed (unworked) area of the main area |
| $S$ | coverage score of a run (Section 3.3) |
| $\lambda_\mathrm{ref}$ | margin of the reference plan on which scores are recorded |
| $\varepsilon$, $\delta$ | tolerated probability of a run with a missed strip; confidence parameter of the PAC rule |
| $k_\star$ | rank of the order statistic used as the margin |
| $\lambda^\star_f$ | field $f$'s own requirement: the smallest margin with P(no miss) = $1-\varepsilon$ (oracle) |
| $\hat q_f$ | model-predicted $(1-\varepsilon)$ score quantile of field $f$ (model scale) |
| $\kappa$ | inflation of the miss level when fewer passes are deployed than calibrated (Section 3.7) |
| $\tau$, $r$ | tolerated gap width; cost ratio of a missed to an over-applied unit area |
| CE, CE-q, CE+ | conformal erosion calibrated on the field's own runs (Table 2) |
| XCE-T, XCE-MC | cross-field conformal erosion with an analytic or Monte Carlo model scale |
| CPrP, UBCP | comparators: conformal predictive programming (Zhao et al., 2024); union-bound conformal planning, pair level (Lindemann et al., 2023) |
| CPP | coverage path planning |
| BCD | boustrophedon cellular decomposition |
| LQR-I | linear-quadratic regulator with integral action |
| XTE | cross-track error reported by the autosteer |
| PAC | probably approximately correct (holds with probability $1-\delta$ over the calibration data) |
| pp | percentage points |

---

## 1. Introduction

Field operations such as spraying, fertilising, seeding and tillage are planned as parallel passes whose spacing equals the implement width minus an overlap. The plan is optimal only if the machine follows it exactly. Real passes deviate from the planned line because of GNSS positioning error, wheel slip on slopes and wet soil, antenna roll on side slopes, mounting offsets and the finite bandwidth of the steering controller. A strip is left unworked whenever two adjacent passes drift apart by more than their overlap, or when the outermost pass drifts away from the field boundary; the relevant quantity is the relative error between adjacent passes, which the industry calls pass-to-pass accuracy. Overlap set to absorb this error applies inputs twice on the overlapped strip. Both errors carry a cost: missed strips lose yield or leave weeds and pests untreated, and overlap wastes seed, fertiliser and pesticide (FAO, 2025; Zhang et al., 2015, 2021). Autonomous machines remove the operator who used to correct visible gaps by eye.

Current practice sets a fixed overlap, typically twice the vendor's pass-to-pass specification or a value learned by experience. Such a margin has no stated reliability and does not adapt to field shape, terrain, receiver grade or implement width. Coverage path planning (CPP) research has produced efficient decompositions, swath-angle optimisation and smooth headland turns (Galceran and Carreras, 2013; Höffmann et al., 2024; Mier et al., 2023, 2025), and terrain-aware planners adjust spacing to 3D geometry (Hameed et al., 2016), but these planners assume perfect execution. Control research reduces tracking error (Lenain et al., 2006; Pannocchia and Rawlings, 2003; Mayne et al., 2005), but a smaller error does not by itself state how often a strip will be missed. Conformal prediction turns logged data into a margin with a finite-sample, distribution-free guarantee and has been used for planning (Lindemann et al., 2023; Zhao et al., 2024). Three features of field coverage are not addressed by these methods: the guarantee must hold for the worst of many pass pairs and field edges at once; the plan on which data are logged and the plan that is deployed differ, and adding passes makes the worst case worse; and a field is worked only a few times per year, while a conformal margin at a miss level of 10% needs at least 9 (marginal) or 22 (PAC) logged runs.

This paper proposes **conformal erosion**, a calibration method that sets the overlap of a coverage plan from logged runs so that the probability of a run with any missed strip is at most a level $\varepsilon$ chosen by the user. Erosion refers to planning every pass as if the implement were narrower by a margin $\lambda$ on each side, which leaves an overlap of $2\lambda$ between adjacent passes; the method chooses $\lambda$. It works with any planner that accepts a margin and needs, for each logged run, the executed track of the implement. Fig. 1 shows the workflow. The contributions are:

1. **A margin calibration method for fields with operation history** (CE, CE-q, CE+; Section 3.4). The margin is an order statistic of the coverage scores of the field's own logged runs; for the plan on which the runs were logged the miss probability is guaranteed without any assumption on the error process.
2. **An extension to fields without operation history** (XCE; Section 3.5). A farm or contractor typically holds many fields with one or two logged operations each. The method pools one run from each of many fields; a model of the vehicle, terrain and GNSS, either an analytic extreme-value model or Monte Carlo runs of a digital twin, predicts each field's margin and is used only to put the fields on a common scale, so the guarantee does not depend on the model's accuracy.
3. **A coverage score that makes the calibration exact** (Section 3.3). Each logged run is reduced to one number, the covering radius of the executed passes including the field edges. A run leaves no strip unworked if and only if its score is below the planned margin, and no other score that certifies complete coverage is smaller, so the calibrated margin is as tight as the data allow.
4. **A pre-registered simulation evaluation** (Sections 3.8 and 4) on 30 to 135 unseen fields per experiment, against conformal planners, practice rules, configuration-aware baselines and learned predictors, with tests of robustness to model misspecification and headland laps and an analysis of when a certified margin is worth its cost.

![](../../figures/paper/fig_workflow.png)

**Fig. 1.** Workflow of the proposed method. Logged runs on a reference plan are reduced to one coverage score each; an order statistic of the scores (scaled by a vehicle–terrain–GNSS model when the scores come from other fields) gives the margin, and the user's planner generates the deployed plan with that margin. The transfer check falls back to the reference plan when the calibrated margin exceeds the reference margin.

All confirmatory experiments were pre-registered in a time-stamped repository before they were run; failed and partially met claims are reported alongside met ones, and exploratory and post hoc analyses are labelled as such (Supplementary Table S20). Section 2 reviews related work, Section 3 describes the method and the simulation study, Section 4 reports the results, Section 5 discusses what is guaranteed, the limitations and practical use, and Section 6 concludes.

---

## 2. Related work

*Coverage path planning.* Boustrophedon cellular decomposition (BCD) with swath-angle optimisation is the standard for agricultural fields (Höffmann et al., 2024). Fields2Cover provides an open implementation with heading search and Dubins turns (Mier et al., 2023), Mier et al. (2025) add continuous-curvature headland paths, and Hameed et al. (2016) compute 3D-terrain-equivalent spacing. None attaches a probability to complete coverage; the proposed method supplies the margin that such planners take as input.

*Robust and model-based margins.* Tube MPC (Mayne et al., 2005), Gaussian chance constraints with Rice's extreme-value correction (Rice, 1944), Gaussian-process cautious control (Hewing et al., 2020), Wasserstein distributionally robust CVaR (Mohajerin Esfahani and Kuhn, 2018) and the scenario approach (Campi and Garatti, 2008) bound tracking error by a model, a worst case or sampled constraints. Parametric models misrepresent the heavy, temporally clustered tail of RTK errors (Table 1), and worst-case sets are conservative.

*Conformal prediction.* Split conformal prediction and its training-conditional (PAC) variant (Vovk, 2012); conformal prediction under covariate shift and beyond exchangeability (Tibshirani et al., 2019; Barber et al., 2023); conformalized quantile regression (CQR; Romano et al., 2019); conformal risk control (Angelopoulos et al., 2024, 2025); hierarchical conformal prediction with one sample per group (Dunn et al., 2023); and functional conformal bands (Lei et al., 2015; Diquigiovanni et al., 2022), of which a sup-normalised coverage score is an instance. Conformal planning methods (Lindemann et al., 2023; Zhao et al., 2024; Sun et al., 2023; Wang and Ning, 2025) do not address a maximum over pass pairs that changes with the plan.

*Extremes of Gaussian processes.* The analytic model of Section 3.5 builds on Kac–Rice formulas and Rice's method (Azaïs and Wschebor, 2009; Piterbarg, 1996), maxima of stationary processes (Leadbetter et al., 1983) and statistical linearisation (Booton, 1954; Kazakov, 1956).

---

## 3. Materials and methods

### 3.1 Problem statement

**Fields, plans and margins.** A field is a polygon; its **main area** $W$ is the field inset by twice the implement width $w$, the remainder being headland. After decomposition and choice of the working direction $x$, a plan is a set of straight pass centrelines $y_1<\dots<y_K$. For a **margin** $\lambda\ge0$ the greedy planner $\pi(\lambda)$ places passes as if the footprint had half-width $w/2-\lambda$, so that adjacent planned footprints overlap by $2\lambda$; the number of passes $K(\lambda)$ does not decrease as $\lambda$ grows. The overlap ratio $J(\lambda)$ is the swath area within $W$ divided by the area of $W$, minus one; an overlap of 8% means that 8% of the main area receives a double dose.

**Execution.** Pass $k$ is driven with lateral offset $e_k(x)$, so its footprint at section $x$ is $[y_k+e_k(x)-w/2,\ y_k+e_k(x)+w/2]$ (Fig. 2). Offsets are random, correlated along and across passes (adjacent passes read the same GNSS error trajectory a pass duration apart), and their distribution depends on the plan through the terrain and time at which each pass is driven. Coverage is evaluated on 1 m sections across $W$.

**Objective.** Let $M(\lambda,e)$ be the missed area of $W$ when $\pi(\lambda)$ is executed with offsets $e$. The task is to choose the smallest overlap whose probability of a run without any missed strip is at least $1-\varepsilon$:
$$
\min_{\lambda}\ J(\lambda)\quad\text{s.t.}\quad \Pr\big[M(\lambda,e)=0\big]\ \ge\ 1-\varepsilon ,
$$
with $\varepsilon$ the tolerated probability of a run with any missed strip (here 0.1). The distribution of $e$ is unknown; what is available are logged runs. Section 3.6 relaxes the event to "no gap wider than a tolerance", and Section 4.5 asks for which costs of a miss the zero-miss objective is worth its overlap.

![](../../figures/paper/fig_schematic.png)

**Fig. 2.** The coverage problem. (a) One simulated run of the DGPS configuration (R3, 6 m implement) on a real paddy field, planned with that field's own 0.9 margin; the main area is inside the dashed line, and the missed strip (red, width exaggerated) is where two adjacent passes drifted apart by more than their planned overlap. (b) Detail of the framed area: planned centrelines (dashed), executed centrelines (solid) and footprint edges (dotted); the widest gap is 12 cm. (c) Cross-section at one along-pass position (schematic): footprints of width $w$ planned at spacing $w-2\lambda$; the chord $[\ell,u]$ is fully covered unless two executed centres are more than $w$ apart (interior gap) or the outermost centre is more than $w/2$ from the boundary (field-edge miss). The coverage score takes the worst of both over all sections (Section 3.3).

### 3.2 Overview of the proposed method

Conformal erosion turns logged runs into a margin in four steps (Fig. 1):

1. **Plan a reference plan.** A plan $\pi(\lambda_\mathrm{ref})$ with a generous margin $\lambda_\mathrm{ref}$ is generated with the user's planner. Runs are logged on this plan, or on the reference plans of other fields.
2. **Score each logged run.** From the executed implement track, each run is reduced to one coverage score $S$ (Section 3.3).
3. **Calibrate the margin.** The margin $\hat\lambda$ is an order statistic of the scores, chosen so that a new run exceeds it with probability at most $\varepsilon$. With field history the scores come from the field itself (Section 3.4); without, from one run on each of many other fields, divided by a model-predicted scale (Section 3.5).
4. **Plan and deploy.** The planner generates $\pi(\hat\lambda)$. A transfer check refuses the deployment if $\hat\lambda$ exceeds $\lambda_\mathrm{ref}$, because a plan with more passes than the calibrated one is not covered by the guarantee (Section 3.7).

Table 2 lists the variants. They share steps 1, 2 and 4 and differ in where the calibration scores come from and how they are scaled.

<!-- source: docs/paper/manuscript.md (method definitions) -->
| Variant | Calibration data | Score scale | Deployed plan | Guarantee on the deployed plan |
|---|---|---|---|---|
| CE | runs on the target field (pilot + certificate batch) | none | the reference plan itself | assumption-free (Appendix A.4) |
| CE-q | $n$ runs on the target field | none | $\pi(\hat\lambda)$, $\hat\lambda\le\lambda_\mathrm{ref}$ | under the coupling assumption (S), factor $\kappa$ (Section 3.7) |
| CE+ | $n$ runs on the target field + 5 training fields | probe-line XTE, gated | $\pi(t\,\sigma(z))$ | as CE-q; requires $t\sigma(z)\le\lambda_\mathrm{ref}$ |
| XCE-T / XCE-MC | one run on each of $n$ other fields, none on the target | model-predicted quantile (analytic model / Monte Carlo twin) | $\pi(\hat q_g v^\star)$ | score guarantee assumption-free; plan via (S) |

*Table 2. Variants of the proposed method. In the pre-registrations XCE-T is called CE-EVT-R.*

### 3.3 Step 2: the coverage score of a run

At section $x$ let $Y(x)$ be the executed centres of the passes relevant to the chord $[\ell(x),u(x)]$ of $W$, sorted. The chord is fully covered if and only if the largest of three distances is at most half the implement width:
$$
r^\star(x)=\max\Big\{\mathrm{dist}(\ell,Y),\ \mathrm{dist}(u,Y),\ \max_{i:\ (c_i+c_{i+1})/2\in[\ell,u]}\tfrac12(c_{i+1}-c_i)\Big\}\ \le\ \tfrac w2 .
$$
The first two terms are the field-edge terms (how far the outermost pass has receded from the boundary), the third the interior term (half the widest gap between adjacent passes). For a run of the reference plan $\pi(\lambda_\mathrm{ref})$ the **coverage score** is
$$
S=\lambda_\mathrm{ref}+\max_x\big(r^\star(x)-w/2\big).
$$
It is the margin that the executed run would have needed to leave no strip unworked: the run is miss-free if and only if $S\le\lambda_\mathrm{ref}$. Computing it requires only a sort of the executed centres in each 1 m section.

Two properties make this score the right input for calibration (proofs in Appendix A.1 and A.3). First, it decides complete coverage exactly, with no assumption on the error process. Second, it is the smallest score that never declares a run with a missed strip miss-free, so any calibration rule built on order statistics deploys no more passes with this score than with any other such score, including the per-pair or per-constraint maxima used by earlier conformal planners. On 6 fields × 200 runs the score reproduced the missed-area outcome on every run (Appendix A.3).

### 3.4 Step 3a: calibration on the field's own runs (CE, CE-q, CE+)

For $n$ calibration scores, the **marginal rule** takes the $k_\star$-th smallest score with $k_\star=\lceil(n+1)(1-\varepsilon)\rceil$; a new run then exceeds it with probability at most $\varepsilon$, on average over calibration data. The **PAC rule** takes the smallest $k_\star$ with $\mathrm{BinomCDF}(k_\star-1;n,1-\varepsilon)\ge1-\delta$, which makes the guarantee hold for the actual calibration data with probability at least $1-\delta$ (here $\delta=0.1$). If $k_\star>n$ there are too few runs and nothing is deployed: at $\varepsilon=\delta=0.1$ the marginal rule needs $n\ge9$ runs and the PAC rule $n\ge22$.

**CE.** CE iterates pilot batches, $\lambda_\mathrm{ref}\leftarrow1.10\,q$ with $q$ the $(1-\varepsilon)$ empirical quantile of pilot scores at $\pi(\lambda_\mathrm{ref})$, until $q\le\lambda_\mathrm{ref}$, freezes the plan, draws a fresh certificate batch, and deploys $\pi(\lambda_\mathrm{ref})$ itself if the certificate quantile $q^\star\le\lambda_\mathrm{ref}$ (refusing otherwise). Because the deployed plan is the one on which the runs were scored, no further assumption is needed.

**CE-q.** CE-q deploys $\pi(q^\star)$, which has no more passes than the reference plan and therefore less overlap; the guarantee carries over from the reference plan under the coupling assumption of Section 3.7.

**CE+.** CE+ fixes the budget at $n$ runs and adds two elements. (1) The reference margin comes from training fields only: $\lambda_\mathrm{ref}=1.25\times$ the largest $(1-\varepsilon)$ score quantile over five training fields. (2) Before the infield passes the machine drives one headland probe line; the autosteer's cross-track-error (XTE) RMS $z$ is a noisy reading of the day's roughness and slip. The normalised score is $\tilde S=S/\sigma(z)$ with $\sigma(z)=\max(a+bz,\ 0.3\,\bar\sigma)$, $(a,b)$ fitted on training fields after dividing each field's scores by its median ($\bar\sigma$ is the mean fitted scale), and a new operation deploys $\lambda=t\,\sigma(z_\mathrm{new})$ with $t$ the conformal quantile of the calibration $\tilde S_i$. The adaptive $\sigma$ is used only if it lowers the mean margin by at least 3% in leave-one-field-out cross-validation on the training fields; otherwise $\sigma$ is constant and CE+ equals CE-q with a training-field reference plan.

**Transfer check (revision).** CE+ must refuse when $t\,\sigma(z_\mathrm{new})>\lambda_\mathrm{ref}$ and fall back to CE, because the deployed plan would then have more passes than the calibrated one. The pre-registered runs did not include this check; Section 4.2 reports how often it would have triggered.

### 3.5 Step 3b: calibration across fields for fields without history (XCE)

A farm or contractor typically holds many fields with one or two logged operations each, and the new field has none. XCE calibrates across fields. For each field $f$ a **model scale** $\hat q_f$ predicts the $(1-\varepsilon)$ quantile of the coverage score on the field's reference plan from the controller settings, the terrain model and the GNSS grade, **without run data**. For calibration field $f_i$ with one logged score $S_i$, the ratio $V_i=S_i/\hat q_{f_i}$ is formed, $v^\star$ is the marginal or PAC order statistic of $\{V_i\}$, and the new field $g$ receives $\lambda_g=\hat q_g\,v^\star$. A field whose prediction fails ($\hat q_f$ not finite) gets $V_f=+\infty$; if this happens on the target field, nothing is deployed.

The model only decides how the scores of different fields are compared. If it is inaccurate, the margins become less tight but the guarantee is unaffected (Section 3.7). Any scale computed from field properties alone gives a valid method of the same form; the evaluation compares the model scale with raw pooling ($\hat q\equiv1$), per-configuration pooling (Mondrian conformal), a vendor-specification scale, a learned scale (CQR-type ridge regression; Romano et al., 2019) and an empirical per-configuration scale.

**Two implementations of the model scale.** *XCE-MC* takes the 0.9 quantile of 1000 Monte Carlo runs of the nominal closed-loop simulator (a digital twin) on the reference plan. *XCE-T* computes the same quantity analytically in five steps (Appendix B):

1. **Closed-loop covariance.** Linearised along the noise-free closed-loop path of each pass, with describing functions for steering saturation and rate limits and a leaky-integrator model of the anti-windup clamp, the offset of one pass is a Gaussian process given the run's operating condition (soil moisture, slip and roughness gains, roll compensation, mounting bias, GNSS error trajectory); its covariance follows from a time-varying Lyapunov recursion.
2. **Exceedance of one pass pair and of the field edges.** The probability that a gap between two passes exceeds a threshold anywhere along the pass is bounded by a discrete Kac–Rice upcrossing sum, and computed exactly by Gaussian Monte Carlo where that bound is loose. A field edge is missed only if every pass that covers it has receded, so its exceedance is a product of single-pass probabilities (Appendix A.12).
3. **Combination over pairs.** Given the condition, non-adjacent pairs are independent, and the probability of no exceedance is approximated by the product over pairs; this product was accurate in validation (0.888, 0.882 and 0.900 against a true 0.900; Table S5).
4. **Mixture over operating conditions**, by sampling 200 conditions.
5. **Scale law.** The required margin grows like $\sqrt{2\log L}$ in the effective length $L$ of the field (a tenfold larger field raises the margin by about 11%; normal extremes converge slowly, Hall, 1979); this heuristic is used only for a comparator scale.

Both implementations need the same inputs and neither uses logged runs. The ratio form was chosen over a probability-integral-transform scale, which failed in the first zero-data experiment because it amplifies errors in the far tail of the predicted distribution (Appendix B.4). Both rest on the simulator's own structure; Sections 4.1 and 4.4 discuss what this implies.

**Why the field-edge terms matter.** An interior gap $(e_{k+1}-e_k)/2$ is a difference of two passes, so error shared by adjacent passes cancels in it, and its standard deviation is $1/\sqrt2$ of that of one pass when the passes are independent. An edge term takes the full error of one pass. Edge terms therefore carry about $\sqrt2$ times the spread of interior terms even without shared error, and more when adjacent passes share part of the GNSS error (in the 1 Hz DGPS series, the correlation at the 13–113 s between adjacent passes at one section is 0.91–0.41; for RTK 0.71–0.54). They are needed for an unbiased prediction under DGPS, but in the simulations they were the binding term of a run in only about 1% (RTK) and 10% (DGPS) of runs, and with headland laps that overlap the main area in 0.1% and 1.9% (Section 4.4).

### 3.6 Tolerated gap width and the choice of $\varepsilon$

Many operations tolerate a narrow unworked strip (spread-pattern overlap of fertiliser spreaders, boom-end taper of sprayers). The calibrated event then becomes "no gap wider than $\tau$": an interior gap has width $2(r^\star-w/2)$ and an edge strip $r^\star-w/2$, so the score $S_\tau=S-\tau/2$ is valid for this event (conservative for edge strips), and the calibrated margin is $\hat\lambda-\tau/2$. The level $\varepsilon$ itself is an economic choice: Section 4.5 compares the expected cost of calibrated and practice margins as a function of the ratio $r$ of the cost of a missed unit area to the cost of an over-applied unit area.

### 3.7 What the method guarantees, and under which assumptions

The guarantee of each variant rests on stated assumptions; the formal statements and proofs are in Appendix A.

- **CE (deploying the calibrated plan).** If the logged runs and the new run of the field are exchangeable (drawn from the same conditions in random order), the marginal rule gives P(deploy and miss) $\le\varepsilon$ and the PAC rule bounds the miss probability given deployment. Nothing is assumed about the error process (Appendix A.4).
- **Calibrate on at least as many passes as will be deployed.** The coverage score is a maximum over pass pairs and edges, so a plan with more passes has a stochastically larger score. A threshold calibrated on the nominal plan $\pi(0)$, as earlier conformal planners do when applied to coverage, has no guarantee on a plan with more passes: with $K_0$ and $K_1>K_0$ i.i.d. pair scores its coverage is $(1-\varepsilon)^{K_1/K_0}<1-\varepsilon$ (Appendix A.6). The transfer check enforces this rule.
- **CE-q, CE+ and XCE (deploying fewer passes).** The guarantee carries over from the reference plan if the two plans can be coupled so that each gap or edge term of the deployed plan exceeds its counterpart on the reference plan by at most a noise-independent amount (assumption S). The miss level is then inflated by at most a factor $\kappa$, which is close to 1 on flat fields; (S) holds exactly for a linear closed loop and approximately for the simulator. In development checks the predicted coverage after a plan change was 0.901, 0.890 and 0.920 against simulated 0.899, 0.885 and 0.922 (Table S5; Appendix A.15).
- **XCE (calibrating across fields).** If the fields are exchangeable (i.i.d. for the PAC rule), each calibration field contributes one run at its reference plan, and the model scale depends only on field properties, then the score guarantee holds whatever the accuracy of the model (Appendix A.17). This is the two-layer setting of Dunn et al. (2023) with one sample per group. The guarantee averages over which fields were calibrated and over their single logged runs. For one fixed set of logged runs, the mean coverage on new fields is one draw of $\mathrm{Beta}(k_\star,n+1-k_\star)$ (standard deviation 0.054 for $n=29$, $k_\star=27$), so a single realisation well below $1-\varepsilon$ does not contradict the guarantee. It is also an average over fields, not a statement per field or per machine; Section 4.3 reports coverage per configuration.
- **What no scale can remove.** Even with an ideal scale (each field's own requirement), the margin of a new field is inflated by a within-field tail ratio set by $n$ and the PAC rule; this is why, within one machine configuration, all field-level scales perform within a few tenths of a point of each other (Appendix A.20; Section 4.3).

**Computational cost.** CE and CE+ add only the score evaluation and an order statistic to a standard planner. The model scale is computed once per field and reference plan, offline: XCE-T took 133–187 s per field in R1, 287–353 s in R2 and 16–51 s in R3 on one core (three fields per regime; Table S21), and XCE-MC with 1000 runs a median of 8–21 s (wall time on a shared four-core machine).

### 3.8 Simulation study

**Data.** All inputs are public. Field boundaries and working directions come from 250 combine-harvester GNSS trajectories of the field–road trajectory dataset of the national agricultural machinery operation platform of China (Wu et al., 2023); density-based clustering extracts 964 fields, of which 137 paddy fields (hilly south of China) and 162 wheat fields (North China Plain) are used. Terrain comes from Copernicus GLO-30 elevation windows (European Space Agency, 2021). GNSS error comes from 12 NOAA CORS station pairs (baselines 5–30 km, in agricultural regions of the US Midwest and Great Plains), 8 days each across four seasons of 2024–2025, processed with RTKLIB (Takasu and Yasuda, 2009) in its demo5 fork (Everett, n.d.) as a moving rover against the reference coordinates at four receiver grades (Table 1). The 30 s epochs are interpolated to 1 Hz and high-frequency residuals of a vehicle GNSS/INS record (Tang et al., 2022) are added. Each simulated run draws a station-pair-day and a start time.

<!-- source: results/table_gnss.txt (scripts/table_gnss.py) -->
| Grade | Processing | RMS | 95% | 99.9% | Max |
|---|---|---|---|---|---|
| RTK | carrier phase, continuous ambiguity resolution (84% of epochs fixed, 16% float) | 2.4 cm | 3.3 cm | 24.5 cm | 1.39 m |
| RTK float | carrier phase, no ambiguity resolution | 2.6 cm | 4.0 cm | 24.6 cm | 1.39 m |
| DGPS | code differential | 32.5 cm | 57.8 cm | 2.05 m | 6.05 m |
| Single point | L1 code | 1.51 m | 2.78 m | 4.97 m | 7.16 m |

*Table 1. Horizontal error of the processed CORS series (96 station-pair-days per grade, 30 s epochs, first 30 min of each day removed). The RTK tail comes from wrong fixes and float drift lasting minutes; a Gaussian with the same RMS underestimates it by orders of magnitude. Static geodetic antennas lack vehicle multipath, canopy masking and correction-link outages, and the stations are in the US while the fields are in China; Section 4.4 therefore also tests a degraded-GNSS variant.*

**Simulator.** A closed-loop simulator (time step 0.05 s, speed 2 m/s) integrates kinematic steering with a first-order steering lag of 0.25 s, 35° saturation and a 30°/s rate limit; terrain slip proportional to the lateral gradient plus Ornstein–Uhlenbeck roughness, both scaled by per-run soil moisture; a 2.6 m antenna with roll compensation $0.85\pm0.05$; a per-run mounting bias (standard deviation 1.5 cm); and GNSS error projected on the lateral axis. Passes are executed in real time order with headland turns, so adjacent passes read the same error series one pass duration apart. The default controller is LQR with integral action (LQR-I); pure pursuit, Stanley, a slip observer (Lenain et al., 2006) and offset-free MPC (Pannocchia and Rawlings, 2003) are alternatives. The footprint is centred on the vehicle reference point (a rigidly mounted implement); Section 4.4 tests a trailed implement. Details are in Appendix C.

<!-- source: experiments/exp_system.py (REGIMES) -->
| Configuration | Fields | GNSS grade | Width $w$ | Soil moisture | Vendor pass-to-pass |
|---|---|---|---|---|---|
| R1 RTK, flat, 3 m | wheat (plain) | RTK | 3 m | Beta(2, 3) | 2.5 cm |
| R2 RTK, hilly-wet, 1.5 m | paddy (hilly) | RTK | 1.5 m | 0.6–0.9 | 2.5 cm |
| R3 DGPS, hilly, 6 m | paddy (hilly) | DGPS | 6 m | Beta(2, 3) | 20 cm |

*Table 3. Machine configurations (one implement width, GNSS grade and controller each). The mixed fleet of Section 4.3 pools all three. Paddy slopes come from the 30 m elevation model, which does not resolve levelled basins; Section 4.4 tests levelled terrain.*

**Metrics.**

- *P(no miss)*: fraction of test runs with zero missed area, pooled over fields (the run-level coverage).
- *Meet rate*: fraction of fields whose P(no miss) over 200 test runs is not significantly below 0.9 (one-sided binomial test at 0.05; a correctly calibrated marginal method meets it on about 85% of fields, a PAC method on about 99%; Appendix A.19).
- *Overlap*: main-area overlap ratio $J$ of the deployed plan; *applied overlap* additionally counts swath reaching into the headland.
- *Missed area*: mean fraction of the main area left unworked.
- *Regret / excess overlap*: overlap minus that of the field's **oracle** plan, the smallest margin whose own P(no miss) is 0.9 on test-distribution runs, in percentage points (pp). The oracle uses test runs and is a reference point, not an attainable method: a method can fall below it on a field by chance.

**Experiments.** Fields are ordered once with a fixed seed and split by index so that each confirmatory experiment uses fields not used by the analyses that designed it (Appendix C.2). The experiments, with their repository names, are:

- *Experiment A, fields with operation history*: A1, a pre-registered comparison on 90 fresh fields (repository "v8"); A2, calibration with few runs (revision, pre-registered).
- *Experiment B, fields without history*: B1–B3, three pre-registered zero-data experiments ("E-low v1–v3"); B4, a pre-registered check of the guarantee over random field splits and redrawn logged runs; B5, configuration-aware baselines and per-configuration coverage (revision, pre-registered).
- *Experiment C, robustness*: C1, model mismatch; C2, headland laps (revision, pre-registered).
- *Cost analysis* (descriptive).

Pre-registrations were committed before the corresponding computations (Supplementary Table S20 lists the status of every result). All registered zero-data experiments used the extreme-value model without the field-edge terms; validity is unaffected, and Section 4.1 reports what the edge terms change.

## 4. Results

### 4.1 How accurate is the model scale?

Fig. 3 compares the predicted 0.9 quantile of the coverage score on each field's reference plan with the empirical 0.9 quantile of 200 independent simulated runs, on the 45 test fields of each configuration. The 200-run reference quantile is itself noisy; the Monte Carlo twin with 1000 fresh runs differs from it by a log standard deviation of 0.030 (R1), 0.032 (R2) and 0.083 (R3), which is essentially this sampling noise. The analytic model differs from it by 0.039, 0.038 and 0.107, with mean bias +1.0%, +0.1% and +0.9%; its own error, net of the reference noise, is therefore about 2–3% under RTK. Under DGPS, the model without field-edge terms was biased low (−5.2%, log standard deviation 0.097, on the same 45 fields). The edge terms (Appendix A.12) were derived after this observation on 15 fields and then computed, unchanged, on the remaining 30 (revision, pre-registered as a descriptive check): on these 30 they moved the bias from −5.7% to +0.9% but widened the scatter from 0.089 to 0.106 (Appendix B.3), so they correct the level of the DGPS margins, not their field-to-field ranking. The analytic model needs 16–353 s per field without and a median of 271 s (up to 40 min) with the edge terms, and the twin a median of 8–21 s (Table S21), all once per field and offline.

These checks verify the model against the simulator it was built from. The model calls the noise-free simulator for the mean path and samples operating conditions from the simulator's own distribution, and its refinements were introduced because earlier checks against the same simulator failed (Appendix B.1). Fig. 3 therefore shows internal consistency, not realism; Section 4.4 asks what happens when the simulated reality differs from the model.

![](../../figures/paper/fig_theory_vs_sim.png)

**Fig. 3.** Predicted versus simulated 0.9 quantile of the coverage score (m, log–log), one point per field, 45 fields per configuration. (a) Analytic extreme-value model (R3 with field-edge terms); (b) Monte Carlo twin (1000 runs of the nominal simulator). The simulated value is the empirical 0.9 quantile of 200 independent runs; the shaded band is ±10%.


### 4.2 Experiment A: fields with operation history

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

**Fig. 4.** Regret (overlap above the per-field oracle, pp) in Experiment A1 for the marginal (a) and PAC (b) guarantee classes; bars are means over 30 fields with 95% intervals, and numbers above bars are pooled P(no miss).

*What the gain is made of.* All compared methods deploy plans from the same family $\pi(\lambda)$ and differ only in how $\lambda$ is chosen, so at equal realised coverage they would deploy the same plan. The gain is calibration tightness: the comparators calibrate pair or per-constraint scores on the nominal plan or through a union bound and over-cover (P 0.92–0.99 at a nominal 0.9), which is what their extra overlap buys; CE+ reaches its target (Fig. 4). Most of the gain comes from the exact score and the reference plan, not from the probe-line normalisation: CE-q, which has neither the normalisation nor the training-field reference plan, reached 8.82%, 25.51% and 16.19% overlap in R1–R3 against 10.35%, 26.72% and 20.63% for CPrP. Measured as regret, CE+ was 27–95% below the comparators in the cells where its regret is positive. The applied overlap including the headland gave the same direction in all 12 comparisons (reductions 2.8–29.3%, all Holm-significant; Table S22).

*Transfer check.* The transfer argument needs the deployed margin to be at most the reference margin. In R1 and R2 this held on every field. In R3 the mean deployed CE+ margin exceeded $\lambda_\mathrm{ref}$ on 9 of 30 fields (marginal) and 19 of 30 (PAC); on those fields the guarantee rests on no theorem, although the measured coverage held (pooled P 0.896 and 0.933, meet rate 0.90 and 1.00). With the transfer check of Section 3.4, these fields fall back to the assumption-free CE, which in R3 deployed 17.77% overlap at P 0.928.

*Other stacks.* On six planner–controller stacks, CE and CE+ met their design meet rates except CE+ on follow-previous-pass guidance in R2 (P 0.850, meet rate 0.70), where steering each pass relative to the previous executed pass couples passes and violates the transfer assumption; the assumption-free CE met its target there (Table S23).

*Practice rules.* The vendor rule (twice the nominal pass-to-pass accuracy) missed some strip on almost every run, but only 0.22%, 0.64% and 0.12% of the main area. The farmer-tuned margin met the target on 70%, 20% and 47% of fields, with 0.8 pp more overlap than CE+ in R1 and 2.6 and 2.2 pp less in R2 and R3. Whether CE+'s extra reliability is worth its overlap is a question of cost (Section 4.5).

**A2, few runs per field (revision, pre-registered).** A2 replaces the 100 calibration runs by $n=9$–100 runs drawn from 200-run banks on 45 fields per configuration (2000 replicates per field; CE-q, the variant CE+ reduces to under constant normalisation; deployed plans evaluated on independent test runs). Both registered predictions were met: marginal mean coverage was 0.896–0.943, never below 0.895, and in line with the exact value $k_\star/(n+1)$ (0.900, 0.938, 0.913, 0.902, 0.901 for $n=9$, 15, 22, 40, 100); the PAC fraction of replicates with coverage at least 0.9 was 0.890–0.951 against a required 0.88 (Table S24). The price of few runs is overlap. With 9 runs the marginal rule cost 1.3, 4.0 and 8.3 pp above the oracle in R1–R3; the PAC rule needs at least 22 runs and then cost 3.4, 10.0 and 18.7 pp, falling to 1.1, 3.2 and 4.3 pp with 100 runs. With fewer than about 20 logged operations per field, cross-field calibration (Experiment B) is the practical route.

### 4.3 Experiment B: fields without operation history

**B1–B3, pre-registered zero-data experiments.** Three experiments were registered in sequence, each designed from the previous one's results and run on fields that no earlier zero-data analysis had used (Table 5; details in Supplementary D.3–D.6).

<!-- source: results/lowdata/summary.txt; results/lowdata_v2/summary.txt; results/lowdata_v2/matched_coverage.txt; results/lowdata_v3/summary.txt -->
| Experiment | Method; test fields; $n$ | Registered claims | Outcome |
|---|---|---|---|
| B1 | probability-integral-transform scale; 148 fields; 30 | valid and ≥ 10% less excess overlap than the strongest valid comparator, every configuration | **Not met** in R1–R3 (+5.35, +3.98, +5.70 pp vs +3.22, +3.26, +1.31 pp) |
| B2 | XCE-T; 90 fields; 29 | C1: R1 PAC, and C2: R3 marginal, ≥ 10% better than raw pooling | **Both met** (Holm p 0.0002, 0.0012), but mostly through realised coverage at one calibration draw: at matched coverage all scales of a configuration lay within 0.42 pp |
| B3 | XCE-T and a gated variant; 45 fields + mixed fleet; 25 | C3: mixed fleet, ≥ 10% better than every comparator, both classes; C4: gated variant never worse than the best comparator | **Partly met.** C3: 5 of 8 comparisons met; C4: 1 of 6 cells |

*Table 5. The pre-registered zero-data sequence (all with the model without field-edge terms). Excess overlap is the deployed overlap minus the per-field oracle overlap.*

B1 failed because the probability-integral-transform scale amplifies tail errors (Appendix B.4). B2 met both claims, but at matched coverage all scales of a configuration lay within a few tenths of a point, so B2 does not show that the model scale is more efficient within one configuration. In B3, XCE-T in R1 (marginal) realised 0.877 against its registered criterion of 0.89, over subsets drawn from one fixed set of logged runs; B4 tests whether such values are draws of the calibration data.

**B4, does the guarantee hold? (pre-registered).** B4 redrew both the calibration fields (25 of 45 per configuration, or of 135 in the mixed fleet) and each calibration field's logged run (from a bank of 200 independent runs), 4000 times per scenario, scale and rule. All 26 cells met their criteria (Table S19a, Fig. S1); the observed marginal means (0.919–0.929), marginal fractions with coverage ≥ 0.9 (0.689–0.767) and PAC fractions (0.911–0.949) agree with their exact targets of 0.923, 0.729 and 0.928. The sub-0.9 values of B2 (0.844) and B3 (0.877) are therefore draws of the calibration data. B4 cannot detect a failure of exchangeability, because it splits a fixed set of fields at random.

**B5, configuration-aware baselines and per-configuration coverage (revision, pre-registered).** The mixed fleet pools three machine configurations. The registered B3 and B4 compared the model scale mainly with configuration-blind pooling, which a contractor would not use. B5 adds per-configuration (Mondrian) pooling, an empirical per-configuration scale, a configuration-aware learned scale (CQR, trained on separate fields) and the Monte Carlo twin, and reports coverage per configuration (Table 6, Fig. 5).

<!-- source: results/revision/rv2_resampling_edges45.txt -->
| Pivot | $n=25$: coverage R1 / R2 / R3 (marginal) | $n=25$ excess, marginal / PAC | $n=60$ excess, marginal / PAC |
|---|---|---|---|
| Raw pooling | 0.999 / 0.998 / **0.779** | +29.19 / +63.97 | +17.12 / +37.98 |
| Spec. × scale law | 0.944 / **0.840** / 0.993 | +12.95 / +23.09 | +9.93 / +14.98 |
| Mondrian (per configuration) | 0.958 / 0.960 / 0.957 | refuses on 56% / 100% of fields | +4.35 / refuses on 74% |
| Per-configuration scale | 0.939 / 0.958 / 0.842 | +4.57 / +19.94 | +1.29 / +6.42 |
| CQR (configuration-aware) | 0.961 / 0.942 / 0.866 | +4.09 / +18.86 | +1.20 / +6.19 |
| **XCE-T** (analytic model) | 0.931 / 0.936 / 0.904 | **+2.89** / +14.56 | **+0.57** / +4.37 |
| **XCE-T** with field-edge terms | 0.927 / 0.931 / 0.917 | +3.03 / **+13.69** | +0.63 / +4.36 |
| **XCE-MC** (Monte Carlo twin) | 0.924 / 0.929 / 0.913 | **+2.68** / **+13.76** | **+0.55** / **+4.19** |

*Table 6. Experiment B5 (revision, pre-registered): mixed fleet of 135 fields, 4000 replicates. Overall validity held for every non-refusing scale (marginal mean coverage 0.896–0.925; PAC fraction 0.892–0.955). Per-configuration coverage is not guaranteed by the theorem; values below 0.88 are in bold. Mondrian excess is over deployed fields; refused fields need another rule. XCE-T without field-edge terms is the registered scale; the row with edge terms uses them on all 45 DGPS fields.*

All four registered predictions were met (Table 6, Fig. 5). Every non-refusing scale was valid overall. Raw pooling covered the DGPS configuration at only 0.779 (marginal) while over-covering the RTK fields at 0.999: the overall guarantee averages over configurations and can hide a badly served one. The model scales covered every configuration at 0.885–0.936; with the field-edge terms the DGPS fields were covered at 0.899–0.924 instead of 0.834–0.904 (Table S26), at the same excess overlap. Mondrian pooling, valid per configuration, needs at least 9 (marginal) or 22 (PAC) calibration fields per configuration; with 25 calibration fields shared by three configurations it refused on 56% of new fields (marginal) and on all (PAC). With 60 calibration fields, the model scales cost 0.55–0.63 pp of excess overlap (marginal) against 1.20–1.29 pp for the learned and empirical configuration-aware scales and 4.35 pp for Mondrian, and 4.2–4.4 pp (PAC) against 6.2–6.4 and 12.2 pp. The configuration-aware scales left the DGPS fields under-covered (0.82–0.87), because a scale learned from one run per field does not capture the heavier DGPS tail. The analytic model and the Monte Carlo twin were equivalent (within 0.8 pp in every cell).

![](../../figures/paper/fig_mixed_fleet.png)

**Fig. 5.** Experiment B5: mean excess overlap of the scales on the mixed fleet with 60 calibration fields (XCE-T with the field-edge terms), marginal (a) and PAC (b) rule (excess over deployed fields; a pale bar marks a scale that refuses on part of the fields), and mean coverage of the DGPS fields under the marginal rule with 25 calibration fields (c; dashed line 0.9).

**B6, model accuracy against learned predictors (post hoc).** Trained on the one run per field that this setting provides, cross-validated ridge regression and gradient boosting on field features did not reach the model's accuracy within the available pools (standard deviation of log(prediction / $\lambda^\star_f$) at the largest pool: 0.070 and 0.109 vs 0.029 in R1; 0.043 and 0.049 vs 0.029 in R2; 0.148 and 0.190 vs 0.056 in R3; Table S25). A feature correction of the model with a cross-validated penalty matched the model in R2 (0.029) and did not improve on it elsewhere. Trained on oracle targets, which need hundreds of runs per field, ridge regression beat the model under RTK (0.021 in R1 and R2) but not under DGPS (0.079). The Monte Carlo twin with 1000 runs was slightly more accurate than the analytic model (0.025, 0.026, 0.047), as expected for an exact simulation of the same model.

### 4.4 Experiment C: robustness

**C1, model mismatch (revision, pre-registered).** Six "truth" variants change the simulated reality while the model scales, the Monte Carlo twin and all fixed scales keep the nominal model: T1 intermittent wet patches with heavy-tailed slip pulses; T2 a trailed implement (hitch length 5 m, downhill crab); T3 per-run speed 1.5–3.0 m/s with 0.15 s steering latency and a 0.3° deadband; T4 GNSS error 1.5 times larger; T5 terrain gradients reduced to a quarter (levelled basins); T6 the combination T1–T4. For every field and variant, 200 calibration runs and a 28-point margin curve were simulated from the truth.

Table 7 shows the result. **Validity.** The score-level guarantee does not involve the model, and all scales remained valid overall in five of six variants. In T1, which adds heavy-tailed slip pulses that roughly double the RTK margin, the overall marginal coverage of every scale fell to 0.892–0.895 with 60 calibration fields (criterion 0.895; exact expectation 0.902), and target-field CE-q with 100 runs reached 0.893 (R1) and 0.891 (R2). The cause is the transfer step, not the conformal step: the reference margin had been set from nominal training fields, and in T1 the deployed RTK margin exceeded it on 91–100% of fields, so the deployed plan had more passes than the calibrated one (Section 3.7). The transfer check of Section 3.4 would have refused these deployments; a reference margin set from data of the actual configuration avoids them. **Model accuracy.** Mismatch that rescales the error moderately left the model useful: with a trailed implement (bias +0.42, the implement low-pass filters the tractor's error), degraded GNSS (−0.35 under DGPS) or levelled terrain, the model scale remained the most efficient scale of the mixed fleet (0.5–0.7 pp against 3.8–42.7 pp for the others). Mismatch that changes the error structure did not: with wet patches the model underpredicted RTK margins by a factor of 2 (bias −0.73), and with a faster vehicle, steering latency and a deadband the DGPS loop became unstable and the model underpredicted by a factor of 2.7; in the combined variant the vendor-specification scale was more efficient than the model (8.7 vs 14.1 pp). The Monte Carlo twin, which shares the model's assumptions, failed in the same cases. **Per-configuration coverage.** Whenever the mismatch affected one configuration more than the others (T2, T3, T4, T6), the model scale no longer equalised coverage across configurations, and the DGPS fields were covered at 0.78–0.85, better than raw pooling (0.71–0.80) but below target. None of the four registered predictions was met in every variant: P4.1 (overall validity) and P4.4 (CE-q validity) failed in T1 only, P4.2 (model log-error standard deviation below 0.15) failed in T1, T3 and T6, P4.3 (model scale excess below half of raw pooling and below the specification scale, 25 calibration fields) held in T2, T4 and T5 only (Table S27).

<!-- source: results/revision/rv4_mismatch_edges45.txt; results/revision/rv2_resampling_edges45.txt; results/revision/rv3_small_n.txt -->
| Truth | Model bias $\log(\hat q/q)$, R1 / R2 / R3 | XCE-T coverage: all / DGPS (raw pooling DGPS) | Excess pp: XCE-T / XCE-MC / spec. × scale / Mondrian / raw | CE-q ($n=100$) coverage R1 / R2 / R3 |
|---|---|---|---|---|
| Nominal | +0.01 / +0.00 / +0.01 | 0.902 / 0.899 (0.718) | 0.63 / 0.55 / 9.93 / 4.35 / 17.12 | 0.896 / 0.909 / 0.898 |
| T1 wet patches | −0.73 / −0.72 / −0.02 | **0.895** / 0.984 (0.823) | 2.39 / 1.77 / 45.53 / 23.49 / 7.81 | **0.893 / 0.891** / 0.897 |
| T2 trailed implement | +0.42 / +0.43 / +0.09 | 0.903 / **0.808** (0.716) | 0.49 / 0.52 / 3.93 / 3.81 / 17.86 | 0.900 / 0.903 / 0.902 |
| T3 speed, latency | +0.00 / +0.01 / −0.99 | 0.903 / 0.853 (0.801) | (R3 under-covered) | 0.899 / 0.899 / 0.924 |
| T4 GNSS × 1.5 | −0.04 / −0.02 / −0.35 | 0.901 / **0.803** (0.711) | 0.69 / 0.75 / 7.66 / 6.99 / 42.73 | 0.896 / 0.902 / 0.897 |
| T5 levelled terrain | −0.01 / +0.01 / +0.02 | 0.902 / 0.908 (0.717) | 0.56 / 0.47 / 9.99 / 3.98 / 16.47 | 0.904 / 0.899 / 0.904 |
| T6 combined | −0.48 / −0.45 / −1.82 | 0.905 / **0.780** (0.753) | 14.09 / 12.33 / 8.71 / 51.01 / 58.34 | 0.908 / 0.899 / 0.949 |

*Table 7. Experiment C1 (revision, pre-registered). Model bias: mean log ratio of the nominal-model quantile (analytic model with edge terms) to the truth quantile, 45 fields per configuration. Coverage and excess: mixed fleet, marginal rule, 60 calibration fields, 2000 replicates; DGPS coverage is the mean over the DGPS target fields. CE-q: mean coverage over 500 replicates per field. XCE-T uses the field-edge terms. Bold: below 0.895 overall, or below 0.85 for one configuration. In T3 the DGPS configuration is under-covered and excess overlap below the oracle is not an efficiency gain. Nominal row: Experiments B5 and A2.*

**C2, headland laps (revision, pre-registered).** The main experiments evaluate the main-area boundary as a hard edge reached only by the outermost pass. C2 adds one headland lap along each side, planned to overlap the main area by $\lambda$ and driven after the infield passes. Even with the hard edge, a boundary term was the binding term of a run in only 1.0% (R1), 0.8% (R2) and 10.0% (R3) of runs at the reference plan; with laps these fell to 0.1%, 0.1% and 1.9%. Laps left the required margin unchanged under RTK and lowered it by about 6% under DGPS (oracle margin 0.391 → 0.366 m; main-area overlap 15.12% → 14.01%). Both registered predictions were met: the boundary share under DGPS fell below 50%, and target-field calibration remained valid with laps (marginal mean coverage 0.897–0.902; PAC fraction 0.885–0.907; Table S28). The field-edge terms therefore matter for an accurate DGPS prediction under a hard edge, but they do not dominate the miss probability, and where headland laps overlap the main area they lose most of their weight.

### 4.5 What a certified margin costs

The certified event "no strip missed with probability 0.9" counts a 1 cm sliver like a 1 m strip. Whether it is worth its overlap depends on what a miss costs. Let $r$ be the cost of leaving one unit of area unworked divided by the cost of over-applying one unit of area (for an input-saving operation, the value of the yield or control lost on a missed strip divided by the input cost per unit area). The expected cost of a margin, in percent of the main area, is then overlap $+\ r\times$ missed area. Table 8 and Fig. 6 evaluate it on the margin curves of the 45 test fields of each configuration (nominal model, descriptive).

<!-- source: results/revision/rv_cost.txt -->
| Config. | Policy | P(no miss) | Overlap % | Missed % | Cost, $r=10$ | $r=30$ | $r=100$ | $r=300$ |
|---|---|---|---|---|---|---|---|---|
| R1 | vendor rule | 0.000 | 2.12 | 0.160 | 3.72 | 6.92 | 18.10 | 50.04 |
| | farmer-tuned | 0.882 | 9.05 | 0.001 | 9.06 | 9.07 | 9.11 | 9.24 |
| | certified, $\varepsilon=0.1$ (ideal) | 0.900 | 8.91 | 0.001 | 8.92 | 8.93 | 8.98 | 9.11 |
| | cost-optimal margin | 0.02–0.50 | 2.5–6.0 | | **3.54** | **4.69** | **5.92** | **7.10** |
| R2 | vendor rule | 0.000 | 5.38 | 0.336 | 8.74 | 15.45 | 38.95 | 106.09 |
| | farmer-tuned | 0.844 | 23.02 | 0.001 | 23.03 | 23.05 | 23.11 | 23.30 |
| | certified, $\varepsilon=0.1$ (ideal) | 0.900 | 24.93 | 0.001 | 24.94 | 24.95 | 24.99 | 25.11 |
| | cost-optimal margin | 0.00–0.32 | 5.9–15.0 | | **8.58** | **11.58** | **14.78** | **17.75** |
| R3 | vendor rule | 0.437 | 7.56 | 0.112 | 8.68 | 10.91 | 18.73 | 41.07 |
| | farmer-tuned | 0.853 | 13.35 | 0.033 | 13.68 | 14.33 | 16.62 | 23.16 |
| | certified, $\varepsilon=0.1$ (ideal) | 0.900 | 15.10 | 0.026 | 15.36 | 15.88 | 17.69 | 22.87 |
| | cost-optimal margin | 0.21–0.89 | 4.6–14.4 | | **7.15** | **10.31** | **15.21** | **21.90** |

*Table 8. Expected cost (overlap % + $r$ × missed-area %) of practice and certified margins (descriptive). "Certified (ideal)" is each field's own 0.9 margin, the target of an exactly calibrated certificate; the cost-optimal margin minimises the expected cost per field given the test distribution and is a reference, not a method.*

![](../../figures/paper/fig_cost.png)

**Fig. 6.** Expected cost (overlap % + $r$ × missed-area %) against the cost ratio $r$ of a missed to an over-applied unit area (both axes logarithmic), for the vendor rule, the farmer-tuned margin, the certified margin at $\varepsilon=0.1$ (each field's own 0.9 margin) and the cost-optimal margin (a reference that requires the test distribution); means over the test fields of each configuration (a–c). The vertical line marks where the certified margin becomes cheaper than the vendor rule.

Three conclusions follow. First, against the vendor rule, the certified margin pays off only above a break-even ratio of $r^\star\approx43$ (R1), 58 (R2) and 88 (R3); with the per-operation results of Experiment A1 the break-even values are 31–35 (RTK) and 88–117 (DGPS). Second, the cost-optimal margin under RTK accepts frequent but tiny misses: even at $r=300$ it has a P(no miss) of only 0.50 (R1) and 0.32 (R2), because RTK misses are slivers of 0.004–0.03% of the area. Only under DGPS, whose misses are wider, does the cost-optimal margin approach the 0.9 level ($r=300$: 0.89). Third, a tolerance helps where implements are narrow: certifying "no gap wider than 2 cm" instead of "no gap" lowers the margin by 1 cm and saves 0.9, 2.0 and 0.4 pp of overlap in R1–R3, and a 5 cm tolerance saves 2.0, 5.0 and 1.1 pp.

The value of $r$ depends on the operation, crop and prices and is not estimated here. As an illustration only, a fertiliser strip whose omission loses a third of a crop worth five times the fertiliser cost gives $r\approx1.7$, while a missed strip that triggers a regulatory, quarantine or resistance-management cost can give $r$ in the hundreds. Below the break-even, a zero-miss margin at $\varepsilon=0.1$ costs more than the vendor rule; the calibration then still states the miss probability of a cheaper margin (the same data bound $P(S>\lambda)$ for every $\lambda$), and $\varepsilon$ and $\tau$ can be chosen by cost. Conformal risk control of the expected missed area (Angelopoulos et al., 2024) would target cost directly, but its finite-sample term $B/(n+1)$, with $B$ the largest possible loss, exceeds the relevant missed-area levels (0.01–0.1%) unless thousands of runs are available.

---

## 5. Discussion

### 5.1 What is guaranteed, and by what

Three layers of the method rest on different assumptions. (i) The coverage score is exact and the smallest valid score, with no assumption (Section 3.3). (ii) The conformal quantile of the score on the reference plan is distribution-free given exchangeable runs (target-field calibration) or exchangeable fields (cross-field calibration); only CE deploys that plan itself and is assumption-free. (iii) Deploying a plan with fewer passes than the reference plan (CE-q, CE+, XCE) needs the transfer assumption (S) and costs a factor $\kappa$; the measured coverage of such plans was at or above the target whenever the deployed margin stayed below the reference margin (Experiments A2, B4, B5, C2); when it did not, coverage fell slightly below target (0.891–0.895 in the wet-patch variant of C1), which the transfer check of Section 3.4 prevents. The extreme-value model and the Monte Carlo twin affect only efficiency. The guarantee for cross-field calibration averages over fields: with configuration-blind pooling the DGPS fields of a mixed fleet were covered at 0.78 while the RTK fields were over-covered, so per-configuration coverage must be checked, and a model scale achieved it (0.89–0.94).

### 5.2 Where the method helps

*With target-field data*, the exact score and the reference plan give tight calibration: CE+ reached its target while two conformal planners over-covered at 4–55% more overlap. The gain over well-calibrated practice is small: the farmer-tuned margin was within a few tenths of a point in R1 and below CE+ in R2 and R3, at lower reliability. *Without target-field data*, a model scale is the only configuration-aware scale that covered every configuration and was efficient: across a mixed fleet it cost 0.6 pp above the per-field optimum (marginal, 60 calibration fields) against 1.2–4.4 pp for configuration-aware baselines and 17 pp for pooling, and per-configuration pooling could not deploy at all under the PAC rule with 25 calibration fields. The analytic model and the Monte Carlo twin were equally good; the twin is simpler to build when a simulator exists, and the analytic model explains the scaling of margins with field size, the role of the field edges, and the information limit.

### 5.3 Where it does not help

Within one machine configuration, all field-level scales, including the ideal one, perform within a few tenths of a point at matched coverage (Experiments B2–B3), because the remaining inflation is set by run-to-run randomness (Section 3.7). The PAC rule with few runs is expensive (3–19 pp above the optimum at $n=22$). And a zero-miss margin at $\varepsilon=0.1$ is not cost-optimal for RTK guidance unless a missed unit costs several hundred times an over-applied one (Section 4.5); for most input-saving operations a tolerance or a larger $\varepsilon$ is the better choice, which the same calibration supports.

### 5.4 Limitations

1. **Simulation only.** Field boundaries, terrain and GNSS errors are real; execution is simulated, with a kinematic vehicle, a rigidly mounted implement in the main experiments, one speed, static US CORS errors applied to Chinese fields, and terrain slopes from a 30 m model. Experiment C1 shows that the guarantee largely survives misspecification while the model's efficiency survives only mismatch that rescales the error; heavy-tailed slip, loop instability or a combination of effects made the model scale no better than simple scales. None of this replaces field data.
2. **Ground truth.** Field validation on an autonomous feed-spreading vehicle with lidar–inertial localisation is in preparation (logging and certification tools are in the repository). The coverage score needs the true implement position. A guidance receiver cannot see its own GNSS error, so calibration runs need an independent reference (for example a PPK rover on the implement); machine logs alone are not sufficient.
3. **Transfer assumption.** CE-q, CE+ and XCE deploy plans other than the reference plan and rely on (S); guidance that couples passes (follow-previous-pass) violated it.
4. **Exchangeability.** Cross-field calibration assumes that calibration and new fields come from one population; a new configuration or field type needs its own calibration fields. Fields worked on the same day share GNSS conditions, which the experiments did not model.
5. **Objective.** The zero-miss event ignores the size of a miss; Section 4.5 quantifies when this matters.

### 5.5 Practical guidance

- Decide the cost ratio $r$ of the operation first. Below a ratio of about 30–100 (RTK–DGPS in these simulations), a zero-miss margin at $\varepsilon=0.1$ costs more than the vendor rule; use a gap tolerance $\tau$ or a larger $\varepsilon$, and use the calibration to state the miss probability of the margin chosen.
- Record the coverage score (covering radius per section, including the field edges) from runs with independent ground truth; it is the tightest valid score.
- Calibrate on a plan with at least as many passes as will be deployed, never on the zero-margin plan; refuse or fall back to CE if the deployed margin exceeds the reference margin.
- With at least 9 (marginal) or 22 (PAC) logged operations per field, calibrate on the field (CE-q/CE+).
- With many fields but one or two operations each, calibrate across fields with a model scale, and check coverage per machine configuration; a Monte Carlo twin of the vehicle is sufficient as the model. Validate the model against a few logged runs of each configuration: where its structure is wrong (heavy-tailed slip, unstable steering), a vendor-specification scale can be as good.
- Headland laps that overlap the main area remove most edge-dominated misses (Section 4.4).

---

## 6. Conclusion

This paper proposed conformal erosion, a calibration method that sets the pass overlap of an agricultural coverage plan so that the probability of a run with any missed strip stays below a level chosen by the user. The method reduces each logged run to one coverage score, the covering radius of the executed passes including the field edges, and takes an order statistic of these scores as the margin; fields without operation history are calibrated across fields, with a vehicle–terrain–GNSS model as the common scale. In a pre-registered simulation study driven by real field boundaries, terrain and GNSS errors:

1. With 100 logged runs per field, the calibrated margin held its target miss probability and used 4–55% less overlap than two conformal planners at the same guarantee level.
2. Without target-field data, the model scale (analytic or Monte Carlo twin) was the only scale that served every machine configuration of a mixed fleet efficiently: 0.6 pp of overlap above the per-field optimum, against 1.2–4.4 pp for configuration-aware baselines.
3. This advantage survived a trailed implement, degraded GNSS and levelled terrain, but not heavy-tailed slip or unstable steering, which the model does not represent. The guarantee itself fell short only when the deployed margin exceeded the calibrated one, a case the transfer check excludes.
4. A zero-miss margin paid off against the vendor rule only when a missed area cost more than about 30–100 times an over-applied one; for most input-saving operations a gap tolerance or a larger miss level is the better setting, and the same calibration states its miss probability.

Field validation with independent ground truth is the next step.

---

## Data availability

Code, processed input data, pre-registrations (with version-control timestamps), raw results and the scripts that generate every table and figure are in the project repository, with a reproduction guide in its README; the archived version will receive a DOI on acceptance. Input data are public: the field–road trajectory dataset (Wu et al., 2023), Copernicus GLO-30 (European Space Agency, 2021), NOAA CORS observations (NOAA, n.d.), and the vehicle GNSS/INS data of Tang et al. (2022).

---

## References

- Angelopoulos, A.N., Bates, S., Candès, E.J., Jordan, M.I., Lei, L., 2025. Learn then test: calibrating predictive algorithms to achieve risk control. Ann. Appl. Stat. 19(2), 1641–1662. https://doi.org/10.1214/24-AOAS1998
- Angelopoulos, A.N., Bates, S., Fisch, A., Lei, L., Schuster, T., 2024. Conformal risk control. In: The Twelfth International Conference on Learning Representations (ICLR 2024). arXiv:2208.02814.
- Azaïs, J.-M., Wschebor, M., 2009. Level Sets and Extrema of Random Processes and Fields. John Wiley & Sons, Hoboken, NJ. https://doi.org/10.1002/9780470434642
- Barber, R.F., Candès, E.J., Ramdas, A., Tibshirani, R.J., 2023. Conformal prediction beyond exchangeability. Ann. Stat. 51(2), 816–845. https://doi.org/10.1214/23-AOS2276
- Booton, R.C., 1954. Nonlinear control systems with random inputs. IRE Trans. Circuit Theory CT-1(1), 9–18.
- Campi, M.C., Garatti, S., 2008. The exact feasibility of randomized solutions of uncertain convex programs. SIAM J. Optim. 19(3), 1211–1230. https://doi.org/10.1137/07069821X
- Diquigiovanni, J., Fontana, M., Vantini, S., 2022. Conformal prediction bands for multivariate functional data. J. Multivar. Anal. 189, 104879. https://doi.org/10.1016/j.jmva.2021.104879
- Dunn, R., Wasserman, L., Ramdas, A., 2023. Distribution-free prediction sets for two-layer hierarchical models. J. Am. Stat. Assoc. 118(544), 2491–2502. https://doi.org/10.1080/01621459.2022.2060112
- European Space Agency, 2021. Copernicus Global Digital Elevation Model, GLO-30 Public (2021 release). Distributed via the AWS Open Data Registry (bucket copernicus-dem-30m). https://doi.org/10.5270/ESA-c5d3d65
- Everett, T. (rtklibexplorer), n.d. RTKLIB demo5: a fork of RTKLIB optimised for low-cost receivers. https://github.com/rtklibexplorer/RTKLIB (rnx2rtkp built from the repository in October 2026; the exact commit was not recorded).
- FAO, 2025. Pesticides use and trade – 1990–2023. FAOSTAT Analytical Briefs, No. 109. Food and Agriculture Organization of the United Nations, Rome. https://www.fao.org/statistics/highlights-archive/highlights-detail/pesticides-use-and-trade-1990-2023/en
- Galceran, E., Carreras, M., 2013. A survey on coverage path planning for robotics. Robot. Auton. Syst. 61(12), 1258–1276. https://doi.org/10.1016/j.robot.2013.09.004
- Hall, P., 1979. On the rate of convergence of normal extremes. J. Appl. Probab. 16(2), 433–439. https://doi.org/10.2307/3212912
- Hameed, I.A., la Cour-Harbo, A., Osen, O.L., 2016. Side-to-side 3D coverage path planning approach for agricultural robots to minimize skip/overlap areas between swaths. Robot. Auton. Syst. 76, 36–45.
- Hewing, L., Kabzan, J., Zeilinger, M.N., 2020. Cautious model predictive control using Gaussian process regression. IEEE Trans. Control Syst. Technol. 28(6), 2736–2743. https://doi.org/10.1109/TCST.2019.2949757
- Höffmann, M., Patel, S., Büskens, C., 2024. Optimal guidance track generation for precision agriculture: a review of coverage path planning techniques. J. Field Robot. 41(3), 823–844. https://doi.org/10.1002/rob.22286
- Kazakov, I.E., 1956. Approximate probability analysis of the operational precision of essentially nonlinear feedback control systems. Autom. Remote Control 17, 423–450.
- Leadbetter, M.R., Lindgren, G., Rootzén, H., 1983. Extremes and Related Properties of Random Sequences and Processes. Springer Series in Statistics. Springer, New York. https://doi.org/10.1007/978-1-4612-5449-2
- Lei, J., Rinaldo, A., Wasserman, L., 2015. A conformal prediction approach to explore functional data. Ann. Math. Artif. Intell. 74, 29–43. https://doi.org/10.1007/s10472-013-9366-6
- Lenain, R., Thuilot, B., Cariou, C., Martinet, P., 2006. High accuracy path tracking for vehicles in presence of sliding: application to farm vehicle automatic guidance for agricultural tasks. Auton. Robots 21(1), 79–97. https://doi.org/10.1007/s10514-006-7806-4
- Lindemann, L., Cleaveland, M., Shim, G., Pappas, G.J., 2023. Safe planning in dynamic environments using conformal prediction. IEEE Robot. Autom. Lett. 8(8), 5116–5123. https://doi.org/10.1109/LRA.2023.3292071
- Mayne, D.Q., Seron, M.M., Raković, S.V., 2005. Robust model predictive control of constrained linear systems with bounded disturbances. Automatica 41(2), 219–224. https://doi.org/10.1016/j.automatica.2004.08.019
- Mier, G., Fennema, R., Valente, J., de Bruin, S., 2025. Continuous curvature path planning for headland coverage with agricultural robots. J. Field Robot. 42(3), 641–656. https://doi.org/10.1002/rob.22489
- Mier, G., Valente, J., de Bruin, S., 2023. Fields2Cover: an open-source coverage path planning library for unmanned agricultural vehicles. IEEE Robot. Autom. Lett. 8(4), 2166–2172. https://doi.org/10.1109/LRA.2023.3248439
- Mohajerin Esfahani, P., Kuhn, D., 2018. Data-driven distributionally robust optimization using the Wasserstein metric: performance guarantees and tractable reformulations. Math. Program. 171(1–2), 115–166. https://doi.org/10.1007/s10107-017-1172-1
- NOAA, n.d. Continuously Operating Reference Stations (CORS) network. AWS Open Data, bucket noaa-cors-pds.
- Pannocchia, G., Rawlings, J.B., 2003. Disturbance models for offset-free model-predictive control. AIChE J. 49(2), 426–437. https://doi.org/10.1002/aic.690490213
- Piterbarg, V.I., 1996. Asymptotic Methods in the Theory of Gaussian Processes and Fields. Translations of Mathematical Monographs, vol. 148. American Mathematical Society, Providence, RI.
- Rice, S.O., 1944. Mathematical analysis of random noise. Bell Syst. Tech. J. 23(3), 282–332. https://doi.org/10.1002/j.1538-7305.1944.tb00874.x
- Romano, Y., Patterson, E., Candès, E., 2019. Conformalized quantile regression. In: Advances in Neural Information Processing Systems 32 (NeurIPS 2019), pp. 3543–3553.
- Sun, J., Jiang, Y., Qiu, J., Nobel, P.T., Kochenderfer, M., Schwager, M., 2023. Conformal prediction for uncertainty-aware planning with diffusion dynamics model. In: Advances in Neural Information Processing Systems 36 (NeurIPS 2023), pp. 80324–80337.
- Takasu, T., Yasuda, A., 2009. Development of the low-cost RTK-GPS receiver with an open source program package RTKLIB. In: International Symposium on GPS/GNSS, International Convention Center Jeju, Korea.
- Tang, H., Zhang, T., Niu, X., Fan, J., Liu, J., 2022. Impact of the Earth rotation compensation on MEMS-IMU preintegration of factor graph optimization. IEEE Sens. J. 22(17), 17194–17204. https://doi.org/10.1109/JSEN.2022.3192552 (vehicle GNSS/INS data: https://github.com/i2Nav-WHU/awesome-gins-datasets)
- Tibshirani, R.J., Barber, R.F., Candès, E.J., Ramdas, A., 2019. Conformal prediction under covariate shift. In: Advances in Neural Information Processing Systems 32 (NeurIPS 2019), pp. 2530–2540.
- Vovk, V., 2012. Conditional validity of inductive conformal predictors. In: Proceedings of the Asian Conference on Machine Learning (ACML 2012). Proc. Mach. Learn. Res. 25, 475–490. https://proceedings.mlr.press/v25/vovk12.html
- Wang, H., Ning, C., 2025. Conformal prediction in the loop: a feedback-based uncertainty model for trajectory optimization. In: Advances in Neural Information Processing Systems 38 (NeurIPS 2025). arXiv:2510.16376.
- Wu, C., Li, D., Zhang, X., Pan, J., Quan, L., Yang, L., Yang, W., Ma, Q., Su, C., Zhai, W., 2023. China's agricultural machinery operation big data system. Comput. Electron. Agric. 205, 107594. https://doi.org/10.1016/j.compag.2022.107594
- Zhang, X., Davidson, E.A., Mauzerall, D.L., Searchinger, T.D., Dumas, P., Shen, Y., 2015. Managing nitrogen for sustainable development. Nature 528(7580), 51–59. https://doi.org/10.1038/nature15743
- Zhang, X., Zou, T., Lassaletta, L., Mueller, N.D., Tubiello, F.N., et al., 2021. Quantification of global and national nitrogen budgets for crop production. Nat. Food 2, 529–540. https://doi.org/10.1038/s43016-021-00318-5
- Zhao, Y., Yu, X., Sesia, M., Deshmukh, J.V., Lindemann, L., 2024. Conformal predictive programming for chance constrained optimization. arXiv:2402.07407.
