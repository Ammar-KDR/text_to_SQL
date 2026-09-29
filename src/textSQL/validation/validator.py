from textSQL.generation.models import (
    GenerationContext,
)

from textSQL.validation.models import (
    SQLAnalysis,
    SQLScopeAnalysis,
    ScopeSourceKind,
    ColumnSourceKind,
    ColumnReference,
    ValidationIssueCode,
    ValidationIssue,
    GroundingValidationResult,
)


class GroundingValidator:
    """
    Validates AST-derived database references
    against the authoritative GenerationContext.

    Responsibilities:

    - reject physical tables not supplied in
      GenerationContext
    - reject physical columns that do not exist
      on their resolved table
    - resolve unqualified columns against the
      physical sources visible in their scope
    - reject ambiguous unqualified columns
    - resolve correlated qualified references
      through parent scopes

    This class does NOT:

    - decide whether a statement is read-only
    - validate join relationships
    - validate logical/derived output columns
    - enforce query complexity
    - rewrite SQL
    - execute SQL
    """

    def validate(
    self,
    analysis: SQLAnalysis,
    context: GenerationContext,
) -> GroundingValidationResult:

        allowed_columns = (
            self._build_allowed_columns(
                context
            )
        )


        scopes = {
            scope.scope_id: scope
            for scope
            in analysis.scopes
        }


        scope_output_cache: dict[
            int,
            set[str],
        ] = {}


        issues = []


        # ====================================================
        # TABLE VALIDATION
        # ====================================================

        for table_name in (
            analysis.physical_tables
        ):

            if (
                table_name
                not in allowed_columns
            ):

                issues.append(

                    ValidationIssue(

                        code=(
                            ValidationIssueCode
                            .UNKNOWN_TABLE
                        ),

                        message=(
                            "SQL references table "
                            f"'{table_name}', which "
                            "was not supplied in the "
                            "GenerationContext."
                        ),

                        object_name=(
                            table_name
                        ),
                    )
                )


        # ====================================================
        # COLUMN VALIDATION
        # ====================================================

        for column in (
            analysis.column_references
        ):

            column_issues = (
                self._validate_column(
                    column=column,
                    scopes=scopes,
                    allowed_columns=(
                        allowed_columns
                    ),
                    scope_output_cache=(
                        scope_output_cache
                    ),
                )
            )


            issues.extend(
                column_issues
            )


        # ====================================================
        # JOIN VALIDATION
        # ====================================================

        join_issues = (
            self._validate_joins(
                analysis=analysis,
                context=context,
            )
        )


        issues.extend(
            join_issues
        )


        # ====================================================
        # DEDUPLICATION
        # ====================================================

        issues = (
            self._deduplicate_issues(
                issues
            )
        )


        return GroundingValidationResult(

            valid=(
                len(issues)
                ==
                0
            ),

            issues=issues,
        )


    # ========================================================
    # CONTEXT INDEX
    # ========================================================


    def _build_allowed_columns(
        self,
        context: GenerationContext,
    ) -> dict[
        str,
        set[str],
    ]:

        return {

            table.qualified_name: {
                column.name
                for column
                in table.columns
            }

            for table
            in context.tables
        }


    # ========================================================
    # COLUMN ROUTING
    # ========================================================


    def _validate_column(
            self,
            column: ColumnReference,
            scopes: dict[
                int,
                SQLScopeAnalysis,
            ],
            allowed_columns: dict[
                str,
                set[str],
            ],
            scope_output_cache: dict[
                int,
                set[str],
            ],
        ) -> list[
            ValidationIssue
        ]:

        if (
            column.source_kind
            ==
            ColumnSourceKind
            .PHYSICAL_TABLE
        ):

            return (
                self
                ._validate_physical_column(
                    column=column,
                    table_name=(
                        column.resolved_table
                    ),
                    allowed_columns=(
                        allowed_columns
                    ),
                )
            )


        if (
            column.source_kind
            ==
            ColumnSourceKind
            .LOGICAL_SCOPE
        ):

            return (
                self
                ._validate_logical_column(
                    column=column,
                    scopes=scopes,
                    allowed_columns=(
                        allowed_columns
                    ),
                    scope_output_cache=(
                        scope_output_cache
                    ),
                )
            )


        if (
            column.source_kind
            ==
            ColumnSourceKind
            .UNQUALIFIED
        ):

            return (
                self
                ._validate_unqualified_column(
                    column=column,
                    scopes=scopes,
                    allowed_columns=(
                        allowed_columns
                    ),
                    scope_output_cache=(
                        scope_output_cache
                    ),
                )
            )


        if (
            column.source_kind
            ==
            ColumnSourceKind
            .EXTERNAL_OR_UNKNOWN
        ):

            return (
                self
                ._validate_external_column(
                    column=column,
                    scopes=scopes,
                    allowed_columns=(
                        allowed_columns
                    ),
                    scope_output_cache=(
                        scope_output_cache
                    ),
                )
            )


        return []

    # ========================================================
    # PHYSICAL COLUMN
    # ========================================================


    def _validate_physical_column(
        self,
        column: ColumnReference,
        table_name: str | None,
        allowed_columns: dict[
            str,
            set[str],
        ],
    ) -> list[
        ValidationIssue
    ]:

        if table_name is None:

            return []


        # If the table itself is unknown, the table
        # validation already reports the root problem.
        #
        # Avoid producing a misleading cascade of
        # UNKNOWN_COLUMN issues.

        if (
            table_name
            not in allowed_columns
        ):

            return []


        if (
            column.name
            in allowed_columns[
                table_name
            ]
        ):

            return []


        qualified_column = (
            f"{table_name}.{column.name}"
        )


        return [

            ValidationIssue(

                code=(
                    ValidationIssueCode
                    .UNKNOWN_COLUMN
                ),

                message=(
                    "SQL references column "
                    f"'{qualified_column}', which "
                    "does not exist in the supplied "
                    "GenerationContext."
                ),

                object_name=(
                    qualified_column
                ),

                scope_id=(
                    column.scope_id
                ),
            )
        ]


    # ========================================================
    # UNQUALIFIED COLUMN
    # ========================================================


    def _validate_unqualified_column(
    self,
    column: ColumnReference,
    scopes: dict[
        int,
        SQLScopeAnalysis,
    ],
    allowed_columns: dict[
        str,
        set[str],
    ],
    scope_output_cache: dict[
        int,
        set[str],
    ],
) -> list[
    ValidationIssue
    ]:

        scope = scopes.get(
            column.scope_id
        )


        if scope is None:

            return []


        candidates = []


        for source in scope.sources:

            # ----------------------------------------------------
            # PHYSICAL SOURCE
            # ----------------------------------------------------

            if (
                source.source_kind
                ==
                ScopeSourceKind
                .PHYSICAL_TABLE
            ):

                table_name = (
                    source.qualified_table
                )


                if (
                    table_name
                    not in allowed_columns
                ):

                    continue


                if (
                    column.name
                    in allowed_columns[
                        table_name
                    ]
                ):

                    candidates.append(
                        source.source_name
                    )


            # ----------------------------------------------------
            # LOGICAL SOURCE
            # ----------------------------------------------------

            elif (
                source.source_kind
                ==
                ScopeSourceKind
                .LOGICAL_SCOPE
                and
                source.source_scope_id
                is not None
            ):

                outputs = (
                    self
                    ._resolve_scope_output_columns(

                        scope_id=(
                            source
                            .source_scope_id
                        ),

                        scopes=scopes,

                        allowed_columns=(
                            allowed_columns
                        ),

                        cache=(
                            scope_output_cache
                        ),
                    )
                )


                if (
                    column.name
                    in outputs
                ):

                    candidates.append(
                        source.source_name
                    )


        # ========================================================
        # UNIQUE OWNER
        # ========================================================

        if len(
            candidates
        ) == 1:

            return []


        # ========================================================
        # AMBIGUOUS
        # ========================================================

        if len(
            candidates
        ) > 1:

            return [

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .AMBIGUOUS_COLUMN
                    ),

                    message=(
                        "Unqualified column "
                        f"'{column.name}' is "
                        "ambiguous within the "
                        "current SQL scope. "
                        "Possible sources: "
                        f"{', '.join(candidates)}."
                    ),

                    object_name=(
                        column.name
                    ),

                    scope_id=(
                        column.scope_id
                    ),
                )
            ]


        # ========================================================
        # UNKNOWN
        # ========================================================

        return [

            ValidationIssue(

                code=(
                    ValidationIssueCode
                    .UNKNOWN_COLUMN
                ),

                message=(
                    "Unqualified column "
                    f"'{column.name}' is not "
                    "exposed by any relation "
                    "visible in the current "
                    "SQL scope."
                ),

                object_name=(
                    column.name
                ),

                scope_id=(
                    column.scope_id
                ),
            )
        ]


    # ========================================================
    # CORRELATED / EXTERNAL COLUMN
    # ========================================================


    def _validate_external_column(
        self,
        column: ColumnReference,
        scopes: dict[
            int,
            SQLScopeAnalysis,
        ],
        allowed_columns: dict[
            str,
            set[str],
        ],
        scope_output_cache: dict[
    int,
    set[str],
],
    ) -> list[
        ValidationIssue
    ]:

        qualifier = (
            column.qualifier
        )


        if qualifier is None:

            return []


        current_scope = (
            scopes.get(
                column.scope_id
            )
        )


        if current_scope is None:

            return []


        parent_scope_id = (
            current_scope
            .parent_scope_id
        )


        while (
            parent_scope_id
            is not None
        ):

            parent_scope = (
                scopes.get(
                    parent_scope_id
                )
            )


            if parent_scope is None:

                break


            matching_source = next(
                (
                    source
                    for source
                    in parent_scope.sources
                    if (
                        source.source_name
                        ==
                        qualifier
                    )
                ),
                None,
            )


            if (
                matching_source
                is not None
            ):

                # Parent physical table.
                if (
                    matching_source
                    .source_kind
                    ==
                    ScopeSourceKind
                    .PHYSICAL_TABLE
                ):

                    table_name = (
                        matching_source
                        .qualified_table
                    )


                    return (
                        self
                        ._validate_resolved_external_column(
                            column=column,
                            table_name=(
                                table_name
                            ),
                            allowed_columns=(
                                allowed_columns
                            ),
                        )
                    )


                # Parent logical relation.
                #
                # Requires projection lineage, so
                # defer it rather than guessing.

                if (
                    matching_source
                    .source_kind
                    ==
                    ScopeSourceKind
                    .LOGICAL_SCOPE
                ):

                    if (
                        matching_source
                        .source_scope_id
                        is None
                    ):

                        return []


                    outputs = (
                        self
                        ._resolve_scope_output_columns(

                            scope_id=(
                                matching_source
                                .source_scope_id
                            ),

                            scopes=scopes,

                            allowed_columns=(
                                allowed_columns
                            ),

                            cache=(
                                scope_output_cache
                            ),
                        )
                    )


                    if (
                        column.name
                        in outputs
                    ):

                        return []


                    qualified_reference = (
                        f"{qualifier}."
                        f"{column.name}"
                    )


                    return [

                        ValidationIssue(

                            code=(
                                ValidationIssueCode
                                .UNKNOWN_COLUMN
                            ),

                            message=(
                                "Correlated logical source "
                                f"'{qualifier}' does not expose "
                                f"column '{column.name}'."
                            ),

                            object_name=(
                                qualified_reference
                            ),

                            scope_id=(
                                column.scope_id
                            ),
                        )
                    ]


            parent_scope_id = (
                parent_scope
                .parent_scope_id
            )


        # No local or parent source owns this
        # qualifier.

        qualified_reference = (
            f"{qualifier}.{column.name}"
        )


        return [

            ValidationIssue(

                code=(
                    ValidationIssueCode
                    .UNKNOWN_COLUMN
                ),

                message=(
                    "SQL references "
                    f"'{qualified_reference}', but "
                    f"source '{qualifier}' is not "
                    "available in the current scope "
                    "or any parent scope."
                ),

                object_name=(
                    qualified_reference
                ),

                scope_id=(
                    column.scope_id
                ),
            )
        ]


    def _validate_resolved_external_column(
        self,
        column: ColumnReference,
        table_name: str | None,
        allowed_columns: dict[
            str,
            set[str],
        ],
    ) -> list[
        ValidationIssue
    ]:

        if table_name is None:

            return []


        if (
            table_name
            not in allowed_columns
        ):

            # Unknown-table validation already handles
            # the root issue.

            return []


        if (
            column.name
            in allowed_columns[
                table_name
            ]
        ):

            return []


        qualified_column = (
            f"{table_name}.{column.name}"
        )


        return [

            ValidationIssue(

                code=(
                    ValidationIssueCode
                    .UNKNOWN_COLUMN
                ),

                message=(
                    "Correlated column "
                    f"'{qualified_column}' does not "
                    "exist in the supplied "
                    "GenerationContext."
                ),

                object_name=(
                    qualified_column
                ),

                scope_id=(
                    column.scope_id
                ),
            )
        ]

    def _validate_logical_column(
    self,
    column: ColumnReference,
    scopes: dict[
        int,
        SQLScopeAnalysis,
    ],
    allowed_columns: dict[
        str,
        set[str],
    ],
    scope_output_cache: dict[
        int,
        set[str],
    ],
) -> list[
    ValidationIssue
]:

        current_scope = (
            scopes.get(
                column.scope_id
            )
        )


        if current_scope is None:

            return []


        logical_source = next(
            (
                source
                for source
                in current_scope.sources
                if (
                    source.source_name
                    ==
                    column.qualifier
                    and
                    source.source_kind
                    ==
                    ScopeSourceKind
                    .LOGICAL_SCOPE
                )
            ),
            None,
        )


        if (
            logical_source is None
            or
            logical_source.source_scope_id
            is None
        ):

            return []


        output_columns = (
            self
            ._resolve_scope_output_columns(
                scope_id=(
                    logical_source
                    .source_scope_id
                ),
                scopes=scopes,
                allowed_columns=(
                    allowed_columns
                ),
                cache=(
                    scope_output_cache
                ),
            )
        )


        if (
            column.name
            in output_columns
        ):

            return []


        logical_column = (
            f"{column.qualifier}."
            f"{column.name}"
        )


        return [

            ValidationIssue(

                code=(
                    ValidationIssueCode
                    .UNKNOWN_COLUMN
                ),

                message=(
                    "Logical SQL source "
                    f"'{column.qualifier}' does "
                    f"not expose column "
                    f"'{column.name}'."
                ),

                object_name=(
                    logical_column
                ),

                scope_id=(
                    column.scope_id
                ),
            )
        ]

    # ========================================================
    # ISSUE DEDUPLICATION
    # ========================================================


    def _deduplicate_issues(
        self,
        issues: list[
            ValidationIssue
        ],
    ) -> list[
        ValidationIssue
    ]:

        unique = []

        seen = set()


        for issue in issues:

            key = (
                issue.code,
                issue.object_name,
                issue.scope_id,
            )


            if key in seen:

                continue


            seen.add(
                key
            )

            unique.append(
                issue
            )


        return unique
    def _resolve_scope_output_columns(
    self,
    scope_id: int,
    scopes: dict[
        int,
        SQLScopeAnalysis,
    ],
    allowed_columns: dict[
        str,
        set[str],
    ],
    cache: dict[
        int,
        set[str],
    ],
    visiting: set[int] | None = None,
) -> set[str]:

        if scope_id in cache:

            return cache[
                scope_id
            ]


        if visiting is None:

            visiting = set()


        if scope_id in visiting:

            # Defensive protection against
            # recursive/cyclic scope structures.
            return set()


        scope = scopes.get(
            scope_id
        )


        if scope is None:

            return set()


        visiting = set(
            visiting
        )

        visiting.add(
            scope_id
        )


        output_columns = set(
            scope.output_columns
        )


        # ========================================================
        # STAR EXPANSION
        # ========================================================

        for star_source in (
            scope.star_sources
        ):

            # SELECT *
            if star_source is None:

                sources = (
                    scope.sources
                )

            # SELECT o.*
            else:

                sources = [
                    source
                    for source
                    in scope.sources
                    if (
                        source.source_name
                        ==
                        star_source
                    )
                ]


            for source in sources:

                # ------------------------------------------------
                # PHYSICAL TABLE
                # ------------------------------------------------

                if (
                    source.source_kind
                    ==
                    ScopeSourceKind
                    .PHYSICAL_TABLE
                ):

                    table_name = (
                        source
                        .qualified_table
                    )


                    if (
                        table_name
                        in allowed_columns
                    ):

                        output_columns.update(
                            allowed_columns[
                                table_name
                            ]
                        )


                # ------------------------------------------------
                # LOGICAL SOURCE
                # ------------------------------------------------

                elif (
                    source.source_kind
                    ==
                    ScopeSourceKind
                    .LOGICAL_SCOPE
                    and
                    source.source_scope_id
                    is not None
                ):

                    output_columns.update(

                        self
                        ._resolve_scope_output_columns(

                            scope_id=(
                                source
                                .source_scope_id
                            ),

                            scopes=(
                                scopes
                            ),

                            allowed_columns=(
                                allowed_columns
                            ),

                            cache=(
                                cache
                            ),

                            visiting=(
                                visiting
                            ),
                        )
                    )


        cache[
            scope_id
        ] = output_columns


        return output_columns

    def _build_relationship_index(
    self,
    context: GenerationContext,
) -> dict[
    tuple[str, str],
    list[
        tuple[
            str,
            set[
                frozenset[str]
            ],
        ]
    ],
]:

        index = {}


        for relationship in (
            context.relationships
        ):

            table_pair = (
                self
                ._table_pair_key(
                    relationship.source_table,
                    relationship.target_table,
                )
            )


            condition_pairs = {

                frozenset(
                    (
                        condition
                        .source_column,

                        condition
                        .target_column,
                    )
                )

                for condition
                in relationship.join_conditions
            }


            index.setdefault(
                table_pair,
                [],
            ).append(
                (
                    relationship
                    .relationship_id,

                    condition_pairs,
                )
            )


        return index


    def _table_pair_key(
        self,
        first_table: str,
        second_table: str,
    ) -> tuple[str, str]:

        return tuple(
            sorted(
                (
                    first_table,
                    second_table,
                )
            )
        )

    def _validate_joins(
    self,
    analysis: SQLAnalysis,
    context: GenerationContext,
) -> list[
    ValidationIssue
]:

        issues = []


        # ========================================================
        # JOIN COVERAGE PER SCOPE
        # ========================================================

        joins_by_scope = {}


        for join in analysis.joins:

            joins_by_scope.setdefault(
                join.scope_id,
                [],
            ).append(
                join
            )


        for scope in analysis.scopes:

            source_count = (
                len(
                    scope.sources
                )
            )


            # A scope with one or zero sources
            # requires no join edge.
            expected_join_count = max(
                0,
                source_count - 1,
            )


            actual_join_count = len(
                joins_by_scope.get(
                    scope.scope_id,
                    [],
                )
            )


            if (
                actual_join_count
                <
                expected_join_count
            ):

                issues.append(

                    ValidationIssue(

                        code=(
                            ValidationIssueCode
                            .INVALID_JOIN
                        ),

                        message=(
                            "SQL scope contains "
                            f"{source_count} relation "
                            "sources but only "
                            f"{actual_join_count} "
                            "validated JOIN edge(s). "
                            "Cartesian or ungrounded "
                            "relation combinations are "
                            "not allowed."
                        ),

                        object_name=(
                            "unmatched_relation_source"
                        ),

                        scope_id=(
                            scope.scope_id
                        ),
                    )
                )


        relationship_index = (
            self
            ._build_relationship_index(
                context
            )
        )


        for join in analysis.joins:

            # ====================================================
            # LOGICAL / UNRESOLVED TARGET
            # ====================================================

            if (
                join.target_source_kind
                !=
                ScopeSourceKind
                .PHYSICAL_TABLE
                or
                join.target_table
                is None
            ):

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "JOIN target is a CTE or "
                            "derived logical source. "
                            "Join lineage validation "
                            "for logical sources is not "
                            "supported yet."
                        ),
                    )
                )

                continue

            # ====================================================
            # CROSS JOIN
            # ====================================================

            if join.is_cross:

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "CROSS JOIN is not allowed "
                            "because it does not use a "
                            "retrieved database relationship."
                        ),
                    )
                )

                continue

            # ====================================================
            # USING / NATURAL
            # ====================================================

            if (
                join.uses_using
                or
                join.is_natural
            ):

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "JOIN USING and NATURAL JOIN "
                            "are not accepted because "
                            "relationship columns cannot "
                            "yet be validated explicitly."
                        ),
                    )
                )

                continue


            # ====================================================
            # CONDITION REQUIRED
            # ====================================================

            if (
                join.condition_sql
                is None
            ):

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "JOIN does not contain an "
                            "explicit ON relationship "
                            "condition."
                        ),
                    )
                )

                continue


            # ====================================================
            # BOOLEAN SHAPE
            # ====================================================

            if (
                join.has_disjunction
                or
                join.has_negation
            ):

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "JOIN relationship conditions "
                            "must use deterministic "
                            "conjunctive equality predicates. "
                            "OR and NOT are not supported."
                        ),
                    )
                )

                continue


            # ====================================================
            # COLUMN COMPARISONS REQUIRED
            # ====================================================

            if not join.comparisons:

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "JOIN ON clause does not "
                            "contain a supported "
                            "column-to-column equality."
                        ),
                    )
                )

                continue


            comparisons_by_table = {}

            comparison_failure = False


            for comparison in (
                join.comparisons
            ):

                left = (
                    comparison.left
                )

                right = (
                    comparison.right
                )


                # -----------------------------------------------
                # Require resolved physical columns
                # -----------------------------------------------

                if not (
                    left.source_kind
                    ==
                    ColumnSourceKind
                    .PHYSICAL_TABLE
                    and
                    right.source_kind
                    ==
                    ColumnSourceKind
                    .PHYSICAL_TABLE
                    and
                    left.resolved_table
                    is not None
                    and
                    right.resolved_table
                    is not None
                ):

                    comparison_failure = (
                        True
                    )

                    break


                # -----------------------------------------------
                # Determine which side is the newly joined source
                # -----------------------------------------------

                left_is_target = (
                    left.qualifier
                    ==
                    join.target_source
                )

                right_is_target = (
                    right.qualifier
                    ==
                    join.target_source
                )


                # Exactly one operand must belong to the
                # newly joined relation.
                if (
                    left_is_target
                    ==
                    right_is_target
                ):

                    comparison_failure = (
                        True
                    )

                    break


                if left_is_target:

                    other_table = (
                        right.resolved_table
                    )

                else:

                    other_table = (
                        left.resolved_table
                    )


                left_column = (
                    f"{left.resolved_table}."
                    f"{left.name}"
                )

                right_column = (
                    f"{right.resolved_table}."
                    f"{right.name}"
                )


                comparison_pair = (
                    frozenset(
                        (
                            left_column,
                            right_column,
                        )
                    )
                )


                comparisons_by_table.setdefault(
                    other_table,
                    set(),
                ).add(
                    comparison_pair
                )


            if comparison_failure:

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "JOIN relationship columns "
                            "could not be resolved to "
                            "physical table columns."
                        ),
                    )
                )

                continue


            if not comparisons_by_table:

                issues.append(

                    self._invalid_join_issue(
                        join=join,
                        message=(
                            "JOIN does not connect the "
                            "new relation to another "
                            "physical relation."
                        ),
                    )
                )

                continue


            # ====================================================
            # RELATIONSHIP MATCHING
            # ====================================================

            for (
                other_table,
                actual_conditions,
            ) in (
                comparisons_by_table
                .items()
            ):

                table_pair = (
                    self
                    ._table_pair_key(
                        join.target_table,
                        other_table,
                    )
                )


                candidates = (
                    relationship_index.get(
                        table_pair,
                        []
                    )
                )


                relationship_matches = any(

                    expected_conditions
                    ==
                    actual_conditions

                    for (
                        _,
                        expected_conditions,
                    )
                    in candidates
                )


                if relationship_matches:

                    continue


                issues.append(

                    self._invalid_join_issue(

                        join=join,

                        message=(
                            "JOIN condition does not "
                            "match any retrieved "
                            "relationship between "
                            f"'{join.target_table}' and "
                            f"'{other_table}'."
                        ),
                    )
                )


        return issues

    def _invalid_join_issue(
    self,
    join,
    message: str,
) -> ValidationIssue:

        return ValidationIssue(

            code=(
                ValidationIssueCode
                .INVALID_JOIN
            ),

            message=message,

            object_name=(
                join.condition_sql
                or
                join.sql
            ),

            scope_id=(
                join.scope_id
            ),
        )