from sqlalchemy.engine import (
    Engine,
)

from textSQL.generation.models import (
    GenerationContext,
)

from textSQL.validation.analyzer import (
    ASTAnalyzer,
)

from textSQL.validation.complexity import (
    ComplexityPolicy,
)

from textSQL.validation.errors import (
    MultipleStatementsError,
    PlannerExplainError,
    SQLAnalysisError,
    SQLParseError,
)

from textSQL.validation.models import (
    SQLValidationResult,
    SQLValidationStatus,
    ValidationIssue,
    ValidationIssueCode,
)

from textSQL.validation.parser import (
    SQLParser,
)

from textSQL.validation.planner import (
    PlannerPolicy,
    PostgresExplainAnalyzer,
)

from textSQL.validation.row_limit import (
    RowLimitPolicy,
)

from textSQL.validation.safety import (
    SafetyPolicy,
)

from textSQL.validation.validator import (
    GroundingValidator,
)


class SQLValidator:
    """
    Final deterministic SQL validation orchestrator.

    Stages:

        SQL text
            ↓
        parser
            ↓
        AST analyzer
            ↓
        safety
            ↓
        grounding
            ↓
        complexity
            ↓
        row-cap rewriting
            ↓
        PostgreSQL EXPLAIN
            ↓
        planner policy
            ↓
        VALID safe SQL

    The validator does NOT:

    - generate SQL
    - repair SQL
    - execute result rows
    - rebuild GenerationContext
    """


    def __init__(
        self,
        engine: Engine,
        max_total_cost: float,
        max_plan_rows: int,
        max_rows: int = 500,
        max_joins: int = 6,
        max_subquery_depth: int = 3,
        explain_analyzer=None,
    ):

        self.parser = (
            SQLParser()
        )

        self.analyzer = (
            ASTAnalyzer()
        )

        self.safety_policy = (
            SafetyPolicy()
        )

        self.grounding_validator = (
            GroundingValidator()
        )

        self.complexity_policy = (
            ComplexityPolicy(
                max_joins=max_joins,
                max_subquery_depth=(
                    max_subquery_depth
                ),
            )
        )

        self.row_limit_policy = (
            RowLimitPolicy(
                max_rows=max_rows
            )
        )


        if explain_analyzer is None:

            explain_analyzer = (
                PostgresExplainAnalyzer(
                    engine
                )
            )


        self.explain_analyzer = (
            explain_analyzer
        )


        self.planner_policy = (
            PlannerPolicy(
                max_total_cost=(
                    max_total_cost
                ),
                max_plan_rows=(
                    max_plan_rows
                ),
            )
        )
    def validate(
        self,
        sql: str,
        context: GenerationContext,
    ) -> SQLValidationResult:

        # ====================================================
        # 1. PARSE
        # ====================================================

        try:

            parsed = (
                self.parser
                .parse(
                    sql
                )
            )


        except MultipleStatementsError as exc:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .BLOCKED
                ),

                issues=[

                    ValidationIssue(

                        code=(
                            ValidationIssueCode
                            .MULTIPLE_STATEMENTS
                        ),

                        message=str(
                            exc
                        ),

                        object_name=sql,
                    )
                ],
            )


        except SQLParseError as exc:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .INVALID
                ),

                issues=[

                    ValidationIssue(

                        code=(
                            ValidationIssueCode
                            .PARSE_ERROR
                        ),

                        message=str(
                            exc
                        ),

                        object_name=sql,
                    )
                ],
            )


        # ====================================================
        # 2. AST ANALYSIS
        # ====================================================

        try:

            analysis = (
                self.analyzer
                .analyze(
                    parsed
                )
            )


        except SQLAnalysisError as exc:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .INVALID
                ),

                issues=[

                    ValidationIssue(

                        code=(
                            ValidationIssueCode
                            .ANALYSIS_ERROR
                        ),

                        message=str(
                            exc
                        ),

                        object_name=sql,
                    )
                ],
            )


        # ====================================================
        # 3. SAFETY POLICY
        #
        # Hard policy violations are BLOCKED.
        #
        # We run safety before grounding because there is
        # no reason to deeply validate schema grounding for
        # a statement we already know must never execute.
        # ====================================================

        safety_result = (
            self.safety_policy
            .validate(
                parsed
            )
        )


        if not safety_result.valid:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .BLOCKED
                ),

                issues=(
                    safety_result.issues
                ),

                analysis=analysis,
            )


        # ====================================================
        # 4. SCHEMA / RELATIONSHIP GROUNDING
        #
        # These are INVALID rather than BLOCKED because
        # they represent generation errors that may later
        # be candidates for one deterministic repair.
        # ====================================================

        grounding_result = (
            self.grounding_validator
            .validate(
                analysis=analysis,
                context=context,
            )
        )


        if not grounding_result.valid:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .INVALID
                ),

                issues=(
                    grounding_result.issues
                ),

                analysis=analysis,
            )


        # ====================================================
        # 5. STRUCTURAL COMPLEXITY
        # ====================================================

        complexity_result = (
            self.complexity_policy
            .validate(
                analysis
            )
        )


        if not complexity_result.valid:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .BLOCKED
                ),

                issues=(
                    complexity_result.issues
                ),

                analysis=analysis,
            )


        # ====================================================
        # 6. DETERMINISTIC ROW CAP
        # ====================================================

        row_limit_result = (
            self.row_limit_policy
            .apply(
                parsed_sql=parsed,
                analysis=analysis,
            )
        )


        candidate_safe_sql = (
            row_limit_result.sql
        )


        # ====================================================
        # 7. POSTGRESQL EXPLAIN
        # ====================================================

        try:

            planner_estimate = (
                self.explain_analyzer
                .analyze(
                    candidate_safe_sql
                )
            )


        except PlannerExplainError as exc:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .BLOCKED
                ),

                issues=[

                    ValidationIssue(

                        code=(
                            ValidationIssueCode
                            .PLANNER_EXPLAIN_FAILED
                        ),

                        message=str(
                            exc
                        ),

                        object_name=(
                            candidate_safe_sql
                        ),
                    )
                ],

                analysis=analysis,
            )


        # ====================================================
        # 8. PLANNER THRESHOLDS
        # ====================================================

        planner_result = (
            self.planner_policy
            .validate(
                planner_estimate
            )
        )


        if not planner_result.valid:

            return SQLValidationResult(

                status=(
                    SQLValidationStatus
                    .BLOCKED
                ),

                issues=(
                    planner_result.issues
                ),

                analysis=analysis,

                planner_estimate=(
                    planner_estimate
                ),
            )


        # ====================================================
        # 9. VALID
        # ====================================================

        return SQLValidationResult(

            status=(
                SQLValidationStatus
                .VALID
            ),

            issues=[],

            analysis=analysis,

            safe_sql=(
                candidate_safe_sql
            ),

            planner_estimate=(
                planner_estimate
            ),
        )