from unittest.mock import (
    MagicMock,
)

from textSQL.generation.models import (
    GenerationColumnContext,
    GenerationContext,
    GenerationJoinCondition,
    GenerationRelationshipContext,
    GenerationTableContext,
)

from textSQL.validation.errors import (
    PlannerExplainError,
)

from textSQL.validation.models import (
    PlannerEstimate,
    SQLValidationStatus,
    ValidationIssueCode,
)

from textSQL.validation.sql_validator import (
    SQLValidator,
)


# ============================================================
# FAKE PLANNER
# ============================================================


class FakeExplainAnalyzer:

    def __init__(
        self,
        estimate=None,
        error=None,
    ):

        self.estimate = (
            estimate
            or
            PlannerEstimate(
                total_cost=50,
                root_plan_rows=100,
                max_plan_rows=100,
                node_count=2,
            )
        )

        self.error = error

        self.received_sql = None


    def analyze(
        self,
        sql: str,
    ):

        self.received_sql = sql


        if self.error:

            raise self.error


        return self.estimate


# ============================================================
# CONTEXT
# ============================================================


def build_context():

    return GenerationContext(

        tables=[

            GenerationTableContext(

                qualified_name=(
                    "public.customers"
                ),

                columns=[

                    GenerationColumnContext(
                        name="customer_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),

                    GenerationColumnContext(
                        name="email",
                        data_type="VARCHAR",
                        nullable=False,
                    ),
                ],
            ),

            GenerationTableContext(

                qualified_name=(
                    "public.orders"
                ),

                columns=[

                    GenerationColumnContext(
                        name="order_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),

                    GenerationColumnContext(
                        name="customer_id",
                        data_type="BIGINT",
                        nullable=False,
                    ),
                ],
            ),
        ],

        relationships=[

            GenerationRelationshipContext(

                relationship_id=(
                    "orders_customers"
                ),

                source_table=(
                    "public.orders"
                ),

                target_table=(
                    "public.customers"
                ),

                relationship_type=(
                    "many-to-one"
                ),

                source_cardinality=(
                    "many"
                ),

                target_cardinality=(
                    "one"
                ),

                join_conditions=[

                    GenerationJoinCondition(

                        source_column=(
                            "public.orders."
                            "customer_id"
                        ),

                        target_column=(
                            "public.customers."
                            "customer_id"
                        ),
                    )
                ],
            )
        ],
    )


# ============================================================
# VALIDATOR
# ============================================================


def build_validator(
    explain_analyzer=None,
    max_total_cost=1000,
    max_plan_rows=10000,
    max_rows=500,
    max_joins=6,
    max_subquery_depth=3,
):

    if explain_analyzer is None:

        explain_analyzer = (
            FakeExplainAnalyzer()
        )


    return SQLValidator(

        engine=MagicMock(),

        max_total_cost=(
            max_total_cost
        ),

        max_plan_rows=(
            max_plan_rows
        ),

        max_rows=max_rows,

        max_joins=max_joins,

        max_subquery_depth=(
            max_subquery_depth
        ),

        explain_analyzer=(
            explain_analyzer
        ),
    )


# ============================================================
# VALID QUERY
# ============================================================


def test_valid_query_returns_safe_sql():

    planner = (
        FakeExplainAnalyzer()
    )


    validator = build_validator(
        explain_analyzer=planner
    )


    result = validator.validate(

        sql="""
        SELECT customer_id
        FROM public.customers
        """,

        context=build_context(),
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .VALID
    )


    assert (
        result.issues
        ==
        []
    )


    assert (
        result.safe_sql
        is not None
    )


    assert (
        "LIMIT 500"
        in
        result.safe_sql.upper()
    )


    assert (
        planner.received_sql
        ==
        result.safe_sql
    )


# ============================================================
# EXISTING SAFE LIMIT
# ============================================================


def test_existing_smaller_limit_remains_safe():

    result = (

        build_validator()

        .validate(

            sql="""
            SELECT customer_id
            FROM public.customers
            LIMIT 10
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .VALID
    )


    assert (
        "LIMIT 10"
        in
        result.safe_sql.upper()
    )


# ============================================================
# PARSE ERROR
# ============================================================


def test_parse_error_is_invalid():

    planner = (
        FakeExplainAnalyzer()
    )


    result = (

        build_validator(
            explain_analyzer=planner
        )

        .validate(
            sql=(
                "SELECT FROM WHERE"
            ),
            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .INVALID
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .PARSE_ERROR

        for issue
        in result.issues
    )


    assert (
        result.safe_sql
        is None
    )


    assert (
        planner.received_sql
        is None
    )


# ============================================================
# MULTIPLE STATEMENTS
# ============================================================


def test_multiple_statements_are_blocked():

    result = (

        build_validator()

        .validate(

            sql="""
            SELECT 1;
            SELECT 2;
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .BLOCKED
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .MULTIPLE_STATEMENTS

        for issue
        in result.issues
    )


    assert (
        result.safe_sql
        is None
    )


# ============================================================
# UNSAFE STATEMENT
# ============================================================


def test_delete_is_blocked():

    planner = (
        FakeExplainAnalyzer()
    )


    result = (

        build_validator(
            explain_analyzer=planner
        )

        .validate(

            sql="""
            DELETE
            FROM public.customers
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .BLOCKED
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .DISALLOWED_STATEMENT

        for issue
        in result.issues
    )


    assert (
        planner.received_sql
        is None
    )


# ============================================================
# UNKNOWN TABLE
# ============================================================


def test_unknown_table_is_invalid():

    planner = (
        FakeExplainAnalyzer()
    )


    result = (

        build_validator(
            explain_analyzer=planner
        )

        .validate(

            sql="""
            SELECT customer_id
            FROM public.fake_customers
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .INVALID
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .UNKNOWN_TABLE

        for issue
        in result.issues
    )


    assert (
        planner.received_sql
        is None
    )


# ============================================================
# UNKNOWN COLUMN
# ============================================================


def test_unknown_column_is_invalid():

    result = (

        build_validator()

        .validate(

            sql="""
            SELECT fake_column
            FROM public.customers
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .INVALID
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .UNKNOWN_COLUMN

        for issue
        in result.issues
    )


# ============================================================
# INVALID JOIN
# ============================================================


def test_invalid_join_is_invalid():

    result = (

        build_validator()

        .validate(

            sql="""
            SELECT
                o.order_id,
                c.customer_id
            FROM public.orders AS o
            JOIN public.customers AS c
                ON (
                    o.order_id
                    =
                    c.customer_id
                )
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .INVALID
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .INVALID_JOIN

        for issue
        in result.issues
    )


# ============================================================
# VALID JOIN
# ============================================================


def test_valid_grounded_join_passes():

    result = (

        build_validator()

        .validate(

            sql="""
            SELECT
                o.order_id,
                c.customer_id
            FROM public.orders AS o
            JOIN public.customers AS c
                ON (
                    o.customer_id
                    =
                    c.customer_id
                )
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .VALID
    )


# ============================================================
# COMPLEXITY
# ============================================================


def test_excessive_join_count_is_blocked():

    result = (

        build_validator(
            max_joins=0
        )

        .validate(

            sql="""
            SELECT
                o.order_id
            FROM public.orders AS o
            JOIN public.customers AS c
                ON (
                    o.customer_id
                    =
                    c.customer_id
                )
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .BLOCKED
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .JOIN_LIMIT_EXCEEDED

        for issue
        in result.issues
    )


# ============================================================
# PLANNER COST
# ============================================================


def test_excessive_planner_cost_is_blocked():

    planner = FakeExplainAnalyzer(

        estimate=PlannerEstimate(

            total_cost=1001,

            root_plan_rows=100,

            max_plan_rows=100,

            node_count=2,
        )
    )


    result = (

        build_validator(
            explain_analyzer=planner,
            max_total_cost=1000,
        )

        .validate(

            sql="""
            SELECT customer_id
            FROM public.customers
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .BLOCKED
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .PLANNER_COST_EXCEEDED

        for issue
        in result.issues
    )


    assert (
        result.safe_sql
        is None
    )


    assert (
        result.planner_estimate
        is not None
    )


# ============================================================
# PLANNER ROWS
# ============================================================


def test_excessive_planner_rows_are_blocked():

    planner = FakeExplainAnalyzer(

        estimate=PlannerEstimate(

            total_cost=50,

            root_plan_rows=500,

            max_plan_rows=10001,

            node_count=2,
        )
    )


    result = (

        build_validator(
            explain_analyzer=planner,
            max_plan_rows=10000,
        )

        .validate(

            sql="""
            SELECT customer_id
            FROM public.customers
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .BLOCKED
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
# EXPLAIN FAILURE
# ============================================================


def test_explain_failure_is_blocked():

    planner = FakeExplainAnalyzer(

        error=PlannerExplainError(

            message=(
                "EXPLAIN failed"
            ),

            sql="SELECT 1",
        )
    )


    result = (

        build_validator(
            explain_analyzer=planner
        )

        .validate(

            sql="""
            SELECT customer_id
            FROM public.customers
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .BLOCKED
    )


    assert any(

        issue.code
        ==
        ValidationIssueCode
        .PLANNER_EXPLAIN_FAILED

        for issue
        in result.issues
    )


    assert (
        result.safe_sql
        is None
    )


# ============================================================
# FINAL VALID RESULT INCLUDES ANALYSIS + PLAN
# ============================================================


def test_valid_result_contains_analysis_and_planner_estimate():

    result = (

        build_validator()

        .validate(

            sql="""
            SELECT customer_id
            FROM public.customers
            """,

            context=build_context(),
        )
    )


    assert (
        result.status
        ==
        SQLValidationStatus
        .VALID
    )


    assert (
        result.analysis
        is not None
    )


    assert (
        result.planner_estimate
        is not None
    )


    assert (
        result.safe_sql
        is not None
    )