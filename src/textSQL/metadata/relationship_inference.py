from textSQL.metadata.models import (
    TableMetadata,
    RelationshipMetadata,
)

from .relationship_reasoning import generate_relationship_reasoning, calculate_relationship_confidence
def detect_junction_tables(
    tables: list[TableMetadata],
) -> list[TableMetadata]:

    junction_tables = []

    for table in tables:

        foreign_keys = table.relationships

        if len(foreign_keys) < 2:
            continue


        fk_columns = {
            fk_column
            for fk in foreign_keys
            for fk_column in fk.foreign_keys
        }


        primary_keys = set(
            table.primary_keys
        )


        # Composite PK made from foreign keys
        if (
            len(primary_keys) > 0
            and primary_keys == fk_columns
        ):
            junction_tables.append(table)


    return junction_tables

def infer_many_to_many(
    junction_table: TableMetadata,
) -> list[RelationshipMetadata]:

    relationships = []


    foreign_keys = (
        junction_table.relationships
    )


    if len(foreign_keys) != 2:
        return relationships


    first = foreign_keys[0]

    second = foreign_keys[1]

    relationships.append(

        RelationshipMetadata(

            source_schema=
                first.target_schema,

            source_table=
                first.target_table,

            target_schema=
                second.target_schema,

            target_table=
                second.target_table,

            relationship_type=
                "many-to-many",

            source_cardinality=
                "many",

            target_cardinality=
                "many",

            through_schema=
                junction_table.schema_name,

            through_table=
                junction_table.name,

            foreign_keys=[
                *first.foreign_keys,
                *second.foreign_keys,
            ],

            join_conditions=[
                *first.join_conditions,
                *second.join_conditions,
            ],

            reasoning=
                generate_relationship_reasoning(

                    relationship_type=
                        "many-to-many",

                    through_table=
                        junction_table.qualified_name,

                    foreign_keys=[
                        *first.foreign_keys,
                        *second.foreign_keys,
                    ],

                    source_optional=False,

                    target_optional=False,
                ),

            confidence=
                calculate_relationship_confidence(

                    relationship_type=
                        "many-to-many",

                    foreign_keys=[
                        *first.foreign_keys,
                        *second.foreign_keys,
                    ],

                    through_table=
                        junction_table.qualified_name,
                ),
        )
    )


    return relationships


def infer_direct_relationship(
    source_table: TableMetadata,
    relationship: RelationshipMetadata,
) -> RelationshipMetadata:

    fk_column = None


    for column in source_table.columns:

        if (
            column.name
            in relationship.foreign_keys
        ):

            fk_column = column

            break


    if fk_column is None:
        return relationship


    if fk_column.is_unique:

        return relationship.model_copy(

            update={

                "relationship_type":
                    "one-to-one",

                "source_cardinality":
                    "one",

                "target_cardinality":
                    "one",

                "source_optional":
                    fk_column.nullable,

                "target_optional":
                    False,

                "reasoning":
                    generate_relationship_reasoning(
                        relationship_type=
                            "one-to-one",
                        through_table=None,
                        foreign_keys=
                            relationship.foreign_keys,
                        source_optional=
                            fk_column.nullable,
                        target_optional=False,
                    ),

                "confidence":
                    calculate_relationship_confidence(
                        relationship_type=
                            "one-to-one",
                        foreign_keys=
                            relationship.foreign_keys,
                        through_table=None,
                    ),
            }
        )


    return relationship.model_copy(

        update={

            "relationship_type":
                "many-to-one",

            "source_cardinality":
                "many",

            "target_cardinality":
                "one",

            "source_optional":
                fk_column.nullable,

            "target_optional":
                False,

            "reasoning":
                generate_relationship_reasoning(
                    relationship_type=
                        "many-to-one",
                    through_table=None,
                    foreign_keys=
                        relationship.foreign_keys,
                    source_optional=
                        fk_column.nullable,
                    target_optional=False,
                ),

            "confidence":
                calculate_relationship_confidence(
                    relationship_type=
                        "many-to-one",
                    foreign_keys=
                        relationship.foreign_keys,
                    through_table=None,
                ),
        }
    )

def infer_self_relationship(
    relationship: RelationshipMetadata,
) -> RelationshipMetadata:

    same_table = (

        relationship.source_table
        ==
        relationship.target_table

        and

        relationship.source_schema
        ==
        relationship.target_schema
    )


    if not same_table:
        return relationship


    return relationship.model_copy(

        update={

            "relationship_type":
                "self-referential",

            "source_cardinality":
                "many",

            "target_cardinality":
                "one",

            "through_table":
                None,

            "reasoning":
                (
                    "Detected self-referential "
                    "relationship where a table "
                    "references itself."
                ),

            "confidence":
                calculate_relationship_confidence(
                    relationship_type=
                        "self-referential",
                    foreign_keys=
                        relationship.foreign_keys,
                    through_table=None,
                ),
        }
    )
def infer_relationships(
    tables: list[TableMetadata],
) -> list[RelationshipMetadata]:

    relationships = []


    # --------------------------------------------------
    # Step 1:
    # Detect semantic many-to-many relationships.
    #
    # These describe business/schema meaning:
    #
    # customers
    #     ↕
    # campaigns
    #
    # through:
    # customer_campaigns
    #
    # They are NOT a replacement for the underlying
    # physical foreign-key relationships.
    # --------------------------------------------------

    junction_tables = (
        detect_junction_tables(
            tables
        )
    )


    for junction in junction_tables:

        relationships.extend(

            infer_many_to_many(
                junction
            )

        )


    # --------------------------------------------------
    # Step 2:
    # Preserve ALL physical foreign-key relationships.
    #
    # Junction tables must NOT be skipped.
    #
    # Example:
    #
    # customer_campaigns.customer_id
    #     -> customers.customer_id
    #
    # customer_campaigns.campaign_id
    #     -> campaigns.campaign_id
    #
    # These physical edges are what SQL generation
    # actually needs.
    # --------------------------------------------------

    for table in tables:

        for relationship in (
            table.relationships
        ):

            same_table = (

                relationship.source_table
                ==
                relationship.target_table

                and

                relationship.source_schema
                ==
                relationship.target_schema
            )


            if same_table:

                inferred = (
                    infer_self_relationship(
                        relationship
                    )
                )

            else:

                inferred = (
                    infer_direct_relationship(
                        table,
                        relationship,
                    )
                )


            relationships.append(
                inferred
            )


    return relationships