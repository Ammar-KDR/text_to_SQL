import json
from typing import Any

from sqlalchemy.engine import (
    Engine,
)

from textSQL.validation.errors import (
    PlannerExplainError,
)

from textSQL.validation.models import (
    PlannerEstimate,
    PlannerValidationResult,
    ValidationIssue,
    ValidationIssueCode,
)


class PostgresExplainAnalyzer:
    """
    Runs PostgreSQL EXPLAIN without ANALYZE and
    extracts deterministic planner estimates.

    This component extracts facts only.

    It does NOT decide whether a plan is allowed.
    """

    EXPLAIN_PREFIX = (
        "EXPLAIN (FORMAT JSON) "
    )


    def __init__(
        self,
        engine: Engine,
    ):

        self.engine = engine


    def analyze(
        self,
        sql: str,
    ) -> PlannerEstimate:

        if not sql.strip():

            raise PlannerExplainError(
                message=(
                    "Cannot EXPLAIN empty SQL."
                ),
                sql=sql,
            )


        try:

            with (
                self.engine.connect()
                as connection
            ):

                transaction = (
                    connection.begin()
                )


                try:

                    result = (
                        connection
                        .exec_driver_sql(
                            self.EXPLAIN_PREFIX
                            +
                            sql
                        )
                    )


                    raw_plan = (
                        result.scalar_one()
                    )


                    estimate = (
                        self
                        ._extract_estimate(
                            raw_plan=(
                                raw_plan
                            ),
                            sql=sql,
                        )
                    )


                finally:

                    transaction.rollback()


        except PlannerExplainError:

            raise


        except Exception as exc:

            raise PlannerExplainError(

                message=(
                    "PostgreSQL EXPLAIN failed."
                ),

                sql=sql,

            ) from exc


        return estimate


    def _extract_estimate(
        self,
        raw_plan: Any,
        sql: str,
    ) -> PlannerEstimate:

        payload = (
            self._decode_payload(
                raw_plan=raw_plan,
                sql=sql,
            )
        )


        # PostgreSQL FORMAT JSON normally returns:
        #
        # [
        #     {
        #         "Plan": {...}
        #     }
        # ]

        if isinstance(
            payload,
            list,
        ):

            if (
                len(payload)
                !=
                1
                or
                not isinstance(
                    payload[0],
                    dict,
                )
            ):

                raise PlannerExplainError(

                    message=(
                        "Unexpected PostgreSQL "
                        "EXPLAIN JSON structure."
                    ),

                    sql=sql,
                )


            document = (
                payload[0]
            )


        elif isinstance(
            payload,
            dict,
        ):

            # Defensive compatibility in case
            # the DB driver exposes the single
            # JSON document directly.

            document = payload


        else:

            raise PlannerExplainError(

                message=(
                    "Unexpected PostgreSQL "
                    "EXPLAIN payload type."
                ),

                sql=sql,
            )


        root_plan = (
            document.get(
                "Plan"
            )
        )


        if not isinstance(
            root_plan,
            dict,
        ):

            raise PlannerExplainError(

                message=(
                    "PostgreSQL EXPLAIN response "
                    "does not contain a Plan."
                ),

                sql=sql,
            )


        try:

            total_cost = float(
                root_plan[
                    "Total Cost"
                ]
            )

            root_plan_rows = int(
                root_plan[
                    "Plan Rows"
                ]
            )


        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise PlannerExplainError(

                message=(
                    "PostgreSQL EXPLAIN Plan "
                    "contains invalid cost or "
                    "row estimates."
                ),

                sql=sql,

            ) from exc


        (
            max_plan_rows,
            node_count,
        ) = (
            self
            ._walk_plan_tree(
                plan=root_plan,
                sql=sql
            )
        )


        return PlannerEstimate(

            total_cost=total_cost,

            root_plan_rows=(
                root_plan_rows
            ),

            max_plan_rows=(
                max_plan_rows
            ),

            node_count=(
                node_count
            ),
        )


    def _decode_payload(
        self,
        raw_plan: Any,
        sql: str,
    ) -> Any:

        if isinstance(
            raw_plan,
            str,
        ):

            try:

                return json.loads(
                    raw_plan
                )

            except json.JSONDecodeError as exc:

                raise PlannerExplainError(

                    message=(
                        "PostgreSQL EXPLAIN "
                        "returned invalid JSON."
                    ),

                    sql=sql,

                ) from exc


        return raw_plan


    def _walk_plan_tree(
    self,
    plan: dict,
    sql: str,
) -> tuple[
    int,
    int,
    ]:
        """
        Recursively walk a PostgreSQL EXPLAIN plan tree.

        Returns:
            tuple[int, int]:
                (
                    maximum Plan Rows found
                    anywhere in the tree,

                    total number of plan nodes,
                )
        """

        # ========================================================
        # CURRENT NODE ROW ESTIMATE
        # ========================================================

        try:

            current_rows = int(
                plan[
                    "Plan Rows"
                ]
            )

        except (
            KeyError,
            TypeError,
            ValueError,
        ) as exc:

            raise PlannerExplainError(

                message=(
                    "A PostgreSQL plan node "
                    "does not contain a valid "
                    "Plan Rows estimate."
                ),

                sql=sql,

            ) from exc


        max_rows = (
            current_rows
        )

        node_count = 1


        # ========================================================
        # CHILD PLAN NODES
        # ========================================================

        children = (
            plan.get(
                "Plans",
                [],
            )
        )


        if children is None:

            children = []


        if not isinstance(
            children,
            list,
        ):

            raise PlannerExplainError(

                message=(
                    "A PostgreSQL plan node "
                    "contains an invalid Plans "
                    "collection."
                ),

                sql=sql,
            )


        # ========================================================
        # RECURSIVE WALK
        # ========================================================

        for child in children:

            if not isinstance(
                child,
                dict,
            ):

                raise PlannerExplainError(

                    message=(
                        "A PostgreSQL child "
                        "plan is invalid."
                    ),

                    sql=sql,
                )


            (
                child_max_rows,
                child_node_count,
            ) = (
                self
                ._walk_plan_tree(
                    plan=child,
                    sql=sql,
                )
            )


            max_rows = max(
                max_rows,
                child_max_rows,
            )


            node_count += (
                child_node_count
            )


        return (
            max_rows,
            node_count,
        )


class PlannerPolicy:
    """
        Applies configured thresholds to planner facts.

        Threshold values are intentionally supplied by
        configuration rather than invented here.
        """


    def __init__(
        self,
        max_total_cost: float,
        max_plan_rows: int,
    ):

        if max_total_cost <= 0:

            raise ValueError(
                "max_total_cost must "
                "be greater than 0"
            )


        if max_plan_rows <= 0:

            raise ValueError(
                "max_plan_rows must "
                "be greater than 0"
            )


        self.max_total_cost = (
            max_total_cost
        )

        self.max_plan_rows = (
            max_plan_rows
        )


    def validate(
        self,
        estimate: PlannerEstimate,
    ) -> PlannerValidationResult:

        issues = []


        # ====================================================
        # TOTAL PLANNER COST
        # ====================================================

        if (
            estimate.total_cost
            >
            self.max_total_cost
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .PLANNER_COST_EXCEEDED
                    ),

                    message=(
                        "PostgreSQL estimated "
                        f"total cost "
                        f"{estimate.total_cost}, "
                        "which exceeds the "
                        "configured maximum of "
                        f"{self.max_total_cost}."
                    ),

                    object_name=str(
                        estimate.total_cost
                    ),
                )
            )


        # ====================================================
        # ESTIMATED PLAN ROWS
        # ====================================================

        if (
            estimate.max_plan_rows
            >
            self.max_plan_rows
        ):

            issues.append(

                ValidationIssue(

                    code=(
                        ValidationIssueCode
                        .PLANNER_ROWS_EXCEEDED
                    ),

                    message=(
                        "PostgreSQL estimated "
                        f"up to "
                        f"{estimate.max_plan_rows} "
                        "rows at a plan node, "
                        "which exceeds the "
                        "configured maximum of "
                        f"{self.max_plan_rows}."
                    ),

                    object_name=str(
                        estimate.max_plan_rows
                    ),
                )
            )


        return PlannerValidationResult(

            valid=(
                len(issues)
                ==
                0
            ),

            estimate=estimate,

            issues=issues,
        )