from sqlglot import exp

from textSQL.validation.models import (
    ParsedSQL,
    RowLimitResult,
    SQLAnalysis,
)


class RowLimitPolicy:
    """
    Enforces a deterministic maximum row count
    on the outermost SQL query.

    Inner query limits are preserved.

    The policy operates on the SQLGlot AST rather
    than modifying raw SQL text.
    """

    DEFAULT_MAX_ROWS = 500


    def __init__(
        self,
        max_rows: int = DEFAULT_MAX_ROWS,
    ):

        if max_rows <= 0:

            raise ValueError(
                "max_rows must be greater than 0"
            )


        self.max_rows = max_rows


    def apply(
        self,
        parsed_sql: ParsedSQL,
        analysis: SQLAnalysis,
    ) -> RowLimitResult:

        ast = parsed_sql.ast


        # ====================================================
        # DEFENSIVE QUERY CHECK
        # ====================================================

        if not isinstance(
            ast,
            exp.Query,
        ):

            raise ValueError(
                "RowLimitPolicy requires a query AST"
            )


        original_limit_value = (
            analysis.outer_limit_value
        )

        original_limit_sql = (
            analysis.outer_limit_sql
        )


        # ====================================================
        # EXISTING SAFE LITERAL LIMIT
        # ====================================================

        if (
            analysis.has_outer_limit
            and
            original_limit_value
            is not None
            and
            0
            <=
            original_limit_value
            <=
            self.max_rows
        ):

            safe_ast = ast.copy()


            return RowLimitResult(

                sql=(
                    safe_ast.sql(
                        dialect="postgres"
                    )
                ),

                max_rows=(
                    self.max_rows
                ),

                original_limit_value=(
                    original_limit_value
                ),

                original_limit_sql=(
                    original_limit_sql
                ),

                final_limit_value=(
                    original_limit_value
                ),

                was_rewritten=False,
            )


        # ====================================================
        # ADD OR CLAMP OUTER LIMIT
        # ====================================================

        safe_ast = ast.limit(
            self.max_rows,
            copy=True,
        )


        return RowLimitResult(

            sql=(
                safe_ast.sql(
                    dialect="postgres"
                )
            ),

            max_rows=(
                self.max_rows
            ),

            original_limit_value=(
                original_limit_value
            ),

            original_limit_sql=(
                original_limit_sql
            ),

            final_limit_value=(
                self.max_rows
            ),

            was_rewritten=True,
        )