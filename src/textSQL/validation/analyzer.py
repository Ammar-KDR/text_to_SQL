from sqlglot import exp

from sqlglot.errors import (
    OptimizeError,
)

from sqlglot.optimizer.scope import (
    Scope,
    build_scope,
    find_all_in_scope,
    
)

from textSQL.validation.errors import (
    SQLAnalysisError,
)

from textSQL.validation.models import (
    ParsedSQL,
    ScopeSourceKind,
    ColumnSourceKind,
    PhysicalTableReference,
    ScopeSourceReference,
    SQLScopeAnalysis,
    ColumnReference,
    SQLAnalysis,
    JoinReference,
    FunctionReference,
    JoinColumnComparison,
)


class ASTAnalyzer:
    """
    Extracts deterministic structural facts
    from a parsed SQL AST.

    Current responsibilities:

    - identify root statement type
    - collect CTE names
    - identify physical tables
    - preserve table aliases
    - identify SQL scopes
    - identify sources available per scope
    - collect column references per scope
    - resolve explicitly qualified columns
      when their source is known locally

    This class does NOT:

    - decide whether SQL is safe
    - validate tables against GenerationContext
    - validate column existence
    - resolve unqualified columns
    - decide whether a column is ambiguous
    - validate joins
    - enforce complexity limits
    - rewrite SQL
    """

    def analyze(
        self,
        parsed_sql: ParsedSQL,
    ) -> SQLAnalysis:

        try:

            root_scope = build_scope(
                parsed_sql.ast
            )


            scopes = (
                list(
                    root_scope.traverse()
                )
                if root_scope
                else []
            )


            scope_ids = {
                id(scope): index
                for index, scope
                in enumerate(scopes)
            }


            table_references = (
                self
                ._extract_table_references(
                    scopes
                )
            )


            scope_analyses = (
                self
                ._extract_scope_analyses(
                    scopes=scopes,
                    scope_ids=scope_ids,
                )
            )


            column_references = (
                self
                ._extract_column_references(
                    scopes=scopes,
                    scope_ids=scope_ids,
                )
            )

            joins = (
                self
                ._extract_joins(
                    scopes=scopes,
                    scope_ids=scope_ids,
                )
            )


            functions = (
                self
                ._extract_functions(
                    parsed_sql.ast
                )
            )


            group_by_expressions = (
                self
                ._extract_group_by(
                    parsed_sql.ast
                )
            )


            order_by_expressions = (
                self
                ._extract_order_by(
                    parsed_sql.ast
                )
            )


            (
                subquery_count,
                max_subquery_depth,
            ) = (
                self
                ._analyze_subqueries(
                    parsed_sql.ast
                )
            )


            (
                has_outer_limit,
                outer_limit_value,
                outer_limit_sql,
            ) = (
                self
                ._extract_outer_limit(
                    parsed_sql.ast
                )
            )


        except OptimizeError as exc:

            raise SQLAnalysisError(
                message=(
                    "SQL AST scope analysis "
                    "failed."
                ),
                raw_sql=(
                    parsed_sql.original_sql
                ),
            ) from exc


        return SQLAnalysis(

            statement_type=(
                parsed_sql.ast.key
            ),

            cte_names=(
                self._extract_cte_names(
                    parsed_sql.ast
                )
            ),

            physical_tables=(
                self._unique_physical_tables(
                    table_references
                )
            ),

            table_references=(
                table_references
            ),

            scopes=(
                scope_analyses
            ),

            column_references=(
                column_references
            ),
                        joins=joins,

            join_count=(
                len(joins)
            ),

            functions=functions,

            function_count=(
                len(functions)
            ),

            group_by_expressions=(
                group_by_expressions
            ),

            order_by_expressions=(
                order_by_expressions
            ),

            subquery_count=(
                subquery_count
            ),

            max_subquery_depth=(
                max_subquery_depth
            ),

            has_outer_limit=(
                has_outer_limit
            ),

            outer_limit_value=(
                outer_limit_value
            ),

            outer_limit_sql=(
                outer_limit_sql
            ),
        )


    # ========================================================
    # CTEs
    # ========================================================


    def _extract_cte_names(
        self,
        ast: exp.Expression,
    ) -> list[str]:

        names = []

        seen = set()


        for cte in ast.find_all(
            exp.CTE
        ):

            name = cte.alias


            if (
                name
                and
                name not in seen
            ):

                names.append(
                    name
                )

                seen.add(
                    name
                )


        return names


    # ========================================================
    # PHYSICAL TABLES
    # ========================================================


    def _extract_table_references(
        self,
        scopes: list[Scope],
    ) -> list[
        PhysicalTableReference
    ]:

        references = []


        for scope in scopes:

            for (
                source_name,
                (
                    _,
                    source,
                ),
            ) in (
                scope
                .selected_sources
                .items()
            ):

                if not isinstance(
                    source,
                    exp.Table,
                ):

                    continue


                references.append(

                    PhysicalTableReference(

                        qualified_name=(
                            self
                            ._qualified_table_name(
                                source
                            )
                        ),

                        source_name=(
                            source_name
                        ),

                        alias=(
                            source.alias
                            or None
                        ),
                    )
                )


        return references


    def _qualified_table_name(
        self,
        table: exp.Table,
    ) -> str:

        parts = [
            part.name
            for part in table.parts
        ]


        return ".".join(
            parts
        )


    def _unique_physical_tables(
        self,
        references: list[
            PhysicalTableReference
        ],
    ) -> list[str]:

        tables = []

        seen = set()


        for reference in references:

            if (
                reference.qualified_name
                in seen
            ):

                continue


            tables.append(
                reference.qualified_name
            )

            seen.add(
                reference.qualified_name
            )


        return tables


    # ========================================================
    # SCOPES
    # ========================================================


    def _extract_scope_analyses(
    self,
    scopes: list[Scope],
    scope_ids: dict[int, int],
) -> list[
    SQLScopeAnalysis
]:

        analyses = []


        for scope in scopes:

            sources = []


            for (
                source_name,
                (
                    _,
                    source,
                ),
            ) in (
                scope
                .selected_sources
                .items()
            ):

                if isinstance(
                    source,
                    exp.Table,
                ):

                    sources.append(

                        ScopeSourceReference(

                            source_name=(
                                source_name
                            ),

                            source_kind=(
                                ScopeSourceKind
                                .PHYSICAL_TABLE
                            ),

                            qualified_table=(
                                self
                                ._qualified_table_name(
                                    source
                                )
                            ),

                            source_scope_id=None,
                        )
                    )

                else:

                    sources.append(

                        ScopeSourceReference(

                            source_name=(
                                source_name
                            ),

                            source_kind=(
                                ScopeSourceKind
                                .LOGICAL_SCOPE
                            ),

                            qualified_table=None,

                            source_scope_id=(
                                scope_ids.get(
                                    id(source)
                                )
                            ),
                        )
                    )


            parent_scope_id = None


            if scope.parent is not None:

                parent_scope_id = (
                    scope_ids.get(
                        id(
                            scope.parent
                        )
                    )
                )


            (
                output_columns,
                star_sources,
            ) = (
                self
                ._extract_scope_outputs(
                    scope
                )
            )


            analyses.append(

                SQLScopeAnalysis(

                    scope_id=(
                        scope_ids[
                            id(scope)
                        ]
                    ),

                    parent_scope_id=(
                        parent_scope_id
                    ),

                    scope_type=(
                        scope
                        .scope_type
                        .name
                        .lower()
                    ),

                    sources=(
                        sources
                    ),

                    output_columns=(
                        output_columns
                    ),

                    star_sources=(
                        star_sources
                    ),
                )
            )


        return analyses

    # ========================================================
    # COLUMNS
    # ========================================================
    def _extract_scope_outputs(
    self,
    scope: Scope,
) -> tuple[
    list[str],
    list[str | None],
]:

        output_columns = []

        star_sources = []

        seen_outputs = set()


        selections = getattr(
            scope.expression,
            "selects",
            [],
        )


        for selection in selections:

            # ----------------------------------------------------
            # STAR OUTPUT
            # ----------------------------------------------------

            if selection.is_star:

                qualifier = None


                # SELECT o.*
                if isinstance(
                    selection,
                    exp.Column,
                ):

                    qualifier = (
                        selection.table
                        or None
                    )


                star_sources.append(
                    qualifier
                )

                continue


            # ----------------------------------------------------
            # NAMED OUTPUT
            # ----------------------------------------------------

            output_name = (
                selection.output_name
            )


            if not output_name:

                # Example:
                #
                # SELECT 1 + 2
                #
                # There is no reliable named output
                # for another scope to reference.
                continue


            if (
                output_name
                in seen_outputs
            ):

                continue


            output_columns.append(
                output_name
            )

            seen_outputs.add(
                output_name
            )


        return (
            output_columns,
            star_sources,
        )

    def _extract_column_references(
        self,
        scopes: list[Scope],
        scope_ids: dict[int, int],
    ) -> list[
        ColumnReference
    ]:

        references = []


        for scope in scopes:

            scope_id = (
                scope_ids[
                    id(scope)
                ]
            )


            columns = (
                find_all_in_scope(
                    scope.expression,
                    exp.Column,
                )
            )


            for column in columns:

                references.append(
                    self
                    ._analyze_column(
                        scope=scope,
                        scope_id=scope_id,
                        column=column,
                    )
                )


        return references


    def _analyze_column(
        self,
        scope: Scope,
        scope_id: int,
        column: exp.Column,
    ) -> ColumnReference:

        qualifier = (
            column.table
            or None
        )


        # ----------------------------------------------------
        # Unqualified column
        # ----------------------------------------------------

        if qualifier is None:

            return ColumnReference(

                name=(
                    column.name
                ),

                qualifier=None,

                sql=(
                    column.sql(
                        dialect="postgres"
                    )
                ),

                scope_id=(
                    scope_id
                ),

                source_kind=(
                    ColumnSourceKind
                    .UNQUALIFIED
                ),

                resolved_table=None,
            )


        # ----------------------------------------------------
        # Qualified column
        # ----------------------------------------------------

        selected_source = (
            scope
            .selected_sources
            .get(
                qualifier
            )
        )


        if selected_source is None:

            return ColumnReference(

                name=(
                    column.name
                ),

                qualifier=(
                    qualifier
                ),

                sql=(
                    column.sql(
                        dialect="postgres"
                    )
                ),

                scope_id=(
                    scope_id
                ),

                source_kind=(
                    ColumnSourceKind
                    .EXTERNAL_OR_UNKNOWN
                ),

                resolved_table=None,
            )


        _, source = (
            selected_source
        )


        if isinstance(
            source,
            exp.Table,
        ):

            return ColumnReference(

                name=(
                    column.name
                ),

                qualifier=(
                    qualifier
                ),

                sql=(
                    column.sql(
                        dialect="postgres"
                    )
                ),

                scope_id=(
                    scope_id
                ),

                source_kind=(
                    ColumnSourceKind
                    .PHYSICAL_TABLE
                ),

                resolved_table=(
                    self
                    ._qualified_table_name(
                        source
                    )
                ),
            )


        return ColumnReference(

            name=(
                column.name
            ),

            qualifier=(
                qualifier
            ),

            sql=(
                column.sql(
                    dialect="postgres"
                )
            ),

            scope_id=(
                scope_id
            ),

            source_kind=(
                ColumnSourceKind
                .LOGICAL_SCOPE
            ),

            resolved_table=None,
        )
    def _extract_joins(
    self,
    scopes: list[Scope],
    scope_ids: dict[int, int],
) -> list[
    JoinReference
]:

        joins = []


        for scope in scopes:

            scope_id = (
                scope_ids[
                    id(scope)
                ]
            )


            # These are the JOIN expressions directly
            # attached to this query scope.
            #
            # This returns a Python list, so we simply
            # iterate over it. Do NOT pass this list to
            # find_all_in_scope().
            scope_joins = (
                scope.expression.args.get(
                    "joins"
                )
                or []
            )


            for join in scope_joins:

                # =================================================
                # TARGET SOURCE
                # =================================================

                target_source = None

                target_source_kind = None

                target_table = None


                if join.this is not None:

                    target_source = (
                        join.this.alias_or_name
                        or None
                    )


                if target_source:

                    selected_source = (
                        scope
                        .selected_sources
                        .get(
                            target_source
                        )
                    )


                    if (
                        selected_source
                        is not None
                    ):

                        _, source = (
                            selected_source
                        )


                        if isinstance(
                            source,
                            exp.Table,
                        ):

                            target_source_kind = (
                                ScopeSourceKind
                                .PHYSICAL_TABLE
                            )

                            target_table = (
                                self
                                ._qualified_table_name(
                                    source
                                )
                            )

                        else:

                            target_source_kind = (
                                ScopeSourceKind
                                .LOGICAL_SCOPE
                            )


                # =================================================
                # JOIN TYPE
                # =================================================

                # SQLGlot exposes these directly
                # as normalized uppercase strings.
                method = (
                    join.method
                )

                side = (
                    join.side
                )

                kind = (
                    join.kind
                )


                parts = [
                    value.lower()
                    for value
                    in (
                        method,
                        side,
                        kind,
                    )
                    if value
                ]


                join_type = (
                    " ".join(parts)
                    if parts
                    else "inner"
                )


                is_cross = (
                    kind
                    ==
                    "CROSS"
                )


                is_natural = (
                    method
                    ==
                    "NATURAL"
                )


                # =================================================
                # CONDITION
                # =================================================

                condition = (
                    join.args.get(
                        "on"
                    )
                )


                normalized_condition = (
                    condition
                )


                while isinstance(
                    normalized_condition,
                    exp.Paren,
                ):

                    normalized_condition = (
                        normalized_condition.this
                    )


                # =================================================
                # COLUMN EQUALITY COMPARISONS
                # =================================================

                comparisons = []


                if condition is not None:

                    equalities = (
                        find_all_in_scope(
                            condition,
                            exp.EQ,
                        )
                    )


                    for equality in equalities:

                        left = (
                            equality.this
                        )

                        right = (
                            equality.expression
                        )


                        if not (
                            isinstance(
                                left,
                                exp.Column,
                            )
                            and
                            isinstance(
                                right,
                                exp.Column,
                            )
                        ):

                            continue


                        comparisons.append(

                            JoinColumnComparison(

                                left=(
                                    self
                                    ._analyze_column(
                                        scope=scope,
                                        scope_id=(
                                            scope_id
                                        ),
                                        column=left,
                                    )
                                ),

                                right=(
                                    self
                                    ._analyze_column(
                                        scope=scope,
                                        scope_id=(
                                            scope_id
                                        ),
                                        column=right,
                                    )
                                ),
                            )
                        )


                # =================================================
                # BOOLEAN STRUCTURE
                # =================================================

                has_disjunction = False

                has_negation = False


                if condition is not None:

                    for node in (
                        condition.walk()
                    ):

                        if isinstance(
                            node,
                            exp.Or,
                        ):

                            has_disjunction = (
                                True
                            )


                        if isinstance(
                            node,
                            exp.Not,
                        ):

                            has_negation = (
                                True
                            )


                # =================================================
                # USING
                # =================================================

                uses_using = bool(
                    join.args.get(
                        "using"
                    )
                )


                # =================================================
                # FINAL REFERENCE
                # =================================================

                joins.append(

                    JoinReference(

                        scope_id=(
                            scope_id
                        ),

                        target_source=(
                            target_source
                        ),

                        target_source_kind=(
                            target_source_kind
                        ),

                        target_table=(
                            target_table
                        ),

                        join_type=(
                            join_type
                        ),

                        is_cross=(
                            is_cross
                        ),

                        condition_sql=(
                            normalized_condition
                            .sql(
                                dialect="postgres"
                            )
                            if normalized_condition
                            else None
                        ),

                        comparisons=(
                            comparisons
                        ),

                        uses_using=(
                            uses_using
                        ),

                        is_natural=(
                            is_natural
                        ),

                        has_disjunction=(
                            has_disjunction
                        ),

                        has_negation=(
                            has_negation
                        ),

                        sql=(
                            join.sql(
                                dialect="postgres"
                            )
                        ),
                    )
                )


        return joins

    def _extract_functions(
    self,
    ast: exp.Expression,
) -> list[
    FunctionReference
]:

        functions = []


        for function in ast.find_all(
            exp.Func
        ):

            if isinstance(
                function,
                exp.Anonymous,
            ):

                name = (
                    function.name
                    .lower()
                )

            else:

                name = (
                    function
                    .sql_name()
                    .lower()
                )


            functions.append(

                FunctionReference(

                    name=name,

                    sql=(
                        function.sql(
                            dialect="postgres"
                        )
                    ),
                )
            )


        return functions

    def _extract_group_by(
    self,
    ast: exp.Expression,
) -> list[str]:

        expressions = []


        for group in ast.find_all(
            exp.Group
        ):

            for expression in (
                group.expressions
            ):

                expressions.append(
                    expression.sql(
                        dialect="postgres"
                    )
                )


        return expressions

    def _extract_order_by(
    self,
    ast: exp.Expression,
) -> list[str]:

        expressions = []


        for order in ast.find_all(
            exp.Order
        ):

            for expression in (
                order.expressions
            ):

                expressions.append(
                    expression.sql(
                        dialect="postgres"
                    )
                )


        return expressions

    def _analyze_subqueries(
    self,
    ast: exp.Expression,
) -> tuple[
    int,
    int,
]:

        subqueries = list(
            ast.find_all(
                exp.Subquery
            )
        )


        maximum_depth = 0


        for subquery in subqueries:

            depth = 1

            parent = (
                subquery.parent
            )


            while parent is not None:

                if isinstance(
                    parent,
                    exp.Subquery,
                ):

                    depth += 1


                parent = (
                    parent.parent
                )


            maximum_depth = max(
                maximum_depth,
                depth,
            )


        return (
            len(subqueries),
            maximum_depth,
        )

    def _extract_outer_limit(
    self,
    ast: exp.Expression,
) -> tuple[
    bool,
    int | None,
    str | None,
]:

        if not isinstance(
            ast,
            exp.Query,
        ):

            return (
                False,
                None,
                None,
            )


        limit = (
            ast.args.get(
                "limit"
            )
        )


        if limit is None:

            return (
                False,
                None,
                None,
            )


        limit_sql = (
            limit.sql(
                dialect="postgres"
            )
        )


        limit_value = None


        expression = (
            limit.expression
        )


        if (
            isinstance(
                expression,
                exp.Literal,
            )
            and
            expression.is_int
        ):

            limit_value = int(
                expression.this
            )


        return (
            True,
            limit_value,
            limit_sql,
        )