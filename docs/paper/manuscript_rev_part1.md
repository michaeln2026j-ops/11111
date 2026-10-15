## 1. Introduction

Field operations such as spraying, fertilising, seeding and tillage are planned as parallel passes whose spacing equals the implement width minus an overlap. The plan is optimal only if the machine follows it exactly. Real passes deviate from the planned line because of GNSS positioning error, wheel slip on slopes and wet soil, antenna roll on side slopes, mounting offsets and the finite bandwidth of the steering controller. A strip is left unworked whenever two adjacent passes drift apart by more than their overlap, or when the outermost pass drifts away from the field boundary; the relevant quantity is the relative error between adjacent passes, which the industry calls pass-to-pass accuracy. Overlap set to absorb this error applies inputs twice on the overlapped strip. Both errors carry a cost: missed strips lose yield or leave weeds and pests untreated, and overlap wastes seed, fertiliser and pesticide (FAO, 2025; Zhang et al., 2015, 2021). Autonomous machines remove the operator who used to correct visible gaps by eye.

Current practice sets a fixed overlap, typically twice the vendor's pass-to-pass specification or a value learned by experience. Such a margin has no stated reliability and does not adapt to field shape, terrain, receiver grade or implement width. Coverage path planning (CPP) research has produced efficient decompositions, swath-angle optimisation and smooth headland turns (Galceran and Carreras, 2013; Höffmann et al., 2024; Mier et al., 2023, 2025), and terrain-aware planners adjust spacing to 3D geometry (Hameed et al., 2016), but these planners assume perfect execution. Control research reduces tracking error (Lenain et al., 2006; Pannocchia and Rawlings, 2003; Mayne et al., 2005), but a smaller error does not by itself state how often a strip will be missed. Conformal prediction gives finite-sample, distribution-free guarantees and has been used for planning (Lindemann et al., 2023; Zhao et al., 2024), but three features of field coverage are not addressed: the guarantee must hold for a maximum over many pass pairs and field edges; the plan that is calibrated and the plan that is deployed differ, and adding passes makes the maximum larger; and a field is worked only a few times per year, while a conformal quantile at a miss level of 10% needs at least 9 (marginal) or 22 (training-conditional, PAC) logged runs.

This paper makes four contributions, all evaluated in simulation driven by real field boundaries, elevation models and GNSS error series.

1. **An exact score for complete coverage.** The event "no strip is missed" is reduced exactly to one number per run, the covering radius of the executed passes including the field edges, and this is the smallest score that can certify complete coverage (Section 3).
2. **Conformal erosion with target-field data.** Calibrating this score on a reference plan gives an assumption-free certificate for that plan (CE) and, under an explicit transfer assumption, for plans with fewer passes (CE-q, CE+) (Sections 4.1–4.2, 5.1–5.2).
3. **Cross-field certification of fields without history (XCE).** A farm or contractor typically holds many fields with one or two logged operations each. A model of the vehicle, terrain and GNSS that predicts each field's required margin, either an analytic extreme-value model or Monte Carlo of a digital twin, is used only to put fields on a common scale; the conformal guarantee does not depend on the model's accuracy (Sections 4.3, 5.3–5.4).
4. **An evaluation that states where the method helps and where it does not.** Pre-registered experiments on 30 to 135 unseen fields per experiment compare against conformal planners, practice rules, configuration-aware baselines and learned predictors; robustness to a misspecified model and to headland laps; the cost at which a certified margin pays off; and an information limit that bounds what any field-level scale can gain (Section 6).

All confirmatory experiments were pre-registered in a time-stamped repository before they were run; failed and partially met claims are reported alongside met ones, and exploratory and post hoc analyses are labelled as such (Supplementary Table S20).

---

## 2. Related work

*Coverage path planning.* Boustrophedon cellular decomposition (BCD) with swath-angle optimisation is the standard for agricultural fields (Höffmann et al., 2024). Fields2Cover provides an open implementation with heading search and Dubins turns (Mier et al., 2023), Mier et al. (2025) add continuous-curvature headland paths, and Hameed et al. (2016) compute 3D-terrain-equivalent spacing. None attaches a probability to complete coverage.

*Robust and model-based margins.* Tube MPC bounds tracking error by a robust invariant set (Mayne et al., 2005); Gaussian chance constraints propagate a parametric error model, optionally with Rice's extreme-value correction (Rice, 1944); Gaussian-process cautious control tightens constraints by a learned variance (Hewing et al., 2020); distributionally robust CVaR constraints use a Wasserstein ambiguity set (Mohajerin Esfahani and Kuhn, 2018); the scenario approach gives PAC guarantees from sampled constraints (Campi and Garatti, 2008). Parametric models misrepresent the heavy, temporally clustered tail of RTK errors (wrong fixes, float drift; Table 1), and worst-case sets are conservative.

*Conformal prediction.* Split conformal prediction and its training-conditional (PAC) variant (Vovk, 2012); conformal prediction under covariate shift and beyond exchangeability (Tibshirani et al., 2019; Barber et al., 2023); conformalized quantile regression (CQR; Romano et al., 2019); conformal risk control (Angelopoulos et al., 2024, 2025); hierarchical conformal prediction with one sample per group (Dunn et al., 2023); and functional conformal bands (Lei et al., 2015; Diquigiovanni et al., 2022), of which a sup-normalised run score is an instance. Conformal planning methods (Lindemann et al., 2023; Zhao et al., 2024; Sun et al., 2023; Wang and Ning, 2025) do not address a decision-dependent maximum over pass pairs.

*Extremes of Gaussian processes.* Kac–Rice formulas and Rice's method (Azaïs and Wschebor, 2009; Piterbarg, 1996); maxima of stationary processes (Leadbetter et al., 1983); statistical linearisation (Booton, 1954; Kazakov, 1956).

---

## 3. Problem formulation

**Fields, plans and margins.** A field is a polygon; its **main area** $W$ is the field inset by twice the implement width $w$, the remainder being headland. After decomposition and choice of the working direction $x$, a plan is a set of straight pass centrelines $y_1<\dots<y_K$. For a **margin** (erosion) $\lambda\ge0$ the greedy planner $\pi(\lambda)$ places passes as if the footprint had half-width $w/2-\lambda$, so that adjacent planned footprints overlap by $2\lambda$; the number of passes $K(\lambda)$ is non-decreasing in $\lambda$ (Appendix A.2). The overlap ratio $J(\lambda)$ is the swath area within $W$ divided by the area of $W$, minus one; an overlap of 8% means that 8% of the main area receives a double dose.

**Execution.** Pass $k$ is driven with lateral offset $e_k(x)$, so its footprint at section $x$ is $[y_k+e_k(x)-w/2,\ y_k+e_k(x)+w/2]$ (Fig. 1). Offsets are random, correlated along and across passes (adjacent passes read the same GNSS error trajectory a pass duration apart), and their law depends on the plan through the terrain and time at which each pass is driven. Coverage is evaluated on 1 m sections across $W$.

![](../../figures/paper/fig_schematic.png)

**Fig. 1.** Plan view of the problem (illustrative). Dashed lines are planned pass centrelines at spacing $w-2\lambda$; solid lines are executed paths and shaded bands the implement footprints of width $w$, which overlap by $2\lambda$ on plan. A strip is missed (orange) in two ways: an *interior gap*, where adjacent passes drift apart by more than the overlap, and a *field-edge miss*, where the outermost pass drifts inward and nothing else covers the boundary. The run score measures the worst of both.

**Objective.** Let $M(\lambda,e)$ be the missed area of $W$ when $\pi(\lambda)$ is executed with offsets $e$. The certified coverage problem is
$$
\min_{\lambda}\ J(\lambda)\quad\text{s.t.}\quad \Pr\big[M(\lambda,e)=0\big]\ \ge\ 1-\varepsilon ,
$$
with $\varepsilon$ the tolerated probability of a run with any missed strip (here 0.1). Section 4.4 generalises the event to "no gap wider than a tolerance" and Section 6.6 asks for which costs of a miss the zero-miss objective is worth its overlap.

**Lemma 1 (exact covering radius).** At section $x$ let $Y(x)$ be the executed centres of the passes relevant to the chord $[\ell(x),u(x)]$ of $W$, sorted. The chord is fully covered iff
$$
r^\star(x)=\max\Big\{\mathrm{dist}(\ell,Y),\ \mathrm{dist}(u,Y),\ \max_{i:\ (c_i+c_{i+1})/2\in[\ell,u]}\tfrac12(c_{i+1}-c_i)\Big\}\ \le\ \tfrac w2 .
$$
For a run of the plan $\pi(\lambda_\mathrm{ref})$ define the **run score** $S=\lambda_\mathrm{ref}+\max_x\big(r^\star(x)-w/2\big)$. Then $\{M=0\}\iff\{S\le\lambda_\mathrm{ref}\}$.

The score is the amount by which every footprint would have to grow (equivalently, the margin that the executed plan would have needed) to close its worst gap. Its interior terms are half the pass-to-pass gaps; the terms $\mathrm{dist}(\ell,Y)$ and $\mathrm{dist}(u,Y)$ are field-edge terms.

**Theorem 1 (the run score is the smallest valid score).** Call a run score valid if it never declares a run with a missed strip miss-free when the executed footprints are grown by the score (a *virtual* erosion of the executed plan; Appendix A.3). Then $S$ is valid and $S\le S'$ for every valid score $S'$, run by run, with no assumption on the error process. Consequently any rule that takes an order statistic of calibration scores (marginal conformal, PAC conformal, the scenario approach) deploys no more passes with $S$ than with any other valid score, such as the per-pair or per-constraint maxima used by earlier conformal planners.

---

## 4. Method

Table 2 summarises the variants. All compute run scores of calibration runs on a **reference plan** $\pi(\lambda_\mathrm{ref})$, take a conformal order statistic, and deploy a plan. For $n$ calibration scores, the **marginal rule** takes the $k_\star$-th smallest score with $k_\star=\lceil(n+1)(1-\varepsilon)\rceil$, which gives $\Pr[S_\mathrm{new}\le\hat\lambda]\ge k_\star/(n+1)\ge1-\varepsilon$ on average over calibration data. The **PAC rule** takes the smallest $k_\star$ with $\mathrm{BinomCDF}(k_\star-1;n,1-\varepsilon)\ge1-\delta$, which gives the guarantee conditionally on the calibration data with probability at least $1-\delta$ (here $\delta=0.1$). If $k_\star>n$ the threshold is infinite and nothing is deployed. At $\varepsilon=\delta=0.1$ the marginal rule needs $n\ge9$ runs and the PAC rule $n\ge22$.

<!-- source: docs/paper/manuscript.md (method definitions) -->
| Variant | Calibration data | Score scale | Deployed plan | Guarantee on the deployed plan |
|---|---|---|---|---|
| CE | runs on the target field (pilot + certificate batch) | none | the reference plan itself | assumption-free (Appendix A.4) |
| CE-q | $n$ runs on the target field | none | $\pi(\hat\lambda)$, $\hat\lambda\le\lambda_\mathrm{ref}$ | under the transfer assumption (S), factor $\kappa$ (Theorem 2) |
| CE+ | $n$ runs on the target field + 5 training fields | probe-line XTE, gated | $\pi(t\,\sigma(z))$ | as CE-q; requires $t\sigma(z)\le\lambda_\mathrm{ref}$ |
| XCE-T / XCE-MC | one run on each of $n$ other fields, none on the target | model-predicted quantile (theory / Monte Carlo twin) | $\pi(\hat q_g v^\star)$ | score guarantee assumption-free; plan via (S) |

*Table 2. Method variants. In the pre-registrations XCE-T is called CE-EVT-R.*

### 4.1 CE: target-field calibration, assumption-free

CE iterates pilot batches, $\lambda_\mathrm{ref}\leftarrow1.10\,q$ with $q$ the $(1-\varepsilon)$ empirical quantile of pilot scores at $\pi(\lambda_\mathrm{ref})$, until $q\le\lambda_\mathrm{ref}$, freezes the plan, draws a fresh certificate batch, and deploys $\pi(\lambda_\mathrm{ref})$ itself if the certificate quantile $q^\star\le\lambda_\mathrm{ref}$ (refusing otherwise). By Lemma 1 the deployed plan is miss-free iff its score is at most $\lambda_\mathrm{ref}$, so no transfer assumption is needed: the marginal rule bounds $P(\text{deploy and miss})$ by $\varepsilon$, and the PAC rule bounds the miss probability given deployment.

### 4.2 CE-q and CE+: deploying fewer passes

CE-q deploys $\pi(q^\star)$, which has no more passes than the reference plan; its guarantee transfers from the reference plan under the coupling assumption of Theorem 2. CE+ fixes the budget at $n$ runs and adds two elements. (1) The reference margin comes from training fields only: $\lambda_\mathrm{ref}=1.25\times$ the largest $(1-\varepsilon)$ score quantile over five training fields. (2) Before the infield passes the machine drives one headland probe line; the autosteer's cross-track-error (XTE) RMS $z$ is a noisy reading of the day's roughness and slip. The normalised score is $\tilde S=S/\sigma(z)$ with $\sigma(z)=\max(a+bz,\ 0.3\,\bar\sigma)$, $(a,b)$ fitted on training fields after dividing each field's scores by its median ($\bar\sigma$ is the mean fitted scale), and a new operation deploys $\lambda=t\,\sigma(z_\mathrm{new})$ with $t$ the conformal quantile of the calibration $\tilde S_i$. The adaptive $\sigma$ is used only if it lowers the mean margin by at least 3% in leave-one-field-out cross-validation on the training fields; otherwise $\sigma$ is constant and CE+ equals CE-q with a training-field reference plan. **Transfer check (revision).** Because the transfer argument needs the deployed plan to have no more passes than the reference plan, CE+ must refuse when $t\,\sigma(z_\mathrm{new})>\lambda_\mathrm{ref}$ and fall back to CE; the pre-registered runs did not include this check, and Section 6.3 reports how often it would have triggered.

### 4.3 XCE: certifying a field without history

A farm or contractor typically holds many fields with one or two logged operations each, and the new field has none. XCE calibrates across fields. For each field $f$ a **model pivot** $\hat q_f$ predicts the $(1-\varepsilon)$ quantile of the run score on the field's reference plan from controller settings, the terrain model and the GNSS grade, **without run data**. For calibration field $f_i$ with one logged score $S_i$, the ratio $V_i=S_i/\hat q_{f_i}$ is formed, $v^\star$ is the marginal or PAC order statistic of $\{V_i\}$, and the new field $g$ receives $\lambda_g=\hat q_g\,v^\star$. A field whose prediction fails ($\hat q_f$ not finite) gets $V_f=+\infty$; if this happens on the target field, nothing is deployed.

**The guarantee does not depend on the model.** $\hat q_f$ is a fixed function of field $f$, independent of all run data. If fields are exchangeable and each contributes one run, the $V$'s are exchangeable and the conformal guarantee holds for the score (Proposition 3). Model error affects only efficiency: the closer $V$ is to identically distributed across fields, the closer $\lambda_g$ is to field $g$'s own requirement. Any field-measurable scale gives a valid method of the same form; we compare the model pivot with raw pooling ($\hat q\equiv1$), per-configuration pooling (Mondrian conformal), a vendor-specification scale, a learned scale (CQR-type ridge regression; Romano et al., 2019) and an empirical per-configuration scale.

**Two implementations of the model pivot.** *XCE-T* uses the analytic extreme-value model of Section 5.3; *XCE-MC* uses the 0.9 quantile of 1000 Monte Carlo runs of the nominal closed-loop simulator (a digital twin) on the reference plan. Both need the same inputs; neither uses logged runs. The ratio form was chosen over a probability-integral-transform pivot, which failed in the first zero-data experiment because it amplifies errors in the far tail of the predicted distribution (Appendix B.4).

### 4.4 Tolerated gap width and the choice of $\varepsilon$

Many operations tolerate a narrow unworked strip (spread-pattern overlap of fertiliser spreaders, boom-end taper of sprayers). The certified event generalises to "no gap wider than $\tau$": an interior gap has width $2(r^\star-w/2)$ and an edge strip $r^\star-w/2$, so the score $S_\tau=S-\tau/2$ is valid for this event (conservative for edge strips), and the certified margin is $\hat\lambda-\tau/2$. The level $\varepsilon$ itself is an economic choice: Section 6.6 compares the expected cost of certified and practice margins as a function of the ratio $r$ of the cost of a missed unit area to the cost of an over-applied unit area.

### 4.5 Computational cost

CE and CE+ add only the score evaluation (a sort of executed centres per 1 m section) and an order statistic to a standard planner. The model pivot is computed once per field and reference plan, offline: XCE-T took 133–187 s per field in R1, 287–353 s in R2 and 16–51 s in R3 on one core (three fields per regime; Table S21), and XCE-MC with 1000 runs took 5–49 s.
