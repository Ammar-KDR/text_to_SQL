from textSQL.metadata.graph import (
    build_schema_graph,
)

from textSQL.metadata.models import (
    RelationshipMetadata,
)


def test_find_join_path():


    relationships = [

        RelationshipMetadata(
            source_table="orders",
            target_table="customers",
            relationship_type="many-to-one",
            source_cardinality="many",
            target_cardinality="one",
            source_optional=False,
            target_optional=False,
            foreign_keys=[
                "customer_id"
            ],
            confidence=0.99
        ),


        RelationshipMetadata(
            source_table="order_items",
            target_table="orders",
            relationship_type="many-to-one",
            source_cardinality="many",
            target_cardinality="one",
            source_optional=False,
            target_optional=False,
            foreign_keys=[
                "order_id"
            ],
            confidence=0.99
        ),

    ]


    graph = build_schema_graph(
        relationships,
        [
            "customers",
            "orders",
            "order_items"
        ]
    )


    path = graph.find_path(
        "customers",
        "order_items"
    )


    assert path is not None

    assert len(path) == 2


    assert (
        path[0].target_table
        ==
        "customers"
        or
        path[0].source_table
        ==
        "customers"
    )