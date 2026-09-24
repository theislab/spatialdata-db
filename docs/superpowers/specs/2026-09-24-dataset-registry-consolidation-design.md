# Dataset registry consolidation — design

**Date:** 2026-09-24
**Status:** Draft for review
**Scope:** Repo organisation across `spatialdata-db` (hub), `spatialdata-db-curation`,
`spatialdata-schemas`. Phase 3 of the spatialdata-db effort (Phase 1 = hub structure,
Phase 2 = UID consolidation into curation, both merged).

## Intent

Establish a single-owner repo layout for all dataset/curation data, eliminating the
duplicated `datasets_10x.csv` scrape and the ambiguity over which repo owns the dataset
registry versus consumes it. This is primarily a **repo-organisation** change; the CSV
column reconciliation is an implementation detail kept deliberately minimal and is
**not** derived from lamin schema/ontology logic.

Success criteria:
- Exactly one owner per concern; no dataset CSV duplicated across repos.
- The hub and any downstream consume dataset data through the `extern/curation`
  submodule only.
- `registry/datasets.csv` is the single canonical dataset registry, with every row
  linked to a uid where one can be assigned deterministically.
- The consolidation is reproducible (a re-runnable tool), and rows a machine cannot
  safely link are reported for human review, never guessed.

Non-goals (explicitly out of scope):
- Redesigning the registry column schema around lamin ulabels/ontologies.
- Adding per-tech normalized extension tables. Keep the current flat
  `registry/datasets.csv`; fold in the scrape's fields pragmatically.
- Any change to `spatialdata-schemas` data (it holds lamin schema definitions only).

## Current state (as of 2026-09-24)

Duplication of the raw 10x scrape (`datasets_10x.csv`, 212 rows, `;`-separated,
34 mixed columns):
- `spatialdata-db/scripts/data/datasets_10x.csv` (tracked)
- `spatialdata-db-hub/scripts/data/datasets_10x.csv` (tracked)
- `spatialdata-db-uids/scripts/data/datasets_10x.csv` (tracked; worktree of `db`)
- `spatialdata-db_old/.../data/datasets_10x.csv` (stale legacy)

Curation (`extern/curation`, sole UID owner since Phase 2):
- `registry/uids.csv` — 119,165 rows, `uid;source;id` (keyspace, canonical).
- `registry/datasets.csv` — 207 rows, `,`-separated, 22 cols; 110 have `local_uid`
  (all 110 match uids in the scrape), 97 have none. All rows are 10x-manufacturer.
- `scripts/metadata/datasets_merged.csv` — 207 rows, ~identical to `datasets.csv`
  plus an extra `Software` column (near-dupe of the registry).
- **The raw scrape `datasets_10x.csv` is NOT in curation** — it lives only in the db
  repos above.

Linkage analysis (scrape ↔ registry):
- 110 registry rows link to scrape uids exactly; 0 registry-only uids.
- 102 scrape uids are absent from the registry (new datasets to fold in).
- Of the 97 uid-less registry rows, ~57 are matchable to a scrape row by normalized
  `primary_source` URL; the remainder collide (one 10x landing page lists multiple
  libraries/replicates), so URL alone is not a unique key.

## Target repo organisation

Single owner per concern, following the Phase 2 pattern (curation owns keyspace, hub
consumes via submodule):

- **`spatialdata-db-curation`** — single source of truth for all curation data + tooling:
  - `registry/uids.csv` — keyspace (unchanged).
  - `registry/datasets.csv` — the one canonical dataset registry (curated **output**).
  - `sources/datasets_10x.csv` — the raw 10x scrape as a clearly-labeled **input**
    (moved here; the scraper refreshes it; it is not the registry).
  - `tools/` — `mint_uids.py` (exists) + `reconcile_datasets.py` (new): turns the
    scrape input into registry rows.
- **`spatialdata-db` (hub)** — consumes curation through `extern/curation`. Deletes its
  own `scripts/data/datasets_10x.csv`. Any code that read the local copy reads the
  submodule path instead.
- **`spatialdata-schemas`** — lamin schema definitions only. Untouched by this work.
- **`spatialdata-db-uids`** (worktree of `db`) — transitional; its copy goes with the
  `db` deletion. **`spatialdata-db_old`** — stale legacy; not modified here (retire
  separately).

Rationale: a new tech (CosmX, CODEX) adds a scrape under `curation/sources/` and reconcile
logic in `curation/tools/` — never a new tracked CSV in the hub or a copy elsewhere.
The hub's dependency on dataset data stays a single submodule edge.

## Reconciliation mechanics (implementation detail)

A re-runnable `curation/tools/reconcile_datasets.py` that reads
`sources/datasets_10x.csv` + `registry/datasets.csv` + `registry/uids.csv` and produces
an updated `registry/datasets.csv` plus a report. Deterministic, idempotent, no network.

Steps:
1. **Exact uid link** — the 110 rows already carrying `local_uid` pass through.
2. **Backfill uid link** — for uid-less registry rows, match to a scrape row by a
   composite key: normalized `primary_source`/`dataset_link` URL **+** `Replicate`.
   Matches inherit the scrape's uid.
3. **Unmatched report** — rows still without a uid (~40 expected) are written to
   `tools/reports/datasets_unmatched.csv` for human review. Never guess a uid.
4. **Fold new datasets** — the 102 scrape-only datasets become new registry rows:
   mint a `dataset_id`, carry the uid, map scrape fields into existing registry columns
   (identity/provenance/classification + biological fields that have a natural column);
   put remaining scrape detail in `notes` rather than adding columns.
5. **Collapse the near-dupe** — reconcile `scripts/metadata/datasets_merged.csv` (the
   extra `Software` column) into `registry/datasets.csv`, then remove it.

Column mapping is minimal and explicit (a small dict in the tool). No ontology lookups.

## Testing / verification

- Tool is idempotent: a second run over its own output is a no-op (byte-identical
  registry, empty diff).
- Invariants asserted by the tool and a test: every registry uid exists in
  `registry/uids.csv`; no duplicate `dataset_id`; no duplicate uid; row count ==
  distinct datasets (207 linked-or-existing + newly folded − dedupe).
- Workflow test (curation): run reconcile on a small fixture → assert linked count,
  unmatched count, and that folding is stable across a re-run.
- Hub: after deleting its `scripts/data/datasets_10x.csv`, `pixi run` build/tests that
  previously read it still pass reading through `extern/curation`.

## Rollout (PR sequence)

1. **curation PR** — add `sources/datasets_10x.csv` (moved scrape), add
   `tools/reconcile_datasets.py` + test, regenerate `registry/datasets.csv`, remove
   `scripts/metadata/datasets_merged.csv`, commit the unmatched report. This is the
   substantive change; review the registry diff carefully.
2. **hub PR** — bump `extern/curation`, delete `scripts/data/datasets_10x.csv`, update
   any reader to the submodule path.
3. **db PR** — delete `scripts/data/datasets_10x.csv` in the `db` repo (covers the
   `db-uids` worktree copy).
4. Retire `spatialdata-db_old` separately (out of scope).

## Risks / open questions

- **~40 unmatched rows**: need a human pass (you) to assign uids or confirm they are
  genuinely new. The tool surfaces them; it does not decide.
- **Replicate semantics**: the composite key assumes `Replicate` disambiguates rows
  sharing a landing-page URL. If `Replicate` is not populated consistently on the
  registry side, more rows fall to the unmatched report (safe, just more manual work).
- **`datasets_merged.csv` extra `Software` column** vs registry `software_name` —
  confirm they carry the same meaning before collapsing.
