"""Build the SpatialData-DB metadata schema into the connected lamin instance.

Bridges to the pinned `extern/schemas` submodule (theislab/spatialdata-schemas),
which we treat as an external, read-only source: this script does not modify it,
it only runs its `build_all()` from the hub's `schema` pixi environment.

Because `build_all()` writes ULabel/Feature/Schema records to whatever lamin
instance is connected (production `scverse/spatialdata-db` by default) and is not
idempotent, writing is gated behind `--yes`:

    pixi run -e schema build-schema -- --yes
    pixi run -e schema build-schema -- --yes --instance scverse/spatialdata-db

Without `--yes` the script only reports what it would do and exits non-zero, so an
accidental invocation never mutates an instance.
"""

import argparse
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[1]
SCHEMA_LAMIN = HUB / "extern" / "schemas" / "lamin"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--yes",
        action="store_true",
        help="Actually write the schema to the connected lamin instance.",
    )
    p.add_argument(
        "--instance",
        default=None,
        help="Assert the connected instance slug matches this before writing.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Build the schema submodule into the connected lamin instance (gated by --yes)."""
    args = _parse_args(argv)

    if not (SCHEMA_LAMIN / "build.py").exists():
        raise SystemExit(
            f"Schema submodule not found at {SCHEMA_LAMIN}. "
            "Run `pixi run sync` (or `git submodule update --init --recursive`) first."
        )

    if not args.yes:
        raise SystemExit(
            "Refusing to run: build_all() writes to the connected lamin instance and "
            "is not idempotent. Re-run with --yes once you have the intended instance "
            "connected (e.g. `pixi run -e schema build-schema -- --yes`)."
        )

    # The schema modules use flat imports (`from utils import ...`).
    sys.path.insert(0, str(SCHEMA_LAMIN))

    import lamindb_setup as ln_setup

    slug = getattr(ln_setup.settings.instance, "slug", None)
    if args.instance and args.instance != slug:
        raise SystemExit(f"Connected instance is '{slug}', but --instance requested '{args.instance}'.")
    print(f"Building schema into lamin instance: {slug}")

    from build import build_all

    versions = build_all()
    print("Built schema versions:", versions)


if __name__ == "__main__":
    main()
