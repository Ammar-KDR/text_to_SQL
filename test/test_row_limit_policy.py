import pytest

from textSQL.validation.analyzer import (
    ASTAnalyzer,
)

from textSQL.validation.parser import (
    SQLParser,
)

from textSQL.validation.row_limit import (
    RowLimitPolicy,
)


# ============================================================
# HELPERS
# ============================================================


def apply_limit(
    sql: str,
    max_rows: int = 500,
):

    parsed = (
        SQLParser()
        .parse(
            sql
        )
    )


    analysis = (
        ASTAnalyzer()
        .analyze(
            parsed
        )
    )


    return (

        RowLimitPolicy(
            max_rows=max_rows
        )

        .apply(
            parsed_sql=parsed,
            analysis=analysis,
        )
    )


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
# NO LIMIT
# ============================================================


def test_missing_outer_limit_is_added():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers;
        """
    )


    assert (
        result.was_rewritten
        is True
    )

    assert (
        result.original_limit_value
        is None
    )

    assert (
        result.final_limit_value
        ==
        500
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.has_outer_limit
        is True
    )

    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# SMALLER EXISTING LIMIT
# ============================================================


def test_existing_smaller_limit_is_preserved():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT 100;
        """
    )


    assert (
        result.was_rewritten
        is False
    )

    assert (
        result.original_limit_value
        ==
        100
    )

    assert (
        result.final_limit_value
        ==
        100
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        100
    )


# ============================================================
# LIMIT EXACTLY AT CAP
# ============================================================


def test_existing_limit_at_cap_is_preserved():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT 500;
        """
    )


    assert (
        result.was_rewritten
        is False
    )

    assert (
        result.final_limit_value
        ==
        500
    )


# ============================================================
# LIMIT ABOVE CAP
# ============================================================


def test_existing_limit_above_cap_is_clamped():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT 1000;
        """
    )


    assert (
        result.was_rewritten
        is True
    )

    assert (
        result.original_limit_value
        ==
        1000
    )

    assert (
        result.final_limit_value
        ==
        500
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# CUSTOM MAXIMUM
# ============================================================


def test_custom_max_rows_is_respected():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers;
        """,
        max_rows=200,
    )


    assert (
        result.final_limit_value
        ==
        200
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        200
    )


# ============================================================
# OFFSET PRESERVED
# ============================================================


def test_offset_is_preserved_when_limit_is_added():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers
        ORDER BY customer_id
        OFFSET 10;
        """
    )


    assert (
        "OFFSET 10"
        in
        result.sql.upper()
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# INNER LIMIT PRESERVED
# ============================================================


def test_inner_limit_is_not_rewritten():

    result = apply_limit(
        """
        SELECT *
        FROM (
            SELECT customer_id
            FROM public.customers
            LIMIT 50
        ) AS customer_data;
        """
    )


    assert (
        result.was_rewritten
        is True
    )


    assert (
        "LIMIT 50"
        in
        result.sql.upper()
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# CTE INNER LIMIT PRESERVED
# ============================================================


def test_cte_limit_is_preserved_and_outer_limit_added():

    result = apply_limit(
        """
        WITH customer_data AS (
            SELECT customer_id
            FROM public.customers
            LIMIT 25
        )
        SELECT *
        FROM customer_data;
        """
    )


    assert (
        "LIMIT 25"
        in
        result.sql.upper()
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# UNION OUTER LIMIT
# ============================================================


def test_union_receives_outer_limit():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers

        UNION

        SELECT customer_id
        FROM public.orders;
        """
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.has_outer_limit
        is True
    )

    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# LARGE UNION LIMIT CLAMPED
# ============================================================


def test_union_large_outer_limit_is_clamped():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers

        UNION

        SELECT customer_id
        FROM public.orders

        LIMIT 1000;
        """
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# PARAMETERIZED LIMIT
# ============================================================


def test_dynamic_limit_is_replaced_with_cap():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT $1;
        """
    )


    assert (
        result.was_rewritten
        is True
    )

    assert (
        result.original_limit_value
        is None
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# LIMIT ALL
# ============================================================


def test_limit_all_is_replaced_with_cap():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT ALL;
        """
    )


    assert (
        result.was_rewritten
        is True
    )


    rewritten = analyze(
        result.sql
    )


    assert (
        rewritten.outer_limit_value
        ==
        500
    )


# ============================================================
# ZERO LIMIT
# ============================================================


def test_zero_limit_is_preserved():

    result = apply_limit(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT 0;
        """
    )


    assert (
        result.was_rewritten
        is False
    )

    assert (
        result.final_limit_value
        ==
        0
    )


# ============================================================
# INVALID CONFIGURATION
# ============================================================


@pytest.mark.parametrize(
    "max_rows",
    [
        0,
        -1,
    ],
)
def test_invalid_max_rows_is_rejected(
    max_rows,
):

    with pytest.raises(
        ValueError
    ):

        RowLimitPolicy(
            max_rows=max_rows
        )