"""Offline guard tests for scripts/build_schema.py.

These never touch a lamin instance: they exercise the two early exits
(missing submodule, and the --yes write-guard) that must fire before any
connection or write happens.
"""

import importlib.util
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_schema.py"


def _load():
    spec = importlib.util.spec_from_file_location("build_schema", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_submodule_exits(monkeypatch, tmp_path):
    mod = _load()
    monkeypatch.setattr(mod, "SCHEMA_LAMIN", tmp_path / "does-not-exist")
    with pytest.raises(SystemExit):
        mod.main(["--yes"])


def test_write_requires_yes(monkeypatch, tmp_path):
    mod = _load()
    # Pretend the submodule is present so we reach (and trip) the --yes guard,
    # not the missing-submodule exit.
    lamin_dir = tmp_path / "lamin"
    lamin_dir.mkdir()
    (lamin_dir / "build.py").write_text("def build_all():\n    return {}\n")
    monkeypatch.setattr(mod, "SCHEMA_LAMIN", lamin_dir)
    with pytest.raises(SystemExit):
        mod.main([])  # no --yes -> must refuse before importing lamindb
