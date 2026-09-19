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

            source_table=
            first.target_table,

            target_table=
            second.target_table,

            relationship_type=
            "many-to-many",

            source_cardinality=
            "many",

            target_cardinality=
            "many",

            through_table=
            junction_table.name,

            
            foreign_keys=[
                first.foreign_keys[0],
                second.foreign_keys[0],
            ],

            reasoning=generate_relationship_reasoning(
                relationship_type="many-to-many",
                through_table=junction_table.name,
                foreign_keys=[
                    first.foreign_keys[0],
                    second.foreign_keys[0],
                ],
                source_optional=False,
                target_optional=False
            ),

            confidence=calculate_relationship_confidence(
                relationship_type="many-to-many",
                foreign_keys=[
                    first.foreign_keys[0],
                    second.foreign_keys[0],
                ],
                through_table=junction_table.name
            )
)
    )


    return relationships


def infer_direct_relationship(
    source_table: TableMetadata,
    relationship: RelationshipMetadata,
) -> RelationshipMetadata:


    fk_column = None


    for column in source_table.columns:

        if column.name in relationship.foreign_keys:

            fk_column = column
            break


    if fk_column is None:

        return relationship


    if fk_column.is_unique:

        return RelationshipMetadata(

            source_table=
            relationship.source_table,

            target_table=
            relationship.target_table,

            relationship_type=
            "one-to-one",

            source_cardinality=
            "one",

            target_cardinality=
            "one",

            foreign_keys=
                relationship.foreign_keys
            ,
           reasoning=generate_relationship_reasoning(
            relationship_type="one-to-one",
            through_table=None,
            foreign_keys=relationship.foreign_keys,
            source_optional=fk_column.nullable,
            target_optional=False
        ),

        confidence=calculate_relationship_confidence(
            relationship_type="one-to-one",
            foreign_keys=relationship.foreign_keys,
            through_table=None
        )
)


    return RelationshipMetadata(
        source_table=
        relationship.source_table,

        target_table=
        relationship.target_table,

        relationship_type=
        "many-to-one",

        source_cardinality=
        "many",

        target_cardinality=
        "one",

        foreign_keys=
            relationship.foreign_keys
        ,
        reasoning=generate_relationship_reasoning(
        relationship_type="many-to-one",
        through_table=None,
        foreign_keys=relationship.foreign_keys,
        source_optional=fk_column.nullable,
        target_optional=False
    ),

    confidence=calculate_relationship_confidence(
        relationship_type="many-to-one",
        foreign_keys=relationship.foreign_keys,
        through_table=None
    ),
    )


def infer_self_relationship(
    relationship: RelationshipMetadata,
) -> RelationshipMetadata:


    if (
        relationship.source_table
        != relationship.target_table
    ):
        return relationship


    return RelationshipMetadata(

        source_table=
        relationship.source_table,

        target_table=
        relationship.target_table,

        relationship_type=
        "self-referential",

        source_cardinality=
        "many",

        target_cardinality=
        "one",

        source_optional=
        relationship.source_optional,

        target_optional=
        relationship.target_optional,

        through_table=None,

        foreign_keys=
        relationship.foreign_keys,

        reasoning=
        "Detected self-referential relationship where a table references itself, representing hierarchical data.",

        confidence=calculate_relationship_confidence(
    relationship_type="self-referential",
    foreign_keys=relationship.foreign_keys,
    through_table=None
)
    )

def infer_relationships(
    tables: list[TableMetadata],
) -> list[RelationshipMetadata]:

    relationships = []


    # Step 1:
    # Detect many-to-many relationships first

    junction_tables = detect_junction_tables(
        tables
    )


    for junction in junction_tables:

        relationships.extend(
            infer_many_to_many(
                junction
            )
        )


    # Step 2:
    # Infer direct FK relationships

    junction_names = {
        table.name
        for table in junction_tables
    }


    for table in tables:

        # Skip junction tables
        # because their meaning was already captured
        if table.name in junction_names:
            continue


        for relationship in table.relationships:


            if (
                relationship.source_table
                ==
                relationship.target_table
            ):

                inferred = infer_self_relationship(
                    relationship
                )


            else:

                inferred = infer_direct_relationship(
                    table,
                    relationship
                )


            relationships.append(
                inferred
            )


    return relationships