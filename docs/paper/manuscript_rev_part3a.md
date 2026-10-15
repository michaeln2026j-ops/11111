## 6. Simulation experiments

### 6.1 Data, simulator, machine configurations and protocol

**Data.** All inputs are public. Field boundaries and working directions come from 250 combine-harvester GNSS trajectories of the field–road trajectory dataset of the national agricultural machinery operation platform of China (Wu et al., 2023); density-based clustering extracts 964 fields, of which 137 paddy fields (hilly south of China) and 162 wheat fields (North China Plain) are used. Terrain comes from Copernicus GLO-30 elevation windows (European Space Agency, 2021). GNSS error comes from 12 NOAA CORS station pairs (baselines 5–30 km, in agricultural regions of the US Midwest and Great Plains), 8 days each across four seasons of 2024–2025, processed with RTKLIB (Takasu and Yasuda, 2009; demo5 fork) as a moving rover against the reference coordinates at four receiver grades (Table 1). The 30 s epochs are interpolated to 1 Hz and high-frequency residuals of a vehicle GNSS/INS record (Tang et al., 2022) are added. Each simulated run draws a station-pair-day and a start time.

<!-- source: results/table_gnss.txt (scripts/table_gnss.py) -->
| Grade | Processing | RMS | 95% | 99.9% | Max |
|---|---|---|---|---|---|
| RTK | carrier phase, continuous ambiguity resolution (84% of epochs fixed, 16% float) | 2.4 cm | 3.3 cm | 24.5 cm | 1.39 m |
| RTK float | carrier phase, no ambiguity resolution | 2.6 cm | 4.0 cm | 24.6 cm | 1.39 m |
| DGPS | code differential | 32.5 cm | 57.8 cm | 2.05 m | 6.05 m |
| Single point | L1 code | 1.51 m | 2.78 m | 4.97 m | 7.16 m |

*Table 1. Horizontal error of the processed CORS series (96 station-pair-days per grade, 30 s epochs, first 30 min of each day removed). The RTK tail comes from wrong fixes and float drift lasting minutes; a Gaussian with the same RMS underestimates it by orders of magnitude. Static geodetic antennas lack vehicle multipath, canopy masking and correction-link outages, and the stations are in the US while the fields are in China; Section 6.5 therefore also tests a degraded-GNSS variant.*

**Simulator.** A closed-loop simulator (time step 0.05 s, speed 2 m/s) integrates kinematic steering with a first-order steering lag of 0.25 s, 35° saturation and a 30°/s rate limit; terrain slip proportional to the lateral gradient plus Ornstein–Uhlenbeck roughness, both scaled by per-run soil moisture; a 2.6 m antenna with roll compensation $0.85\pm0.05$; a per-run mounting bias (standard deviation 1.5 cm); and GNSS error projected on the lateral axis. Passes are executed in real time order with headland turns, so adjacent passes read the same error series one pass duration apart. The default controller is LQR with integral action (LQR-I); pure pursuit, Stanley, a slip observer (Lenain et al., 2006) and offset-free MPC (Pannocchia and Rawlings, 2003) are alternatives. The footprint is centred on the vehicle reference point (a rigidly mounted implement); Section 6.5 tests a trailed implement. Details are in Appendix C.

<!-- source: experiments/exp_system.py (REGIMES) -->
| Configuration | Fields | GNSS grade | Width $w$ | Soil moisture | Vendor pass-to-pass |
|---|---|---|---|---|---|
| R1 RTK, flat, 3 m | wheat (plain) | RTK | 3 m | Beta(2, 3) | 2.5 cm |
| R2 RTK, hilly-wet, 1.5 m | paddy (hilly) | RTK | 1.5 m | 0.6–0.9 | 2.5 cm |
| R3 DGPS, hilly, 6 m | paddy (hilly) | DGPS | 6 m | Beta(2, 3) | 20 cm |

*Table 3. Machine configurations (one implement width, GNSS grade and controller each). The mixed fleet of Section 6.4 pools all three. Paddy slopes come from the 30 m elevation model, which does not resolve levelled basins; Section 6.5 tests levelled terrain.*

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

Pre-registrations were committed before the corresponding computations (Supplementary Table S20 lists the status of every result). All registered zero-data experiments used the extreme-value model without the field-edge terms; validity is unaffected, and Section 6.2 reports what the edge terms change.
