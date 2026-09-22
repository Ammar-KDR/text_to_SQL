from textSQL.metadata.models import RelationshipMetadata


def normalize_relationships(
    relationships: list[RelationshipMetadata],
) -> list[RelationshipMetadata]:

    normalized = []

    seen = set()


    for relationship in relationships:

        join_key = tuple(

            sorted(

                (

                    condition.source_schema,
                    condition.source_table,
                    condition.source_column,
                    condition.target_schema,
                    condition.target_table,
                    condition.target_column,

                )

                for condition
                in relationship.join_conditions

            )
        )


        source = (
            relationship
            .source_qualified_name
        )

        target = (
            relationship
            .target_qualified_name
        )


        if (
            relationship.relationship_type
            ==
            "many-to-many"
        ):

            key = (

                frozenset([
                    source,
                    target,
                ]),

                relationship.relationship_type,

                relationship.through_qualified_name,

                join_key,
            )

        else:

            key = (

                source,

                target,

                relationship.relationship_type,

                join_key,
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