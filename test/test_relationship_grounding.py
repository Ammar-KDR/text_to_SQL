from textSQL.metadata.models import (
    TableMetadata,
    ColumnMetadata,
    RelationshipMetadata,
    JoinConditionMetadata,
)

from textSQL.metadata.relationship_inference import (
    infer_direct_relationship,
)

from textSQL.metadata.relationship_normalization import (
    normalize_relationships,
)


def create_relationship():

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
            "foreign_key",

        source_cardinality=
            "unknown",

        target_cardinality=
            "unknown",

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


def test_relationship_has_qualified_tables():

    relationship = (
        create_relationship()
    )

    assert (
        relationship.source_qualified_name
        ==
        "warehouse.fact_sales"
    )

    assert (
        relationship.target_qualified_name
        ==
        "warehouse.dim_customer"
    )


def test_join_condition_is_exact():

    relationship = (
        create_relationship()
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


def test_direct_inference_preserves_join_conditions():

    relationship = (
        create_relationship()
    )

    table = TableMetadata(

        name=
            "fact_sales",

        schema_name=
            "warehouse",

        columns=[

            ColumnMetadata(

                name=
                    "customer_key",

                data_type=
                    "integer",

                nullable=
                    False,

                is_unique=
                    False,
            )
        ],
    )


    inferred = (
        infer_direct_relationship(
            table,
            relationship,
        )
    )


    assert (
        inferred.relationship_type
        ==
        "many-to-one"
    )

    assert (
        inferred.source_schema
        ==
        "warehouse"
    )

    assert (
        inferred.target_schema
        ==
        "warehouse"
    )

    assert (
        len(
            inferred.join_conditions
        )
        ==
        1
    )

    assert (
        inferred
        .join_conditions[0]
        .target_column
        ==
        "customer_key"
    )


def test_schema_distinct_relationships_not_deduplicated():

    first = create_relationship()


    second = RelationshipMetadata(

        source_schema=
            "archive",

        source_table=
            "fact_sales",

        target_schema=
            "archive",

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
                    "archive",

                source_table=
                    "fact_sales",

                source_column=
                    "customer_key",

                target_schema=
                    "archive",

                target_table=
                    "dim_customer",

                target_column=
                    "customer_key",
            )
        ],
    )


    normalized = (
        normalize_relationships([
            first,
            second,
        ])
    )


    assert (
        len(normalized)
        ==
        2
    )


def test_duplicate_relationship_is_removed():

    first = create_relationship()

    second = create_relationship()


    normalized = (
        normalize_relationships([
            first,
            second,
        ])
    )


    assert (
        len(normalized)
        ==
        1
    )