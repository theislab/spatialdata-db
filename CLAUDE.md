# spatialdata-db

Central hub for the SpatialData-DB stack. This repo (`spatialdata_db`) is the
engine: raw→zarr conversion (`data/<uid>_/…`), the `SpatialDataDBCurator`
(validate/curate against the lamin schema), and lamin registration. Two sibling
repos are vendored under `extern/`:

- `extern/schemas` → spatialdata-schemas — the lamin metadata contract.
  **External / read-only**, pinned at a release tag; a runtime artifact built into
  the instance, not imported. Do not edit in place; bump the tag to advance it.
- `extern/curation` → spatialdata-db-curation — dataset intake, registry, UIDs
  (the single source of truth for UIDs).

## Environment

- pixi only. Commit `pixi.toml`, never `pixi.lock`.
- `pixi run sync` to fetch submodules (`git clone --recursive` on first clone).
- Python per scverse SPEC 0 (current minors; don't pin EOL versions).

## Schema build

- `pixi run -e schema build-schema -- --yes` runs the schema submodule's
  `build_all()` against the **connected** lamin instance (prod by default —
  gated behind `--yes`; pass `--instance <slug>` to assert the target).
- For tests, build against a local throwaway instance; never write to
  `scverse/spatialdata-db` unless explicitly asked.

## Conventions

- Short, maintainer-style output (PRs, commits, comments). No filler.
- Never add "Generated with Claude Code" or any AI-attribution line anywhere.
- Minimal, reviewable diffs; follow scverse conventions and modern Python tooling.
- Stage only relevant files; never `git add -A`.
