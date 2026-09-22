from textSQL.metadata.models import (
    TableMetadata,
    RelationshipMetadata,
    JoinConditionMetadata,
)

from textSQL.metadata.graph import (
    build_schema_graph,
)

from textSQL.retrieval.model import (
    FusedCandidate,
)

from textSQL.retrieval.context_builder import (
    ContextBuilder,
)


# ============================================================
# TEST METADATA
# ============================================================


def relationship(
    source,
    target,
    source_column,
    target_column,
):

    return RelationshipMetadata(

        source_schema=
            "warehouse",

        source_table=
            source,

        target_schema=
            "warehouse",

        target_table=
            target,

        relationship_type=
            "many-to-one",

        source_cardinality=
            "many",

        target_cardinality=
            "one",

        foreign_keys=[
            source_column
        ],

        join_conditions=[

            JoinConditionMetadata(

                source_schema=
                    "warehouse",

                source_table=
                    source,

                source_column=
                    source_column,

                target_schema=
                    "warehouse",

                target_table=
                    target,

                target_column=
                    target_column,
            )

        ],
    )


FACT_TO_PRODUCT = relationship(

    "fact_sales",

    "dim_product",

    "product_key",

    "product_key",
)


PRODUCT_TO_BRAND = relationship(

    "dim_product",

    "dim_brand",

    "brand_key",

    "brand_key",
)


FACT_SALES = TableMetadata(

    name=
        "fact_sales",

    schema_name=
        "warehouse",
)


DIM_PRODUCT = TableMetadata(

    name=
        "dim_product",

    schema_name=
        "warehouse",
)


DIM_BRAND = TableMetadata(

    name=
        "dim_brand",

    schema_name=
        "warehouse",
)


class FakeMetadataIndex:


    def __init__(self):

        self.graph = (
            build_schema_graph(

                relationships=[

                    FACT_TO_PRODUCT,

                    PRODUCT_TO_BRAND,

                ],

                tables=[

                    "warehouse.fact_sales",

                    "warehouse.dim_product",

                    "warehouse.dim_brand",

                ],
            )
        )


        self.objects = {

            "table_warehouse.fact_sales":
                FACT_SALES,

            "table_warehouse.dim_product":
                DIM_PRODUCT,

            "table_warehouse.dim_brand":
                DIM_BRAND,

            FACT_TO_PRODUCT.object_id:
                FACT_TO_PRODUCT,

            PRODUCT_TO_BRAND.object_id:
                PRODUCT_TO_BRAND,
        }


        self.tables = {

            "warehouse.fact_sales":
                FACT_SALES,

            "warehouse.dim_product":
                DIM_PRODUCT,

            "warehouse.dim_brand":
                DIM_BRAND,
        }


    def get_object(
        self,
        object_id,
    ):

        return self.objects.get(
            object_id
        )


    def get_table(
        self,
        table_name,
    ):

        return self.tables.get(
            table_name
        )


# ============================================================
# HELPERS
# ============================================================


def table_candidate(
    table_name,
    score=0.05,
):

    return FusedCandidate(

        object_id=
            f"table_{table_name}",

        object_type=
            "table",

        object_name=
            table_name.split(".")[-1],

        rrf_score=
            score,

        sources=[
            "dense"
        ],
    )


# ============================================================
# DIRECT JOIN PATH
# ============================================================


def test_direct_join_path_is_added():

    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
            "sales by product",

        candidates=[

            table_candidate(
                "warehouse.fact_sales"
            ),

            table_candidate(
                "warehouse.dim_product"
            ),

        ],
    )


    assert (
        len(result.join_paths)
        ==
        1
    )


    path = (
        result.join_paths[0]
    )


    assert path.tables == [

        "warehouse.fact_sales",

        "warehouse.dim_product",

    ]


    assert (
        len(path.relationships)
        ==
        1
    )


    assert (
        path.relationships[0]
        .object_id
        ==
        FACT_TO_PRODUCT.object_id
    )


# ============================================================
# MULTI-HOP PATH
# ============================================================


def test_multihop_join_path_is_added():

    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
            "sales by brand",

        candidates=[

            table_candidate(
                "warehouse.fact_sales"
            ),

            table_candidate(
                "warehouse.dim_brand"
            ),

        ],
    )


    assert (
        len(result.join_paths)
        ==
        1
    )


    path = (
        result.join_paths[0]
    )


    assert path.tables == [

        "warehouse.fact_sales",

        "warehouse.dim_product",

        "warehouse.dim_brand",

    ]


    assert (
        len(path.relationships)
        ==
        2
    )


# ============================================================
# INTERMEDIATE TABLE
# ============================================================


def test_intermediate_table_is_added_to_context():

    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
            "sales by brand",

        candidates=[

            table_candidate(
                "warehouse.fact_sales"
            ),

            table_candidate(
                "warehouse.dim_brand"
            ),

        ],
    )


    qualified_tables = {

        table.qualified_name

        for table in result.tables
    }


    assert (
        "warehouse.fact_sales"
        in qualified_tables
    )

    assert (
        "warehouse.dim_product"
        in qualified_tables
    )

    assert (
        "warehouse.dim_brand"
        in qualified_tables
    )


# ============================================================
# PATH RELATIONSHIPS
# ============================================================


def test_join_path_relationships_are_added_to_context():

    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
            "sales by brand",

        candidates=[

            table_candidate(
                "warehouse.fact_sales"
            ),

            table_candidate(
                "warehouse.dim_brand"
            ),

        ],
    )


    relationship_ids = {

        relationship.object_id

        for relationship
        in result.relationships
    }


    assert (
        FACT_TO_PRODUCT.object_id
        in relationship_ids
    )

    assert (
        PRODUCT_TO_BRAND.object_id
        in relationship_ids
    )


# ============================================================
# DISCONNECTED TABLES
# ============================================================


def test_disconnected_tables_create_no_join_path():

    disconnected = TableMetadata(

        name=
            "unrelated",

        schema_name=
            "warehouse",
    )


    metadata_index = (
        FakeMetadataIndex()
    )


    metadata_index.objects[
        "table_warehouse.unrelated"
    ] = disconnected


    metadata_index.tables[
        "warehouse.unrelated"
    ] = disconnected


    metadata_index.graph.add_table(
        "warehouse.unrelated"
    )


    builder = ContextBuilder(
        metadata_index
    )


    result = builder.build(

        question=
            "unrelated query",

        candidates=[

            table_candidate(
                "warehouse.fact_sales"
            ),

            table_candidate(
                "warehouse.unrelated"
            ),

        ],
    )


    assert (
        result.join_paths
        ==
        []
    )


# ============================================================
# NO DUPLICATE TABLES
# ============================================================


def test_context_does_not_duplicate_tables():

    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
            "sales by product",

        candidates=[

            table_candidate(
                "warehouse.fact_sales"
            ),

            table_candidate(
                "warehouse.fact_sales",
                score=0.04,
            ),

            table_candidate(
                "warehouse.dim_product"
            ),

        ],
    )


    names = [

        table.qualified_name

        for table
        in result.tables
    ]


    assert (
        len(names)
        ==
        len(set(names))
    )