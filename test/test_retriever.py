from textSQL.retrieval.retriever import (
    Retriever,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
    FusedCandidate,
    RetrievedContext,
)


# ============================================================
# HELPERS
# ============================================================


def candidate(
    object_id,
    object_type,
    object_name,
    source,
    score=1.0,
):

    return RetrievalCandidate(

        object_id=
            object_id,

        object_type=
            object_type,

        object_name=
            object_name,

        score=
            score,

        source=
            source,
    )


# ============================================================
# FAKES
# ============================================================


class FakeDenseRetriever:


    def __init__(self):

        self.question = None

        self.limit = None


    def retrieve(
        self,
        question,
        limit,
    ):

        self.question = question

        self.limit = limit


        return [

            candidate(

                "metric_revenue",

                "metric",

                "revenue",

                "dense",

                0.90,
            ),

            candidate(

                "metric_profit",

                "metric",

                "profit",

                "dense",

                0.85,
            ),

        ]


class FakeSeedSelector:


    def __init__(self):

        self.question = None

        self.received = None


    def select(
        self,
        question,
        candidates,
    ):

        self.question = question

        self.received = candidates


        # Simulate explicit-intent pruning:
        #
        # "show revenue"
        #
        # keeps revenue and removes profit.

        return [
            candidates[0]
        ]


class FakeDependencyResolver:


    def __init__(self):

        self.received = None


    def resolve(
        self,
        candidates,
    ):

        self.received = candidates


        return (

            list(candidates)

            +

            [

                candidate(

                    "table_warehouse.fact_sales",

                    "table",

                    "fact_sales",

                    "dependency",
                )

            ]

        )


class FakeGraphRetriever:


    def __init__(self):

        self.received = None


    def retrieve(
        self,
        candidates,
    ):

        self.received = candidates


        # Revenue + fact_sales require no join.

        return []


class FakeFusion:


    def __init__(self):

        self.received = None


    def combine(
        self,
        *candidate_lists,
    ):

        self.received = (
            candidate_lists
        )


        merged = {}


        for candidate_list in (
            candidate_lists
        ):

            for item in candidate_list:

                if (
                    item.object_id
                    in merged
                ):
                    continue


                merged[
                    item.object_id
                ] = FusedCandidate(

                    object_id=
                        item.object_id,

                    object_type=
                        item.object_type,

                    object_name=
                        item.object_name,

                    rrf_score=
                        0.05,

                    sources=[
                        item.source
                    ],
                )


        return list(
            merged.values()
        )


class FakeContextBuilder:


    def __init__(self):

        self.question = None

        self.received = None


    def build(
        self,
        question,
        candidates,
    ):

        self.question = question

        self.received = candidates


        return RetrievedContext(

            question=
                question,

            tables=[],

            relationships=[],

            metrics=[],

            join_paths=[],

            trace=[],
        )


# ============================================================
# CURRENT PIPELINE
# ============================================================


def create_retriever(
    *,
    with_seed_selector=True,
):

    dense = FakeDenseRetriever()

    seed = (
        FakeSeedSelector()
        if with_seed_selector
        else None
    )

    dependency = (
        FakeDependencyResolver()
    )

    graph = (
        FakeGraphRetriever()
    )

    fusion = FakeFusion()

    context = FakeContextBuilder()


    retriever = Retriever(

        dense_retriever=
            dense,

        dependency_resolver=
            dependency,

        graph_retriever=
            graph,

        fusion=
            fusion,

        context_builder=
            context,

        seed_selector=
            seed,
    )


    return (

        retriever,

        dense,

        seed,

        dependency,

        graph,

        fusion,

        context,
    )


# ============================================================
# TESTS
# ============================================================


def test_retriever_returns_retrieved_context():

    (
        retriever,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_retriever()


    result = retriever.retrieve(
        "show revenue"
    )


    assert isinstance(
        result,
        RetrievedContext,
    )


    assert (
        result.question
        ==
        "show revenue"
    )


def test_dense_retrieval_receives_question_and_limit():

    (
        retriever,
        dense,
        _,
        _,
        _,
        _,
        _,
    ) = create_retriever()


    retriever.retrieve(

        "show revenue",

        limit=7,
    )


    assert (
        dense.question
        ==
        "show revenue"
    )


    assert (
        dense.limit
        ==
        7
    )


def test_seed_selector_receives_dense_candidates():

    (
        retriever,
        _,
        seed,
        dependency,
        _,
        _,
        _,
    ) = create_retriever()


    retriever.retrieve(
        "show revenue"
    )


    assert (
        seed.question
        ==
        "show revenue"
    )


    assert (
        len(seed.received)
        ==
        2
    )


    assert (
        seed.received[0]
        .object_id
        ==
        "metric_revenue"
    )


    # Dependency resolution must receive
    # the PRUNED seed set, not all dense
    # candidates.

    assert (
        len(dependency.received)
        ==
        1
    )


    assert (
        dependency.received[0]
        .object_id
        ==
        "metric_revenue"
    )


def test_dependency_output_is_sent_to_graph_retriever():

    (
        retriever,
        _,
        _,
        _,
        graph,
        _,
        _,
    ) = create_retriever()


    retriever.retrieve(
        "show revenue"
    )


    ids = {

        item.object_id

        for item
        in graph.received

    }


    assert (
        "metric_revenue"
        in ids
    )


    assert (
        "table_warehouse.fact_sales"
        in ids
    )


def test_fusion_receives_three_candidate_sources():

    (
        retriever,
        _,
        _,
        _,
        _,
        fusion,
        _,
    ) = create_retriever()


    retriever.retrieve(
        "show revenue"
    )


    assert (
        len(fusion.received)
        ==
        3
    )


    seed_candidates = (
        fusion.received[0]
    )

    dependency_candidates = (
        fusion.received[1]
    )

    graph_candidates = (
        fusion.received[2]
    )


    assert (
        len(seed_candidates)
        ==
        1
    )


    assert (
        len(dependency_candidates)
        ==
        2
    )


    assert (
        graph_candidates
        ==
        []
    )


def test_context_builder_receives_fused_candidates():

    (
        retriever,
        _,
        _,
        _,
        _,
        _,
        context,
    ) = create_retriever()


    retriever.retrieve(
        "show revenue"
    )


    assert (
        context.question
        ==
        "show revenue"
    )


    ids = {

        item.object_id

        for item
        in context.received

    }


    assert (
        "metric_revenue"
        in ids
    )


    assert (
        "table_warehouse.fact_sales"
        in ids
    )


def test_retriever_can_run_without_seed_selector():

    (
        retriever,
        _,
        _,
        dependency,
        _,
        _,
        _,
    ) = create_retriever(
        with_seed_selector=False
    )


    retriever.retrieve(
        "some question"
    )


    # Without SeedSelector the retriever
    # falls back to the complete dense set.

    ids = {

        item.object_id

        for item
        in dependency.received

    }


    assert ids == {

        "metric_revenue",

        "metric_profit",

    }