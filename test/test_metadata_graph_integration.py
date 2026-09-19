from textSQL.metadata.graph import (
    SchemaGraph,
)
from textSQL.metadata.extractor import extract_database_metadata
from textSQL.database.connection import engine
from textSQL.metadata.config import (
    load_metadata_config
)


config = load_metadata_config(
    "src/textSQL/config/metadata_config.yaml"
)

def test_metadata_contains_graph():

    metadata = extract_database_metadata(
        engine,
        config
    )


    assert metadata.graph is not None


    assert isinstance(
        metadata.graph,
        SchemaGraph
    )


    assert (
        "customers"
        in metadata.graph.nodes
    )


    assert (
        "orders"
        in metadata.graph.nodes
    )