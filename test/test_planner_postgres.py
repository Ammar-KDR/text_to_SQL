from textSQL.database.connection import (
    engine,
)

from textSQL.validation.planner import (
    PostgresExplainAnalyzer,
)


def test_real_postgres_explain():

    analyzer = (
        PostgresExplainAnalyzer(
            engine
        )
    )


    estimate = analyzer.analyze(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT 500
        """
    )


    assert (
        estimate.total_cost
        >=
        0
    )

    assert (
        estimate.root_plan_rows
        >=
        0
    )

    assert (
        estimate.max_plan_rows
        >=
        estimate.root_plan_rows
    )

    assert (
        estimate.node_count
        >=
        1
    )