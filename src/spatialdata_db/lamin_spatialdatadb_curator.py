import lamindb as ln
from lamindb.curators import SpatialDataCurator
from spatialdata import SpatialData


class SpatialDataDBCurator(SpatialDataCurator):
    """Curator for SpatialData-DB.

    Thin wrapper over lamindb's :class:`~lamindb.curators.SpatialDataCurator`
    that validates a ``SpatialData`` object against a registered lamin
    ``Schema`` (e.g. ``"Visium"``, ``"Xenium"``, ``"VisiumHD"``). The schema
    encodes the slot layout and categoricals, so those are fetched from the
    instance rather than hard-coded here.
    """

    def __init__(self, dataset: SpatialData, schema: ln.Schema | str) -> None:
        if isinstance(schema, str):
            schema = ln.Schema.get(name=schema)
        super().__init__(dataset, schema)
