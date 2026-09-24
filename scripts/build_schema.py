"""Build the SpatialData-DB metadata schema into the connected lamin instance.

Bridges to the pinned `extern/schemas` submodule (theislab/spatialdata-schemas),
which we treat as an external, read-only source: this script does not modify it,
it only runs its `build_all()` from the hub's `schema` pixi environment.

Usage:
    pixi run -e schema build-schema

The schema records are written to whichever lamin instance is currently
connected (production: scverse/spatialdata-db). Run deliberately.
"""

import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[1]
SCHEMA_LAMIN = HUB / "extern" / "schemas" / "lamin"


def main() -> None:
    if not (SCHEMA_LAMIN / "build.py").exists():
        raise SystemExit(
            f"Schema submodule not found at {SCHEMA_LAMIN}. "
            "Run `pixi run sync` (or `git submodule update --init --recursive`) first."
        )
    # The schema modules use flat imports (`from utils import ...`).
    sys.path.insert(0, str(SCHEMA_LAMIN))
    from build import build_all

    versions = build_all()
    print("Built schema versions:", versions)


if __name__ == "__main__":
    main()
