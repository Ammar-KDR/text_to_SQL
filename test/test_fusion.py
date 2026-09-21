from textSQL.retrieval.fusion import (
    Fusion,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)



def create_candidate(
    object_id: str,
    object_type: str = "table",
    source: str = "dense",
    score: float = 0.9,
):

    return RetrievalCandidate(

        object_id=object_id,

        object_type=object_type,

        object_name=object_id,

        score=score,

        source=source,

    )



def get_ids(
    candidates,
):

    return [
        candidate.object_id
        for candidate in candidates
    ]



def test_rrf_combines_rankings():

    fusion = Fusion(
        k=60
    )


    dense_results = [

        create_candidate(
            "metric_revenue",
            "metric",
            "dense",
            0.95,
        ),

        create_candidate(
            "table_fact_sales",
            "table",
            "dense",
            0.90,
        ),

        create_candidate(
            "table_customer",
            "table",
            "dense",
            0.85,
        ),

    ]


    graph_results = [

        create_candidate(
            "table_fact_sales",
            "table",
            "graph",
            1.0,
        ),

        create_candidate(
            "table_customer",
            "table",
            "graph",
            1.0,
        ),

    ]


    results = fusion.combine(

        dense_results,

        graph_results,

    )


    ids = get_ids(results)


    assert (
        "metric_revenue"
        in ids
    )


    assert (
        "table_fact_sales"
        in ids
    )


    assert (
        "table_customer"
        in ids
    )



def test_duplicate_candidates_are_merged():

    fusion = Fusion()


    results = fusion.combine(

        [

            create_candidate(
                "fact_sales",
                "table",
                "dense",
                0.8,
            )

        ],

        [

            create_candidate(
                "fact_sales",
                "table",
                "dependency",
                1.0,
            )

        ],

    )


    assert len(results) == 1


    fused = results[0]


    assert (
        fused.object_id
        ==
        "fact_sales"
    )


    assert len(
        fused.original_candidates
    ) == 2



def test_sources_are_preserved():

    fusion = Fusion()


    results = fusion.combine(

        [

            create_candidate(
                "fact_sales",
                "table",
                "dense",
                0.9,
            )

        ],

        [

            create_candidate(
                "fact_sales",
                "table",
                "dependency",
                1.0,
            )

        ],

        [

            create_candidate(
                "fact_sales",
                "table",
                "graph",
                1.0,
            )

        ],

    )


    fused = results[0]


    assert set(
        fused.sources
    ) == {

        "dense",

        "dependency",

        "graph",

    }



def test_dense_only_candidate_survives():

    fusion = Fusion()


    results = fusion.combine(

        [

            create_candidate(
                "metric_revenue",
                "metric",
                "dense",
                0.95,
            )

        ],

    )


    assert len(results) == 1


    assert (
        results[0].object_id
        ==
        "metric_revenue"
    )



def test_multiple_signals_increase_rrf_score():

    fusion = Fusion()


    single_source = fusion.combine(

        [

            create_candidate(
                "fact_sales",
                "table",
                "dense",
                0.9,
            )

        ]

    )


    multi_source = fusion.combine(

        [

            create_candidate(
                "fact_sales",
                "table",
                "dense",
                0.9,
            )

        ],

        [

            create_candidate(
                "fact_sales",
                "table",
                "graph",
                1.0,
            )

        ],

    )


    assert (
        multi_source[0].rrf_score
        >
        single_source[0].rrf_score
    )



def test_rrf_ranks_agreement_higher():

    fusion = Fusion()


    results = fusion.combine(

        [

            create_candidate(
                "object_a",
                source="dense",
            ),

            create_candidate(
                "object_b",
                source="dense",
            ),

        ],

        [

            create_candidate(
                "object_b",
                source="graph",
            ),

        ],

    )


    assert (
        results[0].object_id
        ==
        "object_b"
    )