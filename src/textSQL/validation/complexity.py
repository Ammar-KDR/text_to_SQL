from textSQL.validation.models import (
    ComplexityValidationResult,
    SQLAnalysis,
    ValidationIssue,
    ValidationIssueCode,
)


class ComplexityPolicy:
    """
    Enforces deterministic structural complexity limits.

    This policy operates only on AST-derived SQLAnalysis.
    It does not inspect raw SQL strings and does not
    estimate PostgreSQL execution cost.

    Planner cost validation is a separate later stage.
    """

    DEFAULT_MAX_JOINS = 6

    DEFAULT_MAX_SUBQUERY_DEPTH = 3


    def __init__(
        self,
        max_joins: int = DEFAULT_MAX_JOINS,
        max_subquery_depth: int = (
            DEFAULT_MAX_SUBQUERY_DEPTH
        ),
    ):

        if max_joins < 0:
            raise ValueError(
                "max_joins must be >= 0"
            )

        if max_subquery_depth < 0:
            raise ValueError(
                "max_subquery_depth must be >= 0"
            )


        self.max_joins = max_joins

        self.max_subquery_depth = (
            max_subquery_depth
        )


    def validate(
        self,
        analysis: SQLAnalysis,
    ) -> ComplexityValidationResult:

        issues = []


        # ====================================================
        # JOIN COUNT
        # ====================================================

        if (
            analysis.join_count
            >
            self.max_joins
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .JOIN_LIMIT_EXCEEDED
                    ),

                    message=(
                        "Query contains "
                        f"{analysis.join_count} joins, "
                        "which exceeds the configured "
                        f"maximum of {self.max_joins}."
                    ),

                    object_name=str(
                        analysis.join_count
                    ),
                )
            )


        # ====================================================
        # SUBQUERY DEPTH
        # ====================================================

        if (
            analysis.max_subquery_depth
            >
            self.max_subquery_depth
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .SUBQUERY_DEPTH_EXCEEDED
                    ),

                    message=(
                        "Query has maximum subquery "
                        "depth "
                        f"{analysis.max_subquery_depth}, "
                        "which exceeds the configured "
                        "maximum of "
                        f"{self.max_subquery_depth}."
                    ),

                    object_name=str(
                        analysis
                        .max_subquery_depth
                    ),
                )
            )


        return ComplexityValidationResult(

            valid=(
                len(issues)
                ==
                0
            ),

            issues=issues,
        )