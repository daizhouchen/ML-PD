# Contributing

Use Python 3.12 and the locked environment. Run `python -m pytest -q` and a synthetic CLI smoke experiment before proposing changes.

Changes to feature processing, splitting or scoring should include a regression test that catches leakage or incorrect provenance, and update `docs/methodology.md`. Keep held-out data out of fit/parameter-selection calls. Do not choose new seeds or splits based on improved scores.

Do not commit cooperative datasets, subject identifiers or files from `runs/`. New public study data require documented licensing, provenance and a reviewed study design. Public showcase assets must state whether they are synthetic or research results.

Historical notebooks remain an archive. Put new executable functionality in `src/mlpd` and document differences from older experiments instead of silently rewriting historical results.
