import pytest

from textSQL.validation.analyzer import (
    ASTAnalyzer,
)

from textSQL.validation.complexity import (
    ComplexityPolicy,
)

from textSQL.validation.models import (
    ValidationIssueCode,
)

from textSQL.validation.parser import (
    SQLParser,
)


# ============================================================
# HELPERS
# ============================================================


def analyze(
    sql: str,
):

    parsed = (
        SQLParser()
        .parse(
            sql
        )
    )


    return (
        ASTAnalyzer()
        .analyze(
            parsed
        )
    )


# ============================================================
# SIMPLE QUERY
# ============================================================


def test_simple_query_passes():

    analysis = analyze(
        """
        SELECT customer_id
        FROM public.customers;
        """
    )


    result = (
        ComplexityPolicy()
        .validate(
            analysis
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
# JOIN COUNT AT LIMIT
# ============================================================


def test_join_count_at_limit_passes():

    analysis = analyze(
        """
        SELECT *
        FROM public.orders AS o
        JOIN public.customers AS c
            ON o.customer_id = c.customer_id
        JOIN public.order_items AS oi
            ON oi.order_id = o.order_id;
        """
    )


    result = (

        ComplexityPolicy(
            max_joins=2
        )

        .validate(
            analysis
        )
    )


    assert (
        analysis.join_count
        ==
        2
    )

    assert (
        result.valid
        is True
    )


# ============================================================
# JOIN COUNT ABOVE LIMIT
# ============================================================


def test_join_count_above_limit_is_rejected():

    analysis = analyze(
        """
        SELECT *
        FROM public.orders AS o
        JOIN public.customers AS c
            ON o.customer_id = c.customer_id
        JOIN public.order_items AS oi
            ON oi.order_id = o.order_id;
        """
    )


    result = (

        ComplexityPolicy(
            max_joins=1
        )

        .validate(
            analysis
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
        .JOIN_LIMIT_EXCEEDED

        for issue
        in result.issues
    )


# ============================================================
# JOINS ACROSS NESTED SCOPES
# ============================================================


def test_join_count_includes_nested_scopes():

    analysis = analyze(
        """
        SELECT *
        FROM public.customers AS c
        JOIN (
            SELECT
                o.customer_id
            FROM public.orders AS o
            JOIN public.order_items AS oi
                ON oi.order_id = o.order_id
        ) AS order_data
            ON order_data.customer_id = c.customer_id;
        """
    )


    assert (
        analysis.join_count
        ==
        2
    )


    result = (

        ComplexityPolicy(
            max_joins=1
        )

        .validate(
            analysis
        )
    )


    assert (
        result.valid
        is False
    )


# ============================================================
# SUBQUERY DEPTH AT LIMIT
# ============================================================


def test_subquery_depth_at_limit_passes():

    analysis = analyze(
        """
        SELECT *
        FROM public.customers
        WHERE customer_id IN (
            SELECT customer_id
            FROM public.orders
            WHERE order_id IN (
                SELECT order_id
                FROM public.order_items
            )
        );
        """
    )


    assert (
        analysis.max_subquery_depth
        ==
        2
    )


    result = (

        ComplexityPolicy(
            max_subquery_depth=2
        )

        .validate(
            analysis
        )
    )


    assert (
        result.valid
        is True
    )


# ============================================================
# SUBQUERY DEPTH ABOVE LIMIT
# ============================================================


def test_subquery_depth_above_limit_is_rejected():

    analysis = analyze(
        """
        SELECT *
        FROM public.customers
        WHERE customer_id IN (
            SELECT customer_id
            FROM public.orders
            WHERE order_id IN (
                SELECT order_id
                FROM public.order_items
            )
        );
        """
    )


    result = (

        ComplexityPolicy(
            max_subquery_depth=1
        )

        .validate(
            analysis
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
        .SUBQUERY_DEPTH_EXCEEDED

        for issue
        in result.issues
    )


# ============================================================
# SIBLING SUBQUERIES
# ============================================================


def test_sibling_subqueries_do_not_increase_depth():

    analysis = analyze(
        """
        SELECT *
        FROM public.customers
        WHERE customer_id IN (
            SELECT customer_id
            FROM public.orders
        )
        AND customer_id IN (
            SELECT customer_id
            FROM public.orders
        );
        """
    )


    assert (
        analysis.subquery_count
        ==
        2
    )

    assert (
        analysis.max_subquery_depth
        ==
        1
    )


    result = (

        ComplexityPolicy(
            max_subquery_depth=1
        )

        .validate(
            analysis
        )
    )


    assert (
        result.valid
        is True
    )


# ============================================================
# MULTIPLE COMPLEXITY VIOLATIONS
# ============================================================


def test_all_complexity_issues_are_returned():

    analysis = analyze(
        """
        SELECT *
        FROM public.customers AS c
        JOIN public.orders AS o
            ON o.customer_id = c.customer_id
        WHERE c.customer_id IN (
            SELECT customer_id
            FROM public.orders
            WHERE order_id IN (
                SELECT order_id
                FROM public.order_items
            )
        );
        """
    )


    result = (

        ComplexityPolicy(
            max_joins=0,
            max_subquery_depth=1,
        )

        .validate(
            analysis
        )
    )


    assert (
        result.valid
        is False
    )


    codes = {
        issue.code
        for issue
        in result.issues
    }


    assert (
        ValidationIssueCode
        .JOIN_LIMIT_EXCEEDED
        in codes
    )

    assert (
        ValidationIssueCode
        .SUBQUERY_DEPTH_EXCEEDED
        in codes
    )


# ============================================================
# INVALID CONFIGURATION
# ============================================================


@pytest.mark.parametrize(
    (
        "kwargs"
    ),
    [
        {
            "max_joins": -1,
        },
        {
            "max_subquery_depth": -1,
        },
    ],
)
def test_negative_limits_are_rejected(
    kwargs,
):

    with pytest.raises(
        ValueError
    ):

        ComplexityPolicy(
            **kwargs
        )