import pytest

from sqlglot.errors import (
    OptimizeError,
)

from textSQL.validation.analyzer import (
    ASTAnalyzer,
)

from textSQL.validation.errors import (
    SQLAnalysisError,
)

from textSQL.validation.models import (
    SQLAnalysis,
)

from textSQL.validation.parser import (
    SQLParser,
)
from textSQL.validation.models import (
    SQLAnalysis,
    ScopeSourceKind,
    ColumnSourceKind,
    
)

# ============================================================
# HELPERS
# ============================================================


def analyze(
    sql: str,
) -> SQLAnalysis:

    parsed = (
        SQLParser()
        .parse(
            sql
        )
    )


    return (
        ASTAnalyzer()
        .analyze(
            parsed
        )
    )


# ============================================================
# STATEMENT TYPE
# ============================================================


def test_analyzer_extracts_select_statement_type():

    result = analyze(
        """
        SELECT *
        FROM public.orders;
        """
    )


    assert (
        result.statement_type
        ==
        "select"
    )


def test_analyzer_reports_delete_without_blocking():

    """
    ASTAnalyzer reports structure only.

    SafetyPolicy will later reject DELETE.
    """

    result = analyze(
        """
        DELETE
        FROM public.orders;
        """
    )


    assert (
        result.statement_type
        ==
        "delete"
    )


# ============================================================
# PHYSICAL TABLES
# ============================================================


def test_analyzer_extracts_physical_table():

    result = analyze(
        """
        SELECT *
        FROM public.orders;
        """
    )


    assert (
        result.physical_tables
        ==
        [
            "public.orders"
        ]
    )


def test_unaliased_table_reference():

    result = analyze(
        """
        SELECT *
        FROM public.orders;
        """
    )


    assert len(
        result.table_references
    ) == 1


    reference = (
        result.table_references[0]
    )


    assert (
        reference.qualified_name
        ==
        "public.orders"
    )


    assert (
        reference.source_name
        ==
        "orders"
    )


    assert (
        reference.alias
        is None
    )


# ============================================================
# TABLE ALIASES
# ============================================================


def test_analyzer_extracts_table_alias():

    result = analyze(
        """
        SELECT
            o.order_id
        FROM public.orders AS o;
        """
    )


    assert len(
        result.table_references
    ) == 1


    reference = (
        result.table_references[0]
    )


    assert (
        reference.qualified_name
        ==
        "public.orders"
    )


    assert (
        reference.source_name
        ==
        "o"
    )


    assert (
        reference.alias
        ==
        "o"
    )


# ============================================================
# JOINS
# ============================================================


def test_analyzer_extracts_joined_physical_tables():

    result = analyze(
        """
        SELECT
            o.order_id,
            c.customer_id
        FROM public.orders AS o
        JOIN public.customers AS c
            ON o.customer_id = c.customer_id;
        """
    )


    assert set(
        result.physical_tables
    ) == {
        "public.orders",
        "public.customers",
    }


    aliases = {
        reference.alias
        for reference
        in result.table_references
    }


    assert aliases == {
        "o",
        "c",
    }


# ============================================================
# CTE RESOLUTION
# ============================================================


def test_cte_is_not_reported_as_physical_table():

    result = analyze(
        """
        WITH customer_totals AS (
            SELECT
                customer_id,
                COUNT(*) AS order_count
            FROM public.orders
            GROUP BY customer_id
        )
        SELECT
            customer_id,
            order_count
        FROM customer_totals;
        """
    )


    assert (
        result.cte_names
        ==
        [
            "customer_totals"
        ]
    )


    assert (
        result.physical_tables
        ==
        [
            "public.orders"
        ]
    )


    assert (
        "customer_totals"
        not in result.physical_tables
    )


# ============================================================
# DERIVED SUBQUERY
# ============================================================


def test_derived_subquery_is_not_physical_table():

    result = analyze(
        """
        SELECT
            recent_orders.order_id
        FROM (
            SELECT
                order_id
            FROM public.orders
        ) AS recent_orders;
        """
    )


    assert (
        result.physical_tables
        ==
        [
            "public.orders"
        ]
    )


    assert (
        "recent_orders"
        not in result.physical_tables
    )


# ============================================================
# SELF JOIN
# ============================================================


def test_self_join_deduplicates_physical_tables_but_preserves_references():

    result = analyze(
        """
        SELECT
            previous_order.order_id,
            next_order.order_id
        FROM public.orders AS previous_order
        JOIN public.orders AS next_order
            ON (
                previous_order.customer_id
                =
                next_order.customer_id
            );
        """
    )


    assert (
        result.physical_tables
        ==
        [
            "public.orders"
        ]
    )


    assert len(
        result.table_references
    ) == 2


    aliases = {
        reference.alias
        for reference
        in result.table_references
    }


    assert aliases == {
        "previous_order",
        "next_order",
    }


# ============================================================
# SCOPE ANALYSIS FAILURE
# ============================================================


def test_duplicate_source_alias_is_analysis_error():

    sql = """
    SELECT *
    FROM public.orders AS x
    JOIN public.customers AS x
        ON x.customer_id = x.customer_id;
    """


    parsed = (
        SQLParser()
        .parse(
            sql
        )
    )


    with pytest.raises(
        SQLAnalysisError
    ) as error:

        (
            ASTAnalyzer()
            .analyze(
                parsed
            )
        )


    assert (
        error.value.raw_sql
        ==
        sql
    )


    assert isinstance(
        error.value.__cause__,
        OptimizeError,
    )

# ============================================================
# COLUMN REFERENCES
# ============================================================


def test_qualified_column_resolves_to_physical_table():

    result = analyze(
        """
        SELECT
            o.order_id
        FROM public.orders AS o;
        """
    )


    assert len(
        result.column_references
    ) == 1


    column = (
        result.column_references[0]
    )


    assert (
        column.name
        ==
        "order_id"
    )


    assert (
        column.qualifier
        ==
        "o"
    )


    assert (
        column.source_kind
        ==
        ColumnSourceKind
        .PHYSICAL_TABLE
    )


    assert (
        column.resolved_table
        ==
        "public.orders"
    )


def test_unqualified_column_is_not_guessed():

    result = analyze(
        """
        SELECT
            customer_id
        FROM public.orders;
        """
    )


    column = (
        result.column_references[0]
    )


    assert (
        column.name
        ==
        "customer_id"
    )


    assert (
        column.qualifier
        is None
    )


    assert (
        column.source_kind
        ==
        ColumnSourceKind
        .UNQUALIFIED
    )


    assert (
        column.resolved_table
        is None
    )


# ============================================================
# LOGICAL SOURCES
# ============================================================


def test_cte_column_is_classified_as_logical_source():

    result = analyze(
        """
        WITH customer_totals AS (
            SELECT
                o.customer_id,
                COUNT(*) AS order_count
            FROM public.orders AS o
            GROUP BY o.customer_id
        )
        SELECT
            ct.order_count
        FROM customer_totals AS ct;
        """
    )


    outer_column = next(
        column
        for column
        in result.column_references
        if (
            column.name
            ==
            "order_count"
        )
    )


    assert (
        outer_column.qualifier
        ==
        "ct"
    )


    assert (
        outer_column.source_kind
        ==
        ColumnSourceKind
        .LOGICAL_SCOPE
    )


    assert (
        outer_column.resolved_table
        is None
    )


def test_derived_table_column_is_logical_source():

    result = analyze(
        """
        SELECT
            recent.order_id
        FROM (
            SELECT
                o.order_id
            FROM public.orders AS o
        ) AS recent;
        """
    )


    outer_column = next(
        column
        for column
        in result.column_references
        if (
            column.qualifier
            ==
            "recent"
        )
    )


    assert (
        outer_column.source_kind
        ==
        ColumnSourceKind
        .LOGICAL_SCOPE
    )


# ============================================================
# SCOPE SEPARATION
# ============================================================


def test_nested_queries_keep_columns_in_separate_scopes():

    result = analyze(
        """
        SELECT
            customer_id
        FROM public.orders
        WHERE customer_id IN (
            SELECT
                customer_id
            FROM public.customers
        );
        """
    )


    customer_columns = [
        column
        for column
        in result.column_references
        if (
            column.name
            ==
            "customer_id"
        )
    ]


    scope_ids = {
        column.scope_id
        for column
        in customer_columns
    }


    assert len(
        scope_ids
    ) == 2


# ============================================================
# SCOPE SOURCES
# ============================================================


def test_cte_scope_sources_distinguish_physical_and_logical():

    result = analyze(
        """
        WITH customer_totals AS (
            SELECT
                o.customer_id
            FROM public.orders AS o
        )
        SELECT
            ct.customer_id
        FROM customer_totals AS ct;
        """
    )


    all_sources = [
        source
        for scope
        in result.scopes
        for source
        in scope.sources
    ]


    physical_source = next(
        source
        for source
        in all_sources
        if (
            source.source_kind
            ==
            ScopeSourceKind
            .PHYSICAL_TABLE
        )
    )


    logical_source = next(
        source
        for source
        in all_sources
        if (
            source.source_kind
            ==
            ScopeSourceKind
            .LOGICAL_SCOPE
        )
    )


    assert (
        physical_source.qualified_table
        ==
        "public.orders"
    )


    assert (
        logical_source.source_name
        ==
        "ct"
    )


    assert (
        logical_source.qualified_table
        is None
    )


# ============================================================
# CORRELATED / UNKNOWN REFERENCES
# ============================================================


def test_outer_scope_reference_is_not_misclassified_as_local_table():

    result = analyze(
        """
        SELECT
            o.order_id
        FROM public.orders AS o
        WHERE EXISTS (
            SELECT 1
            FROM public.order_items AS oi
            WHERE
                oi.order_id
                =
                o.order_id
        );
        """
    )


    external_reference = next(
        column
        for column
        in result.column_references
        if (
            column.qualifier
            ==
            "o"
            and
            column.source_kind
            ==
            ColumnSourceKind
            .EXTERNAL_OR_UNKNOWN
        )
    )


    assert (
        external_reference.name
        ==
        "order_id"
    )


    assert (
        external_reference.resolved_table
        is None
    )


def test_scope_records_explicit_output_columns():

    result = analyze(
        """
        SELECT
            o.customer_id,
            SUM(o.total_amount)
                AS total_spend
        FROM public.orders AS o
        GROUP BY o.customer_id;
        """
    )


    scope = next(
        scope
        for scope
        in result.scopes
        if (
            "total_spend"
            in scope.output_columns
        )
    )


    assert set(
        scope.output_columns
    ) == {
        "customer_id",
        "total_spend",
    }


def test_scope_records_unqualified_star():

    result = analyze(
        """
        SELECT *
        FROM public.orders;
        """
    )


    scope = result.scopes[0]


    assert (
        scope.star_sources
        ==
        [
            None
        ]
    )


def test_logical_source_links_to_child_scope():

    result = analyze(
        """
        WITH totals AS (
            SELECT
                o.customer_id
            FROM public.orders AS o
        )
        SELECT
            t.customer_id
        FROM totals AS t;
        """
    )


    logical_source = next(
        source
        for scope
        in result.scopes
        for source
        in scope.sources
        if (
            source.source_name
            ==
            "t"
        )
    )


    assert (
        logical_source
        .source_scope_id
        is not None
    )

def test_analyzer_extracts_join_structure():

    result = analyze(
        """
        SELECT
            o.order_id,
            c.customer_id
        FROM public.orders AS o
        LEFT JOIN public.customers AS c
            ON (
                o.customer_id
                =
                c.customer_id
            );
        """
    )


    assert (
        result.join_count
        ==
        1
    )


    join = (
        result.joins[0]
    )


    assert (
        join.target_source
        ==
        "c"
    )


    assert (
        "left"
        in join.join_type
    )


    assert (
        join.condition_sql
        ==
        "o.customer_id = c.customer_id"
    )

def test_analyzer_extracts_functions():

    result = analyze(
        """
        SELECT
            COUNT(*) AS order_count,
            SUM(o.total_amount)
                AS revenue
        FROM public.orders AS o;
        """
    )


    names = [
        function.name
        for function
        in result.functions
    ]


    assert (
        result.function_count
        ==
        2
    )


    assert set(
        names
    ) == {
        "count",
        "sum",
    }

def test_analyzer_extracts_group_and_order_expressions():

    result = analyze(
        """
        SELECT
            o.customer_id,
            SUM(o.total_amount)
                AS revenue
        FROM public.orders AS o
        GROUP BY
            o.customer_id
        ORDER BY
            revenue DESC;
        """
    )


    assert (
        "o.customer_id"
        in result.group_by_expressions
    )


    assert any(
        "revenue"
        in expression
        and
        "DESC"
        in expression.upper()

        for expression
        in result.order_by_expressions
    )

def test_sibling_subqueries_have_depth_one():

    result = analyze(
        """
        SELECT *
        FROM public.orders
        WHERE customer_id IN (
            SELECT customer_id
            FROM public.customers
        )
        AND order_id IN (
            SELECT order_id
            FROM public.order_items
        );
        """
    )


    assert (
        result.subquery_count
        ==
        2
    )


    assert (
        result.max_subquery_depth
        ==
        1
    )

def test_nested_subquery_depth_is_measured():

    result = analyze(
        """
        SELECT *
        FROM public.orders
        WHERE customer_id IN (
            SELECT customer_id
            FROM public.customers
            WHERE customer_id IN (
                SELECT order_id
                FROM public.order_items
            )
        );
        """
    )


    assert (
        result.subquery_count
        ==
        2
    )


    assert (
        result.max_subquery_depth
        ==
        2
    )

def test_outer_limit_is_extracted():

    result = analyze(
        """
        SELECT *
        FROM public.orders
        LIMIT 50;
        """
    )


    assert (
        result.has_outer_limit
        is True
    )


    assert (
        result.outer_limit_value
        ==
        50
    )

def test_inner_limit_does_not_count_as_outer_limit():

    result = analyze(
        """
        SELECT *
        FROM (
            SELECT *
            FROM public.orders
            LIMIT 5
        ) AS x;
        """
    )


    assert (
        result.has_outer_limit
        is False
    )


    assert (
        result.outer_limit_value
        is None
    )

def test_join_comparison_columns_are_resolved():

    result = analyze(
        """
        SELECT
            o.order_id
        FROM public.orders AS o
        JOIN public.customers AS c
            ON (
                o.customer_id
                =
                c.customer_id
            );
        """
    )


    join = (
        result.joins[0]
    )


    assert len(
        join.comparisons
    ) == 1


    comparison = (
        join.comparisons[0]
    )


    assert (
        comparison.left.resolved_table
        ==
        "public.orders"
    )


    assert (
        comparison.left.name
        ==
        "customer_id"
    )


    assert (
        comparison.right.resolved_table
        ==
        "public.customers"
    )


    assert (
        comparison.right.name
        ==
        "customer_id"
    )


def test_join_records_disjunction():

    result = analyze(
        """
        SELECT *
        FROM public.orders AS o
        JOIN public.customers AS c
            ON (
                o.customer_id
                =
                c.customer_id

                OR

                c.email = 'x@example.com'
            );
        """
    )


    assert (
        result.joins[0]
        .has_disjunction
        is True
    )

def test_cross_join_is_identified():

    result = analyze(
        """
        SELECT *
        FROM public.orders AS o
        CROSS JOIN public.customers AS c;
        """
    )


    assert (
        result.join_count
        ==
        1
    )


    assert (
        "cross"
        in result.joins[0]
        .join_type
        .lower()
    )


def test_cross_join_is_identified():

    result = analyze(
        """
        SELECT *
        FROM public.orders AS o
        CROSS JOIN public.customers AS c;
        """
    )


    assert (
        result.join_count
        ==
        1
    )


    join = (
        result.joins[0]
    )


    assert (
        join.target_source
        ==
        "c"
    )


    assert (
        join.target_table
        ==
        "public.customers"
    )


    assert (
        join.is_cross
        is True
    )


    assert (
        join.condition_sql
        is None
    )