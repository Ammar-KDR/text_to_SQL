from textSQL.metadata.models import (
    RelationshipMetadata,
    JoinConditionMetadata,
)

from textSQL.metadata.graph import (
    SchemaGraph,
    build_schema_graph,
)

from textSQL.retrieval.graph_retriever import (
    GraphRetriever,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)


# ============================================================
# RELATIONSHIPS
# ============================================================


def warehouse_relationship():

    return RelationshipMetadata(

        source_schema=
            "warehouse",

        source_table=
            "fact_sales",

        target_schema=
            "warehouse",

        target_table=
            "dim_customer",

        relationship_type=
            "many-to-one",

        source_cardinality=
            "many",

        target_cardinality=
            "one",

        foreign_keys=[
            "customer_key"
        ],

        join_conditions=[

            JoinConditionMetadata(

                source_schema=
                    "warehouse",

                source_table=
                    "fact_sales",

                source_column=
                    "customer_key",

                target_schema=
                    "warehouse",

                target_table=
                    "dim_customer",

                target_column=
                    "customer_key",
            )

        ],
    )


def public_relationship():

    return RelationshipMetadata(

        source_schema=
            "public",

        source_table=
            "orders",

        target_schema=
            "public",

        target_table=
            "customers",

        relationship_type=
            "many-to-one",

        source_cardinality=
            "many",

        target_cardinality=
            "one",

        foreign_keys=[
            "customer_id"
        ],

        join_conditions=[

            JoinConditionMetadata(

                source_schema=
                    "public",

                source_table=
                    "orders",

                source_column=
                    "customer_id",

                target_schema=
                    "public",

                target_table=
                    "customers",

                target_column=
                    "customer_id",
            )

        ],
    )


# ============================================================
# GRAPH NODE IDENTITY
# ============================================================


def test_graph_uses_qualified_nodes():

    graph = build_schema_graph(

        relationships=[
            warehouse_relationship(),
            public_relationship(),
        ],

        tables=[

            "warehouse.fact_sales",

            "warehouse.dim_customer",

            "public.orders",

            "public.customers",
        ],
    )


    assert (
        "warehouse.fact_sales"
        in graph.nodes
    )

    assert (
        "warehouse.dim_customer"
        in graph.nodes
    )

    assert (
        "public.orders"
        in graph.nodes
    )

    assert (
        "public.customers"
        in graph.nodes
    )


# ============================================================
# QUALIFIED PATH
# ============================================================


def test_graph_finds_qualified_path():

    relationship = (
        warehouse_relationship()
    )


    graph = build_schema_graph(

        relationships=[
            relationship
        ],

        tables=[

            "warehouse.fact_sales",

            "warehouse.dim_customer",

        ],
    )


    path = graph.find_path(

        "warehouse.fact_sales",

        "warehouse.dim_customer",

    )


    assert path is not None

    assert len(path) == 1

    assert (
        path[0].object_id
        ==
        relationship.object_id
    )


# ============================================================
# SCHEMA ISOLATION
# ============================================================


def test_same_bare_name_is_schema_distinct():

    graph = SchemaGraph()


    graph.add_table(
        "public.orders"
    )

    graph.add_table(
        "archive.orders"
    )


    assert (
        "public.orders"
        in graph.nodes
    )

    assert (
        "archive.orders"
        in graph.nodes
    )


    assert len(graph.nodes) == 2


def test_graph_does_not_guess_bare_name():

    graph = SchemaGraph()


    graph.add_table(
        "public.orders"
    )


    path = graph.find_path(
        "orders",
        "public.orders",
    )


    assert path is None


# ============================================================
# NO CROSS-SCHEMA ACCIDENTAL PATH
# ============================================================


def test_graph_does_not_cross_schema_without_relationship():

    graph = build_schema_graph(

        relationships=[
            warehouse_relationship()
        ],

        tables=[

            "warehouse.fact_sales",

            "warehouse.dim_customer",

            "public.fact_sales",

        ],
    )


    path = graph.find_path(

        "public.fact_sales",

        "warehouse.dim_customer",

    )


    assert path is None


# ============================================================
# RELATIONSHIP OBJECT ID
# ============================================================


def test_relationship_object_id_is_schema_aware():

    relationship = (
        warehouse_relationship()
    )


    assert (
        "warehouse.fact_sales"
        in relationship.object_id
    )

    assert (
        "warehouse.dim_customer"
        in relationship.object_id
    )

    assert (
        "customer_key"
        in relationship.object_id
    )


# ============================================================
# GRAPH RETRIEVER
# ============================================================


class FakeMetadataIndex:
    pass


def test_graph_retriever_uses_qualified_table_ids():

    relationship = (
        warehouse_relationship()
    )


    graph = build_schema_graph(

        relationships=[
            relationship
        ],

        tables=[

            "warehouse.fact_sales",

            "warehouse.dim_customer",

        ],
    )


    retriever = GraphRetriever(

        metadata_index=
            FakeMetadataIndex(),

        graph=
            graph,
    )


    candidates = [

        RetrievalCandidate(

            object_id=
                "table_warehouse.fact_sales",

            object_type=
                "table",

            object_name=
                "fact_sales",

            score=
                1.0,

            source=
                "dependency",
        ),

        RetrievalCandidate(

            object_id=
                "table_warehouse.dim_customer",

            object_type=
                "table",

            object_name=
                "dim_customer",

            score=
                1.0,

            source=
                "dense",
        ),
    ]


    results = retriever.retrieve(
        candidates
    )


    assert len(results) == 1


    result = results[0]


    assert (
        result.object_id
        ==
        relationship.object_id
    )


    assert (
        result.object_type
        ==
        "relationship"
    )


    assert (
        "warehouse.fact_sales"
        in result.object_name
    )


# ============================================================
# OLD UNSCHEMA-QUALIFIED OBJECTS STILL WORK IN UNIT TESTS
# ============================================================


def test_graph_remains_compatible_with_unqualified_metadata():

    relationship = RelationshipMetadata(

        source_table=
            "orders",

        target_table=
            "customers",

        relationship_type=
            "many-to-one",

        source_cardinality=
            "many",

        target_cardinality=
            "one",

        foreign_keys=[
            "customer_id"
        ],
    )


    graph = build_schema_graph(

        relationships=[
            relationship
        ],

        tables=[
            "orders",
            "customers",
        ],
    )


    path = graph.find_path(
        "orders",
        "customers",
    )


    assert path is not None

    assert len(path) == 1


def test_graph_retriever_does_not_duplicate_shared_edges():

    fact_to_product = RelationshipMetadata(

        source_schema=
            "warehouse",

        source_table=
            "fact_sales",

        target_schema=
            "warehouse",

        target_table=
            "dim_product",

        relationship_type=
            "many-to-one",

        source_cardinality=
            "many",

        target_cardinality=
            "one",

        foreign_keys=[
            "product_key"
        ],

        join_conditions=[

            JoinConditionMetadata(

                source_schema=
                    "warehouse",

                source_table=
                    "fact_sales",

                source_column=
                    "product_key",

                target_schema=
                    "warehouse",

                target_table=
                    "dim_product",

                target_column=
                    "product_key",
            )

        ],
    )


    product_to_campaign = RelationshipMetadata(

        source_schema=
            "warehouse",

        source_table=
            "dim_product",

        target_schema=
            "warehouse",

        target_table=
            "dim_campaign",

        relationship_type=
            "many-to-one",

        source_cardinality=
            "many",

        target_cardinality=
            "one",

        foreign_keys=[
            "campaign_key"
        ],

        join_conditions=[

            JoinConditionMetadata(

                source_schema=
                    "warehouse",

                source_table=
                    "dim_product",

                source_column=
                    "campaign_key",

                target_schema=
                    "warehouse",

                target_table=
                    "dim_campaign",

                target_column=
                    "campaign_key",
            )

        ],
    )


    graph = build_schema_graph(

        relationships=[

            fact_to_product,

            product_to_campaign,

        ],

        tables=[

            "warehouse.fact_sales",

            "warehouse.dim_product",

            "warehouse.dim_campaign",

        ],
    )


    retriever = GraphRetriever(

        metadata_index=
            FakeMetadataIndex(),

        graph=
            graph,
    )


    candidates = [

        RetrievalCandidate(

            object_id=
                "table_warehouse.fact_sales",

            object_type=
                "table",

            object_name=
                "fact_sales",

            score=1.0,

            source="dependency",
        ),

        RetrievalCandidate(

            object_id=
                "table_warehouse.dim_product",

            object_type=
                "table",

            object_name=
                "dim_product",

            score=1.0,

            source="dependency",
        ),

        RetrievalCandidate(

            object_id=
                "table_warehouse.dim_campaign",

            object_type=
                "table",

            object_name=
                "dim_campaign",

            score=1.0,

            source="dependency",
        ),

    ]


    results = retriever.retrieve(
        candidates
    )


    ids = [

        result.object_id

        for result in results

    ]


    assert (
        len(ids)
        ==
        len(set(ids))
    )


    assert (
        ids.count(
            fact_to_product.object_id
        )
        ==
        1
    )