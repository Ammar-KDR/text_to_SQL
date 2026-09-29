from sqlglot import exp

from textSQL.validation.models import (
    ParsedSQL,
    ValidationIssueCode,
    ValidationIssue,
    SafetyValidationResult,
)


class SafetyPolicy:
    """
    Enforces structural SQL safety rules.

    Only read-only query expressions are
    allowed.

    Responsibilities:

    - reject non-query root statements
    - reject write operations hidden inside
      an otherwise read-only query
    - reject SELECT INTO
    - reject row-locking SELECT statements
    - reject sequence-mutating functions

    This class does NOT:

    - validate tables or columns
    - validate joins
    - enforce complexity limits
    - add LIMIT
    - inspect EXPLAIN plans
    - execute SQL
    """

    UNSAFE_SEQUENCE_FUNCTIONS = {
        "nextval",
        "setval",
    }


    # ========================================================
    # PUBLIC API
    # ========================================================


    def validate(
        self,
        parsed_sql: ParsedSQL,
    ) -> SafetyValidationResult:

        ast = parsed_sql.ast

        issues = []


        # ====================================================
        # ROOT STATEMENT ALLOWLIST
        # ====================================================

        if not isinstance(
            ast,
            exp.Query,
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .DISALLOWED_STATEMENT
                    ),

                    message=(
                        "Only read-only query "
                        "statements are allowed. "
                        f"Received root statement "
                        f"'{ast.key}'."
                    ),

                    object_name=(
                        ast.key
                    ),
                )
            )


            return SafetyValidationResult(
                valid=False,
                issues=issues,
            )


        # ====================================================
        # NESTED WRITE / CONTROL OPERATIONS
        # ====================================================

        issues.extend(
            self._find_disallowed_nodes(
                ast
            )
        )


        # ====================================================
        # SELECT INTO
        # ====================================================

        issues.extend(
            self._find_select_into(
                ast
            )
        )


        # ====================================================
        # ROW LOCKS
        # ====================================================

        issues.extend(
            self._find_row_locks(
                ast
            )
        )


        # ====================================================
        # SEQUENCE MUTATION
        # ====================================================

        issues.extend(
            self._find_sequence_mutations(
                ast
            )
        )


        issues = (
            self._deduplicate_issues(
                issues
            )
        )


        return SafetyValidationResult(

            valid=(
                len(issues)
                ==
                0
            ),

            issues=issues,
        )


    # ========================================================
    # NESTED DISALLOWED OPERATIONS
    # ========================================================


    def _find_disallowed_nodes(
        self,
        ast: exp.Expression,
    ) -> list[
        ValidationIssue
    ]:

        issues = []


        disallowed_types = (

            # DML
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Merge,
            exp.Copy,

            # DDL
            exp.Create,
            exp.Alter,
            exp.Drop,
            exp.TruncateTable,

            # Session / privilege / transaction
            exp.Set,
            exp.Grant,
            exp.Revoke,
            exp.Transaction,
            exp.Commit,
            exp.Rollback,

            # Generic or procedural commands
            exp.Command,
            exp.Execute,
        )


        for node in ast.walk():

            if node is ast:

                continue


            if not isinstance(
                node,
                disallowed_types,
            ):

                continue


            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .DISALLOWED_STATEMENT
                    ),

                    message=(
                        "Read-only query contains "
                        "a prohibited operation: "
                        f"'{node.key}'."
                    ),

                    object_name=(
                        node.key
                    ),
                )
            )


        return issues


    # ========================================================
    # SELECT INTO
    # ========================================================


    def _find_select_into(
        self,
        ast: exp.Expression,
    ) -> list[
        ValidationIssue
    ]:

        issues = []


        for into in ast.find_all(
            exp.Into
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .SELECT_INTO
                    ),

                    message=(
                        "SELECT INTO is prohibited "
                        "because it creates or writes "
                        "a database relation."
                    ),

                    object_name=(
                        into.sql(
                            dialect="postgres"
                        )
                    ),
                )
            )


        return issues


    # ========================================================
    # ROW LOCKING
    # ========================================================


    def _find_row_locks(
        self,
        ast: exp.Expression,
    ) -> list[
        ValidationIssue
    ]:

        issues = []


        for lock in ast.find_all(
            exp.Lock
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .ROW_LOCK
                    ),

                    message=(
                        "Row-locking SELECT clauses "
                        "are prohibited."
                    ),

                    object_name=(
                        lock.sql(
                            dialect="postgres"
                        )
                    ),
                )
            )


        return issues


    # ========================================================
    # SEQUENCE MUTATION
    # ========================================================


    def _find_sequence_mutations(
        self,
        ast: exp.Expression,
    ) -> list[
        ValidationIssue
    ]:

        issues = []


        # ----------------------------------------------------
        # PostgreSQL nextval(...) / setval(...)
        # ----------------------------------------------------

        for function in ast.find_all(
            exp.Anonymous
        ):

            function_name = (
                function.name
                .lower()
            )


            if (
                function_name
                not in
                self.UNSAFE_SEQUENCE_FUNCTIONS
            ):

                continue


            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .SEQUENCE_MUTATION
                    ),

                    message=(
                        "Sequence-mutating function "
                        f"'{function_name}' is "
                        "prohibited."
                    ),

                    object_name=(
                        function_name
                    ),
                )
            )


        # ----------------------------------------------------
        # Defensive support for dialects / AST forms using
        # NEXT VALUE FOR.
        # ----------------------------------------------------

        for _ in ast.find_all(
            exp.NextValueFor
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .SEQUENCE_MUTATION
                    ),

                    message=(
                        "Sequence mutation through "
                        "NEXT VALUE FOR is prohibited."
                    ),

                    object_name=(
                        "next_value_for"
                    ),
                )
            )


        return issues


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