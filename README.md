# Certified coverage planning under execution uncertainty

Code, processed data, pre-registrations and raw results of the paper *Certified Coverage Planning under Execution
Uncertainty: Conformal Erosion with Model-Pivoted Cross-Field Calibration for Agricultural Field Operations*
(manuscript: `docs/paper/manuscript.md`; supplementary material: `docs/paper/supplementary.md`).

All results are from simulation driven by real field boundaries, elevation models and GNSS error series.

## Environment

```
python3 -m pip install -r requirements-lock.txt   # exact versions used (Python 3.13); requirements.txt gives minimums
```
Every script is deterministic (seeds are derived from fixed keys with `exp_system._seed`). No GPU is needed.

## Layout

| Path | Content |
|---|---|
| `experiments/core.py` | fields, terrain, closed-loop simulator, planner, exact run score (Lemma 1), evaluator |
| `experiments/exp_system.py`, `ceplus.py`, `baselines/` | system comparison (Experiment A1), CE / CE-q / CE+, all baselines |
| `experiments/evt_theory.py` | analytic extreme-value model (pivot of XCE-T) |
| `experiments/exp_lowdata.py` | zero-data experiments B1-B3 (repository name E-low) |
| `experiments/truth.py`, `laps.py` | model-mismatch variants (C1) and headland laps (C2) |
| `experiments/data/` | processed inputs: field polygons (`fields.json`), DEM windows (`dem/`), CORS GNSS error series (`cors_errors.npz`) |
| `docs/prereg_*.md` | pre-registrations, each committed before the computations it governs (see `git log`) |
| `results/` | raw results; `results/revision/` holds the revision experiments |
| `scripts/` | analyses, tables and figures |

## Reproducing the paper

Simulation-heavy steps are cached; every cached input of an analysis is committed, so the analyses and figures
run from a fresh clone without simulation.

| Paper item | Script | Output |
|---|---|---|
| Table 1 (GNSS errors) | `scripts/table_gnss.py` | `results/table_gnss.txt` |
| Table 4, Fig. 3 (Experiment A1) | `experiments/exp_system.py` (shards), `scripts/merge_shards.py`, `scripts/analyze_v8.py`, `scripts/rev_v8_reanalysis.py` | `results/v8/`, `results/revision/rv1_v8_reanalysis.txt` |
| Experiment A2 (few runs) | `scripts/rev_resample.py rv3` | `results/revision/rv3_small_n.txt` |
| Table 5 (B1-B3) | `experiments/exp_lowdata.py`, `scripts/analyze_lowdata.py`, `scripts/analyze_lowdata_v3.py` | `results/lowdata*/summary*.txt` |
| B4 (coverage check) | `scripts/validity_resample.py` | `results/lowdata_v3/validity_resample*.txt` |
| Table 6, Fig. 5 (B5) | `scripts/rev_resample.py rv2` | `results/revision/rv2_resampling.txt` |
| B6, Fig. 2 (model accuracy) | `scripts/rev_ml.py`, `scripts/rev_edges.py`, `scripts/check_boundary.py` | `results/revision/rv7_ml.txt`, `rv6_edges_R3.txt` |
| Experiment C (robustness) | `scripts/rev_sims.py` (simulation), `scripts/rev_resample.py rv4`, `scripts/rev_laps.py` | `results/revision/rv4_mismatch.txt`, `rv5_laps.txt` |
| Cost analysis | `scripts/rev_cost.py` | `results/revision/rv_cost.txt` |
| All figures | `scripts/make_paper_figures.py` | `figures/paper/*.pdf, *.png, *.tif` |
| Word / PDF manuscript | `cd docs/paper && pandoc manuscript.md -f markdown+tex_math_dollars -o manuscript.docx --resource-path=.:../..` | |

**Note on the extended margin curves.** `scripts/extend_curves.py` extended the cached margin curves of the zero-data
experiments below $0.6\lambda^\star$ in place. Files written before that step (`results/lowdata_v2/matched_coverage.txt`,
`results/lowdata_v3/summary.txt`, `results/lowdata_v3/validity_resample.txt`) are the registered readings and are kept
unchanged; re-running their scripts now reads the extended curves. The extended readings are
`results/lowdata_v3/summary_extended_curves.txt`, `results/lowdata_v3/validity_resample_extended_curves.txt` and
`results/revision/matched_coverage_extended_curves.txt` (largest difference to the registered reading: one cell,
+3.18 vs +3.10 pp).

## Data sources

- Field boundaries: field–road trajectory dataset of China's agricultural machinery operation platform (Wu et al.,
  2023, Comput. Electron. Agric. 205, 107594); see the dataset's own terms of use.
- Terrain: Copernicus GLO-30 DEM (European Space Agency, 2021, doi:10.5270/ESA-c5d3d65), Copernicus licence.
- GNSS: NOAA CORS observations (public, `s3://noaa-cors-pds`), processed with RTKLIB demo5 (`experiments/data_cors.py`).
- Vehicle GNSS/INS residuals: i2Nav-WHU awesome-gins-datasets (Tang et al., 2022); see the dataset's licence.

The processing scripts that rebuild `experiments/data/` from these sources are `experiments/data_*.py`.
