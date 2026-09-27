import json

from textSQL.generation.errors import (
    InvalidStructuredOutputError,
)


class GenerationOutputNormalizer:

    STATUS_PREFIXES = {

        "GENERATED:":
            "generated",

        "CLARIFICATION_REQUIRED:":
            "clarification_required",

        "UNANSWERABLE:":
            "unanswerable",
    }


    def normalize(
    self,
    raw_response: str,
) -> str:

            try:

                data = json.loads(
                    raw_response
                )

            except json.JSONDecodeError as exc:

                raise (
                    InvalidStructuredOutputError(
                        message=(
                            "LLM returned invalid JSON."
                        ),
                        raw_response=(
                            raw_response
                        ),
                        validation_errors=[
                            str(exc)
                        ],
                    )
                ) from exc


            # ========================================================
            # NORMALIZE EMPTY SQL
            # ========================================================

            sql = data.get(
                "sql"
            )


            if (
                isinstance(
                    sql,
                    str,
                )
                and
                not sql.strip()
            ):

                data["sql"] = None


            # ========================================================
            # NORMALIZE OPTIONAL LISTS
            # ========================================================

            for field in (
                "tables_used",
                "columns_used",
                "assumptions",
                "clarification_options",
            ):

                if data.get(field) is None:

                    data[field] = []

            valid_statuses = {
                "generated",
                "clarification_required",
                "unanswerable",
            }


            original_status = (
                data.get(
                    "status"
                )
            )


            explanation = (
                data.get(
                    "explanation"
                )
            )


            # ========================================================
            # REPAIR ELIGIBILITY
            # ========================================================
            #
            # The normalizer repairs contradictions.
            # It does NOT manufacture a valid result
            # from incomplete or malformed output.
            #
            # Examples that must remain invalid:
            #
            # {"status": "generated"}
            #
            # {"status": "something_invalid"}
            #
            # {"sql": null}
            #
            # These should reach Pydantic unchanged
            # and fail validation.

            if (
                original_status
                not in valid_statuses
            ):

                return json.dumps(
                    data
                )


            if (
                not isinstance(
                    explanation,
                    str,
                )
                or
                not explanation.strip()
            ):

                return json.dumps(
                    data
    )


            # ========================================================
            # STRUCTURAL STATUS REPAIR
            # ========================================================

            sql = data.get(
                "sql"
            )

            clarification_question = (
                data.get(
                    "clarification_question"
                )
            )


            # Actual SQL exists.
            if (
                isinstance(
                    sql,
                    str,
                )
                and
                sql.strip()
            ):

                data["status"] = (
                    "generated"
                )


            # No SQL, but model gave us an explicit
            # clarification question.
            elif (
                clarification_question
                and
                str(
                    clarification_question
                ).strip()
            ):

                data["status"] = (
                    "clarification_required"
                )

                data["sql"] = None

                data["tables_used"] = []

                data["columns_used"] = []


            # No SQL and no clarification question.
            #
            # There is no executable answer and no
            # clarification interaction to perform.
            else:

                data["status"] = (
                    "unanswerable"
                )

                data["sql"] = None

                data["tables_used"] = []

                data["columns_used"] = []

                data[
                    "clarification_question"
                ] = None

                data[
                    "clarification_options"
                ] = []


            self._normalize_explanation_prefix(
                data
            )

            return json.dumps(
                data
            )
    def _status_from_explanation(
        self,
        explanation: str,
    ) -> str | None:

        normalized = (
            explanation
            .strip()
            .upper()
        )


        for (
            prefix,
            status,
        ) in self.STATUS_PREFIXES.items():

            if normalized.startswith(
                prefix
            ):

                return status


        return None


    def _repair_unanswerable(
        self,
        data: dict,
    ) -> None:

        sql = data.get(
            "sql"
        )


        if (
            sql is not None
            and
            str(sql).strip()
        ):

            # Model produced actual SQL while claiming
            # UNANSWERABLE.
            #
            # Too contradictory to repair safely.
            return


        data["status"] = (
            "unanswerable"
        )

        data["sql"] = None

        data["tables_used"] = []

        data["columns_used"] = []

        data[
            "clarification_question"
        ] = None

        data[
            "clarification_options"
        ] = []


    def _repair_clarification(
        self,
        data: dict,
    ) -> None:

        sql = data.get(
            "sql"
        )


        if (
            sql is not None
            and
            str(sql).strip()
        ):

            return


        question = (
            data.get(
                "clarification_question"
            )
        )


        # We cannot invent a missing question.
        if not question:

            return


        data["status"] = (
            "clarification_required"
        )

        data["sql"] = None

        data["tables_used"] = []

        data["columns_used"] = []


    def _repair_generated(
        self,
        data: dict,
    ) -> None:

        sql = data.get(
            "sql"
        )


        # Can't turn something into GENERATED
        # without actual SQL.
        if (
            not sql
            or
            not str(sql).strip()
        ):

            return


        data["status"] = (
            "generated"
        )


    def _normalize_empty_sql(
        self,
        data: dict,
    ) -> None:

        sql = data.get(
            "sql"
        )


        if (
            isinstance(
                sql,
                str,
            )
            and
            not sql.strip()
        ):

            data["sql"] = None
    def _normalize_explanation_prefix(
    self,
    data: dict,
) -> None:

        status = data.get(
            "status"
        )

        explanation = str(
            data.get(
                "explanation",
                "",
            )
        ).strip()


        prefixes = {

            "generated":
                "GENERATED:",

            "clarification_required":
                "CLARIFICATION_REQUIRED:",

            "unanswerable":
                "UNANSWERABLE:",
        }


        expected_prefix = (
            prefixes.get(
                status
            )
        )


        if expected_prefix is None:
            return


        # Remove an existing status prefix,
        # even if the model supplied the wrong one.

        for prefix in (
            prefixes.values()
        ):

            if (
                explanation
                .upper()
                .startswith(prefix)
            ):

                explanation = (
                    explanation[
                        len(prefix):
                    ]
                    .strip()
                )

                break


        data["explanation"] = (

            f"{expected_prefix} "
            f"{explanation}"

        ).strip()