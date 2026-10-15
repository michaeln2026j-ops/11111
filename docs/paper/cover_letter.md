[Date]

The Editor-in-Chief
*Computers and Electronics in Agriculture*

Dear Editor,

We submit the manuscript **"Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Model-Pivoted Cross-Field Calibration for Agricultural Field Operations"** for consideration as a Research Paper in *Computers and Electronics in Agriculture*.

**The problem.** Coverage path planners assume exact execution. In practice, GNSS error, wheel slip and controller dynamics make adjacent passes drift apart and leave unworked strips. Practice responds with a fixed overlap that carries no stated reliability, and the overlap needed varies between fields, terrains, GNSS grades and implements.

**What the paper contributes.**

1. **An exact score.** Complete coverage of a field by an executed plan is equivalent to one number per run, the covering radius of the executed passes, and this is the smallest score that can certify it.
2. **Certified margins with field history.** Conformal calibration of this score gives a miss probability that is assumption-free for the calibrated plan and transfers to plans with fewer passes under an explicit, stated assumption.
3. **Certified margins without field history.** A model of vehicle, terrain and GNSS (analytic or a Monte Carlo twin) puts fields on a common scale for cross-field calibration; the guarantee does not depend on the model's accuracy.
4. **A transparent simulation study.** All confirmatory experiments were pre-registered in a time-stamped repository. The study reports where the method helps (tighter than two conformal planners at the same guarantee; the only efficient scale across a mixed machine fleet), where it does not (within one configuration; under heavy-tailed slip or unstable steering the model loses its advantage), and when a zero-miss certificate is worth its overlap at all (only when a missed area costs about 30–100 times an over-applied one).

**Why it fits the journal.** The work turns a routine decision, how much overlap to plan, into a quantity with a stated reliability, and shows what that reliability costs in agronomic terms. It works with standard guidance hardware and public terrain data, and its limits, including the need for independent ground truth in calibration runs, are stated explicitly.

**Status of the evidence.** All results are from simulation driven by real field boundaries, elevation models and GNSS error series; this is stated in the abstract, the graphical abstract and the limitations. Every registered outcome is reported, including failed and partially met claims. Code, processed data, pre-registrations and raw results will be openly available with a DOI upon publication.

This manuscript has not been published and is not under consideration elsewhere. All authors have approved the submission and declare no competing interests.

Sincerely,

[Corresponding author name]
[Affiliation]
[Email]
