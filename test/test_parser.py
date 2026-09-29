import pytest

from sqlglot import exp

from sqlglot.errors import (
    ParseError,
)

from textSQL.validation.errors import (
    SQLParseError,
    MultipleStatementsError,
)

from textSQL.validation.models import (
    ParsedSQL,
)

from textSQL.validation.parser import (
    SQLParser,
)


# ============================================================
# SUCCESSFUL PARSING
# ============================================================


def test_parser_returns_typed_result():

    sql = """
    SELECT
        order_id,
        customer_id
    FROM public.orders;
    """

    parser = SQLParser()

    result = parser.parse(
        sql
    )


    assert isinstance(
        result,
        ParsedSQL,
    )


    assert (
        result.original_sql
        ==
        sql
    )


    assert isinstance(
        result.ast,
        exp.Select,
    )


def test_parser_uses_postgres_dialect():

    sql = """
    SELECT
        created_at::date
    FROM public.orders;
    """

    result = (
        SQLParser()
        .parse(
            sql
        )
    )


    assert isinstance(
        result.ast,
        exp.Select,
    )


def test_parser_accepts_cte_select():

    sql = """
    WITH customer_orders AS (
        SELECT
            customer_id,
            COUNT(*) AS order_count
        FROM public.orders
        GROUP BY customer_id
    )
    SELECT
        customer_id,
        order_count
    FROM customer_orders;
    """

    result = (
        SQLParser()
        .parse(
            sql
        )
    )


    assert isinstance(
        result.ast,
        exp.Select,
    )


    ctes = list(
        result.ast.find_all(
            exp.CTE
        )
    )


    assert len(
        ctes
    ) == 1


    assert (
        ctes[0].alias_or_name
        ==
        "customer_orders"
    )


def test_trailing_semicolon_is_single_statement():

    sql = (
        "SELECT * "
        "FROM public.orders;"
    )


    result = (
        SQLParser()
        .parse(
            sql
        )
    )


    assert isinstance(
        result.ast,
        exp.Select,
    )


# ============================================================
# PARSER DOES NOT ENFORCE SAFETY POLICY
# ============================================================


def test_parser_accepts_delete_as_valid_syntax():

    """
    DELETE is syntactically valid PostgreSQL.

    SQLParser must parse it successfully.

    Rejecting write operations belongs to
    SafetyPolicy, not SQLParser.
    """

    sql = """
    DELETE
    FROM public.orders;
    """


    result = (
        SQLParser()
        .parse(
            sql
        )
    )


    assert isinstance(
        result.ast,
        exp.Delete,
    )


# ============================================================
# EMPTY SQL
# ============================================================


def test_empty_sql_is_rejected():

    parser = SQLParser()


    with pytest.raises(
        SQLParseError,
        match="cannot be empty",
    ):

        parser.parse(
            "   "
        )


# ============================================================
# MALFORMED SQL
# ============================================================


def test_malformed_sql_is_rejected():

    sql = """
    SELECT foo(
    FROM public.orders;
    """


    with pytest.raises(
        SQLParseError
    ) as error:

        SQLParser().parse(
            sql
        )


    assert (
        error.value.raw_sql
        ==
        sql
    )


    assert isinstance(
        error.value.__cause__,
        ParseError,
    )


# ============================================================
# MULTIPLE STATEMENTS
# ============================================================


def test_multiple_statements_are_rejected():

    sql = """
    SELECT *
    FROM public.orders;

    DELETE
    FROM public.orders;
    """


    with pytest.raises(
        MultipleStatementsError
    ) as error:

        SQLParser().parse(
            sql
        )


    assert (
        error.value.statement_count
        ==
        2
    )


    assert (
        error.value.raw_sql
        ==
        sql
    )