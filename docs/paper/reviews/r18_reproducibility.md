# Review r18: Reproducibility and code

**Manuscript:** Certified Coverage Planning under Execution Uncertainty: Conformal Erosion with Theory-Pivoted Calibration for Agricultural Field Operations (Computers and Electronics in Agriculture)
**Reviewer role:** reproducibility and code reviewer
**Material inspected:** `docs/paper/manuscript.md`, `docs/paper/supplementary.md`, and the repository at HEAD `e8307f5` (review started at `e4011c0`; the commits in between change only `scripts/make_paper_figures.py`, the figure files, figure captions and review files, and every figure check below was repeated on `e8307f5`).
**Method:** I read every analysis and run script that the paper cites. I re-ran every analysis script that only reads existing result files, in two scratch copies so that no repository file was modified:
- a **clean clone** (`git archive HEAD`, i.e. exactly what a third party receives);
- a **full copy** of the author's working tree, which also contains the git-ignored `.pkl` intermediates and v8 shard CSVs.

Outputs were compared byte by byte (text) or pixel by pixel (PNG). No simulations were run.

---

## 1. Summary

The repository is unusually complete for a simulation paper:
- Processed inputs are committed: 964 field polygons, 496 DEM windows and 96 station-days × 4 grades of CORS error series.
- Seeds are explicit and independent of `PYTHONHASHSEED`.
- Pre-registrations are committed before their results, and none was edited afterwards.
- Every table in the manuscript carries an HTML comment naming its source file.

On the author's own working tree, almost every analysis I could run reproduced its committed output exactly:
- v8 (Table 5), E-low v1 and v2 (Table 6), the feature-pivot and learning-curve outputs (Table 9 lower block, S12–S14), the v7 summary (S1–S4), and the information-limit prediction (Fig. 7) are byte-identical.
- The extended v3 summary (Table 8, S18) is byte-identical.
- All 8 paper figures are pixel-identical.

**A third party cloning the repository cannot do the same.** The analyses for E-low v3, the resampling check, matched coverage, the feature predictors and Fig. 2 read about 4 MB of `.pkl` intermediates that are listed in `.gitignore`. The v8 analysis reads git-ignored shard CSVs. On a clean clone:
- four of the analysis scripts crash with misleading errors (`Singular matrix`, `No objects to concatenate`);
- the figure script exits successfully but writes a Fig. 2 with *n = 0* fields for R1, R2 and R3.

In addition:
- The registered E-low v3 reading (`results/lowdata_v3/summary.txt`, cited in Tables 6 and 8 and S15–S17) can no longer be regenerated even on the author's machine, because `scripts/extend_curves.py` overwrote the curve pickles in place.
- Several cited result files were produced by renaming outputs or by an unscripted step.
- There is no README, no LICENSE, no pinned environment, no compute budget and no public archive.
- Key provenance documents (pre-registrations, theory notes, experiments report) are 31–57% Chinese.

I also found two numerical inconsistencies between the manuscript and its own source files (Table 3; the regret range in Section 6.3 and Table S20).

None of these problems touches the scientific logic. All of them can be fixed in one or two days.

## 2. Recommendation and scores

**Recommendation (reproducibility aspect): major revision.** The fixes are mechanical: commit the intermediates, add a README with a table-to-command map, regenerate or relabel the registered v3 reading, pin the environment, archive with a DOI, and state licences.

| Criterion | Score (1–10) | Rationale |
|---|---|---|
| Reproducibility | **5** | Everything I ran reproduces exactly on the author's tree. A clean clone reproduces only E-low v1, v7, Figs. 3–7 and (by hand, from the CSV) Table 5. The registered v3 reading is not regenerable. |
| Code quality | **6** | Explicit common-random-number seeding, provenance docstrings, consistent `HERE`-relative paths in the main pipeline. But: scripts overwrite committed results in place, fail silently or cryptically on missing inputs, leave hard-coded absolute paths in data and explore scripts, and keep obsolete pipelines next to current ones. |
| Documentation | **3** | No README or LICENSE. No document maps tables to commands. Obsolete `run_all.sh` and `docs/AUTODL.md` (Chinese, private-repo instructions). Pre-registrations and theory notes are partly in Chinese. "Notes for the authors (remove before submission)" remains in the Supplementary. |
| Data availability | **5** | Processed inputs are in the repo, which is a real strength. But: the repo is private with no URL or DOI in the paper, raw-data rebuild paths point to the author's home directory, the RTKLIB commit was not recorded, and the data-source licences are not stated. |

## 3. Strengths

1. **Processed inputs are committed.** These include `experiments/data/fields.json` (964 fields; 162 wheat and 137 paddy are used after filtering, matching Section 6.1), 496 DEM windows, `cors_errors.npz` with per-epoch metadata and `cors_summary.csv` (384 station-pair-day-grade rows). So the simulator is self-contained and the raw downloads are not needed to re-run experiments.
2. **Seeding is careful.** Every random stream derives from `exp_system._seed(...)` (stated to be "independent of the field, the shard and PYTHONHASHSEED") or from field-indexed seeds. Common random numbers are shared across systems (`exp_system.evaluate`). The field order is fixed by `core.load_fields(seed=0)`.
3. **The pre-registrations are verifiably ordered in the git history.** Each pre-registration file has a single commit, before its first result:

   | Pre-registration (first commit) | First result (first commit) |
   |---|---|
   | `prereg_lowdata.md` 05:27 | 13:49 |
   | `prereg_lowdata_v2.md` 14:49 | 16:38 |
   | `prereg_lowdata_v3.md` 17:04 | 18:55 |
   | `prereg_validity.md` 19:04 | 19:50 |
   | `theory_v8.md` 02:39 / 02:57 | v8 result 21:33 |

4. **Analyses reproduce bit-exactly when their inputs are present.** See the table in Section 6. The regret table (`results/v8/regret_table.txt`) also re-derives exactly from the `regret_pp` and `oracle_overlap` columns of `results/v8/system_v8.csv`.
5. **Tables are traceable.** Each manuscript table names its source file in an HTML comment, and Table S20 labels the status of every result.
6. **Field-logger tests pass.** `tools/feedcar/test_feedcar.py` passes ("ALL TESTS PASSED") without ROS.
7. **Figures are built from result files only.** `scripts/make_paper_figures.py` does no re-simulation, and on the full tree all 8 figures regenerate pixel-identically to the committed PNGs.

## 4. Major issues

### M1. Intermediate files needed by the main analyses are git-ignored, so a clean clone cannot reproduce Tables 6 (v3 row), 7, 8, 9 (lower block), S11–S19 or Fig. 2

- **Location:** `.gitignore` lines 3–10 (`results/lowdata*/A_*.pkl`, `curve_*.pkl`, `hist_*.pkl`, `results/system_v8_shard*.csv`). Readers of these files:
  - `scripts/analyze_lowdata_v3.py` (l. 46, 169)
  - `scripts/validity_resample.py` (l. 30–55)
  - `scripts/matched_coverage.py` (l. 45–51)
  - `scripts/feature_pivot.py` (l. 37)
  - `scripts/feature_learning_curve.py`
  - `scripts/predict_limit.py` (l. 25)
  - `scripts/check_boundary.py`, `scripts/time_theory.py`
  - `scripts/make_paper_figures.py` (l. 160)
  - `scripts/analyze_v8.py` (l. 29)
- **Evidence (clean clone of HEAD):**
  - `analyze_v8.py` exits with `ValueError: No objects to concatenate`.
  - `analyze_lowdata_v3.py` and `feature_pivot.py` exit with `numpy.linalg.LinAlgError: Singular matrix`.
  - `feature_learning_curve.py` exits with `ValueError: a must be a positive integer`.
  - `make_paper_figures.py` exits 0 and writes `fig_theory_vs_sim.png` with legend entries "R1 … (n = 0)", "R2 … (n = 0)", "R3 … (n = 0)", i.e. a silently wrong Fig. 2. The other 7 figures are pixel-identical.
- **Why it matters:** The paper's Data availability statement promises "raw results and the scripts that generate every table and figure". For the zero-data half of the paper this is currently not true for anyone but the author. The silent Fig. 2 failure is the most dangerous case.
- **Fix:**
  1. Remove these patterns from `.gitignore` and commit the files. They total about 4 MB: lowdata 0.6 MB, v2 1.1 MB, v3 0.5 MB, v8 shards 1.6 MB.
  2. Alternatively, put them in the DOI archive and add a `scripts/fetch_intermediates.sh`.
  3. Let `analyze_v8.py` fall back to the committed `results/v8/system_v8.csv` when no shards are present.
  4. Make every reader fail loudly when its glob is empty (`assert files, f"no A_*.pkl in {d}; see README"`).

### M2. The registered E-low v3 reading is no longer regenerable, and rerunning overwrites it

- **Location:** `scripts/extend_curves.py` ("Updates curve_*.pkl in place"), `scripts/analyze_lowdata_v3.py` (writes `results/lowdata_v3/summary.txt`, l. 244), `scripts/validity_resample.py` (writes `validity_resample.txt`, l. 96).
- **Evidence:** On the full tree, `analyze_lowdata_v3.py` now reproduces `summary_extended_curves.txt` byte for byte, and differs from the registered `summary.txt` in 50 diff lines. Running it also **overwrites** `summary.txt`. That file is the registered result cited in:
  - Table 6 (v3 row);
  - Table 8, column 1 ("registered");
  - Tables S15–S17;
  - the "40.9% less excess" and Holm p values in Sections 6.4 and 6.6.

  The same happens with `validity_resample.py` and `validity_resample.txt` (registered reading, Table S19). No script writes `summary_extended_curves.txt` or `validity_resample_extended_curves.txt`: they were created by running the scripts after `extend_curves.py` and renaming the output by hand (commit `f50e92e` adds only the two text files).
- **Why it matters:** The pre-registered result, which is the paper's evidentiary core for C3, C4 and C5, is not regenerable from the code. Anyone re-running the pipeline also destroys the committed registered file.
- **Fix:**
  1. Give `extend_curves.py` a separate output (`curve_ext_*.pkl`) or keep the original grid under a key.
  2. Add a `--curves {registered,extended}` flag and an explicit `--out` to `analyze_lowdata_v3.py` and `validity_resample.py`.
  3. Regenerate and commit both readings with the commands recorded.
  4. Make all analysis scripts write to new files (or refuse to overwrite a committed file without `--force`).

### M3. No README, no table-to-command map, and obsolete or misleading entry points

- **Location:** repository root (no `README*`). Also:
  - `scripts/run_all.sh` runs the superseded v4 experiments (`exp_main.py --tag _v4`, `exp_cross.py`, …), none of which feed the paper.
  - `docs/AUTODL.md` (29% Chinese) tells users to clone a private branch `claude/quirky-fermat-nr94ww` with a personal access token.
  - `results/superseded_v3/`, `figures/superseded/`, `figures/fig*.png`, `experiments/make_figures*.py`, `make_tables.py`, `sim/` and `control/queue/` sit next to current code without labels.
- **Why it matters:** A reader cannot tell which of the 31 scripts and 22 experiment modules produce the paper. The only orchestration script with a generic name (`run_all.sh`) runs the wrong experiments. Some steps are invisible:
  - `results/v7/summary.txt` is the concatenation of `agg7.py` and `pareto7.py` output (I verified the first 137 lines are identical to `agg7.py`).
  - E-low v2 requires `analyze_lowdata.py results/lowdata_v2 --v2`.
- **Fix:** Add a `README.md` with:
  1. the environment set-up;
  2. a "reproduce the paper from committed results (minutes)" section with one command per table and figure (Section 6 below can serve as a template);
  3. a "re-run the simulations (CPU hours, cores)" section listing `run_v8.sh`, `run_lowdata*.sh`, `curves_v3.py`, `extend_curves.py`, `validity_resample.py`, `check_boundary.py R3` and `check_boundary.py R1 R2 --limit 4`, in order;
  4. a "rebuild inputs from raw data" section.

  Then move superseded material to `archive/` or delete it, and add a `Makefile` or `reproduce.sh` with a `paper` target.

### M4. The environment is not pinned, and dependencies are incomplete

- **Location:** `requirements.txt` (only `>=` lower bounds, "newer minor versions should work").
- **Evidence:** The environment I used was Python 3.13, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5, scikit-learn 1.9.1, matplotlib 3.11.2. These are well above the floors, and outputs still matched. But:
  - The committed `.pkl` intermediates are numpy-version-dependent pickles.
  - Matched-coverage rows using ridge/CQR differ slightly (see M5).
  - `rasterio` and `py7zr` are listed but absent here.
  - Imports missing from `requirements.txt`: `threadpoolctl` (guarded), `hatanaka` (needed by `data_cors.py`), `osqp` (verification only), `pyyaml` and ROS `rospy` (`tools/feedcar`).
  - RTKLIB demo5 is a binary dependency whose commit "was not recorded" (manuscript reference list).
  - Fonts matter for the figures (Liberation Sans).
- **Fix:**
  1. Add a lock file with exact versions (`pip freeze > requirements-lock.txt`, or `environment.yml`) recorded from the environment that produced the committed results, and state the Python version.
  2. Split optional extras (`requirements-data.txt`, `requirements-logger.txt`).
  3. Prefer `.npz` or `.parquet` over pickles for long-term archives.
  4. Record the RTKLIB commit hash in the archive, or ship the `rnx2rtkp` config files plus the `.pos` outputs.
  5. Add a Dockerfile or `environment.yml`.

### M5. Several cited numbers are not produced by any script or do not match their sources

1. **Table 3, R3 "First version" "36.0 / 37.3 (−3.5%)".** The cited source `docs/theory_evt.md` (l. 345) says: "36.0 / 37.09 (**−2.9%**; the earlier recorded reference value was 37.3, uniformly use 37.09)". The manuscript uses the value its own source says to discard. **Fix:** change it to 36.0 / 37.09 (−2.9%).
2. **Section 6.3 and Table S20: "CE+ is 27–92% below the comparators in the ten comparisons where its regret is positive".** Both `results/v8/regret_table.txt` and my recomputation from `system_v8.csv` give 95% for R3 marginal vs Lindemann ((8.94 − 0.45)/8.94). The commit message `170c4f3` also says "27–95%". **Fix:** change it to 27–95%.
3. **Table 1 (GNSS error statistics)** cites `docs/experiments_report.md`, a Chinese document, and no script computes it. Recomputing from the committed `cors_errors.npz` (horizontal error, all series) gives RTK-fixed:
   - all epochs: RMS 2.9 cm, p95 3.6 cm, p99.9 31 cm;
   - first 30 min removed (as Supplementary C.1 states): RMS 2.4 cm, p95 3.3 cm, p99.9 24.5 cm;
   - Table 1: RMS 2.7 cm, p95 4.2 cm, p99.9 24 cm.

   DGPS gives 32.5 cm, 58 cm and 2.05 m against Table 1's 30 cm, 53 cm and 1.8 m. The maxima match (1.39 m, 6.0 m, 7.2 m). Table 1 may have been computed on segmented or interpolated series (≥ 2 h segments, 1 Hz). **Fix:** add a script (e.g. `scripts/table1_gnss.py`) that states the exact definition and writes `results/gnss_stats.txt`, and cite that file.
4. **Table 9, upper block (0.047, 0.388, 0.433, 0.136, 0.054)** is cited from `docs/prereg_lowdata_v3.md` §0, a design-probe table in a mixed-language document. I found no script that computes it. **Fix:** commit the probe script and its output.
5. **`results/v8/regret_table.txt`** (Table 5 regret column, Fig. 3 numbers) has no generating script. The numbers do re-derive from the CSV. **Fix:** add the few lines to `analyze_v8.py`.
6. **`results/lowdata_v2/matched_coverage.txt` (Table S11)** no longer reproduces exactly. Rerunning on the full tree changes 10 lines. The one cited in the text is R3 PAC "CQR, field features (one-run trained)", where the rerun gives +3.18 pp against the committed and cited +3.10 pp (Section D.4, "+2.73 and +3.10 pp in R3"). The other 9 are sensitivity rows (ε = 0.2 or n_cal = 10). The likely cause is that `extend_curves.py` also mutated the v2 curve pickles (see M2); library drift is also possible. **Fix:** regenerate under a pinned environment and record which curve grid it uses.

### M6. Data provenance and licences are not stated, and the code has no licence

- **Location:** manuscript "Data availability"; repository root (no LICENSE); `experiments/data_fields.py` l. 23–24, `data_rtk.py` l. 16, `data_cors.py` l. 90–91.
- **Issues:**
  1. **No code licence.** Without one, the code cannot legally be reused even when public.
  2. **Upstream licences are not stated in the paper.** I could not verify the upstream licences online from this session, so they need to be checked:
     - **Field–road trajectory dataset** (Wu et al., 2023; GitHub `wefwrffa`): licence not stated anywhere in the repo. The repo **redistributes derived georeferenced field polygons** (`fields.json` contains lon/lat and ENU polygons of 964 real fields from a Chinese national machinery platform). Redistribution rights must be confirmed.
     - **Copernicus GLO-30:** free, but its licence requires a specific attribution notice. The repo redistributes 496 DEM windows (`experiments/data/dem/*.npz`).
     - **NOAA CORS:** US federal data, generally unrestricted; acknowledge NGS.
     - **i2Nav awesome-gins-datasets** (Tang et al., 2022): licence not stated. Its residuals are embedded in the simulator via `rtk_error.npz`.
     - **CitrusFarm:** `data_citrus.py` states CC BY-SA 4.0. The repo redistributes 7 `gt_*.csv` files, which requires attribution and ShareAlike for the derived data.
     - **RTKLIB:** BSD-2-Clause, used as a tool only.
  3. **Raw rebuild paths are hard-coded to the author's machine:**
     - `/home/user/wefwrffa/field-road-trajectory-dataset/paddy_*/*.xlsx`
     - `/home/user/data/wheat/*/*.xlsx` (how the wheat files are obtained, presumably extracted from a `.7z` given `py7zr`, is undocumented)
     - `/home/user/data/i2nav`
     - `/home/user/data/cors` and `/home/user/RTKLIB` (overridable by environment variables)
     - `CURL_CA_BUNDLE=/root/.ccr/ca-bundle.crt` (`data_dem.py` l. 21, a sandbox-specific proxy CA)
     - `/home/user/11111/...` in `scripts/explore/*.py`
  4. **No public location.** The repository is private (`docs/AUTODL.md`), the paper gives no URL, and the DOI is a "TODO".
- **Fix:**
  1. Add `LICENSE` (e.g. MIT or BSD-3 for the code) and `DATA_LICENSES.md` listing each source, URL, version or access date, licence and attribution text.
  2. Confirm redistribution rights for the Wu et al. polygons and i2Nav residuals; if they are not granted, ship only the rebuild scripts plus checksums.
  3. Replace absolute paths with CLI arguments or environment variables with documented defaults relative to `data/raw/`.
  4. Remove the proxy CA line.
  5. Archive a tagged release on Zenodo (or similar) and cite the DOI and URL in Data availability.

## 5. Minor issues

1. **Author notes left in the submission.** `docs/paper/supplementary.md` Appendix E is titled "Notes for the authors (remove before submission)". It is part of the submission package (`supplementary.docx`, `supplementary_preview.pdf`). Remove it.
2. **Unresolved TODOs.** The manuscript still contains two "TODO" items: Section 6.7, real-vehicle validation, and the DOI in Data availability. A reproducibility reviewer will read "TODO: archive with a DOI" as data not yet available.
3. **Language.** The cited provenance documents `docs/prereg_lowdata*.md`, `prereg_validity.md`, `theory_v8.md`, `theory_evt.md`, `theory_limit.md` and `experiments_report.md` contain 31–57% Chinese characters. An international reviewer cannot audit the pre-registered claims against the paper. Provide English versions, or English translations alongside the frozen originals (with the original commit hash cited for timestamping).
4. **Pre-registration evidence.** It rests on git commit timestamps in a private repository, all on one calendar day. These timestamps are set by the author and can be rewritten. Supplementary Appendix E already suggests OSF. At minimum, include the commit hashes of each pre-registration in the paper and push a signed tag or archive snapshot.
5. **Data availability omits `docs/theory_v8.md`.** That file holds the v8 pre-registration (`scripts/run_v8.sh` header: "pre-registered in docs/theory_v8.md section 3").
6. **No compute budget.** The paper does not state CPU-hours or cores for v8 (45 shards), E-low phase A (≈ 90–150 fields × 16–353 s of theory plus oracle simulations), the v3 curves or the 200-run history banks. `docs/AUTODL.md` recommends ≥ 32 cores. Add a table of wall time and cores per experiment.
7. **Silent shape assumptions.** `merge_shards.py` checks run consistency, but `analyze_v8.py` concatenates whatever shards it finds without checking that all 45 are present. Assert `len(files) == 45`.
8. **Exploratory scripts hard-code `/home/user/11111`.** These are `scripts/explore/pivots.py`, `probe.py` and `transfer.py`, and they support "exploratory analysis" statements in Section 6.4. Make the paths relative.
9. **`pickle.load(open(...))` without context managers** throughout. The files are never closed explicitly, and loading pickles from an archive is a code-execution risk for third parties. Prefer `np.savez`.
10. **`results/logs/` is git-ignored** (1.4 MB, 321 files) but contains the only record of the run commands and timings (`jobs_v8.txt`, `run_v8_local.log`). Consider committing it or including it in the archive.
11. **The `experiments/__pycache__`, `scripts/__pycache__` and `experiments/baselines/__pycache__` directories exist locally.** They are ignored, so this is harmless, but `.pyc` files should not go into the archive tarball.
12. **The CitrusFarm replay results** (`results/real.csv`, `real_aci.csv`) are committed but "not summarised". Either summarise them in the Supplementary or move them out of `results/`.
13. **Table 7 uses `validity_resample_extended_curves.txt`.** The re-run on the full tree completed 19 of 26 cells within my 2-minute cap, and all 19 matched the committed file exactly; the remaining 7 are unchecked. A full run takes roughly 3 minutes on 4 cores. Document this in the README.
14. **`docs/paper/draft.md` is described as "the full archive of the analysis"** but is a 134 k-character working draft. Label it clearly as non-authoritative, or remove it from the submission repository.

## 6. Paper item → script → status

Status key:
- **reproduced:** I re-ran the script in this review and the output is identical to the committed file, or I re-derived the cited numbers from committed data.
- **reproduced (author tree only):** identical, but it needs git-ignored files.
- **not checked:** needs simulation or theory runs (beyond the 2-minute limit), or no script exists.
- **broken:** the script fails, the output differs from what is cited, or the cited value disagrees with its source.

| Paper item | Source file cited | Producing script / command | Status |
|---|---|---|---|
| Table 1 GNSS error statistics | `docs/experiments_report.md` | none (data from `experiments/data_cors.py`) | **broken**: no script; recomputation from `cors_errors.npz` gives different RMS, p95 and p99.9 under both natural definitions; maxima match |
| Table 2 regimes | `docs/experiments_report.md` | `experiments/exp_system.py` `REGIMES` | reproduced (configuration matches the code) |
| Table 3 theory q0.9 (developmental) | `docs/theory_evt.md` §6.2 | `scripts/check_evt.py` (simulation) | not checked; **broken** transcription: R3 first version should be 37.09 / −2.9% per source |
| Table 4 field-edge terms | `results/lowdata_v3/check_boundary_R3.txt`, `check_boundary_R1_R2.txt` | `scripts/check_boundary.py R3`; `scripts/check_boundary.py R1 R2 --limit 4` (theory runs) | not checked (numbers match the files) |
| Table 5 v8 confirmatory | `results/v8/summary.txt`, `regret_table.txt` | `scripts/analyze_v8.py` (merges git-ignored shards); regret: no script | reproduced (author tree only; the clean clone crashes); regret re-derived from `system_v8.csv`; text "27–92%" **broken** (should be 27–95%) |
| Table S22 v8 applied overlap | `results/v8/summary.txt` | `scripts/analyze_v8.py` | reproduced (author tree only) |
| Table 6, E-low v1 row | `results/lowdata/summary.txt` | `scripts/analyze_lowdata.py` | **reproduced on a clean clone** |
| Table 6, E-low v2 row; S8–S10 | `results/lowdata_v2/summary.txt` | `scripts/analyze_lowdata.py results/lowdata_v2 --v2` | reproduced (summary and tests CSV identical) |
| Table 6, v2 matched coverage; S11 | `results/lowdata_v2/matched_coverage.txt` | `scripts/matched_coverage.py` (needs `.pkl`) | **broken**: 10 lines differ on rerun, incl. the cited R3 PAC CQR value (+3.18 vs +3.10 pp); the main reported pivot spreads are unchanged |
| Table 6, E-low v3 row; Table 8 col. 1; S15–S17 | `results/lowdata_v3/summary.txt` | `scripts/analyze_lowdata_v3.py` | **broken**: not regenerable after `extend_curves.py`; rerun overwrites the registered file; clean clone crashes |
| Table 8 col. 2; S18 | `results/lowdata_v3/summary_extended_curves.txt` | `extend_curves.py`, then `analyze_lowdata_v3.py` + manual rename | reproduced (author tree only; output byte-identical) |
| Table 7; Table 8 col. 3; Fig. 4; Fig. 5 | `results/lowdata_v3/validity_resample_extended_curves.txt` | `scripts/validity_resample.py` after `extend_curves.py` + manual rename | reproduced for 19/26 cells (author tree only; 2-minute cap); remaining 7 not checked |
| Table S19 registered resampling | `results/lowdata_v3/validity_resample.txt` | `scripts/validity_resample.py` (pre-extension curves) | **broken**: not regenerable after `extend_curves.py` |
| Table 9 upper block (design probe) | `docs/prereg_lowdata_v3.md` §0 | none found | not checked (no script) |
| Table 9 lower block; S14; Fig. 6 | `results/lowdata_v2/feature_learning_curve.txt` | `scripts/feature_learning_curve.py` | reproduced (author tree only; clean clone crashes) |
| Table S12, S13 | `results/lowdata_v2/feature_pivot.txt` | `scripts/feature_pivot.py` | reproduced (author tree only; clean clone crashes) |
| Tables S1–S4 (v7) | `results/v7/summary.txt` | `scripts/agg7.py results/v7` + `scripts/pareto7.py results/v7` (concatenated, undocumented) | reproduced (`agg7` part identical) |
| Table S5 layer validation | `docs/theory_evt.md` §6 | `scripts/check_evt.py` (simulation) | not checked |
| Table S21 theory runtime | `results/lowdata_v3/theory_runtime.txt` | `scripts/time_theory.py` (runs the theory on 9 fields, ~30 min) | not checked |
| Fig. 1 schematic; graphical abstract | none | `scripts/make_paper_figures.py` | reproduced (pixel-identical) |
| Fig. 2 theory vs simulation | `results/lowdata_v2`, `results/lowdata_v3` `.pkl`, `check_boundary_R3.txt` | `scripts/make_paper_figures.py` | reproduced on the author tree; **broken on a clean clone** (silently plots n = 0 for R1–R3) |
| Fig. 3 v8 regret | `results/v8/system_v8.csv` | `scripts/make_paper_figures.py` | **reproduced on a clean clone** (pixel-identical) |
| Figs. 4, 5 | `validity_resample_extended_curves.txt` | `scripts/make_paper_figures.py` | **reproduced on a clean clone** (pixel-identical, from the committed text file) |
| Fig. 6 learning curves | `feature_learning_curve.txt` | `scripts/make_paper_figures.py` | **reproduced on a clean clone** (from the committed text file) |
| Fig. 7 information limit | `docs/theory_limit.md`, `feature_pivot.txt` | `scripts/predict_limit.py` (needs `.pkl`) + `make_paper_figures.py` | reproduced (predicted 1.296 ± 0.347, 1.257 ± 0.328, 1.847 ± 0.740 match `theory_limit.md` to the shown precision); figure pixel-identical |
| Section 4.4 / 7.4 runtime 16–353 s | `theory_runtime.txt` | `scripts/time_theory.py` | not checked |
| Section 5.1 numerical check (6 fields × 200 runs) | none cited | unclear (probably `scripts/check_evt.py` or `explore/`) | not checked (no source named) |
| Theorem 5 numeric check (S5 transfer rows) | `docs/theory_evt.md` | `scripts/check_transfer.py` (simulation) | not checked |
| Field logger / offline certification (Section 6.7) | none | `tools/feedcar/test_feedcar.py` | reproduced ("ALL TESTS PASSED") |

**Scripts run in this review** (scratch copies only; no repository file was modified):
- `analyze_v8.py`, `analyze_lowdata.py` (v1 and `--v2`), `analyze_lowdata_v3.py`
- `feature_pivot.py`, `feature_learning_curve.py`, `matched_coverage.py`
- `validity_resample.py` (2-minute cap), `predict_limit.py`
- `agg7.py`, `make_paper_figures.py` (both versions), `tools/feedcar/test_feedcar.py`
- an import smoke test of `core`, `exp_lib`, `evt_theory`, `ceplus`, `exp_system`, `exp_lowdata`
