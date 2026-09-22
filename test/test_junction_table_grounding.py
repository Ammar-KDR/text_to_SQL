from textSQL.metadata.models import (
    ColumnMetadata,
    DatabaseMetadata,
    SchemaMetadata,
    TableMetadata,
    RelationshipMetadata,
    JoinConditionMetadata,
)

from textSQL.metadata.relationship_inference import (
    infer_relationships,
)

from textSQL.metadata.relationship_normalization import (
    normalize_relationships,
)

from textSQL.metadata.graph import (
    build_schema_graph,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.context_builder import (
    ContextBuilder,
)

from textSQL.retrieval.model import (
    FusedCandidate,
)


# ============================================================
# HELPERS
# ============================================================


def physical_fk(
    source_table,
    source_column,
    target_table,
    target_column,
):

    return RelationshipMetadata(

        source_schema=
            "public",

        source_table=
            source_table,

        target_schema=
            "public",

        target_table=
            target_table,

        relationship_type=
            "foreign_key",

        source_cardinality=
            "unknown",

        target_cardinality=
            "unknown",

        foreign_keys=[
            source_column
        ],

        join_conditions=[

            JoinConditionMetadata(

                source_schema=
                    "public",

                source_table=
                    source_table,

                source_column=
                    source_column,

                target_schema=
                    "public",

                target_table=
                    target_table,

                target_column=
                    target_column,
            )

        ],
    )


def create_tables():

    customers = TableMetadata(

        name=
            "customers",

        schema_name=
            "public",

        columns=[

            ColumnMetadata(

                name=
                    "customer_id",

                data_type=
                    "integer",

                nullable=
                    False,

                is_primary_key=
                    True,

                is_unique=
                    True,
            )

        ],

        primary_keys=[
            "customer_id"
        ],
    )


    campaigns = TableMetadata(

        name=
            "campaigns",

        schema_name=
            "public",

        columns=[

            ColumnMetadata(

                name=
                    "campaign_id",

                data_type=
                    "integer",

                nullable=
                    False,

                is_primary_key=
                    True,

                is_unique=
                    True,
            )

        ],

        primary_keys=[
            "campaign_id"
        ],
    )


    customer_fk = physical_fk(

        "customer_campaigns",

        "customer_id",

        "customers",

        "customer_id",
    )


    campaign_fk = physical_fk(

        "customer_campaigns",

        "campaign_id",

        "campaigns",

        "campaign_id",
    )


    customer_campaigns = (
        TableMetadata(

            name=
                "customer_campaigns",

            schema_name=
                "public",

            columns=[

                ColumnMetadata(

                    name=
                        "customer_id",

                    data_type=
                        "integer",

                    nullable=
                        False,

                    is_primary_key=
                        True,
                ),

                ColumnMetadata(

                    name=
                        "campaign_id",

                    data_type=
                        "integer",

                    nullable=
                        False,

                    is_primary_key=
                        True,
                ),

            ],

            relationships=[

                customer_fk,

                campaign_fk,

            ],

            primary_keys=[

                "customer_id",

                "campaign_id",

            ],
        )
    )


    return [

        customers,

        campaigns,

        customer_campaigns,

    ]


# ============================================================
# RELATIONSHIP INFERENCE
# ============================================================


def test_junction_preserves_physical_relationships():

    tables = create_tables()


    relationships = (
        normalize_relationships(

            infer_relationships(
                tables
            )

        )
    )


    physical = [

        relationship

        for relationship
        in relationships

        if (
            relationship
            .source_qualified_name
            ==
            "public.customer_campaigns"
        )

    ]


    targets = {

        relationship
        .target_qualified_name

        for relationship
        in physical

    }


    assert (
        "public.customers"
        in targets
    )

    assert (
        "public.campaigns"
        in targets
    )


# ============================================================
# SEMANTIC MANY-TO-MANY
# ============================================================


def test_semantic_many_to_many_is_preserved():

    tables = create_tables()


    relationships = (
        normalize_relationships(

            infer_relationships(
                tables
            )

        )
    )


    many_to_many = [

        relationship

        for relationship
        in relationships

        if (
            relationship
            .relationship_type
            ==
            "many-to-many"
        )

    ]


    assert (
        len(many_to_many)
        ==
        1
    )


    relationship = (
        many_to_many[0]
    )


    assert (
        relationship
        .through_qualified_name
        ==
        "public.customer_campaigns"
    )


    endpoints = {

        relationship
        .source_qualified_name,

        relationship
        .target_qualified_name,

    }


    assert endpoints == {

        "public.customers",

        "public.campaigns",

    }


# ============================================================
# GRAPH MUST USE PHYSICAL EDGES
# ============================================================


def test_graph_routes_through_junction_table():

    tables = create_tables()


    relationships = (
        normalize_relationships(

            infer_relationships(
                tables
            )

        )
    )


    graph = build_schema_graph(

        relationships=
            relationships,

        tables=[

            table.qualified_name

            for table
            in tables

        ],
    )


    path = graph.find_path(

        "public.customers",

        "public.campaigns",

    )


    assert path is not None


    # Must be:
    #
    # customers
    #   -> customer_campaigns
    #   -> campaigns

    assert (
        len(path)
        ==
        2
    )


    assert all(

        relationship
        .relationship_type
        !=
        "many-to-many"

        for relationship
        in path

    )


    assert any(

        relationship
        .source_qualified_name
        ==
        "public.customer_campaigns"

        and

        relationship
        .target_qualified_name
        ==
        "public.customers"

        for relationship
        in path

    )


    assert any(

        relationship
        .source_qualified_name
        ==
        "public.customer_campaigns"

        and

        relationship
        .target_qualified_name
        ==
        "public.campaigns"

        for relationship
        in path

    )


# ============================================================
# FINAL CONTEXT MUST INCLUDE JUNCTION TABLE
# ============================================================


def test_context_builder_adds_junction_table():

    tables = create_tables()


    relationships = (
        normalize_relationships(

            infer_relationships(
                tables
            )

        )
    )


    graph = build_schema_graph(

        relationships=
            relationships,

        tables=[

            table.qualified_name

            for table
            in tables

        ],
    )


    metadata = DatabaseMetadata(

        database_name=
            "test_db",

        schemas=[

            SchemaMetadata(

                name=
                    "public",

                schema_type=
                    "operational",

                tables=
                    tables,
            )

        ],

        relationships=
            relationships,

        metrics=[],

        graph=
            graph,
    )


    index = MetadataIndex(

        metadata,

        graph,
    )


    builder = ContextBuilder(
        index
    )


    context = builder.build(

        question=
            "show customers by campaign",

        candidates=[

            FusedCandidate(

                object_id=
                    "table_public.customers",

                object_type=
                    "table",

                object_name=
                    "customers",

                rrf_score=
                    0.05,

                sources=[
                    "dense"
                ],
            ),

            FusedCandidate(

                object_id=
                    "table_public.campaigns",

                object_type=
                    "table",

                object_name=
                    "campaigns",

                rrf_score=
                    0.04,

                sources=[
                    "dense"
                ],
            ),

        ],
    )


    assert (
        len(context.join_paths)
        ==
        1
    )


    path = (
        context.join_paths[0]
    )


    assert path.tables == [

        "public.customers",

        "public.customer_campaigns",

        "public.campaigns",

    ]


    context_tables = {

        table.qualified_name

        for table
        in context.tables

    }


    assert (
        "public.customer_campaigns"
        in context_tables
    )


    assert (
        len(
            path.relationships
        )
        ==
        2
    )


# ============================================================
# EXACT FK CONDITIONS SURVIVE
# ============================================================


def test_junction_join_conditions_are_exact():

    tables = create_tables()


    relationships = (
        normalize_relationships(

            infer_relationships(
                tables
            )

        )
    )


    physical = [

        relationship

        for relationship
        in relationships

        if (
            relationship
            .source_qualified_name
            ==
            "public.customer_campaigns"
        )

    ]


    joins = {

        (
            condition
            .source_qualified_column,

            condition
            .target_qualified_column,
        )

        for relationship
        in physical

        for condition
        in relationship.join_conditions

    }


    assert (

        "public.customer_campaigns.customer_id",

        "public.customers.customer_id",

    ) in joins


    assert (

        "public.customer_campaigns.campaign_id",

        "public.campaigns.campaign_id",

    ) in joins