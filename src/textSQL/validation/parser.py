from sqlglot import parse

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


class SQLParser:
    """
    Parses exactly one PostgreSQL statement
    into a SQLGlot AST.

    Responsibilities:

    - validate that SQL is not empty
    - parse using the PostgreSQL dialect
    - translate SQLGlot parse failures
    - reject multiple statements

    This class does NOT:

    - decide whether a statement is read-only
    - validate tables or columns
    - validate joins
    - enforce complexity limits
    - rewrite LIMIT
    - execute SQL
    """

    DIALECT = "postgres"


    def parse(
        self,
        sql: str,
    ) -> ParsedSQL:

        if not sql.strip():

            raise SQLParseError(
                message=(
                    "SQL cannot be empty."
                ),
                raw_sql=sql,
            )


        try:

            parsed_statements = parse(
                sql,
                read=self.DIALECT,
            )

        except ParseError as exc:

            raise SQLParseError(
                message=(
                    "Generated SQL could not "
                    "be parsed as PostgreSQL."
                ),
                raw_sql=sql,
            ) from exc


        statements = [
            statement
            for statement
            in parsed_statements
            if statement is not None
        ]


        if not statements:

            raise SQLParseError(
                message=(
                    "SQL did not contain a "
                    "parseable statement."
                ),
                raw_sql=sql,
            )


        if len(statements) != 1:

            raise MultipleStatementsError(
                statement_count=(
                    len(statements)
                ),
                raw_sql=sql,
            )


        return ParsedSQL(
            original_sql=sql,
            ast=statements[0],
        )