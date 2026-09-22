import pytest

from textSQL.database.connection import (
    engine,
)

from textSQL.metadata.config import (
    load_metadata_config,
)

from textSQL.metadata.extractor import (
    extract_database_metadata,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.dependency_resolver import (
    DependencyResolver,
)

from textSQL.retrieval.context_builder import (
    ContextBuilder,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
    FusedCandidate,
)


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture(scope="module")
def metadata():

    config = load_metadata_config(
        "src/textSQL/config/metadata_config.yaml"
    )

    return extract_database_metadata(
        engine,
        config,
    )


@pytest.fixture(scope="module")
def metadata_index(metadata):

    return MetadataIndex(
        metadata,
        metadata.graph,
    )


# ============================================================
# HELPERS
# ============================================================


def all_tables(metadata):

    return [

        table

        for schema in metadata.schemas

        for table in schema.tables

    ]


def table_map(metadata):

    return {

        table.qualified_name:
            table

        for table in all_tables(metadata)

    }


# ============================================================
# SCHEMA IDENTITY
# ============================================================


def test_real_tables_have_schema_identity(
    metadata,
):

    tables = all_tables(
        metadata
    )

    assert len(tables) > 0


    for table in tables:

        assert (
            table.schema_name
            is not None
        )

        assert "." in (
            table.qualified_name
        )


def test_expected_schemas_exist(
    metadata,
):

    schemas = {

        schema.name

        for schema
        in metadata.schemas

    }


    assert "public" in schemas

    assert "warehouse" in schemas


def test_known_tables_are_qualified(
    metadata,
):

    tables = table_map(
        metadata
    )


    assert (
        "public.orders"
        in tables
    )

    assert (
        "public.customers"
        in tables
    )

    assert (
        "warehouse.fact_sales"
        in tables
    )

    assert (
        "warehouse.dim_customer"
        in tables
    )


# ============================================================
# METRIC CATALOG
# ============================================================


def test_metric_catalog_exists(
    metadata,
):

    assert len(
        metadata.metrics
    ) > 0


    names = {

        metric.name

        for metric
        in metadata.metrics

    }


    assert "revenue" in names

    assert "profit" in names


def test_all_metric_tables_resolve(
    metadata,
    metadata_index,
):

    for metric in metadata.metrics:

        for table_name in (
            metric.required_tables
        ):

            table = (
                metadata_index
                .get_table(
                    table_name
                )
            )


            assert (
                table is not None
            ), (
                f"Metric '{metric.name}' "
                f"references unresolved table "
                f"'{table_name}'"
            )


def test_metric_columns_exist(
    metadata,
    metadata_index,
):

    for metric in metadata.metrics:

        available_columns = set()


        for table_name in (
            metric.required_tables
        ):

            table = (
                metadata_index
                .get_table(
                    table_name
                )
            )


            assert table is not None


            available_columns.update(

                column.name

                for column
                in table.columns

            )


        for column_name in (
            metric.required_columns
        ):

            assert (
                column_name
                in available_columns
            ), (
                f"Metric '{metric.name}' "
                f"references unknown column "
                f"'{column_name}'"
            )


def test_metric_dependencies_exist(
    metadata,
):

    metric_names = {

        metric.name

        for metric
        in metadata.metrics

    }


    for metric in metadata.metrics:

        for dependency in (
            metric.required_metrics
        ):

            assert (
                dependency
                in metric_names
            ), (
                f"Metric '{metric.name}' "
                f"depends on unknown metric "
                f"'{dependency}'"
            )


def test_authoritative_sources_resolve(
    metadata,
    metadata_index,
):

    for metric in metadata.metrics:

        if (
            metric.authoritative_source
            is None
        ):
            continue


        table = (
            metadata_index
            .get_table(
                metric.authoritative_source
            )
        )


        assert (
            table is not None
        ), (
            f"Metric '{metric.name}' "
            f"has unresolved authoritative "
            f"source "
            f"'{metric.authoritative_source}'"
        )


# ============================================================
# RELATIONSHIP GROUNDING
# ============================================================


def test_relationships_have_exact_join_conditions(
    metadata,
):

    tables = table_map(
        metadata
    )


    assert len(
        metadata.relationships
    ) > 0


    for relationship in (
        metadata.relationships
    ):

        assert (
            relationship.source_schema
            is not None
        )

        assert (
            relationship.target_schema
            is not None
        )


        assert (
            relationship
            .source_qualified_name
            in tables
        )


        assert (
            relationship
            .target_qualified_name
            in tables
        )


        assert (
            len(
                relationship
                .join_conditions
            )
            > 0
        ), (
            "Relationship has no exact "
            "join conditions: "
            f"{relationship.object_id}"
        )


        for condition in (
            relationship.join_conditions
        ):

            source_table_name = (

                f"{condition.source_schema}."
                f"{condition.source_table}"

            )


            target_table_name = (

                f"{condition.target_schema}."
                f"{condition.target_table}"

            )


            assert (
                source_table_name
                in tables
            )


            assert (
                target_table_name
                in tables
            )


            source_columns = {

                column.name

                for column
                in tables[
                    source_table_name
                ].columns

            }


            target_columns = {

                column.name

                for column
                in tables[
                    target_table_name
                ].columns

            }


            assert (
                condition.source_column
                in source_columns
            ), (
                f"Missing source column: "
                f"{condition.source_qualified_column}"
            )


            assert (
                condition.target_column
                in target_columns
            ), (
                f"Missing target column: "
                f"{condition.target_qualified_column}"
            )


# ============================================================
# GRAPH INTEGRITY
# ============================================================


def test_graph_uses_qualified_table_names(
    metadata,
):

    expected_tables = {

        table.qualified_name

        for table
        in all_tables(metadata)

    }


    assert (
        expected_tables
        .issubset(
            metadata.graph.nodes
        )
    )


def test_public_orders_customer_path(
    metadata,
):

    path = (
        metadata.graph
        .find_path(
            "public.orders",
            "public.customers",
        )
    )


    assert path is not None

    assert len(path) >= 1


def test_warehouse_sales_customer_path(
    metadata,
):

    path = (
        metadata.graph
        .find_path(
            "warehouse.fact_sales",
            "warehouse.dim_customer",
        )
    )


    assert path is not None

    assert len(path) >= 1


    relationship = path[0]


    assert (
        len(
            relationship
            .join_conditions
        )
        > 0
    )


    join = (
        relationship
        .join_conditions[0]
    )


    assert (
        join.source_qualified_column
        ==
        "warehouse.fact_sales.customer_key"
    )


    assert (
        join.target_qualified_column
        ==
        "warehouse.dim_customer.customer_key"
    )


# ============================================================
# METADATA INDEX
# ============================================================


def test_real_index_uses_qualified_table_ids(
    metadata_index,
):

    table = (
        metadata_index
        .get_object(
            "table_warehouse.fact_sales"
        )
    )


    assert table is not None


    assert (
        table.qualified_name
        ==
        "warehouse.fact_sales"
    )


def test_unique_bare_table_lookup_still_works(
    metadata_index,
):

    table = (
        metadata_index
        .get_table(
            "fact_sales"
        )
    )


    assert table is not None


    assert (
        table.qualified_name
        ==
        "warehouse.fact_sales"
    )


# ============================================================
# DEPENDENCY RESOLUTION
# ============================================================


def test_revenue_metric_resolves_fact_sales(
    metadata_index,
):

    resolver = DependencyResolver(
        metadata_index
    )


    candidates = [

        RetrievalCandidate(

            object_id=
                "metric_revenue",

            object_type=
                "metric",

            object_name=
                "revenue",

            score=
                1.0,

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
        "table_warehouse.fact_sales"
        in ids
    )


# ============================================================
# FINAL RETRIEVED CONTEXT
# ============================================================


def test_context_builder_produces_real_join_path(
    metadata_index,
):

    builder = ContextBuilder(
        metadata_index
    )


    candidates = [

        FusedCandidate(

            object_id=
                "table_warehouse.fact_sales",

            object_type=
                "table",

            object_name=
                "fact_sales",

            rrf_score=
                0.05,

            sources=[
                "dependency"
            ],
        ),

        FusedCandidate(

            object_id=
                "table_warehouse.dim_customer",

            object_type=
                "table",

            object_name=
                "dim_customer",

            rrf_score=
                0.04,

            sources=[
                "dense"
            ],
        ),

    ]


    context = builder.build(

        question=
            "show revenue by customer",

        candidates=
            candidates,
    )


    assert (
        len(context.join_paths)
        >= 1
    )


    path = context.join_paths[0]


    assert (
        "warehouse.fact_sales"
        in path.tables
    )


    assert (
        "warehouse.dim_customer"
        in path.tables
    )


    assert (
        len(path.relationships)
        >= 1
    )


    qualified_tables = {

        table.qualified_name

        for table
        in context.tables

    }


    assert (
        "warehouse.fact_sales"
        in qualified_tables
    )


    assert (
        "warehouse.dim_customer"
        in qualified_tables
    )


def test_retrieved_context_contains_exact_join(
    metadata_index,
):

    builder = ContextBuilder(
        metadata_index
    )


    context = builder.build(

        question=
            "show revenue by customer",

        candidates=[

            FusedCandidate(

                object_id=
                    "table_warehouse.fact_sales",

                object_type=
                    "table",

                object_name=
                    "fact_sales",

                rrf_score=
                    0.05,

                sources=[
                    "dependency"
                ],
            ),

            FusedCandidate(

                object_id=
                    "table_warehouse.dim_customer",

                object_type=
                    "table",

                object_name=
                    "dim_customer",

                rrf_score=
                    0.04,

                sources=[
                    "dense"
                ],
            ),

        ],
    )


    joins = [

        condition

        for relationship
        in context.relationships

        for condition
        in relationship.join_conditions

    ]


    assert any(

        (
            join.source_qualified_column
            ==
            "warehouse.fact_sales.customer_key"

            and

            join.target_qualified_column
            ==
            "warehouse.dim_customer.customer_key"
        )

        or

        (
            join.target_qualified_column
            ==
            "warehouse.fact_sales.customer_key"

            and

            join.source_qualified_column
            ==
            "warehouse.dim_customer.customer_key"
        )

        for join in joins
    )