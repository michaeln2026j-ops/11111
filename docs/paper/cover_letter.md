[Date]

The Editor-in-Chief
*Computers and Electronics in Agriculture*

Dear Editor,

We submit the manuscript **"Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations"** for consideration as a Research Paper in *Computers and Electronics in Agriculture*.

**The problem.** Coverage path planners for field operations assume exact execution. In practice, GNSS error, wheel slip and controller dynamics make adjacent passes drift apart and leave unworked strips. Farmers and vendors respond with a fixed overlap, but no stated probability of complete coverage comes with it, and the overlap needed varies strongly between fields, terrains, GNSS grades and implements.

**What the paper contributes.**

1. **An exact reduction.** The zero-miss event of a coverage plan is reduced to a scalar run score (the covering radius of the executed passes). We prove that this is the smallest score that yields valid certificates.
2. **Distribution-free certificates.** Conformal erosion calibrates the footprint margin from logged runs and gives finite-sample, distribution-free guarantees of miss-free operation. A coupling inequality bounds the effect of re-planning.
3. **Certification without field history.** A five-layer extreme-value theory of execution error predicts each field's required margin from controller, terrain and GNSS statistics alone. Used as a pivot for cross-field conformal calibration, it certifies fields that have never been worked. The method takes 0.3–6 min per field on one CPU core.
4. **Evaluation.** The evaluation uses real field boundaries, elevation models and multi-station GNSS error series, under three machine configurations. A pre-registered comparison on 90 fresh fields met every validity and efficiency claim: 4.0–54.7% less overlap than two recent conformal planners at the same guarantee level. A pre-registered resampling check confirmed the coverage guarantee in all 26 cells.

**Why it fits the journal.** The work turns a routine agronomic decision, how much to overlap, into a certified, computable quantity. It can be used directly with standard guidance hardware, auto-steer logs and public terrain data. It also connects agricultural guidance with current methods in conformal prediction and extreme-value theory.

**Transparency.** Every confirmatory experiment was pre-registered in a timestamped repository before it was run. All registered outcomes, including one zero-data experiment that failed and the cells in which no method can improve (an information limit we derive and predict), are reported in full. Code, data-processing scripts, pre-registrations and raw results will be made openly available upon publication.

This manuscript has not been published and is not under consideration elsewhere. All authors have approved the submission and declare no competing interests.

Thank you for considering our work.

Sincerely,

[Corresponding author name]
[Affiliation]
[Email]
