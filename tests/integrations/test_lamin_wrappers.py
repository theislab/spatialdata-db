import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock

import lamindb as ln
import pytest

from spatialdata_db.integrations import store_dataset

DEFAULT_FILE_NAME = "test_data.zarr"


@pytest.fixture(scope="function")
def fake_artifact(tmp_path):
    artifact = MagicMock(spec=ln.Artifact)  # Mock with ln.Artifact attributes
    zarr_path = tmp_path / DEFAULT_FILE_NAME
    zarr_path.mkdir()

    artifact.cache = MagicMock(return_value=str(zarr_path))  # Explicitly add the `cache` method
    return artifact


def test_store_artifact_custom_path(fake_artifact, tmp_path):
    """Test storing artifact in a provided directory."""
    artifact = fake_artifact
    target_path = tmp_path / "custom_dir"
    target_path.mkdir()

    result_path = store_dataset(artifact, path=target_path)

    assert Path(result_path).exists()
    assert Path(result_path).parent == target_path


def test_store_artifact_rename(fake_artifact, tmp_path):
    """Test storing artifact with a custom name."""
    artifact = fake_artifact
    target_path = tmp_path / "custom_dir"
    target_path.mkdir()

    new_name = "renamed_data.zarr"
    result_path = store_dataset(artifact, path=target_path, name=new_name)

    assert Path(result_path).exists()
    assert Path(result_path).name == new_name
    assert Path(result_path).parent == target_path


def test_store_artifact_file_not_found(tmp_path):
    """Test that FileNotFoundError is raised if artifact.cache() points to a non-existent file."""
    artifact = MagicMock(spec=ln.Artifact)
    zarr_path = tmp_path / "missing.zarr"

    # Explicitly add the `cache` method
    artifact.cache = MagicMock(return_value=str(zarr_path))

    target_path = tmp_path / "custom_dir"
    with pytest.raises(FileNotFoundError):
        store_dataset(artifact, path=target_path)


def test_store_artifact_permission_error(fake_artifact, tmp_path):
    """Test that PermissionError is raised if the target directory is not writable."""
    artifact = fake_artifact
    locked_dir = tmp_path / "locked"
    locked_dir.mkdir()
    os.chmod(locked_dir, 0o400)  # Read-only directory

    with pytest.raises(PermissionError):
        store_dataset(artifact, path=locked_dir)

    os.chmod(locked_dir, 0o700)  # Restore permissions


def test_store_artifact_os_error(fake_artifact, monkeypatch, tmp_path):
    """Test that OSError is raised if a simulated system error occurs."""
    artifact = fake_artifact

    def mock_move(*args, **kwargs):
        raise OSError("Mocked OS error")

    monkeypatch.setattr(shutil, "move", mock_move)

    target_path = tmp_path / "custom_dir"
    with pytest.raises(OSError, match="Mocked OS error"):
        store_dataset(artifact, path=target_path)


def test_store_artifact_overwrite_false(fake_artifact, tmp_path):
    """Test that FileExistsError is raised if overwrite=False and file exists."""
    artifact = fake_artifact
    target_path = tmp_path / "existing_dir"
    target_path.mkdir()
    existing_file = target_path / DEFAULT_FILE_NAME
    existing_file.mkdir()

    with pytest.raises(FileExistsError):
        store_dataset(artifact, path=target_path, overwrite=False)


def test_store_artifact_overwrite_true(fake_artifact, tmp_path):
    """Test that artifact is stored correctly when overwrite=True."""
    artifact = fake_artifact
    target_path = tmp_path / "existing_dir"
    target_path.mkdir()
    existing_file = target_path / DEFAULT_FILE_NAME
    existing_file.mkdir()

    result_path = store_dataset(artifact, path=target_path, overwrite=True)

    assert Path(result_path).exists()
    assert Path(result_path).name == DEFAULT_FILE_NAME
