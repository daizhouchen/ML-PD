# Changelog

## Repository organization — 2026-09-26

- Separated current Python code (`src/`), current tutorials (`notebooks/`), research/developer guides (`guides/`), the Pages site (`docs/`) and historical artifacts (`archive/`).
- Moved and renamed eight historical notebooks without changing their contents; added an old-to-new path index.
- Added a task-based README, complete run guide, module map and directory entry points. Updated site, Notebook and documentation links.
- Grouped static assets under `docs/assets/` and marked generated results for GitHub review. Kept the public site URL, experiment implementation and published numerical results unchanged.
- Formatted the HTML, CSS and JavaScript sources for readable maintenance.


## 0.2.0 — 2026-09-26

- Added an installable Python package and CLI for explicit data validation, synthetic fixtures, four classification tasks, nested evaluation and figure generation.
- Moved preprocessing and RFE inside inner-CV training pipelines. Added subject-separated outer and inner splits, reproducible seeds and run fingerprints.
- Added seven comparison models including a prior baseline, fold-level metrics, OOF confusion matrices, mean per-fold OVR ROC and feature-selection frequency.
- Added tests for input failures, grouped splits, actual preprocessing fit partitions, a real nested run and private-report publication rejection.
- Added a static research showcase with task/model/metric controls, downloadable synthetic aggregate results and standalone SVG figures.
- Retained historical notebooks without rewriting old experimental outputs. Documented their methodological limitations and removed unsupported progression/diagnosis claims from the main project introduction.
- Original cooperative data remain unavailable; no new clinical or original-cohort performance claim is made.
