from textSQL.metadata.graph import (
    SchemaGraph,
    build_schema_graph,
)

from textSQL.metadata.models import (
    RelationshipMetadata,
)


def test_schema_graph_creation():

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
            reasoning=
            "Orders belong to customers.",
            confidence=0.99
        ),


        RelationshipMetadata(
            source_table="orders",
            target_table="order_items",
            relationship_type="one-to-many",
            source_cardinality="one",
            target_cardinality="many",
            source_optional=False,
            target_optional=False,
            foreign_keys=[
                "order_id"
            ],
            reasoning=
            "Orders contain items.",
            confidence=0.99
        ),

    ]


    tables = [
        "customers",
        "orders",
        "order_items",
    ]


    graph = build_schema_graph(
        relationships,
        tables,
    )


    # Test nodes

    assert "customers" in graph.nodes
    assert "orders" in graph.nodes
    assert "order_items" in graph.nodes



    # Test edges exist

    assert len(
        graph.edges["orders"]
    ) == 2



    # Test bidirectional access

    assert len(
        graph.edges["customers"]
    ) == 1


    assert len(
        graph.edges["order_items"]
    ) == 1



    # Check relationship metadata preserved

    customer_relationship = (
        graph.edges["customers"][0]
    )


    assert (
        customer_relationship.source_table
        ==
        "orders"
    )


    assert (
        customer_relationship.target_table
        ==
        "customers"
    )


    assert (
        customer_relationship.relationship_type
        ==
        "many-to-one"
    )



def test_empty_graph():

    graph = build_schema_graph(
        relationships=[],
        tables=[]
    )


    assert len(graph.nodes) == 0

    assert len(graph.edges) == 0