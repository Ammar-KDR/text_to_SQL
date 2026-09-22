from textSQL.metadata.models import (
    DatabaseMetadata,
    SchemaMetadata,
    TableMetadata,
    MetricMetadata,
)

from textSQL.metadata.graph import (
    SchemaGraph,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.dependency_resolver import (
    DependencyResolver,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)


def create_metadata():

    fact_sales = TableMetadata(

        name=
            "fact_sales",

        schema_name=
            "warehouse",
    )


    dim_product = TableMetadata(

        name=
            "dim_product",

        schema_name=
            "warehouse",
    )


    revenue = MetricMetadata(

        name=
            "revenue",

        description=
            "Revenue",

        domain=
            "sales",

        formula=
            "SUM(fact_sales.revenue)",

        authoritative_source=
            "fact_sales",

        required_tables=[
            "fact_sales"
        ],

        required_columns=[
            "revenue"
        ],

        required_metrics=[],

        business_rules=[],

        forbidden_sources=[],

        synonyms=[
            "sales"
        ],
    )


    product_revenue = MetricMetadata(

        name=
            "product_revenue",

        description=
            "Revenue grouped by product",

        domain=
            "product",

        formula=
            "SUM(fact_sales.revenue) "
            "GROUP BY product_key",

        authoritative_source=
            "fact_sales",

        required_tables=[
            "fact_sales",
            "dim_product",
        ],

        required_columns=[
            "product_key",
            "revenue",
        ],

        required_metrics=[
            "revenue"
        ],

        business_rules=[],

        forbidden_sources=[],

        synonyms=[
            "product sales"
        ],
    )


    top_products = MetricMetadata(

        name=
            "top_products",

        description=
            "Products ranked by revenue",

        domain=
            "product",

        formula=
            "ORDER BY product_revenue DESC",

        authoritative_source=
            "fact_sales",

        required_tables=[
            "fact_sales",
            "dim_product",
        ],

        required_columns=[
            "product_key",
            "revenue",
        ],

        required_metrics=[
            "product_revenue"
        ],

        business_rules=[],

        forbidden_sources=[],

        synonyms=[
            "best products"
        ],
    )


    return DatabaseMetadata(

        database_name=
            "test_db",

        schemas=[

            SchemaMetadata(

                name=
                    "warehouse",

                schema_type=
                    "OLAP",

                tables=[

                    fact_sales,

                    dim_product,

                ],
            )

        ],

        relationships=[],

        metrics=[

            revenue,

            product_revenue,

            top_products,

        ],

        graph=None,
    )


def test_recursive_metric_dependencies():

    metadata = (
        create_metadata()
    )


    index = MetadataIndex(

        metadata,

        SchemaGraph(),
    )


    resolver = (
        DependencyResolver(
            index
        )
    )


    candidates = [

        RetrievalCandidate(

            object_id=
                "metric_top_products",

            object_type=
                "metric",

            object_name=
                "top_products",

            score=
                0.95,

            source=
                "dense",
        )

    ]


    resolved = resolver.resolve(
        candidates
    )


    ids = {

        candidate.object_id

        for candidate
        in resolved

    }


    assert (
        "metric_top_products"
        in ids
    )

    assert (
        "metric_product_revenue"
        in ids
    )

    assert (
        "metric_revenue"
        in ids
    )

    assert (
        "table_warehouse.fact_sales"
        in ids
    )

    assert (
        "table_warehouse.dim_product"
        in ids
    )


def test_dependencies_are_not_duplicated():

    metadata = (
        create_metadata()
    )


    index = MetadataIndex(

        metadata,

        SchemaGraph(),
    )


    resolver = (
        DependencyResolver(
            index
        )
    )


    candidates = [

        RetrievalCandidate(

            object_id=
                "metric_top_products",

            object_type=
                "metric",

            object_name=
                "top_products",

            score=
                0.95,

            source=
                "dense",
        ),

        RetrievalCandidate(

            object_id=
                "metric_revenue",

            object_type=
                "metric",

            object_name=
                "revenue",

            score=
                0.90,

            source=
                "dense",
        ),

    ]


    resolved = resolver.resolve(
        candidates
    )


    ids = [

        candidate.object_id

        for candidate
        in resolved

    ]


    assert (
        len(ids)
        ==
        len(set(ids))
    )


def test_cyclic_metric_dependencies_do_not_loop():

    metadata = (
        create_metadata()
    )


    metric_a = MetricMetadata(

        name=
            "metric_a",

        description=
            "A",

        domain=
            "test",

        formula=
            "A",

        required_tables=[],

        required_columns=[],

        required_metrics=[
            "metric_b"
        ],

        business_rules=[],

        forbidden_sources=[],

        synonyms=[],
    )


    metric_b = MetricMetadata(

        name=
            "metric_b",

        description=
            "B",

        domain=
            "test",

        formula=
            "B",

        required_tables=[],

        required_columns=[],

        required_metrics=[
            "metric_a"
        ],

        business_rules=[],

        forbidden_sources=[],

        synonyms=[],
    )


    metadata.metrics.extend([
        metric_a,
        metric_b,
    ])


    index = MetadataIndex(

        metadata,

        SchemaGraph(),
    )


    resolver = (
        DependencyResolver(
            index
        )
    )


    result = resolver.resolve([

        RetrievalCandidate(

            object_id=
                "metric_metric_a",

            object_type=
                "metric",

            object_name=
                "metric_a",

            score=
                1.0,

            source=
                "dense",
        )

    ])


    ids = {

        candidate.object_id

        for candidate
        in result

    }


    assert (
        "metric_metric_a"
        in ids
    )

    assert (
        "metric_metric_b"
        in ids
    )