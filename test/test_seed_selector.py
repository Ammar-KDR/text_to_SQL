from textSQL.metadata.models import (
    DatabaseMetadata,
    MetricMetadata,
)

from textSQL.metadata.graph import (
    SchemaGraph,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)

from textSQL.retrieval.seed_selector import (
    SeedSelector,
)


def metric(
    name,
    synonyms=None,
):

    return MetricMetadata(

        name=name,

        description=name,

        domain="test",

        formula=name,

        required_tables=[],

        required_columns=[],

        required_metrics=[],

        business_rules=[],

        forbidden_sources=[],

        synonyms=(
            synonyms
            or []
        ),
    )


def create_index():

    metrics = [

        metric(
            "revenue",
            ["sales"],
        ),

        metric(
            "product_revenue",
            ["product sales"],
        ),

        metric(
            "profit",
        ),

        metric(
            "campaign_revenue",
        ),

        metric(
            "customer_lifetime_value",
            [
                "customer value",
                "lifetime revenue",
            ],
        ),

        metric(
            "payment_success_rate",
        ),

        metric(
            "top_products",
        ),

    ]


    metadata = DatabaseMetadata(

        database_name=
            "test",

        schemas=[],

        relationships=[],

        metrics=
            metrics,

        graph=None,
    )


    return MetadataIndex(

        metadata,

        SchemaGraph(),
    )


def candidate(
    name,
    score,
):

    return RetrievalCandidate(

        object_id=
            f"metric_{name}",

        object_type=
            "metric",

        object_name=
            name,

        score=
            score,

        source=
            "dense",
    )


def test_simple_revenue_is_pruned():

    selector = SeedSelector(
        create_index()
    )


    results = selector.select(

        "show revenue",

        [

            candidate(
                "revenue",
                0.7199,
            ),

            candidate(
                "product_revenue",
                0.6977,
            ),

            candidate(
                "profit",
                0.6866,
            ),

            candidate(
                "campaign_revenue",
                0.6762,
            ),

            candidate(
                "customer_lifetime_value",
                0.6753,
            ),

        ],
    )


    ids = {

        result.object_id

        for result in results

    }


    assert ids == {
        "metric_revenue"
    }


def test_explicit_revenue_beats_semantic_clv():

    selector = SeedSelector(
        create_index()
    )


    results = selector.select(

        "show revenue by customer",

        [

            candidate(
                "customer_lifetime_value",
                0.7283,
            ),

            candidate(
                "revenue",
                0.7116,
            ),

            candidate(
                "product_revenue",
                0.6917,
            ),

            candidate(
                "profit",
                0.6786,
            ),

        ],
    )


    ids = {

        result.object_id

        for result in results

    }


    assert (
        "metric_revenue"
        in ids
    )

    assert (
        "metric_customer_lifetime_value"
        not in ids
    )

    assert (
        "metric_product_revenue"
        not in ids
    )

    assert (
        "metric_profit"
        not in ids
    )


def test_top_products_keeps_explicit_revenue():

    selector = SeedSelector(
        create_index()
    )


    results = selector.select(

        "what were the top 10 products by revenue?",

        [

            candidate(
                "top_products",
                0.7239,
            ),

            candidate(
                "revenue",
                0.6876,
            ),

            candidate(
                "product_revenue",
                0.6850,
            ),

        ],
    )


    ids = {

        result.object_id

        for result in results

    }


    assert (
        "metric_top_products"
        in ids
    )

    assert (
        "metric_revenue"
        in ids
    )

    assert (
        "metric_product_revenue"
        not in ids
    )


def test_near_tie_is_preserved():

    selector = SeedSelector(
        create_index()
    )


    results = selector.select(

        "some query",

        [

            candidate(
                "revenue",
                0.7000,
            ),

            candidate(
                "profit",
                0.6900,
            ),

            candidate(
                "campaign_revenue",
                0.6500,
            ),

        ],
    )


    ids = {

        result.object_id

        for result in results

    }


    assert ids == {

        "metric_revenue",

        "metric_profit",

    }