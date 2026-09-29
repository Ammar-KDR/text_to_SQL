from dataclasses import dataclass

from enum import Enum

from pydantic import (
    BaseModel,
    Field,
)
from typing import Any

from sqlglot import exp


# ============================================================
# PARSER OUTPUT
# ============================================================


@dataclass(
    slots=True
)
class ParsedSQL:
    """
    Successful output of SQLParser.

    Exactly one syntactically valid PostgreSQL
    statement is represented by this object.
    """

    original_sql: str

    ast: exp.Expression


# ============================================================
# ANALYSIS ENUMS
# ============================================================


class ScopeSourceKind(
    str,
    Enum,
):

    PHYSICAL_TABLE = (
        "physical_table"
    )

    LOGICAL_SCOPE = (
        "logical_scope"
    )


class ColumnSourceKind(
    str,
    Enum,
):

    PHYSICAL_TABLE = (
        "physical_table"
    )

    LOGICAL_SCOPE = (
        "logical_scope"
    )

    UNQUALIFIED = (
        "unqualified"
    )

    EXTERNAL_OR_UNKNOWN = (
        "external_or_unknown"
    )


# ============================================================
# TABLE ANALYSIS
# ============================================================


class PhysicalTableReference(
    BaseModel
):
    """
    One physical table occurrence.

    The same physical table may appear more
    than once, for example in a self-join.
    """

    qualified_name: str

    source_name: str

    alias: str | None = None


# ============================================================
# SCOPE ANALYSIS
# ============================================================


class ScopeSourceReference(
    BaseModel
):
    """
    One relation visible inside a SQL scope.
    """

    source_name: str

    source_kind: ScopeSourceKind

    qualified_table: (
        str | None
    ) = None

    # For a CTE or derived subquery, points
    # to the SQLScopeAnalysis that produces
    # this logical relation.
    source_scope_id: (
        int | None
    ) = None


class SQLScopeAnalysis(
    BaseModel
):
    """
    Structural information about one SQL
    query scope.
    """

    scope_id: int

    parent_scope_id: (
        int | None
    ) = None

    scope_type: str

    sources: list[
        ScopeSourceReference
    ] = Field(
        default_factory=list
    )

    # Explicit named projections:
    #
    # SELECT customer_id
    # SELECT SUM(x) AS total_spend
    #
    # produce:
    #
    # ["customer_id", "total_spend"]
    output_columns: list[str] = Field(
        default_factory=list
    )

    # None means:
    #
    # SELECT *
    #
    # "o" means:
    #
    # SELECT o.*
    #
    # Star expansion requires schema/context,
    # so ASTAnalyzer records the fact without
    # guessing the actual columns.
    star_sources: list[
        str | None
    ] = Field(
        default_factory=list
    )

# ============================================================
# COLUMN ANALYSIS
# ============================================================


class ColumnReference(
    BaseModel
):
    """
    One column expression found inside a
    specific SQL scope.

    Unqualified columns are deliberately not
    assigned to a physical table here.
    """

    name: str

    qualifier: (
        str | None
    ) = None

    sql: str

    scope_id: int

    source_kind: ColumnSourceKind

    resolved_table: (
        str | None
    ) = None


# ============================================================
# COMPLETE ANALYSIS
# ============================================================
class JoinColumnComparison(
    BaseModel
):
    """
    One column-to-column equality predicate
    extracted from a JOIN ON condition.
    """

    left: ColumnReference

    right: ColumnReference

class JoinReference(
    BaseModel
):
    """
    One JOIN expression found in a SQL scope.

    This describes the JOIN structurally.
    Grounding against retrieved relationships
    happens later.
    """

    scope_id: int

    target_source: (
        str | None
    ) = None

    target_source_kind: (
        ScopeSourceKind | None
    ) = None

    target_table: (
        str | None
    ) = None

    join_type: str

    is_cross: bool = False

    condition_sql: (
        str | None
    ) = None

    comparisons: list[
        JoinColumnComparison
    ] = Field(
        default_factory=list
    )

    uses_using: bool = False

    is_natural: bool = False

    has_disjunction: bool = False

    has_negation: bool = False

    sql: str


class FunctionReference(
    BaseModel
):
    """
    One SQL function invocation.
    """

    name: str

    sql: str


class SQLAnalysis(
    BaseModel
):
    """
    Deterministic facts extracted from the
    SQL AST.

    No safety or grounding decision is made.
    """

    statement_type: str

    cte_names: list[str] = Field(
        default_factory=list
    )

    physical_tables: list[str] = Field(
        default_factory=list
    )

    table_references: list[
        PhysicalTableReference
    ] = Field(
        default_factory=list
    )

    scopes: list[
        SQLScopeAnalysis
    ] = Field(
        default_factory=list
    )

    column_references: list[
        ColumnReference
    ] = Field(
        default_factory=list
    )

    joins: list[
        JoinReference
    ] = Field(
        default_factory=list
    )

    join_count: int = 0

    functions: list[
        FunctionReference
    ] = Field(
        default_factory=list
    )

    function_count: int = 0

    group_by_expressions: list[str] = Field(
        default_factory=list
    )

    order_by_expressions: list[str] = Field(
        default_factory=list
    )

    subquery_count: int = 0

    max_subquery_depth: int = 0

    has_outer_limit: bool = False

    outer_limit_value: (
        int | None
    ) = None

    outer_limit_sql: (
        str | None
    ) = None

# ============================================================
# VALIDATION ISSUES
# ============================================================


class ValidationIssueCode(
    str,
    Enum,
):

    UNKNOWN_TABLE = (
        "unknown_table"
    )

    UNKNOWN_COLUMN = (
        "unknown_column"
    )

    AMBIGUOUS_COLUMN = (
        "ambiguous_column"
    )


    # ========================================================
    # SAFETY
    # ========================================================

    DISALLOWED_STATEMENT = (
        "disallowed_statement"
    )

    SELECT_INTO = (
        "select_into"
    )

    ROW_LOCK = (
        "row_lock"
    )

    SEQUENCE_MUTATION = (
        "sequence_mutation"
    )
    INVALID_JOIN = (
    "invalid_join"
    )
    JOIN_LIMIT_EXCEEDED = "join_limit_exceeded"

    SUBQUERY_DEPTH_EXCEEDED = (
        "subquery_depth_exceeded"
    )
    PLANNER_COST_EXCEEDED = (
    "planner_cost_exceeded"
    )

    PLANNER_ROWS_EXCEEDED = (
        "planner_rows_exceeded"
    )
    PARSE_ERROR = "parse_error"

    MULTIPLE_STATEMENTS = (
        "multiple_statements"
    )

    ANALYSIS_ERROR = (
        "analysis_error"
    )

    PLANNER_EXPLAIN_FAILED = (
        "planner_explain_failed"
    )

class ValidationIssue(
    BaseModel
):
    """
    One deterministic validation problem.

    Issues describe what failed without
    deciding the final pipeline status yet.
    """

    code: ValidationIssueCode

    message: str

    object_name: (
        str | None
    ) = None

    scope_id: (
        int | None
    ) = None


class GroundingValidationResult(
    BaseModel
):
    """
    Result of validating AST-derived database
    objects against GenerationContext.
    """

    valid: bool

    issues: list[
        ValidationIssue
    ] = Field(
        default_factory=list
    )

class SafetyValidationResult(
    BaseModel
):
    """
    Result of deterministic SQL safety
    validation.

    Safety is independent from schema
    grounding.
    """

    valid: bool

    issues: list[
        ValidationIssue
    ] = Field(
        default_factory=list
    )

class ComplexityValidationResult(
    BaseModel
):
    valid: bool

    issues: list[
        ValidationIssue
    ] = Field(
        default_factory=list
    )

class RowLimitResult(
    BaseModel
):
    """
    Result of deterministic outer row-cap enforcement.
    """

    sql: str

    max_rows: int

    original_limit_value: (
        int | None
    ) = None

    original_limit_sql: (
        str | None
    ) = None

    final_limit_value: int

    was_rewritten: bool

class PlannerEstimate(
    BaseModel
):
    """
    Facts extracted from PostgreSQL EXPLAIN.
    """

    total_cost: float

    root_plan_rows: int

    max_plan_rows: int

    node_count: int


class PlannerValidationResult(
    BaseModel
):
    valid: bool

    estimate: PlannerEstimate

    issues: list[
        ValidationIssue
    ] = Field(
        default_factory=list
    )




class SQLExecutionResult(
    BaseModel
):
    columns: list[str]

    rows: list[
        dict[str, Any]
    ]

    row_count: int




class SQLValidationStatus(
    str,
    Enum,
):
    VALID = "VALID"

    INVALID = "INVALID"

    BLOCKED = "BLOCKED"

class SQLValidationResult(
    BaseModel
):
    """
    Final application-level SQL validation result.

    safe_sql is present only when the query has
    passed every validation and planner stage.
    """

    status: SQLValidationStatus

    issues: list[
        ValidationIssue
    ] = Field(
        default_factory=list
    )

    analysis: (
        SQLAnalysis | None
    ) = None

    safe_sql: (
        str | None
    ) = None

    planner_estimate: (
        PlannerEstimate | None
    ) = None