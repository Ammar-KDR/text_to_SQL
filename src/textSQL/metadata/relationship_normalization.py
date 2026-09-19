from textSQL.metadata.models import RelationshipMetadata


def normalize_relationships(
    relationships: list[RelationshipMetadata],
) -> list[RelationshipMetadata]:

    normalized = []

    seen = set()


    for relationship in relationships:


        # Only many-to-many is direction independent
        if relationship.relationship_type == "many-to-many":

            key = (
                frozenset(
                    [
                        relationship.source_table,
                        relationship.target_table,
                    ]
                ),
                relationship.relationship_type,
                relationship.through_table,
            )

        else:

            # Direction matters
            key = (
                relationship.source_table,
                relationship.target_table,
                relationship.relationship_type,
                tuple(relationship.foreign_keys),
            )


        if key in seen:
            continue


        seen.add(key)


        relationship.foreign_keys = sorted(
            relationship.foreign_keys
        )


        normalized.append(
            relationship
        )


    return normalized