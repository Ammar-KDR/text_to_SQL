from textSQL.retrieval.fusion import (
    Fusion,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)


def candidate(
    object_id,
    source,
):

    return RetrievalCandidate(

        object_id=
            object_id,

        object_type=
            "metric",

        object_name=
            object_id,

        score=
            1.0,

        source=
            source,
    )


def test_same_source_does_not_vote_twice():

    fusion = Fusion(
        k=60
    )


    revenue = candidate(
        "metric_revenue",
        "dense",
    )


    results = fusion.combine(

        [
            revenue
        ],

        [
            revenue
        ],
    )


    assert len(results) == 1


    result = results[0]


    expected = (
        1 / 61
    )


    assert (
        result.rrf_score
        ==
        expected
    )


    assert (
        result.sources
        ==
        ["dense"]
    )


def test_different_sources_can_both_vote():

    fusion = Fusion(
        k=60
    )


    dense = candidate(
        "metric_revenue",
        "dense",
    )


    dependency = candidate(
        "metric_revenue",
        "dependency",
    )


    results = fusion.combine(

        [
            dense
        ],

        [
            dependency
        ],
    )


    assert len(results) == 1


    result = results[0]


    expected = (
        (1 / 61)
        +
        (1 / 61)
    )


    assert (
        result.rrf_score
        ==
        expected
    )


    assert set(
        result.sources
    ) == {
        "dense",
        "dependency",
    }


def test_duplicate_graph_vote_is_ignored():

    fusion = Fusion(
        k=60
    )


    graph_candidate = (
        RetrievalCandidate(

            object_id=
                "relationship_a_b",

            object_type=
                "relationship",

            object_name=
                "a -> b",

            score=
                1.0,

            source=
                "graph",
        )
    )


    results = fusion.combine(

        [
            graph_candidate,
            graph_candidate,
        ]

    )


    assert len(results) == 1


    assert (
        results[0].rrf_score
        ==
        1 / 61
    )


def test_real_dependency_overlap_does_not_double_dense():

    fusion = Fusion(
        k=60
    )


    revenue_dense = candidate(
        "metric_revenue",
        "dense",
    )


    fact_sales_dependency = (
        RetrievalCandidate(

            object_id=
                "table_warehouse.fact_sales",

            object_type=
                "table",

            object_name=
                "fact_sales",

            score=
                1.0,

            source=
                "dependency",
        )
    )


    dense_candidates = [
        revenue_dense
    ]


    # This mirrors DependencyResolver:
    #
    # original dense candidate
    # +
    # newly added dependency
    dependency_candidates = [

        revenue_dense,

        fact_sales_dependency,

    ]


    results = fusion.combine(

        dense_candidates,

        dependency_candidates,
    )


    result_map = {

        result.object_id:
            result

        for result in results

    }


    assert (
        result_map[
            "metric_revenue"
        ].rrf_score
        ==
        1 / 61
    )


    assert (
        result_map[
            "table_warehouse.fact_sales"
        ].rrf_score
        ==
        1 / 62
    )