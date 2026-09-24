# Dataset Registry Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate all dataset data into `spatialdata-db-curation` as single owner — fold the raw 10x scrape into the canonical `registry/datasets.csv` via a re-runnable tool, and delete the duplicated scrape copies from the hub and db repos.

**Architecture:** A new `tools/reconcile_datasets.py` in curation reuses the existing `tools/canon.py` (source canonicalization, fingerprints, registry I/O, deterministic `dataset_id` derivation) to link scrape UIDs into the registry, fold in scrape-only datasets, and emit an unmatched report for rows a machine cannot safely link. Consumers (hub, db) then read dataset data only through `extern/curation` and drop their local copies.

**Tech Stack:** Python 3.11–3.14, stdlib `csv`, curation's `tools/canon.py`, pytest (added to curation dev env), pixi for tasks.

**Spec:** `docs/superpowers/specs/2026-09-24-dataset-registry-consolidation-design.md` (in `spatialdata-db-hub`)

## Global Constraints

- Python support: **3.11–3.14** (scverse / SPEC-0). No `match`-only-3.10 tricks needed; target the floor.
- **No pandas in registry I/O** — reuse `tools/canon.py` (stdlib `csv`). `mint_uids.py` uses pandas but the registry layer is stdlib; keep it that way for stable diffs.
- **Reuse `canon.py`**, do not reimplement: `load_registry`, `write_registry`, `canonical_source`, `fingerprint`, `ensure_fingerprints_row`.
- Curation tool style: `#!/usr/bin/env python3`, `from __future__ import annotations`, flat `from canon import ...` (scripts run from repo root as `python tools/<name>.py`, so `tools/` is `sys.path[0]`).
- Test runner: **pytest**, added to curation's dev env via pixi; tests in `tests/`; `pixi run test` → `pytest`. `tests/conftest.py` puts `tools/` on `sys.path`.
- **Never commit `pixi.lock`** (must be gitignored in curation).
- Minimal, localized diffs. No drive-by refactors. No CI changes unless a task says so.
- Commit messages: terse, maintainer-style, Conventional Commits. **No AI attribution / "Generated with Claude Code" lines.**
- Registry paths (relative to curation root): input `sources/datasets_10x.csv`, output `registry/datasets.csv`, keyspace `registry/uids.csv`, report `tools/reports/datasets_unmatched.csv`.

## Review Focus

- **URL variants** (scheme, `www.`, trailing slash, `utm_*`/tracking params) must not split a match — `canonical_source` already normalizes these; pin it in Task 2's key test.
- **Empty/missing `Replicate`** on a registry row must degrade to "unmatched" (never a wrong uid) — covered in Task 2.
- **Scrape `uid` absent from `registry/uids.csv`** (keyspace gap) must **fail loudly**, not silently write an unlinked uid — covered in Task 4's invariant.
- **Duplicate uid in the scrape** (`uid` vs the legacy `uid_old` column) must not create duplicate registry rows — key on `uid`; covered in Task 3.
- **Idempotent re-run**: a second run over its own output changes nothing (byte-identical registry, identical report) — covered in Task 4.

---

## Task 1: Curation dev env + reconcile scaffold

**Files:**
- Modify: `pixi.toml` (add pytest to a `test` feature + `test` task + `linux-64` platform; ensure `pixi.lock` gitignored)
- Modify: `.gitignore` (add `pixi.lock` if absent)
- Create: `tests/conftest.py`
- Create: `tools/reconcile_datasets.py` (scaffold: imports, constants, `load_scrape`, `source_fp`)
- Test: `tests/test_reconcile_scaffold.py`

**Interfaces:**
- Produces: `load_scrape(path: str) -> list[dict[str, str]]`; `source_fp(url: str) -> str` (canonical fingerprint of a URL, `""` if empty/uncanonicalizable).

- [ ] **Step 1: Add pytest to curation via pixi**

Run (from curation root):
```bash
pixi project platform add linux-64
pixi add --feature test pytest
pixi task add test "pytest -q"
```
Confirm `pixi.lock` is untracked/ignored:
```bash
grep -qxF 'pixi.lock' .gitignore || printf 'pixi.lock\n' >> .gitignore
git status --porcelain pixi.lock   # expect empty (ignored)
```

- [ ] **Step 2: conftest puts tools/ on sys.path**

Create `tests/conftest.py`:
```python
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
```

- [ ] **Step 3: Write the failing test**

Create `tests/test_reconcile_scaffold.py`:
```python
import reconcile_datasets as rc


def test_source_fp_normalizes_url_variants():
    a = rc.source_fp("https://www.10xgenomics.com/datasets/foo/")
    b = rc.source_fp("http://10xgenomics.com/datasets/foo?utm_source=x")
    assert a and a == b


def test_source_fp_empty_is_blank():
    assert rc.source_fp("") == ""
    assert rc.source_fp(None) == ""


def test_load_scrape_reads_semicolon(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("Datasets;uid;dataset_link\nA;10abc;https://x/y\n", encoding="utf-8")
    rows = rc.load_scrape(str(p))
    assert rows == [{"Datasets": "A", "uid": "10abc", "dataset_link": "https://x/y"}]
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pixi run test tests/test_reconcile_scaffold.py`
Expected: FAIL (`ModuleNotFoundError: reconcile_datasets` / attributes missing).

- [ ] **Step 5: Write minimal implementation**

Create `tools/reconcile_datasets.py`:
```python
#!/usr/bin/env python3
"""Reconcile the raw 10x scrape into the canonical dataset registry.

Reads sources/datasets_10x.csv (scrape input) + registry/datasets.csv
(canonical output) + registry/uids.csv (keyspace), links scrape UIDs into the
registry, folds in scrape-only datasets, and writes an unmatched report for
rows a machine cannot safely link. Reuses tools/canon.py.

    python tools/reconcile_datasets.py           # write registry + report
    python tools/reconcile_datasets.py --check   # nonzero exit if a run would change files
"""
from __future__ import annotations

import argparse
import csv

from canon import (
    canonical_source,
    ensure_fingerprints_row,
    fingerprint,
    load_registry,
    write_registry,
)

SCRAPE = "sources/datasets_10x.csv"
REGISTRY = "registry/datasets.csv"
UIDS = "registry/uids.csv"
UNMATCHED = "tools/reports/datasets_unmatched.csv"

SCRAPE_TO_REGISTRY = {
    "Datasets": "name",
    "Products": "product",
    "Software": "software_name",
    "Pipeline Version": "software_version",
    "dataset_link": "primary_source",
    "Publish Date": "release_date",
    "uid": "local_uid",
}
NOTE_FIELDS = [
    "Chemistry Version", "Subpipeline", "Species", "Disease State",
    "Anatomical entity", "organ", "tech", "Preservation Method",
    "Staining Method", "Biomaterial type", "10x Instrument(s)",
    "Feature Barcode", "Cells or nuclei", "Cell Nuclei count",
]


def load_scrape(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def source_fp(url: str | None) -> str:
    c = canonical_source(url or "")
    return fingerprint(c) if c else ""
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pixi run test tests/test_reconcile_scaffold.py`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pixi.toml .gitignore tests/conftest.py tests/test_reconcile_scaffold.py tools/reconcile_datasets.py
git commit -m "chore(curation): add pytest env + reconcile scaffold"
```

---

## Task 2: UID backfill + unmatched report

**Files:**
- Modify: `tools/reconcile_datasets.py` (add `scrape_key`, `registry_key`, `backfill_uids`)
- Test: `tests/test_reconcile_link.py`

**Interfaces:**
- Consumes: `source_fp` (Task 1).
- Produces:
  - `scrape_key(row) -> tuple[str, str]` = `(source_fp(dataset_link), Replicate.strip())`
  - `registry_key(row) -> tuple[str, str]` = `(primary_fingerprint or source_fp(primary_source), Replicate.strip())`
  - `backfill_uids(registry: list[dict], scrape: list[dict]) -> tuple[list[dict], list[dict]]` → returns `(registry_with_uids_filled, unmatched_rows)`. Only fills rows whose `local_uid` is empty; a row stays unmatched if its key is absent, ambiguous (maps to >1 scrape uid), or its `Replicate` component is empty. Never overwrites an existing `local_uid`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_reconcile_link.py`:
```python
import reconcile_datasets as rc


def _scrape(**kw):
    base = {"Datasets": "", "dataset_link": "", "Replicate": "", "uid": ""}
    base.update(kw)
    return base


def _reg(**kw):
    base = {"dataset_id": "", "primary_source": "", "primary_fingerprint": "",
            "Replicate": "", "local_uid": ""}
    base.update(kw)
    return base


def test_backfill_matches_by_fingerprint_and_replicate():
    scrape = [_scrape(dataset_link="https://www.10xgenomics.com/datasets/a/",
                      Replicate="1", uid="10abc")]
    reg = [_reg(primary_source="http://10xgenomics.com/datasets/a", Replicate="1")]
    out, unmatched = rc.backfill_uids(reg, scrape)
    assert out[0]["local_uid"] == "10abc"
    assert unmatched == []


def test_empty_replicate_is_unmatched_not_guessed():
    scrape = [_scrape(dataset_link="https://x/a", Replicate="", uid="10abc")]
    reg = [_reg(primary_source="https://x/a", Replicate="")]
    out, unmatched = rc.backfill_uids(reg, scrape)
    assert out[0]["local_uid"] == ""
    assert len(unmatched) == 1


def test_ambiguous_key_is_unmatched():
    scrape = [_scrape(dataset_link="https://x/a", Replicate="1", uid="10abc"),
              _scrape(dataset_link="https://x/a", Replicate="1", uid="10def")]
    reg = [_reg(primary_source="https://x/a", Replicate="1")]
    out, unmatched = rc.backfill_uids(reg, scrape)
    assert out[0]["local_uid"] == ""
    assert len(unmatched) == 1


def test_existing_uid_never_overwritten():
    scrape = [_scrape(dataset_link="https://x/a", Replicate="1", uid="10zzz")]
    reg = [_reg(primary_source="https://x/a", Replicate="1", local_uid="10abc")]
    out, unmatched = rc.backfill_uids(reg, scrape)
    assert out[0]["local_uid"] == "10abc"
    assert unmatched == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pixi run test tests/test_reconcile_link.py`
Expected: FAIL (`backfill_uids` not defined).

- [ ] **Step 3: Write minimal implementation**

Append to `tools/reconcile_datasets.py`:
```python
def scrape_key(row: dict[str, str]) -> tuple[str, str]:
    return (source_fp(row.get("dataset_link", "")), (row.get("Replicate") or "").strip())


def registry_key(row: dict[str, str]) -> tuple[str, str]:
    fp = (row.get("primary_fingerprint") or "").strip() or source_fp(row.get("primary_source", ""))
    return (fp, (row.get("Replicate") or "").strip())


def _scrape_uid_index(scrape: list[dict[str, str]]) -> dict[tuple[str, str], set[str]]:
    idx: dict[tuple[str, str], set[str]] = {}
    for r in scrape:
        fp, rep = scrape_key(r)
        uid = (r.get("uid") or "").strip()
        if not fp or not rep or not uid:
            continue
        idx.setdefault((fp, rep), set()).add(uid)
    return idx


def backfill_uids(
    registry: list[dict[str, str]], scrape: list[dict[str, str]]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    idx = _scrape_uid_index(scrape)
    out: list[dict[str, str]] = []
    unmatched: list[dict[str, str]] = []
    for row in registry:
        row = dict(row)
        if (row.get("local_uid") or "").strip():
            out.append(row)
            continue
        fp, rep = registry_key(row)
        uids = idx.get((fp, rep), set()) if fp and rep else set()
        if len(uids) == 1:
            row["local_uid"] = next(iter(uids))
        else:
            unmatched.append(row)
        out.append(row)
    return out, unmatched
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pixi run test tests/test_reconcile_link.py`
Expected: PASS (all 4).

- [ ] **Step 5: Commit**

```bash
git add tools/reconcile_datasets.py tests/test_reconcile_link.py
git commit -m "feat(curation): backfill dataset UIDs by fingerprint+replicate"
```

---

## Task 3: Fold scrape-only datasets into the registry

**Files:**
- Modify: `tools/reconcile_datasets.py` (add `build_notes`, `fold_new`)
- Test: `tests/test_reconcile_fold.py`

**Interfaces:**
- Consumes: `SCRAPE_TO_REGISTRY`, `NOTE_FIELDS`, `ensure_fingerprints_row` (canon).
- Produces:
  - `build_notes(scrape_row) -> str` = `"; ".join(f"{k}={v}")` over non-empty `NOTE_FIELDS`.
  - `fold_new(registry, scrape) -> list[dict]` → returns registry rows unchanged followed by one new row per scrape `uid` **not already present** in `registry.local_uid`. New rows carry only the registry's own columns; `dataset_id` and `primary_fingerprint` are set by `ensure_fingerprints_row`; `manufacturer="10x Genomics"`, `primary_source_type="url"`. Deduplicates scrape rows by `uid` (first occurrence wins), so `uid_old` never produces a second row.

- [ ] **Step 1: Write the failing test**

Create `tests/test_reconcile_fold.py`:
```python
import reconcile_datasets as rc

FIELDS = ["status", "dataset_id", "name", "primary_source_type", "primary_source",
          "primary_fingerprint", "manufacturer", "product", "software_name",
          "software_version", "release_date", "notes", "local_uid", "Replicate"]


def _reg(**kw):
    base = {c: "" for c in FIELDS}
    base.update(kw)
    return base


def _scrape(**kw):
    base = {"Datasets": "", "Products": "", "Software": "", "Pipeline Version": "",
            "dataset_link": "", "Publish Date": "", "Replicate": "", "uid": "",
            "uid_old": "", "Species": "", "organ": "", "tech": ""}
    base.update(kw)
    return base


def test_new_dataset_folded_with_mapped_columns():
    reg = [_reg(local_uid="10aaa", dataset_id="ds_existing")]
    scrape = [_scrape(Datasets="Brain", Products="Xenium",
                      dataset_link="https://x/brain", uid="10bbb",
                      Species="Human", organ="brain")]
    out = rc.fold_new(reg, scrape)
    assert len(out) == 2
    new = out[1]
    assert new["local_uid"] == "10bbb"
    assert new["name"] == "Brain"
    assert new["product"] == "Xenium"
    assert new["manufacturer"] == "10x Genomics"
    assert new["primary_source_type"] == "url"
    assert new["dataset_id"].startswith("ds_") and len(new["dataset_id"]) == 15
    assert "Species=Human" in new["notes"] and "organ=brain" in new["notes"]
    assert set(new.keys()) == set(FIELDS)  # no extra columns leaked in


def test_uid_already_in_registry_not_refolded():
    reg = [_reg(local_uid="10bbb")]
    scrape = [_scrape(dataset_link="https://x/brain", uid="10bbb")]
    assert len(rc.fold_new(reg, scrape)) == 1


def test_duplicate_scrape_uid_folds_once():
    reg = []
    scrape = [_scrape(dataset_link="https://x/a", uid="10bbb", uid_old="10old"),
              _scrape(dataset_link="https://x/a2", uid="10bbb", uid_old="10old2")]
    # empty registry: fold_new needs fieldnames from scrape mapping; see impl note
    out = rc.fold_new([_reg(local_uid="10aaa")], scrape)
    new_uids = [r["local_uid"] for r in out if r["local_uid"] == "10bbb"]
    assert len(new_uids) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pixi run test tests/test_reconcile_fold.py`
Expected: FAIL (`fold_new` not defined).

- [ ] **Step 3: Write minimal implementation**

Append to `tools/reconcile_datasets.py`:
```python
def build_notes(scrape_row: dict[str, str]) -> str:
    parts = [f"{k}={scrape_row[k].strip()}" for k in NOTE_FIELDS
             if (scrape_row.get(k) or "").strip()]
    return "; ".join(parts)


def fold_new(
    registry: list[dict[str, str]], scrape: list[dict[str, str]]
) -> list[dict[str, str]]:
    if not registry:
        raise ValueError("registry must be non-empty to supply column schema")
    fieldnames = list(registry[0].keys())
    have = {(r.get("local_uid") or "").strip() for r in registry}
    out = [dict(r) for r in registry]
    seen: set[str] = set()
    for s in scrape:
        uid = (s.get("uid") or "").strip()
        if not uid or uid in have or uid in seen:
            continue
        seen.add(uid)
        row = {c: "" for c in fieldnames}
        for src, dst in SCRAPE_TO_REGISTRY.items():
            if dst in row:
                row[dst] = (s.get(src) or "").strip()
        if "manufacturer" in row:
            row["manufacturer"] = "10x Genomics"
        if "primary_source_type" in row:
            row["primary_source_type"] = "url"
        if "notes" in row:
            row["notes"] = build_notes(s)
        enriched = ensure_fingerprints_row(dict(row))
        for k in ("dataset_id", "primary_fingerprint"):
            if k in row:
                row[k] = enriched.get(k, row[k])
        out.append(row)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pixi run test tests/test_reconcile_fold.py`
Expected: PASS (all 3).

- [ ] **Step 5: Commit**

```bash
git add tools/reconcile_datasets.py tests/test_reconcile_fold.py
git commit -m "feat(curation): fold scrape-only datasets into registry"
```

---

## Task 4: Orchestration, keyspace invariant, idempotency + regenerate registry

**Files:**
- Modify: `tools/reconcile_datasets.py` (add `load_uid_keyspace`, `check_keyspace`, `write_unmatched`, `reconcile`, `main`, `__main__`)
- Create: `sources/datasets_10x.csv` (the scrape, copied from `spatialdata-db/scripts/data/datasets_10x.csv`)
- Create: `tools/reports/.gitkeep`
- Regenerate: `registry/datasets.csv` (tool output — committed)
- Create: `tools/reports/datasets_unmatched.csv` (tool output — committed)
- Test: `tests/test_reconcile_run.py`

**Interfaces:**
- Consumes: `backfill_uids` (Task 2), `fold_new` (Task 3), `load_registry`/`write_registry` (canon).
- Produces:
  - `load_uid_keyspace(path) -> set[str]` — the `uid` column of `registry/uids.csv` (`;`-separated).
  - `check_keyspace(registry, keyspace) -> list[str]` — list of `local_uid`s present in the registry but absent from the keyspace (empty == valid).
  - `reconcile(registry, scrape, keyspace) -> tuple[list[dict], list[dict]]` → `(new_registry, unmatched)`; raises `ValueError` listing offending uids if `check_keyspace` is non-empty.
  - `main(argv=None) -> int` — reads the three files, runs `reconcile`, and in `--check` mode returns non-zero if outputs would change, else writes `registry/datasets.csv` + `tools/reports/datasets_unmatched.csv` and returns 0.

- [ ] **Step 1: Write the failing test**

Create `tests/test_reconcile_run.py`:
```python
import reconcile_datasets as rc

FIELDS = ["status", "dataset_id", "name", "primary_source_type", "primary_source",
          "primary_fingerprint", "manufacturer", "product", "software_name",
          "software_version", "release_date", "notes", "local_uid", "Replicate"]


def _reg(**kw):
    base = {c: "" for c in FIELDS}
    base.update(kw)
    return base


def _scrape(**kw):
    base = {"Datasets": "", "Products": "", "Software": "", "Pipeline Version": "",
            "dataset_link": "", "Publish Date": "", "Replicate": "", "uid": "",
            "uid_old": "", "Species": ""}
    base.update(kw)
    return base


def test_reconcile_rejects_uid_outside_keyspace():
    reg = [_reg(local_uid="10zzz", dataset_id="ds_x")]
    try:
        rc.reconcile(reg, [], keyspace={"10aaa"})
        assert False, "expected ValueError"
    except ValueError as e:
        assert "10zzz" in str(e)


def test_reconcile_is_idempotent():
    reg = [_reg(local_uid="10aaa", dataset_id="ds_a", primary_source="https://x/a",
                Replicate="1")]
    scrape = [_scrape(dataset_link="https://x/b", Replicate="1", uid="10bbb",
                      Datasets="B")]
    keyspace = {"10aaa", "10bbb"}
    first, un1 = rc.reconcile(reg, scrape, keyspace)
    second, un2 = rc.reconcile(first, scrape, keyspace)
    assert first == second
    assert un1 == un2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pixi run test tests/test_reconcile_run.py`
Expected: FAIL (`reconcile` not defined).

- [ ] **Step 3: Write minimal implementation**

Append to `tools/reconcile_datasets.py`:
```python
def load_uid_keyspace(path: str) -> set[str]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        return {(r.get("uid") or "").strip() for r in reader if (r.get("uid") or "").strip()}


def check_keyspace(registry: list[dict[str, str]], keyspace: set[str]) -> list[str]:
    bad = []
    for r in registry:
        uid = (r.get("local_uid") or "").strip()
        if uid and uid not in keyspace:
            bad.append(uid)
    return sorted(set(bad))


def reconcile(
    registry: list[dict[str, str]], scrape: list[dict[str, str]], keyspace: set[str]
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    linked, unmatched = backfill_uids(registry, scrape)
    folded = fold_new(linked, scrape)
    bad = check_keyspace(folded, keyspace)
    if bad:
        raise ValueError(f"UIDs not in keyspace registry/uids.csv: {bad}")
    return folded, unmatched


def write_unmatched(path: str, rows: list[dict[str, str]]) -> None:
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["dataset_id", "name", "primary_source", "Replicate"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="nonzero exit if a run would change outputs")
    args = ap.parse_args(argv)

    registry = load_registry(REGISTRY)
    scrape = load_scrape(SCRAPE)
    keyspace = load_uid_keyspace(UIDS)
    new_registry, unmatched = reconcile(registry, scrape, keyspace)

    if args.check:
        changed = new_registry != registry
        print("CHANGED" if changed else "OK")
        return 1 if changed else 0

    write_registry(REGISTRY, new_registry)
    write_unmatched(UNMATCHED, unmatched)
    print(f"registry rows: {len(new_registry)}  unmatched: {len(unmatched)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pixi run test tests/test_reconcile_run.py`
Expected: PASS (both).

- [ ] **Step 5: Copy the scrape into curation and generate outputs**

```bash
mkdir -p sources tools/reports && touch tools/reports/.gitkeep
cp ../spatialdata-db/scripts/data/datasets_10x.csv sources/datasets_10x.csv
python tools/reconcile_datasets.py
python tools/reconcile_datasets.py --check   # expect "OK" + exit 0 (idempotent)
python tools/validate.py registry/datasets.csv   # existing validator still passes
```
Expected: first run prints the row/unmatched counts (~40 unmatched); `--check` prints `OK`.

- [ ] **Step 6: Full test suite**

Run: `pixi run test`
Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add tools/reconcile_datasets.py tests/test_reconcile_run.py \
        sources/datasets_10x.csv tools/reports/.gitkeep \
        registry/datasets.csv tools/reports/datasets_unmatched.csv
git commit -m "feat(curation): reconcile 10x scrape into canonical registry"
```

---

## Task 5: Collapse the near-duplicate `datasets_merged.csv`

**Files:**
- Create: `tools/check_merged_subsumed.py` (one-shot verification)
- Delete: `scripts/metadata/datasets_merged.csv`
- Test: `tests/test_merged_subsumed.py`

**Interfaces:**
- Produces: `extra_info(merged, registry) -> list[str]` — dataset_ids where `datasets_merged.csv`'s `Software` column holds a non-empty value that is absent from the registry row's `software_name`/`software_version`. Empty list == merged adds nothing → safe to delete.

- [ ] **Step 1: Write the failing test**

Create `tests/test_merged_subsumed.py`:
```python
import check_merged_subsumed as cm


def test_no_extra_info_when_software_covered():
    merged = [{"dataset_id": "ds_a", "Software": "spaceranger"}]
    reg = [{"dataset_id": "ds_a", "software_name": "spaceranger", "software_version": "3.1"}]
    assert cm.extra_info(merged, reg) == []


def test_extra_info_flags_uncovered_software():
    merged = [{"dataset_id": "ds_a", "Software": "xeniumranger"}]
    reg = [{"dataset_id": "ds_a", "software_name": "spaceranger", "software_version": "3.1"}]
    assert cm.extra_info(merged, reg) == ["ds_a"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pixi run test tests/test_merged_subsumed.py`
Expected: FAIL (module missing).

- [ ] **Step 3: Write minimal implementation**

Create `tools/check_merged_subsumed.py`:
```python
#!/usr/bin/env python3
"""Verify scripts/metadata/datasets_merged.csv adds nothing beyond registry.

Only the extra `Software` column is unique to the merged file; if every value
is already reflected in the registry row's software_name/software_version, the
merged file is redundant and safe to delete.
"""
from __future__ import annotations

import csv
import sys


def _load(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extra_info(merged: list[dict[str, str]], registry: list[dict[str, str]]) -> list[str]:
    reg = {r.get("dataset_id", ""): r for r in registry}
    flagged = []
    for m in merged:
        sw = (m.get("Software") or "").strip()
        if not sw:
            continue
        r = reg.get(m.get("dataset_id", ""))
        covered = r is not None and sw in (
            (r.get("software_name") or "").strip(),
            (r.get("software_version") or "").strip(),
        )
        if not covered:
            flagged.append(m.get("dataset_id", ""))
    return flagged


def main() -> int:
    merged = _load("scripts/metadata/datasets_merged.csv")
    registry = _load("registry/datasets.csv")
    flagged = extra_info(merged, registry)
    if flagged:
        print(f"NOT subsumed; Software uncovered for: {sorted(set(flagged))}")
        return 1
    print("OK: datasets_merged.csv is subsumed by registry; safe to delete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pixi run test tests/test_merged_subsumed.py`
Expected: PASS.

- [ ] **Step 5: Verify against real data, then delete**

```bash
python tools/check_merged_subsumed.py   # expect "OK ... safe to delete"
git rm scripts/metadata/datasets_merged.csv
```
If it prints `NOT subsumed`, STOP and report the flagged dataset_ids — do not delete; the uncovered `Software` values need folding into the registry first.

- [ ] **Step 6: Commit**

```bash
git add tools/check_merged_subsumed.py tests/test_merged_subsumed.py
git commit -m "chore(curation): drop datasets_merged.csv (subsumed by registry)"
```

- [ ] **Step 7: Open the curation PR**

```bash
git push -u origin HEAD
gh pr create --repo theislab/spatialdata-db-curation --fill
```
PR body: terse, maintainer-style; note the ~40 unmatched rows in `tools/reports/datasets_unmatched.csv` need a human uid pass. No AI attribution line.

---

## Task 6: Hub reads curation via submodule; drop local scrape copy

**Files (repo: `spatialdata-db`, worktree `spatialdata-db-hub`, branch off `main`):**
- Modify: `extern/curation` (submodule pointer → merged curation commit)
- Delete: `scripts/data/datasets_10x.csv`
- Modify: any file that reads `scripts/data/datasets_10x.csv` → read `extern/curation/registry/datasets.csv` (or `extern/curation/sources/datasets_10x.csv` if the raw scrape is genuinely needed)

- [ ] **Step 1: Find readers of the local copy**

Run: `git grep -n "datasets_10x.csv" -- . ':!extern'`
Record each hit; each becomes a path update below.

- [ ] **Step 2: Bump the submodule to merged curation**

```bash
git -C extern/curation fetch origin
git -C extern/curation checkout origin/main
git add extern/curation
```

- [ ] **Step 3: Repoint readers, then delete the copy**

For each reader found in Step 1, change the path to `extern/curation/registry/datasets.csv` (canonical) — or the `sources/` scrape only where raw 10x columns are required. Then:
```bash
git rm scripts/data/datasets_10x.csv
```

- [ ] **Step 4: Verify the build/tests still pass reading via submodule**

Run: `pixi run test`  (and the hub's schema build, e.g. `pixi run build-schema` if defined — check `pixi task list`)
Expected: PASS with no reference to the deleted local copy.

- [ ] **Step 5: Commit + PR**

```bash
git add -u && git add extern/curation
git commit -m "refactor(hub): read datasets from extern/curation, drop local copy"
git push -u origin HEAD
gh pr create --repo theislab/spatialdata-db --fill
```

---

## Task 7: Remove the db-side scrape copy

**Files (repo: `spatialdata-db`, branch off `main`):**
- Delete: `scripts/data/datasets_10x.csv`
- Modify: any db reader of that path → `extern/curation` (mirror Task 6 findings)

> Note: `spatialdata-db-uids` is a worktree of `spatialdata-db`; deleting the file on a `db` branch covers that copy. `spatialdata-db_old` is stale legacy and is retired separately (out of scope).

- [ ] **Step 1: Find readers**

Run: `git grep -n "datasets_10x.csv" -- . ':!extern'`

- [ ] **Step 2: Repoint readers + delete**

Update each hit to the `extern/curation` path, then `git rm scripts/data/datasets_10x.csv`.

- [ ] **Step 3: Verify**

Run: `pixi run test` (or the db repo's declared test task from `pixi task list`)
Expected: PASS.

- [ ] **Step 4: Commit + PR**

```bash
git add -u
git commit -m "chore(db): drop datasets_10x.csv, read from curation"
git push -u origin HEAD
gh pr create --repo theislab/spatialdata-db --fill
```

---

## Self-review notes

- **Spec coverage:** target layout → Tasks 1,4,6,7; reconcile tool (link/report/fold/mint) → Tasks 1–4; merged dedupe → Task 5; hub/db de-duplication via submodule → Tasks 6,7; schemas untouched (no task). ✔
- **Placeholders:** none — every code/test step carries real content.
- **Type consistency:** `source_fp`, `scrape_key`, `registry_key`, `backfill_uids`, `fold_new`, `reconcile`, `main` signatures match across Tasks 1–4; `extra_info` isolated to Task 5. ✔
- **Review Focus:** URL variants (T2), empty Replicate (T2), keyspace gap (T4), duplicate scrape uid (T3), idempotency (T4) — each pinned to a test. ✔
- **Assumption to verify during T4:** the real `registry/datasets.csv` header includes `notes`, `manufacturer`, `primary_source_type`, `software_name`, `software_version` (confirmed 2026-09-24). `all_sources`/`fingerprints` are NOT on-disk columns, so `fold_new` correctly drops the extra keys `ensure_fingerprints_row` adds.
