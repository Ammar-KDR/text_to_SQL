import re

from textSQL.metadata.models import (
    TableMetadata,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
    TemporalConstraint,
    TemporalResolution,
)


class TemporalDependencyResolver:

    def __init__(
        self,
        metadata_index: MetadataIndex,
    ):

        self.metadata_index = (
            metadata_index
        )


    def resolve(
        self,
        question: str,
        candidates: list[
            RetrievalCandidate
        ],
    ) -> TemporalResolution:

        resolved = list(
            candidates
        )


        period = (
            self._resolve_period(
                question
            )
        )


        if period is None:

            return TemporalResolution(
                candidates=resolved,
                constraints=[],
            )


        date_dimension = (
            self.metadata_index
            .get_table(
                "dim_date"
            )
        )


        if date_dimension is None:

            return TemporalResolution(
                candidates=resolved,
                constraints=[],
            )


        # We need an actual date column.
        #
        # Do not assume date_key contains a
        # YYYYMMDD encoding.
        if not self._has_column(
            date_dimension,
            "full_date",
        ):

            return TemporalResolution(
                candidates=resolved,
                constraints=[],
            )


        # Only use the warehouse date dimension
        # when an already-selected table is
        # directly related to it.
        #
        # fact_sales -> dim_date       ✓
        # payments   -> dim_date       ✗
        if not self._has_direct_date_path(
            resolved,
            date_dimension,
        ):

            return TemporalResolution(
                candidates=resolved,
                constraints=[],
            )


        date_dimension_id = (
            f"table_"
            f"{date_dimension.qualified_name}"
        )


        existing_ids = {

            candidate.object_id

            for candidate
            in resolved
        }


        if (
            date_dimension_id
            not in existing_ids
        ):

            resolved.append(

                RetrievalCandidate(

                    object_id=(
                        date_dimension_id
                    ),

                    object_type="table",

                    object_name=(
                        date_dimension.name
                    ),

                    score=1.0,

                    source="temporal",
                )
            )


        constraint = TemporalConstraint(

            phrase=(
                period[
                    "phrase"
                ]
            ),

            column=(
                f"{date_dimension.qualified_name}"
                ".full_date"
            ),

            start_expression=(
                period[
                    "start_expression"
                ]
            ),

            end_expression=(
                period[
                    "end_expression"
                ]
            ),

            start_inclusive=True,

            end_inclusive=False,
        )


        return TemporalResolution(

            candidates=resolved,

            constraints=[
                constraint
            ],
        )


    # ========================================================
    # PERIOD RESOLUTION
    # ========================================================


    def _resolve_period(
        self,
        question: str,
    ) -> dict | None:

        normalized = (
            question
            .lower()
            .strip()
        )


        period_rules = [

            # ------------------------------------------------
            # PREVIOUS / LAST
            # ------------------------------------------------

            (
                r"\b(?:last|previous)\s+week\b",

                "week",

                "1 week",
            ),

            (
                r"\b(?:last|previous)\s+month\b",

                "month",

                "1 month",
            ),

            (
                r"\b(?:last|previous)\s+quarter\b",

                "quarter",

                "3 months",
            ),

            (
                r"\b(?:last|previous)\s+year\b",

                "year",

                "1 year",
            ),
        ]


        for (
            pattern,
            grain,
            interval,
        ) in period_rules:

            match = re.search(
                pattern,
                normalized,
            )


            if match is None:
                continue


            return {

                "phrase":
                    match.group(0),

                "start_expression":
                    (
                        f"DATE_TRUNC("
                        f"'{grain}', "
                        f"CURRENT_DATE"
                        f") - "
                        f"INTERVAL "
                        f"'{interval}'"
                    ),

                "end_expression":
                    (
                        f"DATE_TRUNC("
                        f"'{grain}', "
                        f"CURRENT_DATE"
                        f")"
                    ),
            }


        # ----------------------------------------------------
        # CURRENT / THIS
        # ----------------------------------------------------

        current_rules = [

            (
                r"\b(?:this|current)\s+week\b",
                "week",
                "1 week",
            ),

            (
                r"\b(?:this|current)\s+month\b",
                "month",
                "1 month",
            ),

            (
                r"\b(?:this|current)\s+quarter\b",
                "quarter",
                "3 months",
            ),

            (
                r"\b(?:this|current)\s+year\b",
                "year",
                "1 year",
            ),
        ]


        for (
            pattern,
            grain,
            interval,
        ) in current_rules:

            match = re.search(
                pattern,
                normalized,
            )


            if match is None:
                continue


            return {

                "phrase":
                    match.group(0),

                "start_expression":
                    (
                        f"DATE_TRUNC("
                        f"'{grain}', "
                        f"CURRENT_DATE"
                        f")"
                    ),

                "end_expression":
                    (
                        f"DATE_TRUNC("
                        f"'{grain}', "
                        f"CURRENT_DATE"
                        f") + "
                        f"INTERVAL "
                        f"'{interval}'"
                    ),
            }


        return None


    # ========================================================
    # GRAPH CHECK
    # ========================================================


    def _has_direct_date_path(
        self,
        candidates: list[
            RetrievalCandidate
        ],
        date_dimension: TableMetadata,
    ) -> bool:

        for candidate in candidates:

            if (
                candidate.object_type
                !=
                "table"
            ):
                continue


            table = (
                self.metadata_index
                .get_object(
                    candidate.object_id
                )
            )


            if not isinstance(
                table,
                TableMetadata,
            ):
                continue


            if (
                table.qualified_name
                ==
                date_dimension.qualified_name
            ):

                return True


            path = (
                self.metadata_index
                .graph
                .find_path(

                    table.qualified_name,

                    date_dimension
                    .qualified_name,
                )
            )


            if (
                path is not None
                and
                len(path) == 1
            ):

                return True


        return False


    @staticmethod
    def _has_column(
        table: TableMetadata,
        column_name: str,
    ) -> bool:

        return any(

            column.name
            ==
            column_name

            for column
            in table.columns
        )