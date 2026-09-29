import json
from unittest.mock import (
    MagicMock,
)

import pytest

from textSQL.validation.errors import (
    PlannerExplainError,
)

from textSQL.validation.models import (
    PlannerEstimate,
    ValidationIssueCode,
)

from textSQL.validation.planner import (
    PlannerPolicy,
    PostgresExplainAnalyzer,
)


# ============================================================
# HELPERS
# ============================================================


def build_plan():

    return [
        {
            "Plan": {
                "Node Type": "Limit",
                "Total Cost": 125.50,
                "Plan Rows": 500,
                "Plans": [
                    {
                        "Node Type": (
                            "Hash Join"
                        ),
                        "Total Cost": 5000.00,
                        "Plan Rows": 20000,
                        "Plans": [
                            {
                                "Node Type": (
                                    "Seq Scan"
                                ),
                                "Total Cost": (
                                    1000.00
                                ),
                                "Plan Rows": (
                                    100000
                                ),
                            },
                            {
                                "Node Type": (
                                    "Seq Scan"
                                ),
                                "Total Cost": (
                                    400.00
                                ),
                                "Plan Rows": (
                                    5000
                                ),
                            },
                        ],
                    }
                ],
            }
        }
    ]


def build_mock_engine(
    raw_plan,
):

    engine = MagicMock()

    connection = MagicMock()

    transaction = MagicMock()

    result = MagicMock()


    (
        engine
        .connect
        .return_value
        .__enter__
        .return_value
    ) = connection


    connection.begin.return_value = (
        transaction
    )


    (
        connection
        .exec_driver_sql
        .return_value
    ) = result


    result.scalar_one.return_value = (
        raw_plan
    )


    return (
        engine,
        connection,
        transaction,
    )


# ============================================================
# EXTRACT PLAN FACTS
# ============================================================


def test_explain_analyzer_extracts_plan_facts():

    (
        engine,
        _,
        _,
    ) = build_mock_engine(
        build_plan()
    )


    estimate = (

        PostgresExplainAnalyzer(
            engine
        )

        .analyze(
            """
            SELECT *
            FROM public.customers
            LIMIT 500
            """
        )
    )


    assert (
        estimate.total_cost
        ==
        125.50
    )

    assert (
        estimate.root_plan_rows
        ==
        500
    )

    assert (
        estimate.max_plan_rows
        ==
        100000
    )

    assert (
        estimate.node_count
        ==
        4
    )


# ============================================================
# EXPLAIN, NOT EXPLAIN ANALYZE
# ============================================================


def test_analyzer_uses_plain_explain():

    (
        engine,
        connection,
        _,
    ) = build_mock_engine(
        build_plan()
    )


    (
        PostgresExplainAnalyzer(
            engine
        )

        .analyze(
            "SELECT 1"
        )
    )


    executed_sql = (
        connection
        .exec_driver_sql
        .call_args
        .args[0]
    )


    assert executed_sql.startswith(
        "EXPLAIN (FORMAT JSON) "
    )


    assert (
        "EXPLAIN ANALYZE"
        not in executed_sql.upper()
    )


# ============================================================
# TRANSACTION ROLLBACK
# ============================================================


def test_explain_transaction_is_rolled_back():

    (
        engine,
        _,
        transaction,
    ) = build_mock_engine(
        build_plan()
    )


    (
        PostgresExplainAnalyzer(
            engine
        )

        .analyze(
            "SELECT 1"
        )
    )


    (
        transaction
        .rollback
        .assert_called_once()
    )


# ============================================================
# STRING JSON PAYLOAD
# ============================================================


def test_json_string_payload_is_supported():

    raw_plan = json.dumps(
        build_plan()
    )


    (
        engine,
        _,
        _,
    ) = build_mock_engine(
        raw_plan
    )


    estimate = (

        PostgresExplainAnalyzer(
            engine
        )

        .analyze(
            "SELECT 1"
        )
    )


    assert (
        estimate.max_plan_rows
        ==
        100000
    )


# ============================================================
# MALFORMED PLAN
# ============================================================


def test_malformed_plan_is_rejected():

    (
        engine,
        _,
        _,
    ) = build_mock_engine(
        [
            {
                "wrong": "shape"
            }
        ]
    )


    with pytest.raises(
        PlannerExplainError
    ):

        (
            PostgresExplainAnalyzer(
                engine
            )

            .analyze(
                "SELECT 1"
            )
        )


# ============================================================
# DATABASE FAILURE
# ============================================================


def test_database_explain_failure_is_translated():

    engine = MagicMock()

    connection = MagicMock()

    transaction = MagicMock()


    (
        engine
        .connect
        .return_value
        .__enter__
        .return_value
    ) = connection


    connection.begin.return_value = (
        transaction
    )


    (
        connection
        .exec_driver_sql
        .side_effect
    ) = RuntimeError(
        "database error"
    )


    with pytest.raises(
        PlannerExplainError
    ) as exc_info:

        (
            PostgresExplainAnalyzer(
                engine
            )

            .analyze(
                "SELECT 1"
            )
        )


    assert (
        exc_info.value.__cause__
        is not None
    )


    (
        transaction
        .rollback
        .assert_called_once()
    )


# ============================================================
# POLICY PASSES
# ============================================================


def test_plan_within_thresholds_passes():

    estimate = PlannerEstimate(

        total_cost=100,

        root_plan_rows=500,

        max_plan_rows=1000,

        node_count=3,
    )


    result = (

        PlannerPolicy(
            max_total_cost=100,
            max_plan_rows=1000,
        )

        .validate(
            estimate
        )
    )


    assert (
        result.valid
        is True
    )

    assert (
        result.issues
        ==
        []
    )


# ============================================================
# COST EXCEEDED
# ============================================================


def test_total_cost_above_threshold_is_rejected():

    estimate = PlannerEstimate(

        total_cost=100.01,

        root_plan_rows=100,

        max_plan_rows=100,

        node_count=1,
    )


    result = (

        PlannerPolicy(
            max_total_cost=100,
            max_plan_rows=1000,
        )

        .validate(
            estimate
        )
    )


    assert (
        result.valid
        is False
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .PLANNER_COST_EXCEEDED

        for issue
        in result.issues
    )


# ============================================================
# ROWS EXCEEDED
# ============================================================


def test_plan_rows_above_threshold_are_rejected():

    estimate = PlannerEstimate(

        total_cost=50,

        root_plan_rows=500,

        max_plan_rows=1001,

        node_count=4,
    )


    result = (

        PlannerPolicy(
            max_total_cost=100,
            max_plan_rows=1000,
        )

        .validate(
            estimate
        )
    )


    assert (
        result.valid
        is False
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .PLANNER_ROWS_EXCEEDED

        for issue
        in result.issues
    )


# ============================================================
# BOTH ISSUES RETURNED
# ============================================================


def test_all_planner_violations_are_returned():

    estimate = PlannerEstimate(

        total_cost=101,

        root_plan_rows=500,

        max_plan_rows=1001,

        node_count=4,
    )


    result = (

        PlannerPolicy(
            max_total_cost=100,
            max_plan_rows=1000,
        )

        .validate(
            estimate
        )
    )


    codes = {
        issue.code
        for issue
        in result.issues
    }


    assert (
        ValidationIssueCode
        .PLANNER_COST_EXCEEDED
        in codes
    )

    assert (
        ValidationIssueCode
        .PLANNER_ROWS_EXCEEDED
        in codes
    )


# ============================================================
# INVALID CONFIGURATION
# ============================================================


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "max_total_cost": 0,
            "max_plan_rows": 100,
        },
        {
            "max_total_cost": -1,
            "max_plan_rows": 100,
        },
        {
            "max_total_cost": 100,
            "max_plan_rows": 0,
        },
        {
            "max_total_cost": 100,
            "max_plan_rows": -1,
        },
    ],
)
def test_invalid_thresholds_are_rejected(
    kwargs,
):

    with pytest.raises(
        ValueError
    ):

        PlannerPolicy(
            **kwargs
        )