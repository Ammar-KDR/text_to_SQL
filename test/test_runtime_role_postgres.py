import pytest

from sqlalchemy.exc import (
    DBAPIError,
)

from textSQL.database.connection import (
    runtime_engine,
)


# ============================================================
# HELPERS
# ============================================================


def require_runtime_engine():

    assert (
        runtime_engine
        is not None
    ), (
        "RUNTIME_DATABASE_URL must be configured "
        "before running runtime-role tests."
    )


    return runtime_engine


def get_sqlstate(
    exc: BaseException,
) -> str | None:

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
# CORRECT ROLE
# ============================================================


def test_runtime_engine_uses_restricted_role():

    engine = (
        require_runtime_engine()
    )


    with engine.connect() as connection:

        current_user = (
            connection
            .exec_driver_sql(
                "SELECT current_user"
            )
            .scalar_one()
        )


    assert (
        current_user
        ==
        "textsql_runtime"
    )


# ============================================================
# SELECT ALLOWED
# ============================================================


def test_runtime_role_can_select():

    engine = (
        require_runtime_engine()
    )


    with engine.connect() as connection:

        result = (
            connection
            .exec_driver_sql(
                """
                SELECT customer_id
                FROM public.customers
                LIMIT 1
                """
            )
        )


        rows = (
            result.fetchall()
        )


    assert (
        len(rows)
        <=
        1
    )


# ============================================================
# PRIVILEGE CATALOG CHECK
# ============================================================


def test_runtime_role_has_only_select_table_privileges():

    engine = (
        require_runtime_engine()
    )


    with engine.connect() as connection:

        privileges = (
            connection
            .exec_driver_sql(
                """
                SELECT
                    has_table_privilege(
                        current_user,
                        'public.customers',
                        'SELECT'
                    ),
                    has_table_privilege(
                        current_user,
                        'public.customers',
                        'INSERT'
                    ),
                    has_table_privilege(
                        current_user,
                        'public.customers',
                        'UPDATE'
                    ),
                    has_table_privilege(
                        current_user,
                        'public.customers',
                        'DELETE'
                    )
                """
            )
            .one()
        )


    assert (
        privileges[0]
        is True
    )

    assert (
        privileges[1]
        is False
    )

    assert (
        privileges[2]
        is False
    )

    assert (
        privileges[3]
        is False
    )


# ============================================================
# SCHEMA CREATE DENIED
# ============================================================


def test_runtime_role_cannot_create_in_application_schemas():

    engine = (
        require_runtime_engine()
    )


    with engine.connect() as connection:

        public_create = (
            connection
            .exec_driver_sql(
                """
                SELECT has_schema_privilege(
                    current_user,
                    'public',
                    'CREATE'
                )
                """
            )
            .scalar_one()
        )


        warehouse_create = (
            connection
            .exec_driver_sql(
                """
                SELECT has_schema_privilege(
                    current_user,
                    'warehouse',
                    'CREATE'
                )
                """
            )
            .scalar_one()
        )


    assert (
        public_create
        is False
    )

    assert (
        warehouse_create
        is False
    )


# ============================================================
# UPDATE DENIED WITHOUT READ-ONLY TRANSACTION
# ============================================================





# ============================================================
# DDL DENIED
# ============================================================


# ============================================================
# ROLE DEFAULT IS READ ONLY
# ============================================================


def test_runtime_role_defaults_to_read_only():

    engine = (
        require_runtime_engine()
    )


    with engine.connect() as connection:

        value = (
            connection
            .exec_driver_sql(
                """
                SHOW default_transaction_read_only
                """
            )
            .scalar_one()
        )


    assert (
        value
        ==
        "on"
    )

# ============================================================
# UPDATE DENIED EVEN IF SESSION READ-ONLY DEFAULT IS BYPASSED
# ============================================================


def test_runtime_role_rejects_update_by_privilege():

    engine = (
        require_runtime_engine()
    )


    with engine.connect() as connection:

        # ====================================================
        # INTENTIONALLY BYPASS ROLE READ-ONLY DEFAULT
        # ====================================================
        #
        # ALTER ROLE configured new transactions as
        # read-only.
        #
        # For THIS TEST ONLY, change the session default so
        # the next transaction is READ WRITE.
        #
        # This lets us prove that table privileges provide an
        # independent protection layer.
        # ====================================================

        connection.exec_driver_sql(
            """
            SET SESSION CHARACTERISTICS
            AS TRANSACTION READ WRITE
            """
        )


        # Finish the current transaction.
        #
        # The new session characteristic applies to the
        # following transaction.

        connection.commit()


        # ====================================================
        # BYPASS EVERYTHING ELSE
        # ====================================================
        #
        # No SQLValidator.
        # No SafetyPolicy.
        # No ReadOnlySQLExecutor.
        # No SET TRANSACTION READ ONLY.
        #
        # WHERE FALSE guarantees that even in the event of a
        # serious privilege misconfiguration, no row qualifies
        # for modification.
        # ====================================================

        with pytest.raises(
            DBAPIError
        ) as exc_info:

            connection.exec_driver_sql(
                """
                UPDATE public.customers
                SET customer_id = customer_id
                WHERE FALSE
                """
            )


        assert (
            get_sqlstate(
                exc_info.value
            )
            ==
            "42501"
        )

# ============================================================
# DDL DENIED EVEN IF SESSION READ-ONLY DEFAULT IS BYPASSED
# ============================================================


def test_runtime_role_rejects_create_table_by_privilege():

    engine = (
        require_runtime_engine()
    )


    with engine.connect() as connection:

        # Make the next transaction READ WRITE so the test
        # reaches the actual schema privilege check.

        connection.exec_driver_sql(
            """
            SET SESSION CHARACTERISTICS
            AS TRANSACTION READ WRITE
            """
        )


        connection.commit()


        with pytest.raises(
            DBAPIError
        ) as exc_info:

            connection.exec_driver_sql(
                """
                CREATE TABLE public
                .textsql_runtime_should_not_exist (
                    id INTEGER
                )
                """
            )


        assert (
            get_sqlstate(
                exc_info.value
            )
            ==
            "42501"
        )