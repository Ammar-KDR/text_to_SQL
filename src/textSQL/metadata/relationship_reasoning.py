def generate_relationship_reasoning(
    relationship_type,
    through_table,
    foreign_keys,
    source_optional,
    target_optional
):

    if relationship_type == "many-to-many":

        return (
            f"Detected junction table '{through_table}' "
            f"containing foreign keys {foreign_keys} "
            f"connecting two entities."
        )


    if relationship_type == "one-to-one":

        return (
            "Detected one-to-one relationship because "
            "the foreign key column is unique."
        )


    if relationship_type == "foreign_key":

        optionality = (
            "optional"
            if source_optional
            else "required"
        )

        return (
            f"Detected foreign key relationship. "
            f"Source record is {optionality} "
            f"based on foreign key nullability."
        )


    return "Relationship inferred from schema constraints."


def calculate_relationship_confidence(
    relationship_type,
    foreign_keys,
    through_table
):

    if relationship_type == "many-to-many":

        if through_table and len(foreign_keys) == 2:
            return 0.98

        return 0.85


    if relationship_type == "one-to-one":

        return 0.95


    if relationship_type == "foreign_key":

        return 0.99


    return 0.70