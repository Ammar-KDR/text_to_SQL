from textSQL.metadata.models import (
    DatabaseMetadata,
    SchemaMetadata,
    TableMetadata,
    ColumnMetadata,
    RelationshipMetadata,
    JoinConditionMetadata,
)

from textSQL.metadata.graph import (
    build_schema_graph,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)

from textSQL.retrieval.temporal_resolver import (
    TemporalDependencyResolver,
)


def build_index():

    fact_sales = TableMetadata(

        name="fact_sales",

        schema_name="warehouse",

        columns=[

            ColumnMetadata(
                name="date_key",
                data_type="INTEGER",
                nullable=False,
            ),

            ColumnMetadata(
                name="revenue",
                data_type="NUMERIC",
                nullable=False,
            ),
        ],
    )


    dim_date = TableMetadata(

        name="dim_date",

        schema_name="warehouse",

        columns=[

            ColumnMetadata(
                name="date_key",
                data_type="INTEGER",
                nullable=False,
                is_primary_key=True,
            ),

            ColumnMetadata(
                name="full_date",
                data_type="DATE",
                nullable=False,
            ),

            ColumnMetadata(
                name="quarter",
                data_type="INTEGER",
                nullable=False,
            ),
        ],
    )


    payments = TableMetadata(

        name="payments",

        schema_name="public",

        columns=[

            ColumnMetadata(
                name="attempted_at",
                data_type="TIMESTAMP",
                nullable=False,
            ),
        ],
    )


    relationship = (
        RelationshipMetadata(

            source_schema="warehouse",

            source_table="fact_sales",

            target_schema="warehouse",

            target_table="dim_date",

            relationship_type=(
                "many-to-one"
            ),

            source_cardinality="many",

            target_cardinality="one",

            join_conditions=[

                JoinConditionMetadata(

                    source_schema="warehouse",

                    source_table="fact_sales",

                    source_column="date_key",

                    target_schema="warehouse",

                    target_table="dim_date",

                    target_column="date_key",
                )
            ],
        )
    )


    tables = [
        fact_sales,
        dim_date,
        payments,
    ]


    graph = build_schema_graph(

        [relationship],

        [
            table.qualified_name
            for table
            in tables
        ],
    )


    metadata = DatabaseMetadata(

        database_name="test",

        schemas=[

            SchemaMetadata(
                name="warehouse",
                schema_type="analytical",
                tables=[
                    fact_sales,
                    dim_date,
                ],
            ),

            SchemaMetadata(
                name="public",
                schema_type="operational",
                tables=[
                    payments
                ],
            ),
        ],

        relationships=[
            relationship
        ],

        metrics=[],

        graph=graph,
    )


    return MetadataIndex(
        metadata,
        graph,
    )


def candidate(
    qualified_name: str,
):

    bare_name = (
        qualified_name
        .split(".")[-1]
    )


    return RetrievalCandidate(

        object_id=(
            f"table_{qualified_name}"
        ),

        object_type="table",

        object_name=bare_name,

        score=1.0,

        source="test",
    )


def test_last_quarter_adds_date_dimension():

    resolver = (
        TemporalDependencyResolver(
            build_index()
        )
    )


    result = resolver.resolve(

        "show revenue last quarter",

        [
            candidate(
                "warehouse.fact_sales"
            )
        ],
    )


    ids = {

        item.object_id

        for item
        in result.candidates
    }


    assert (
        "table_warehouse.dim_date"
        in ids
    )


    assert len(
        result.constraints
    ) == 1


    constraint = (
        result.constraints[0]
    )


    assert (
        constraint.column
        ==
        "warehouse.dim_date.full_date"
    )


    assert (
        constraint.start_expression
        ==
        (
            "DATE_TRUNC('quarter', "
            "CURRENT_DATE) - "
            "INTERVAL '3 months'"
        )
    )


    assert (
        constraint.end_expression
        ==
        (
            "DATE_TRUNC('quarter', "
            "CURRENT_DATE)"
        )
    )


def test_operational_timestamp_does_not_add_dim_date():

    resolver = (
        TemporalDependencyResolver(
            build_index()
        )
    )


    result = resolver.resolve(

        "completed payments last month",

        [
            candidate(
                "public.payments"
            )
        ],
    )


    ids = {

        item.object_id

        for item
        in result.candidates
    }


    assert (
        "table_warehouse.dim_date"
        not in ids
    )


    assert (
        result.constraints
        ==
        []
    )


def test_no_temporal_phrase_does_nothing():

    resolver = (
        TemporalDependencyResolver(
            build_index()
        )
    )


    result = resolver.resolve(

        "show revenue",

        [
            candidate(
                "warehouse.fact_sales"
            )
        ],
    )


    ids = {

        item.object_id

        for item
        in result.candidates
    }


    assert ids == {
        "table_warehouse.fact_sales"
    }


    assert (
        result.constraints
        ==
        []
    )


def test_last_month_uses_calendar_boundaries():

    resolver = (
        TemporalDependencyResolver(
            build_index()
        )
    )


    result = resolver.resolve(

        "show revenue last month",

        [
            candidate(
                "warehouse.fact_sales"
            )
        ],
    )


    constraint = (
        result.constraints[0]
    )


    assert (
        constraint.start_expression
        ==
        (
            "DATE_TRUNC('month', "
            "CURRENT_DATE) - "
            "INTERVAL '1 month'"
        )
    )


    assert (
        constraint.end_expression
        ==
        (
            "DATE_TRUNC('month', "
            "CURRENT_DATE)"
        )
    )


    assert (
        constraint.start_inclusive
        is True
    )

    assert (
        constraint.end_inclusive
        is False
    )