from textSQL.retrieval.graph_retriever import (
    GraphRetriever,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)

from textSQL.metadata.graph import (
    SchemaGraph,
)

from textSQL.metadata.models import (
    RelationshipMetadata,
)



class FakeMetadataIndex:
    """
    GraphRetriever does not need metadata lookup
    currently, but we provide it because it is
    part of the constructor.
    """

    pass



def create_test_graph():

    graph = SchemaGraph()


    graph.add_table(
        "fact_sales"
    )

    graph.add_table(
        "dim_customer"
    )


    relationship = RelationshipMetadata(

    source_table=
    "fact_sales",

    target_table=
    "dim_customer",

    relationship_type=
    "many-to-one",

    source_cardinality=
    "many",

    target_cardinality=
    "one",

    through_table=None,

    foreign_keys=[
        "customer_key"
    ],

    business_meaning=
    "Connects sales with customers.",

    description=
    "Sales belong to customers."

)


    graph.add_relationship(
        relationship
    )


    return graph



def create_table_candidate(
    table_name,
):

    return RetrievalCandidate(

        object_id=
        f"table_{table_name}",

        object_type=
        "table",

        object_name=
        table_name,

        score=1.0,

        source=
        "dependency",

    )



def test_graph_retriever_finds_relationship():


    graph = create_test_graph()


    retriever = GraphRetriever(

        metadata_index=
        FakeMetadataIndex(),

        graph=
        graph,

    )


    candidates = [

        create_table_candidate(
            "fact_sales"
        ),

        create_table_candidate(
            "dim_customer"
        ),

    ]


    results = retriever.retrieve(
        candidates
    )


    assert len(results) == 1


    relationship = results[0]


    assert (
        relationship.object_type
        ==
        "relationship"
    )


    assert (
        relationship.source
        ==
        "graph"
    )


    assert (
        "fact_sales"
        in relationship.object_id
    )


    assert (
        "dim_customer"
        in relationship.object_id
    )



def test_graph_retriever_returns_empty_for_disconnected_tables():


    graph = SchemaGraph()


    graph.add_table(
        "fact_sales"
    )

    graph.add_table(
        "dim_campaign"
    )


    retriever = GraphRetriever(

        metadata_index=
        FakeMetadataIndex(),

        graph=
        graph,

    )


    candidates = [

        create_table_candidate(
            "fact_sales"
        ),

        create_table_candidate(
            "dim_campaign"
        ),

    ]


    results = retriever.retrieve(
        candidates
    )


    assert results == []



def test_graph_retriever_does_not_duplicate_relationships():


    graph = create_test_graph()


    retriever = GraphRetriever(

        metadata_index=
        FakeMetadataIndex(),

        graph=
        graph,

    )


    candidates = [

        create_table_candidate(
            "fact_sales"
        ),

        create_table_candidate(
            "dim_customer"
        ),

    ]


    results = retriever.retrieve(
        candidates
    )


    ids = [

        result.object_id

        for result in results

    ]


    assert len(ids) == len(set(ids))