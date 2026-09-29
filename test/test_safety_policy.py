import pytest

from textSQL.validation.models import (
    ValidationIssueCode,
)

from textSQL.validation.parser import (
    SQLParser,
)

from textSQL.validation.safety import (
    SafetyPolicy,
)


# ============================================================
# HELPERS
# ============================================================


def validate(
    sql: str,
):

    parsed = (
        SQLParser()
        .parse(
            sql
        )
    )


    return (
        SafetyPolicy()
        .validate(
            parsed
        )
    )


# ============================================================
# SAFE READ-ONLY QUERIES
# ============================================================


def test_simple_select_passes():

    result = validate(
        """
        SELECT
            order_id
        FROM public.orders;
        """
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


def test_cte_select_passes():

    result = validate(
        """
        WITH recent_orders AS (
            SELECT
                order_id
            FROM public.orders
        )
        SELECT
            order_id
        FROM recent_orders;
        """
    )


    assert (
        result.valid
        is True
    )


def test_union_query_passes():

    result = validate(
        """
        SELECT
            customer_id
        FROM public.orders

        UNION

        SELECT
            customer_id
        FROM public.customers;
        """
    )


    assert (
        result.valid
        is True
    )


# ============================================================
# TOP-LEVEL WRITE / DDL / CONTROL STATEMENTS
# ============================================================


@pytest.mark.parametrize(
    "sql",
    [

        """
        DELETE
        FROM public.orders;
        """,

        """
        UPDATE public.orders
        SET customer_id = 1;
        """,

        """
        INSERT INTO public.orders (
            order_id,
            customer_id
        )
        VALUES (
            1,
            1
        );
        """,

        """
        CREATE TABLE public.tmp_orders (
            order_id BIGINT
        );
        """,

        """
        ALTER TABLE public.orders
        ADD COLUMN unsafe_column INTEGER;
        """,

        """
        DROP TABLE public.orders;
        """,

        """
        TRUNCATE TABLE public.orders;
        """,

        """
        COPY public.orders
        TO '/tmp/orders.csv';
        """,

        """
        SET statement_timeout = 0;
        """,

        """
        GRANT SELECT
        ON public.orders
        TO some_user;
        """,

        """
        REVOKE SELECT
        ON public.orders
        FROM some_user;
        """,

        """
        COMMIT;
        """,

        """
        ROLLBACK;
        """,

        """
        CALL some_procedure();
        """,
    ],
)
def test_non_query_statements_are_blocked(
    sql,
):

    result = validate(
        sql
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .DISALLOWED_STATEMENT

        for issue
        in result.issues
    )


# ============================================================
# WRITE HIDDEN INSIDE CTE
# ============================================================


def test_data_modifying_cte_is_blocked():

    result = validate(
        """
        WITH deleted_orders AS (
            DELETE
            FROM public.orders
            WHERE order_id = 1
            RETURNING order_id
        )
        SELECT
            order_id
        FROM deleted_orders;
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .DISALLOWED_STATEMENT

        and

        issue.object_name
        ==
        "delete"

        for issue
        in result.issues
    )


# ============================================================
# SELECT INTO
# ============================================================


def test_select_into_is_blocked():

    result = validate(
        """
        SELECT
            order_id
        INTO copied_orders
        FROM public.orders;
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .SELECT_INTO

        for issue
        in result.issues
    )


# ============================================================
# ROW LOCKING
# ============================================================


@pytest.mark.parametrize(
    "lock_clause",
    [
        "FOR UPDATE",
        "FOR SHARE",
    ],
)
def test_row_locking_select_is_blocked(
    lock_clause,
):

    result = validate(
        f"""
        SELECT *
        FROM public.orders
        {lock_clause};
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .ROW_LOCK

        for issue
        in result.issues
    )


# ============================================================
# SEQUENCE MUTATION
# ============================================================


@pytest.mark.parametrize(
    (
        "sql",
        "function_name",
    ),
    [

        (
            """
            SELECT nextval(
                'order_sequence'
            );
            """,
            "nextval",
        ),

        (
            """
            SELECT setval(
                'order_sequence',
                100
            );
            """,
            "setval",
        ),
    ],
)
def test_sequence_mutation_is_blocked(
    sql,
    function_name,
):

    result = validate(
        sql
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .SEQUENCE_MUTATION

        and

        issue.object_name
        ==
        function_name

        for issue
        in result.issues
    )


# ============================================================
# ORDINARY FUNCTIONS REMAIN ALLOWED
# ============================================================


def test_safe_aggregate_functions_are_allowed():

    result = validate(
        """
        SELECT
            COUNT(*) AS order_count,
            SUM(total_amount) AS revenue
        FROM public.orders;
        """
    )


    assert (
        result.valid
        is True
    )

def test_merge_is_blocked():

    result = validate(
        """
        MERGE INTO public.orders AS target
        USING public.orders AS source
            ON (
                target.order_id
                =
                source.order_id
            )
        WHEN MATCHED THEN
            UPDATE SET
                customer_id
                =
                source.customer_id;
        """
    )


    assert (
        result.valid
        is False
    )


    assert any(
        issue.code
        ==
        ValidationIssueCode
        .DISALLOWED_STATEMENT

        for issue
        in result.issues
    )