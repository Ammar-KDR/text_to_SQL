from unittest.mock import (
    MagicMock,
    call,
)

import pytest

from textSQL.validation.errors import (
    SQLExecutionError,
)

from textSQL.validation.executor import (
    ReadOnlySQLExecutor,
)


# ============================================================
# HELPERS
# ============================================================


def build_mock_engine(
    rows=None,
    columns=None,
):

    if rows is None:

        rows = [
            {
                "customer_id": 1,
                "email": "a@example.com",
            },
            {
                "customer_id": 2,
                "email": "b@example.com",
            },
        ]


    if columns is None:

        columns = [
            "customer_id",
            "email",
        ]


    engine = MagicMock()

    connection = MagicMock()

    transaction = MagicMock()

    query_result = MagicMock()


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


    transaction.is_active = True


    # First three calls are:
    #
    # 1. SET TRANSACTION READ ONLY
    # 2. SET LOCAL statement_timeout
    # 3. SET LOCAL lock_timeout
    #
    # Fourth call is the actual SQL query.

    connection.exec_driver_sql.side_effect = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
        query_result,
    ]


    query_result.keys.return_value = (
        columns
    )


    (
        query_result
        .mappings
        .return_value
        .all
        .return_value
    ) = rows


    return (
        engine,
        connection,
        transaction,
        query_result,
    )


# ============================================================
# SUCCESSFUL EXECUTION
# ============================================================


def test_read_only_executor_returns_rows():

    (
        engine,
        _,
        _,
        _,
    ) = build_mock_engine()


    result = (

        ReadOnlySQLExecutor(
            engine
        )

        .execute(
            """
            SELECT
                customer_id,
                email
            FROM public.customers
            LIMIT 500
            """
        )
    )


    assert (
        result.columns
        ==
        [
            "customer_id",
            "email",
        ]
    )


    assert (
        result.row_count
        ==
        2
    )


    assert (
        result.rows[0][
            "customer_id"
        ]
        ==
        1
    )


# ============================================================
# READ ONLY SET BEFORE QUERY
# ============================================================


def test_transaction_is_set_read_only_before_query():

    (
        engine,
        connection,
        _,
        _,
    ) = build_mock_engine()


    sql = (
        "SELECT customer_id "
        "FROM public.customers "
        "LIMIT 500"
    )


    (
        ReadOnlySQLExecutor(
            engine
        )

        .execute(
            sql
        )
    )


    executed = [
        call.args[0]
        for call
        in (
            connection
            .exec_driver_sql
            .call_args_list
        )
    ]


    assert (
        executed[0]
        ==
        "SET TRANSACTION READ ONLY"
    )


    assert (
        executed[-1]
        ==
        sql
    )


# ============================================================
# STATEMENT TIMEOUT
# ============================================================


def test_statement_timeout_is_set():

    (
        engine,
        connection,
        _,
        _,
    ) = build_mock_engine()


    (
        ReadOnlySQLExecutor(
            engine=engine,
            statement_timeout_ms=2500,
            lock_timeout_ms=500,
        )

        .execute(
            "SELECT 1"
        )
    )


    executed = [
        item.args[0]
        for item
        in (
            connection
            .exec_driver_sql
            .call_args_list
        )
    ]


    assert (
        "SET LOCAL statement_timeout = "
        "'2500ms'"
        in executed
    )


# ============================================================
# LOCK TIMEOUT
# ============================================================


def test_lock_timeout_is_set():

    (
        engine,
        connection,
        _,
        _,
    ) = build_mock_engine()


    (
        ReadOnlySQLExecutor(
            engine=engine,
            statement_timeout_ms=2500,
            lock_timeout_ms=700,
        )

        .execute(
            "SELECT 1"
        )
    )


    executed = [
        item.args[0]
        for item
        in (
            connection
            .exec_driver_sql
            .call_args_list
        )
    ]


    assert (
        "SET LOCAL lock_timeout = "
        "'700ms'"
        in executed
    )


# ============================================================
# ORDER OF PROTECTION
# ============================================================


def test_protection_commands_run_before_query():

    (
        engine,
        connection,
        _,
        _,
    ) = build_mock_engine()


    (
        ReadOnlySQLExecutor(
            engine
        )

        .execute(
            "SELECT 1"
        )
    )


    executed = [
        item.args[0]
        for item
        in (
            connection
            .exec_driver_sql
            .call_args_list
        )
    ]


    assert (
        executed
        ==
        [
            (
                "SET TRANSACTION "
                "READ ONLY"
            ),
            (
                "SET LOCAL "
                "statement_timeout = "
                "'5000ms'"
            ),
            (
                "SET LOCAL "
                "lock_timeout = "
                "'1000ms'"
            ),
            "SELECT 1",
        ]
    )


# ============================================================
# SUCCESS ALWAYS ROLLS BACK
# ============================================================


def test_successful_execution_rolls_back():

    (
        engine,
        _,
        transaction,
        _,
    ) = build_mock_engine()


    (
        ReadOnlySQLExecutor(
            engine
        )

        .execute(
            "SELECT 1"
        )
    )


    (
        transaction
        .rollback
        .assert_called_once()
    )


    (
        transaction
        .commit
        .assert_not_called()
    )


# ============================================================
# QUERY FAILURE ROLLS BACK
# ============================================================


def test_query_failure_rolls_back():

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


    transaction.is_active = True


    connection.exec_driver_sql.side_effect = [
        MagicMock(),
        MagicMock(),
        MagicMock(),
        RuntimeError(
            "query failed"
        ),
    ]


    with pytest.raises(
        SQLExecutionError
    ) as exc_info:

        (
            ReadOnlySQLExecutor(
                engine
            )

            .execute(
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
# READ-ONLY SETUP FAILURE
# ============================================================


def test_read_only_setup_failure_is_translated():

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


    transaction.is_active = True


    (
        connection
        .exec_driver_sql
        .side_effect
    ) = RuntimeError(
        "SET TRANSACTION failed"
    )


    with pytest.raises(
        SQLExecutionError
    ):

        (
            ReadOnlySQLExecutor(
                engine
            )

            .execute(
                "SELECT 1"
            )
        )


    (
        transaction
        .rollback
        .assert_called_once()
    )


# ============================================================
# EMPTY RESULT
# ============================================================


def test_empty_query_result_is_supported():

    (
        engine,
        _,
        _,
        _,
    ) = build_mock_engine(
        rows=[],
        columns=[
            "customer_id"
        ],
    )


    result = (

        ReadOnlySQLExecutor(
            engine
        )

        .execute(
            """
            SELECT customer_id
            FROM public.customers
            WHERE 1 = 0
            """
        )
    )


    assert (
        result.columns
        ==
        [
            "customer_id"
        ]
    )

    assert (
        result.rows
        ==
        []
    )

    assert (
        result.row_count
        ==
        0
    )


# ============================================================
# EMPTY SQL
# ============================================================


def test_empty_sql_is_rejected():

    engine = MagicMock()


    with pytest.raises(
        SQLExecutionError
    ):

        (
            ReadOnlySQLExecutor(
                engine
            )

            .execute(
                "   "
            )
        )


    (
        engine
        .connect
        .assert_not_called()
    )


# ============================================================
# INVALID CONFIGURATION
# ============================================================


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "statement_timeout_ms": 0,
        },
        {
            "statement_timeout_ms": -1,
        },
        {
            "lock_timeout_ms": 0,
        },
        {
            "lock_timeout_ms": -1,
        },
    ],
)
def test_invalid_timeout_configuration_is_rejected(
    kwargs,
):

    engine = MagicMock()


    with pytest.raises(
        ValueError
    ):

        ReadOnlySQLExecutor(
            engine=engine,
            **kwargs,
        )