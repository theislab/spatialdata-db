# Hub restructure: spatialdata-db as parent, schemas + curation as submodules

## Goal

Make `theislab/spatialdata-db` the central hub. Co-locate `spatialdata-schemas`
and `spatialdata-db-curation` as git submodules under `extern/`, orchestrate
everything through pixi, and remove the cross-repo duplication (esp. UIDs).

## Constraints (decided)

- **Mechanism:** git submodules under `extern/`.
- **Boundary:** curation owns intake + registry + **UIDs** (single source of truth);
  db owns conversion + validation + lamin registration.
- **Schema pinning:** schemas submodule pinned at a release **tag**; hub builds it
  with the hub's own env (schemas repo is external / read-only to us — no pixi there).
- **We do NOT modify the schemas repo.** Pin at existing tag **v0.0.3** for now;
  bump the pointer to v0.0.4/v0.0.5 once those land upstream.
- pixi for everything; never commit `pixi.lock`.

## Phase 1 — submodules + pixi orchestration (this PR, low-risk, reversible)

- [ ] Add submodule `extern/schemas` → theislab/spatialdata-schemas, pinned at `v0.0.3`.
- [ ] Add submodule `extern/curation` → theislab/spatialdata-db-curation (main).
- [ ] `scripts/build_schema.py` — imports `extern/schemas/lamin/build.py` and runs
      `build_all()` against the connected lamin instance (hub env has lamindb+bionty).
- [ ] pixi tasks in `pyproject.toml`: `sync`, `build-schema`, `curation` (delegates
      via `--manifest-path extern/curation/pixi.toml` where useful).
- [ ] `.gitignore`: ensure `pixi.lock` + `.pixi/` ignored.
- [ ] README "Hub layout" + `git clone --recursive` / `pixi run sync` note.
- Verify: `git submodule status` shows both pinned; `pixi run sync` idempotent;
  `python scripts/build_schema.py --help`/import works (no write in CI).

## Phase 2 — UID single source of truth → curation (DONE)

- [x] Audited: both files were the same 4 × 29,791 keyspace; curation's had 965
      uids corrupted by a `10x` → `10x Genomics` find-replace leaking into the uid.
- [x] Curation (spatialdata-db-curation#4): repaired the 965 uids + added
      `tools/mint_uids.py`. Curation is now the sole owner/writer.
- [x] db: deleted `uid_master.csv`, `create_uids.ipynb`, `update_uid_master.py`;
      bumped the `extern/curation` submodule; README points to curation.
- Verified: curation keyspace == db's clean set (0 diff); 107 assignments preserved.
- Deferred to Phase 3: dataset→UID assignments (`datasets_10x.csv` vs `datasets.csv`).

## Phase 3 — dedupe registries + integration smoke CI

- [ ] Reconcile `db/scripts/data/datasets_10x.csv` vs `curation/registry/datasets.csv`.
- [ ] Hub CI job: `sync` → `build-schema` (throwaway instance) → convert one tiny
      dataset → curate → assert valid. Guards the three-layer contract.

## Phase 4 — docs + housekeeping

- [ ] Unify docs (hub readthedocs links out to schema/curation).
- [ ] Fix `pyproject.toml` homepage URLs `timtreis/…` → `theislab/…`.
- [ ] Submodule-bump automation (periodic PR to advance schema tag / curation main).

## Risks / open items

- Submodule friction: contributors must clone `--recursive`; mitigated by `pixi run sync` + README.
- Schema-as-submodule pinned-at-tag is a runtime artifact, not code — document "do not edit `extern/schemas` in place".
- Phase 2 touches the primary key across repos — highest risk, isolated to its own PR.
