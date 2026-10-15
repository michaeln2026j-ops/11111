## 5. Theory

This section states what is guaranteed and under which assumptions, and describes the extreme-value model in words. Formal statements and proofs are in Appendix A, which also lists the status of every result (theorem, bound, or heuristic remark).

### 5.1 Which plan is calibrated matters

*In practice: calibrate on a plan with at least as many passes as the plan you will deploy.* The run score is a maximum over pass pairs and field edges. A plan with more passes has more terms in the maximum and a stochastically larger score.

**Proposition 1 (nominal-plan calibration does not transfer).** A method that calibrates on the nominal plan $\pi(0)$ and deploys $\pi(\hat\lambda)$ with more passes has no distribution-free guarantee on the deployed plan: with $K_0$ and $K_1>K_0$ i.i.d. pair scores, a threshold calibrated at level $1-\varepsilon$ on $\pi(0)$ gives coverage $(1-\varepsilon)^{K_1/K_0}<1-\varepsilon$ on $\pi(\hat\lambda)$.

The conformal planners of Lindemann et al. (2023) and Zhao et al. (2024), applied to coverage, calibrate on the nominal plan. CE and its variants calibrate on a reference plan with $\lambda_\mathrm{ref}\ge\hat\lambda$, which gives the right direction.

### 5.2 Transfer from the reference plan to the deployed plan

*In practice: deploying a plan with fewer passes than the reference plan costs at most a factor $\kappa$ on the miss level; on flat fields $\kappa\approx1$.*

**Theorem 2 (transfer under superposition).** Couple the reference plan $\pi_0$ and the deployed plan $\pi_1$ by sharing the operating condition and the per-pass noise, and assume (S): for coupled runs, each matched gap or edge term of $\pi_1$ exceeds that of $\pi_0$ by at most $\bar\Delta$, a bound that does not depend on the noise. Then, for every threshold $t$,
$$
1-F_{\pi_1}(t)\le 1-F_{\pi_0}(t-\bar\Delta)=\kappa(t)\,\big(1-F_{\pi_0}(t)\big),
$$
and deploying $\pi(\hat\lambda)$ with $\hat\lambda\le\lambda_\mathrm{ref}$ gives $P(\text{miss})\le\sup_{t\le\lambda_\mathrm{ref}}\kappa(t)\,\varepsilon$ (marginal rule), or $\kappa(\hat\lambda)\,\varepsilon$ conditionally on calibration with probability at least $1-\delta$ (PAC rule).

(S) holds exactly for a linear closed loop, because the response to the plan-dependent deterministic inputs (terrain, timing of the GNSS error) superposes on the response to the noise, and approximately for the nonlinear simulator. $\bar\Delta$ is dominated by the roll-induced antenna offset, which differs between the passes of the two plans when the cross-slope does, plus a GNSS timing term; on flat fields $\bar\Delta\approx0$. In the development checks, the coverage after a plan change was predicted as 0.901, 0.890 and 0.920 against simulated 0.899, 0.885 and 0.922 (Table S5). A weaker, model-free version with a hazard-rate constant is given in Appendix A.7.

### 5.3 Validity of cross-field calibration

**Proposition 3 (XCE validity).** If fields are exchangeable (i.i.d. for the PAC statement), each calibration field contributes one run at its reference plan, and $\hat q_f\in(0,\infty]$ depends only on field $f$, then $\Pr[S_\mathrm{new}\le\hat q_g v^\star]\ge k_\star/(n+1)\ge1-\varepsilon$ for the marginal rule, and the PAC rule gives the conditional statement. The zero-miss guarantee for the deployed plan follows by Theorem 2.

*Proof.* $S_\mathrm{new}\le\hat q_gv^\star\iff V_\mathrm{new}\le v^\star$; apply the split-conformal lemma to the exchangeable $V$. $\square$

This is the two-level setting of Dunn et al. (2023) with one sample per group. The guarantee averages over which fields calibrate and over the outcome of each calibration field's single run. Given a fixed set of logged runs, the coverage averaged over new fields is a draw from $\mathrm{Beta}(k_\star,n+1-k_\star)$: at $n=29$ and $k_\star=27$ its standard deviation is about 0.054, so one realised coverage can fall well below $1-\varepsilon$ without contradicting the guarantee. The guarantee is also an average over fields, not a per-field or per-machine statement; Section 6.4 reports coverage per machine configuration.

### 5.4 A model of the required margin

The model pivot of XCE needs a prediction of each field's $(1-\varepsilon)$ score quantile from quantities known before any operation: the controller and its gains, the terrain model of the field, the soil-moisture range, the GNSS receiver grade (through an error series of that grade) and the implement width. The analytic model chains five steps (Appendix B):

1. **Closed-loop covariance.** Linearised along the noise-free closed-loop path of each pass, with describing functions for steering saturation and rate limits and a leaky-integrator model of the anti-windup clamp, the offset of one pass is a Gaussian process given the run's operating condition (soil moisture, slip and roughness gains, roll compensation, mounting bias, GNSS error trajectory); its covariance follows from a time-varying Lyapunov recursion.
2. **Exceedance of one pass pair and of the field edges.** The probability that a gap between two passes exceeds a threshold anywhere along the pass is bounded by a discrete Kac–Rice upcrossing sum, and computed exactly by Gaussian Monte Carlo where that bound is loose. For a field edge, the edge is missed only if every pass that covers it has receded; given the operating condition these are independent, so the edge exceedance is bounded by a product of single-pass probabilities (Appendix A.12).
3. **Combination over pairs.** Given the condition, non-adjacent pairs are independent, and the probability of no exceedance is approximated by the product over pairs. A Bonferroni sandwich bounds the error, but at the 0.9 level that bound is of the same size as $\varepsilon$; the product form is accurate empirically (0.888, 0.882 and 0.900 against a true 0.900; Table S5), not by the bound.
4. **Mixture over operating conditions**, by sampling 200 conditions.
5. **Scale law.** For a stationary pair process the extremes are Gumbel, and the required margin grows like $\sqrt{2\log L}$ in the effective length $L$; this is a heuristic guide (a tenfold larger field raises the margin by about 11%), used only for a comparator pivot.

The model rests on the simulator's own structure: it calls the noise-free simulator for the mean path and samples operating conditions from the simulator's distribution. Its accuracy against that simulator is therefore a check of internal consistency, not of realism; Section 6.5 tests what happens when reality differs from the model. The same holds for the Monte Carlo twin, which is the simulator itself with fresh random numbers.

**Physical reading of the edge terms.** An interior gap $(e_{k+1}-e_k)/2$ is a difference of two passes, so error shared by adjacent passes cancels in it, and its standard deviation is $1/\sqrt2$ of that of one pass when the passes are independent. An edge term takes the full error of one pass. Edge terms therefore carry about $\sqrt2$ times the spread of interior terms even without any shared error, and more when part of the GNSS error is shared by adjacent passes (in the 1 Hz DGPS error series, the correlation of the error at lags of 13–113 s, the time between adjacent passes at the same section, is 0.91–0.41; for RTK it is 0.71–0.54). Under the hard-edge evaluation used in the main experiments the edges then bind more often under DGPS; with headland laps that overlap the main area they become pair-like terms (Section 6.5).

### 5.5 Margin inflation under the ideal scale

**Proposition 4.** Let $G_f$ be the score distribution on field $f$, $\lambda^\star_f=G_f^{-1}(1-\varepsilon)$ the field's own requirement, and take the ideal (unavailable) pivot $\hat q_f=\lambda^\star_f$. With $H(v)=\mathbb E_f[G_f(v\lambda^\star_f)]$, every new field receives $\lambda_g/\lambda^\star_g=H^{-1}(B)$ with $B\sim\mathrm{Beta}(k_\star,n+1-k_\star)$.

For the PAC rule with $n=29$, $k_\star=n$ and $\mathbb E B=29/30$; if normalised shapes coincide, the inflation is a within-field tail ratio that the ideal pivot cannot remove. This is an identity for the ideal pivot, not a lower bound over all pivots: another pivot changes $H$, and in one cell raw pooling was cheaper than the ideal pivot (Section 6.4). Both decisive quantities, the between-field spread relative to the model error and the within-field tail ratio, can be computed from the model before any experiment.
