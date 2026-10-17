[Date]

The Editor-in-Chief
*Computers and Electronics in Agriculture*

Dear Editor,

We submit the manuscript **"Calibrating pass overlap from logged runs to bound the probability of missed strips in agricultural field coverage"** for consideration as a Research Paper in *Computers and Electronics in Agriculture*.

**The problem.** Guidance systems space parallel passes at the implement width minus an overlap. GNSS error, wheel slip and controller dynamics make adjacent passes drift apart and leave unworked strips, and the fixed overlaps used in practice carry no stated reliability; the overlap needed varies between fields, terrains, GNSS grades and implements.

**What the paper contributes.** It proposes conformal erosion, a method that calibrates the overlap margin from logged field operations. The output is a line-spacing setting for the guidance terminal at which the probability of an operation leaving any strip unworked stays below a level chosen by the user; equally, the method states the miss probability of any other margin or gap tolerance.

1. **A coverage score** reduces each logged operation to one number that decides exactly whether a strip was missed, field edges included, and gives margins no larger than the per-pair scores of earlier conformal planners.
2. **Calibration with field history**: the margin is an order statistic of the scores, with a bound that needs no assumption on the error distribution, only exchangeable operations; a transfer check ensures that the deployed plan has no more passes than the calibrated one.
3. **Calibration without field history**: one logged operation from each of many fields is pooled, scaled by a vehicle–terrain–GNSS model (analytic or a Monte Carlo twin); the model affects efficiency, not the field-averaged bound.
4. **A transparent simulation study.** All confirmatory experiments were pre-registered. The study reports where the method helps (4–55% less overlap than two conformal planners with field history; 0.6 percentage points above the per-field optimum across a mixed fleet without it), where it does not (within one configuration; under heavy-tailed slip, unstable steering or guidance that couples passes), and when a zero-miss margin is worth its overlap at all (only when a missed area costs roughly 40–90 times an over-applied one).

**Why it fits the journal.** The work turns a routine decision, how much overlap to plan, into a quantity with a stated reliability, and shows what that reliability costs in agronomic terms. It works with standard guidance hardware and public terrain data, and its limits, including the need for an independent reference of the implement position in the logged operations, are stated explicitly.

**Status of the evidence.** All results are from simulation driven by real field boundaries, elevation models and GNSS error series; this is stated in the abstract, the graphical abstract and the limitations. Every registered outcome is reported, including failed and partially met claims. Code, processed data, pre-registrations and raw results will be openly available with a DOI upon publication.

This manuscript has not been published and is not under consideration elsewhere. All authors have approved the submission and declare no competing interests.

Sincerely,

[Corresponding author name]
[Affiliation]
[Email]
