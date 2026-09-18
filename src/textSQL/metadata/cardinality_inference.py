from textSQL.metadata.models import (
    RelationshipMetadata,
    TableMetadata,
)

def infer_cardinality(
    relationship,
    tables
):

    # Many-to-many already handled
    if relationship.relationship_type == "many-to-many":

        relationship.source_cardinality = "many"
        relationship.target_cardinality = "many"

        return relationship


    source_table = next(
        (
            table
            for table in tables
            if table.name == relationship.source_table
        ),
        None,
    )


    if source_table is None:
        return relationship


    fk_column = relationship.foreign_keys[0]


    column_metadata = next(
        (
            column
            for column in source_table.columns
            if column.name == fk_column
        ),
        None,
    )


    if column_metadata is None:
        return relationship


    # Cardinality

    if column_metadata.is_unique:

        relationship.source_cardinality = "one"

    else:

        relationship.source_cardinality = "many"


    relationship.target_cardinality = "one"


    # Optionality

    relationship.source_optional = (
        column_metadata.nullable
    )


    return relationship