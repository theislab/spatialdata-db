import warnings
import shutil
from pathlib import Path
from typing import Optional, Union
import lamindb as ln

LAMIN_TRACK_WARNING = "! run input wasn't tracked, call `ln.track()` and re-run"

def store_artifact(artifact: ln.Artifact, path: Union[str, Path] = Path("."), name: Optional[str] = None) -> str:
    """
    Store a cached artifact in a specified directory, rename it if needed, and suppress lamin's warning if the notebook is not tracked.

    Parameters:
    - artifact (lamindb.Artifact): The artifact object from lamindb.
    - path (Union[str, Path]): Directory where the cached artifact should be stored (default: ".").
    - name (Optional[str]): If provided, renames the cached artifact to this name (default: None).

    Returns:
    - str: The absolute path to the stored artifact.

    Raises:
    - FileNotFoundError: If the artifact cannot be found after caching.
    - PermissionError: If moving the artifact fails due to insufficient permissions.
    - RuntimeError: If caching fails for any reason.
    """
    target_dir = Path(path).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        warnings.filterwarnings("ignore", message=LAMIN_TRACK_WARNING)
        cached_path = Path(artifact.cache()).resolve()
    except Exception as e:
        raise RuntimeError(f"Failed to cache artifact: {e}")

    final_path = target_dir / (name if name else cached_path.name)

    if cached_path != final_path:
        try:
            shutil.move(str(cached_path), str(final_path))
        except PermissionError as e:
            raise PermissionError(f"Failed to move artifact due to insufficient permissions: {e}") from e
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Failed to find cached artifact: {e}") from e
        except OSError as e:
            raise OSError(f"Failed to move artifact due to an OS error: {e}") from e

    return str(final_path)
