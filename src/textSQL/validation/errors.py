class SQLParserError(Exception):
    """
    Base error for failures that occur
    while parsing generated SQL.
    """

    pass


class SQLParseError(
    SQLParserError
):
    """
    Raised when the supplied SQL cannot be
    parsed as PostgreSQL.
    """

    def __init__(
        self,
        message: str,
        raw_sql: str,
    ):

        super().__init__(
            message
        )

        self.raw_sql = raw_sql


class MultipleStatementsError(
    SQLParserError
):
    """
    Raised when generated SQL contains more
    than one executable SQL statement.
    """

    def __init__(
        self,
        statement_count: int,
        raw_sql: str,
    ):

        super().__init__(
            (
                "Expected exactly one SQL "
                "statement, but found "
                f"{statement_count}."
            )
        )

        self.statement_count = (
            statement_count
        )

        self.raw_sql = raw_sql


class SQLAnalysisError(Exception):
    """
    Raised when a syntactically valid AST
    cannot be analyzed into SQL scopes.
    """

    def __init__(
        self,
        message: str,
        raw_sql: str,
    ):

        super().__init__(
            message
        )

        self.raw_sql = raw_sql


class PlannerExplainError(
    Exception
):
    """
    PostgreSQL could not produce or return
    a usable EXPLAIN plan.
    """

    def __init__(
        self,
        message: str,
        sql: str,
    ):

        super().__init__(
            message
        )

        self.message = message

        self.sql = sql



class SQLExecutionError(
    Exception
):
    """
    SQL execution failed inside the
    protected read-only transaction.
    """

    def __init__(
        self,
        message: str,
        sql: str,
    ):

        super().__init__(
            message
        )

        self.message = message

        self.sql = sql