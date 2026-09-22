from textSQL.retrieval.index import MetadataIndex

from textSQL.metadata.models import (
    DatabaseMetadata,
    SchemaMetadata,
    TableMetadata,
    ColumnMetadata,
    MetricMetadata,
)

from textSQL.metadata.graph import SchemaGraph



def create_test_metadata():

    customers_table = TableMetadata(

        name="customers",

        description="Customer information",

        columns=[

            ColumnMetadata(
                name="customer_id",
                data_type="integer",
                nullable=False,
                is_primary_key=True,
            ),

            ColumnMetadata(
                name="customer_name",
                data_type="varchar",
                nullable=False,
            ),
        ],
    )


    orders_table = TableMetadata(

        name="orders",

        description="Customer orders",

        columns=[

            ColumnMetadata(
                name="order_id",
                data_type="integer",
                nullable=False,
                is_primary_key=True,
            ),

            ColumnMetadata(
                name="customer_id",
                data_type="integer",
                nullable=False,
            ),

            ColumnMetadata(
                name="total_amount",
                data_type="decimal",
                nullable=False,
            ),
        ],
    )


    revenue_metric = MetricMetadata(

        name="revenue",

        domain="sales",

        synonyms=[
            "sales",
            "income",
        ],

        description=
        "Total generated revenue",

        formula=
        "SUM(orders.total_amount)",

        authoritative_source=
        "orders",

        required_tables=[
            "orders",
        ],

        required_columns=[
            "total_amount",
        ],

        required_metrics=[],

        business_rules=[
            "Exclude cancelled orders",
        ],

        forbidden_sources=[],
    )


    return DatabaseMetadata(

        database_name="test_db",

        schemas=[

            SchemaMetadata(

                name="public",

                schema_type="OLTP",

                tables=[

                    customers_table,

                    orders_table,
                ],
            )
        ],

        relationships=[],

        metrics=[
            revenue_metric
        ],

        graph=None,
    )



def test_tables_are_indexed():

    metadata = create_test_metadata()

    graph = SchemaGraph()


    index = MetadataIndex(
        metadata,
        graph,
    )


    # Canonical table identities are
    # schema-qualified.

    assert (
        "public.customers"
        in index.tables
    )

    assert (
        "public.orders"
        in index.tables
    )


    # Bare table names remain usable
    # through get_table() only when
    # they resolve unambiguously.

    customers = (
        index.get_table(
            "customers"
        )
    )

    orders = (
        index.get_table(
            "orders"
        )
    )


    assert customers is not None

    assert orders is not None


    assert (
        customers.qualified_name
        ==
        "public.customers"
    )

    assert (
        orders.qualified_name
        ==
        "public.orders"
    )



def test_columns_are_indexed():

    metadata = create_test_metadata()

    graph = SchemaGraph()


    index = MetadataIndex(
        metadata,
        graph,
    )


    assert "customer_id" in index.columns

    assert "total_amount" in index.columns


    assert len(
        index.columns["customer_id"]
    ) == 2



def test_metrics_are_indexed():

    metadata = create_test_metadata()

    graph = SchemaGraph()


    index = MetadataIndex(
        metadata,
        graph,
    )


    assert "revenue" in index.metrics


    metric = index.metrics["revenue"]


    assert metric.name == "revenue"

    assert metric.domain == "sales"



def test_metric_synonyms_are_indexed():

    metadata = create_test_metadata()

    graph = SchemaGraph()


    index = MetadataIndex(
        metadata,
        graph,
    )


    assert "sales" in index.metric_aliases


    metric = index.metric_aliases["sales"]


    assert metric.name == "revenue"



def test_graph_is_attached():

    metadata = create_test_metadata()

    graph = SchemaGraph()


    index = MetadataIndex(
        metadata,
        graph,
    )


    assert index.graph is graph

def test_generic_object_lookup():

    metadata = create_test_metadata()

    graph = SchemaGraph()

    index = MetadataIndex(
        metadata,
        graph,
    )

    metric = index.get_object(
        "metric_revenue"
    )

    assert metric.name == "revenue"