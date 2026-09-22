from textSQL.metadata.graph import (
    SchemaGraph,
)

from textSQL.metadata.extractor import (
    extract_database_metadata,
)

from textSQL.database.connection import (
    engine,
)

from textSQL.metadata.config import (
    load_metadata_config,
)


config = load_metadata_config(
    "src/textSQL/config/metadata_config.yaml"
)


def test_metadata_contains_graph():

    metadata = extract_database_metadata(
        engine,
        config,
    )


    assert metadata.graph is not None

    assert isinstance(
        metadata.graph,
        SchemaGraph,
    )


    # Graph identities are schema-qualified.
    assert (
        "public.customers"
        in metadata.graph.nodes
    )

    assert (
        "public.orders"
        in metadata.graph.nodes
    )


def test_graph_contains_warehouse_tables():

    metadata = extract_database_metadata(
        engine,
        config,
    )


    assert (
        "warehouse.fact_sales"
        in metadata.graph.nodes
    )

    assert (
        "warehouse.dim_customer"
        in metadata.graph.nodes
    )


def test_graph_does_not_use_bare_table_identity():

    metadata = extract_database_metadata(
        engine,
        config,
    )


    assert (
        "customers"
        not in metadata.graph.nodes
    )

    assert (
        "orders"
        not in metadata.graph.nodes
    )


def test_public_orders_customer_path_exists():

    metadata = extract_database_metadata(
        engine,
        config,
    )


    path = metadata.graph.find_path(

        "public.orders",

        "public.customers",
    )


    assert path is not None

    assert len(path) >= 1


def test_warehouse_sales_customer_path_exists():

    metadata = extract_database_metadata(
        engine,
        config,
    )


    path = metadata.graph.find_path(

        "warehouse.fact_sales",

        "warehouse.dim_customer",
    )


    assert path is not None

    assert len(path) >= 1