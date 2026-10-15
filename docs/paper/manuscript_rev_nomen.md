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
| $S$ | run score (covering radius minus $w/2$, plus the planned margin; Lemma 1) |
| $\lambda_\mathrm{ref}$ | margin of the reference plan on which scores are calibrated |
| $\varepsilon$, $\delta$ | tolerated probability of a run with a missed strip; PAC confidence parameter |
| $k_\star$ | rank of the conformal order statistic |
| $\lambda^\star_f$ | field $f$'s own requirement: the smallest margin with P(no miss) = $1-\varepsilon$ (oracle) |
| $\hat q_f$ | model-predicted $(1-\varepsilon)$ score quantile of field $f$ (pivot) |
| $\kappa$ | transfer factor from the reference plan to the deployed plan (Theorem 2) |
| $\tau$, $r$ | tolerated gap width; cost ratio of a missed to an over-applied unit area |
| CE, CE-q, CE+ | conformal erosion with target-field runs (Table 2) |
| XCE-T, XCE-MC | cross-field conformal erosion with an analytic or Monte Carlo model pivot |
| CPrP, UBCP | comparators: conformal predictive programming (Zhao et al., 2024); union-bound conformal planning, pair level (Lindemann et al., 2023) |
| CPP | coverage path planning |
| BCD | boustrophedon cellular decomposition |
| LQR-I | linear-quadratic regulator with integral action |
| XTE | cross-track error reported by the autosteer |
| PAC | probably approximately correct (training-conditional) |
| pp | percentage points |
