from textSQL.retrieval.retriever import (
    Retriever,
)


class FakeDenseRetriever:


    def retrieve(
        self,
        question,
        limit,
    ):

        return [

            # metric
            create_candidate(
                "metric_revenue",
                "metric",
                "revenue",
                "dense",
            ),

            # customer dimension
            create_candidate(
                "table_dim_customer",
                "table",
                "dim_customer",
                "dense",
            )

        ]



class FakeDependencyResolver:


    def resolve(
        self,
        candidates,
    ):

        return candidates + [

            create_candidate(
                "table_fact_sales",
                "table",
                "fact_sales",
                "dependency",
            )

        ]



class FakeGraphRetriever:


    def retrieve(
        self,
        candidates,
    ):

        return [

            create_candidate(
                "relationship_fact_sales_dim_customer",
                "relationship",
                "fact_sales_dim_customer",
                "graph",
            )

        ]



class FakeFusion:



    def combine(
        self,
        *args,
    ):

        merged = {}

        for group in args:

            for candidate in group:

                merged[
                    candidate.object_id
                ] = candidate


        return list(
            merged.values()
        )


class FakeContextBuilder:


    def build(
        self,
        question,
        candidates,
    ):

        return {

            "question": question,

            "count": len(candidates),

        }



def create_candidate(
    object_id,
    object_type,
    object_name,
    source,
):

    from textSQL.retrieval.model import (
        RetrievalCandidate,
    )


    return RetrievalCandidate(

        object_id=object_id,

        object_type=object_type,

        object_name=object_name,

        score=1.0,

        source=source,

    )



def test_full_retrieval_pipeline():


    retriever = Retriever(

        FakeDenseRetriever(),

        FakeDependencyResolver(),

        FakeGraphRetriever(),

        FakeFusion(),

        FakeContextBuilder(),

    )


    result = retriever.retrieve(
        "show revenue by customer"
    )


    assert (
        result["question"]
        ==
        "show revenue by customer"
    )


    assert (
        result["count"]
        ==
        4
    )