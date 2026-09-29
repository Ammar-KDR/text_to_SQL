import pytest

from textSQL.database.connection import (
    engine,
)

from textSQL.validation.errors import (
    SQLExecutionError,
)

from textSQL.validation.executor import (
    ReadOnlySQLExecutor,
)


# ============================================================
# HELPERS
# ============================================================


def get_sqlstate(
    exc: BaseException,
) -> str | None:

    """
    Walk through SQLAlchemy / DBAPI exception layers
    and return a PostgreSQL SQLSTATE if available.
    """

    current = exc


    while current is not None:

        sqlstate = getattr(
            current,
            "sqlstate",
            None,
        )


        if sqlstate:

            return sqlstate


        pgcode = getattr(
            current,
            "pgcode",
            None,
        )


        if pgcode:

            return pgcode


        original = getattr(
            current,
            "orig",
            None,
        )


        if (
            original is not None
            and
            original is not current
        ):

            current = original

            continue


        current = getattr(
            current,
            "__cause__",
            None,
        )


    return None


# ============================================================
# REAL SELECT STILL WORKS
# ============================================================


def test_real_postgres_read_only_select_succeeds():

    executor = (
        ReadOnlySQLExecutor(
            engine
        )
    )


    result = executor.execute(
        """
        SELECT customer_id
        FROM public.customers
        LIMIT 1
        """
    )


    assert (
        result.row_count
        <=
        1
    )


    assert (
        "customer_id"
        in
        result.columns
    )


# ============================================================
# APPLICATION VALIDATION BYPASS
# ============================================================


def test_real_postgres_rejects_update_when_validation_is_bypassed():

    """
    Deliberately bypass:

        SQLParser
        ASTAnalyzer
        GroundingValidator
        SafetyPolicy
        ComplexityPolicy
        RowLimitPolicy
        PlannerPolicy

    and send a write statement directly to
    ReadOnlySQLExecutor.

    WHERE FALSE guarantees that even if the database
    protection were accidentally absent, no row could
    actually be modified.
    """

    executor = (
        ReadOnlySQLExecutor(
            engine
        )
    )


    malicious_sql = """
        UPDATE public.customers
        SET customer_id = customer_id
        WHERE FALSE
    """


    with pytest.raises(
        SQLExecutionError
    ) as exc_info:

        executor.execute(
            malicious_sql
        )


    underlying_error = (
        exc_info.value.__cause__
    )


    assert (
        underlying_error
        is not None
    )


    assert (
        get_sqlstate(
            underlying_error
        )
        ==
        "25006"
    )