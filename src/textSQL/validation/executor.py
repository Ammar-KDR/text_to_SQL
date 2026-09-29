from sqlalchemy.engine import (
    Engine,
)

from textSQL.validation.errors import (
    SQLExecutionError,
)

from textSQL.validation.models import (
    SQLExecutionResult,
)


class ReadOnlySQLExecutor:
    """
    Executes SQL inside a fresh PostgreSQL
    read-only transaction.

    Defense-in-depth guarantees:

    - fresh connection checkout
    - explicit transaction
    - SET TRANSACTION READ ONLY
    - local statement timeout
    - local lock timeout
    - no commit
    - rollback after execution
    - connection returned/closed by context manager

    Application-level validation must still happen
    before this executor is called.

    PostgreSQL read-only transaction enforcement is
    the database-level backup boundary.
    """

    DEFAULT_STATEMENT_TIMEOUT_MS = (
        5000
    )

    DEFAULT_LOCK_TIMEOUT_MS = (
        1000
    )


    def __init__(
        self,
        engine: Engine,
        statement_timeout_ms: int = (
            DEFAULT_STATEMENT_TIMEOUT_MS
        ),
        lock_timeout_ms: int = (
            DEFAULT_LOCK_TIMEOUT_MS
        ),
    ):

        if statement_timeout_ms <= 0:

            raise ValueError(
                "statement_timeout_ms must "
                "be greater than 0"
            )


        if lock_timeout_ms <= 0:

            raise ValueError(
                "lock_timeout_ms must "
                "be greater than 0"
            )


        self.engine = engine

        self.statement_timeout_ms = (
            statement_timeout_ms
        )

        self.lock_timeout_ms = (
            lock_timeout_ms
        )


    def execute(
        self,
        sql: str,
    ) -> SQLExecutionResult:

        if not sql.strip():

            raise SQLExecutionError(
                message=(
                    "Cannot execute empty SQL."
                ),
                sql=sql,
            )


        try:

            with (
                self.engine.connect()
                as connection
            ):

                transaction = (
                    connection.begin()
                )


                try:

                    # =========================================
                    # DATABASE READ-ONLY BOUNDARY
                    # =========================================

                    connection.exec_driver_sql(
                        "SET TRANSACTION READ ONLY"
                    )


                    # =========================================
                    # STATEMENT TIMEOUT
                    # =========================================

                    connection.exec_driver_sql(
                        (
                            "SET LOCAL "
                            "statement_timeout = "
                            f"'{self.statement_timeout_ms}ms'"
                        )
                    )


                    # =========================================
                    # LOCK TIMEOUT
                    # =========================================

                    connection.exec_driver_sql(
                        (
                            "SET LOCAL "
                            "lock_timeout = "
                            f"'{self.lock_timeout_ms}ms'"
                        )
                    )


                    # =========================================
                    # EXECUTE QUERY
                    # =========================================

                    result = (
                        connection
                        .exec_driver_sql(
                            sql
                        )
                    )


                    # =========================================
                    # MATERIALIZE RESULTS
                    # =========================================

                    columns = list(
                        result.keys()
                    )


                    mappings = (
                        result
                        .mappings()
                        .all()
                    )


                    rows = [
                        dict(row)
                        for row
                        in mappings
                    ]


                    execution_result = (
                        SQLExecutionResult(

                            columns=columns,

                            rows=rows,

                            row_count=len(
                                rows
                            ),
                        )
                    )


                finally:

                    # We intentionally NEVER commit.
                    #
                    # Even successful SELECT execution
                    # ends with rollback.

                    if transaction.is_active:

                        transaction.rollback()


        except SQLExecutionError:

            raise


        except Exception as exc:

            raise SQLExecutionError(

                message=(
                    "Read-only SQL execution "
                    "failed."
                ),

                sql=sql,

            ) from exc


        return execution_result