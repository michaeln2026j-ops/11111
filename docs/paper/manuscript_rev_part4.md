### 6.6 What a certified margin costs

The certified event "no strip missed with probability 0.9" counts a 1 cm sliver like a 1 m strip. Whether it is worth its overlap depends on what a miss costs. Let $r$ be the cost of leaving one unit of area unworked divided by the cost of over-applying one unit of area (for an input-saving operation, the value of the yield or control lost on a missed strip divided by the input cost per unit area). The expected cost of a margin, in percent of the main area, is then overlap $+\ r\times$ missed area. Table 8 evaluates it on the margin curves of 35 fields per configuration (nominal model, descriptive).

<!-- source: results/revision/rv_cost.txt -->
| Config. | Policy | P(no miss) | Overlap % | Missed % | Cost, $r=10$ | $r=30$ | $r=100$ | $r=300$ |
|---|---|---|---|---|---|---|---|---|
| R1 | vendor rule | 0.000 | 2.15 | 0.159 | 3.73 | 6.91 | 18.02 | 49.78 |
| | farmer-tuned | 0.879 | 9.05 | 0.001 | 9.06 | 9.07 | 9.12 | 9.26 |
| | certified, $\varepsilon=0.1$ (ideal) | 0.900 | 8.93 | 0.001 | 8.94 | 8.95 | 9.00 | 9.13 |
| | cost-optimal margin | 0.03–0.49 | 2.5–6.0 | | **3.57** | **4.73** | **5.93** | **7.11** |
| R2 | vendor rule | 0.000 | 5.39 | 0.340 | 8.78 | 15.58 | 39.36 | 107.32 |
| | farmer-tuned | 0.847 | 23.02 | 0.001 | 23.03 | 23.05 | 23.11 | 23.28 |
| | certified, $\varepsilon=0.1$ (ideal) | 0.900 | 24.83 | 0.001 | 24.83 | 24.84 | 24.88 | 24.99 |
| | cost-optimal margin | 0.00–0.33 | 5.9–15.0 | | **8.60** | **11.60** | **14.82** | **17.78** |
| R3 | vendor rule | 0.435 | 7.59 | 0.111 | 8.71 | 10.93 | 18.71 | 40.95 |
| | farmer-tuned | 0.850 | 13.25 | 0.032 | 13.57 | 14.21 | 16.47 | 22.90 |
| | certified, $\varepsilon=0.1$ (ideal) | 0.900 | 15.12 | 0.025 | 15.37 | 15.88 | 17.63 | 22.65 |
| | cost-optimal margin | 0.21–0.88 | 4.5–14.3 | | **7.05** | **10.26** | **14.99** | **21.57** |

*Table 8. Expected cost (overlap % + $r$ × missed-area %) of practice and certified margins (descriptive). "Certified (ideal)" is each field's own 0.9 margin, the target of an exactly calibrated certificate; the cost-optimal margin minimises the expected cost per field given the test distribution and is a reference, not a method.*

Three conclusions follow. First, against the vendor rule, the certified margin pays off only above a break-even ratio of $r^\star\approx43$ (R1), 57 (R2) and 88 (R3); with the per-operation results of Experiment A1 the break-even values are 31–35 (RTK) and 88–117 (DGPS). Second, the cost-optimal margin under RTK accepts frequent but tiny misses: even at $r=300$ it has a P(no miss) of only 0.49 (R1) and 0.33 (R2), because RTK misses are slivers of 0.004–0.03% of the area. Only under DGPS, whose misses are wider, does the cost-optimal margin approach the 0.9 level ($r=300$: 0.88). Third, a tolerance helps where implements are narrow: certifying "no gap wider than 2 cm" instead of "no gap" lowers the margin by 1 cm and saves 0.9, 2.0 and 0.5 pp of overlap in R1–R3, and a 5 cm tolerance saves 2.0, 5.0 and 1.1 pp.

The value of $r$ depends on the operation, crop and prices and is for the user to set: input-saving operations with partial compensation by neighbouring rows (fertiliser, seeding of tillering cereals) suggest values of order 1–10, while operations in which a missed strip carries a regulatory, quarantine or resistance-management cost, or whose input is cheap relative to the crop, can justify much larger values. For $r$ below the break-even, a certified zero-miss margin at $\varepsilon=0.1$ costs more than the vendor rule; the certificate is then still useful as a statement of the miss probability that a cheaper margin carries, since the same calibration data give a conservative estimate of $P(S>\lambda)$ for every $\lambda$, and $\varepsilon$ and $\tau$ can be chosen by cost. Conformal risk control of the expected missed area (Angelopoulos et al., 2024) would target cost directly, but its finite-sample correction $B/(n+1)$, with $B$ the largest possible loss, exceeds the relevant missed-area levels (0.01–0.1%) unless thousands of runs are available.

### 6.7 Real-vehicle validation

All results above are from simulation. Field validation on an autonomous feed-spreading vehicle with lidar-inertial localisation, with independent ground truth of the implement position, is in preparation; the logging and certification tools are in the repository (`tools/feedcar`).

---

## 7. Discussion

### 7.1 What is guaranteed, and by what

Three layers of the method rest on different assumptions. (i) The run score is exact and the smallest valid score, with no assumption (Lemma 1, Theorem 1). (ii) The conformal quantile of the score on the reference plan is distribution-free given exchangeable runs (target-field calibration) or exchangeable fields (cross-field calibration); only CE deploys that plan itself and is assumption-free. (iii) Deploying a plan with fewer passes than the reference plan (CE-q, CE+, XCE) needs the transfer assumption (S) and costs a factor $\kappa$; in every experiment the measured coverage of such plans was at or above the target (Experiments A2, B4, C1), including R3 fields on which CE+ violated the transfer check. The extreme-value model and the Monte Carlo twin affect only efficiency. The guarantee for cross-field calibration averages over fields: with configuration-blind pooling the DGPS fields of a mixed fleet were covered at 0.78 while the RTK fields were over-covered, so per-configuration coverage must be checked, and a model pivot achieved it (0.89–0.94).

### 7.2 Where the method helps

*With target-field data*, the exact score and the reference plan give tight calibration: CE+ reached its target while two conformal planners over-covered at 4–55% more overlap. The gain over well-calibrated practice is small: the farmer-tuned margin was within a few tenths of a point in R1 and below CE+ in R2 and R3, at lower reliability. *Without target-field data*, a model pivot is the only configuration-aware scale that covered every configuration and was efficient: across a mixed fleet it cost 0.6 pp above the per-field optimum (marginal, 60 calibration fields) against 1.2–4.4 pp for configuration-aware baselines and 17 pp for pooling, and per-configuration pooling could not deploy at all under the PAC rule with 25 calibration fields. The analytic model and the Monte Carlo twin were equally good; the twin is simpler to build when a simulator exists, and the analytic model explains the scaling of margins with field size, the role of the field edges, and the information limit.

### 7.3 Where it does not help

Within one machine configuration, all field-level pivots, including the ideal one, perform within a few tenths of a point at matched coverage (Experiments B2–B3), because the remaining inflation is set by run-to-run randomness (Proposition 4). The PAC rule with few runs is expensive (3–19 pp above the optimum at $n=22$). And a zero-miss margin at $\varepsilon=0.1$ is not cost-optimal for RTK guidance unless a missed unit costs several hundred times an over-applied one (Section 6.6); for most input-saving operations a tolerance or a larger $\varepsilon$ is the better choice, which the same calibration supports.

### 7.4 Limitations

1. **Simulation only.** Field boundaries, terrain and GNSS errors are real; execution is simulated, with a kinematic vehicle, a rigidly mounted implement in the main experiments, one speed, static US CORS errors applied to Chinese fields, and terrain slopes from a 30 m model. Experiment C1 shows that the guarantee survives misspecification but the model's efficiency does not always; none of this replaces field data.
2. **Ground truth.** The run score needs the true implement position. A guidance receiver cannot see its own GNSS error, so calibration runs need an independent reference (for example a PPK rover on the implement); machine logs alone are not sufficient.
3. **Transfer assumption.** CE-q, CE+ and XCE deploy plans other than the reference plan and rely on (S); guidance that couples passes (follow-previous-pass) violated it.
4. **Exchangeability.** Cross-field calibration assumes that calibration and new fields come from one population; a new configuration or field type needs its own calibration fields. Fields worked on the same day share GNSS conditions, which the experiments did not model.
5. **Objective.** The zero-miss event ignores the size of a miss; Section 6.6 quantifies when this matters.

### 7.5 Practical guidance

- Decide the cost ratio $r$ of the operation first. Below a ratio of about 30–100 (RTK–DGPS in these simulations), a zero-miss margin at $\varepsilon=0.1$ costs more than the vendor rule; use a gap tolerance $\tau$ or a larger $\varepsilon$, and use the calibration to state the miss probability of the margin chosen.
- Record the run score (covering radius per section, including the field edges) from runs with independent ground truth; it is the tightest valid score.
- Calibrate on a plan with at least as many passes as will be deployed, never on the zero-margin plan; refuse or fall back to CE if the deployed margin exceeds the reference margin.
- With at least 9 (marginal) or 22 (PAC) logged operations per field, calibrate on the field (CE-q/CE+).
- With many fields but one or two operations each, calibrate across fields with a model pivot, and check coverage per machine configuration; a Monte Carlo twin of the vehicle is sufficient as the model.
- Headland laps that overlap the main area remove most edge-dominated misses (Section 6.5).

---

## 8. Conclusion

Complete coverage of a field by a plan executed with error reduces exactly to one number per run, the covering radius of the executed passes, which is the smallest score that can certify it. Calibrated with conformal prediction on a reference plan, it gives a miss probability that is assumption-free for that plan and transfers to plans with fewer passes under an explicit coupling assumption. In simulations driven by real fields, terrain and GNSS errors, the certificate held in every pre-registered check; with target-field data it was tighter than two conformal planners, and without target-field data a model of the vehicle, terrain and GNSS, analytic or Monte Carlo, was the only scale that served every machine configuration of a mixed fleet efficiently. Whether a zero-miss certificate is worth its overlap is an economic question: in these simulations it pays off against the vendor rule only when a missed area costs more than about 30–100 times an over-applied one, and a gap tolerance or a larger miss level is the better choice for most input-saving operations. Field validation with independent ground truth is the next step.
