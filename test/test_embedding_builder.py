from textSQL.metadata.models import (
    DatabaseMetadata,
    SchemaMetadata,
    TableMetadata,
    ColumnMetadata,
)

from textSQL.embeddings.builder import (
    MetadataEmbeddingBuilder,
)


def test_table_embedding_contains_semantic_metadata():

    table = TableMetadata(

        name="customer_events",

        schema_name="public",

        description=(
            "Customer behavioral activity."
        ),

        business_role=(
            "Tracks customer interactions."
        ),

        columns=[

            ColumnMetadata(

                name="event_type",

                data_type="VARCHAR",

                nullable=False,

                description=(
                    "Type of customer event."
                ),

                business_meaning=(
                    "product_view means a "
                    "customer viewed a product."
                ),

                allowed_values=[
                    "product_view",
                    "search",
                    "add_to_cart",
                ],
            )
        ],
    )


    metadata = DatabaseMetadata(

        database_name="test",

        schemas=[

            SchemaMetadata(

                name="public",

                schema_type="operational",

                tables=[
                    table
                ],
            )
        ],

        relationships=[],

        metrics=[],
    )


    builder = (
        MetadataEmbeddingBuilder(
            metadata
        )
    )


    documents = (
        builder.build()
    )


    assert len(
        documents
    ) == 1


    content = (
        documents[0]
        .content
    )


    assert (
        "Customer behavioral activity"
        in content
    )

    assert (
        "Tracks customer interactions"
        in content
    )

    assert (
        "event_type"
        in content
    )

    assert (
        "product_view"
        in content
    )

    assert (
        "customer viewed a product"
        in content
    )

    assert (
        "add_to_cart"
        in content
    )