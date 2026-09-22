from textSQL.retrieval.model import (
    RetrievalCandidate,
)

from .index import (
    MetadataIndex,
)

from textSQL.metadata.models import (
    MetricMetadata,
)


class DependencyResolver:


    def __init__(
        self,
        metadata_index: MetadataIndex,
    ):

        self.metadata_index = (
            metadata_index
        )


    def resolve(
        self,
        candidates: list[
            RetrievalCandidate
        ],
    ) -> list[
        RetrievalCandidate
    ]:

        resolved = list(
            candidates
        )


        existing_ids = {

            candidate.object_id

            for candidate
            in resolved
        }


        visited_metrics = set()


        for candidate in list(
            candidates
        ):

            obj = (
                self.metadata_index
                .get_object(
                    candidate.object_id
                )
            )


            if isinstance(
                obj,
                MetricMetadata,
            ):

                self._resolve_metric(

                    metric=obj,

                    resolved=resolved,

                    existing_ids=
                        existing_ids,

                    visited_metrics=
                        visited_metrics,
                )


        return resolved


    def _resolve_metric(
        self,
        metric: MetricMetadata,
        resolved: list[
            RetrievalCandidate
        ],
        existing_ids: set[str],
        visited_metrics: set[str],
    ):

        metric_name = (
            metric.name.lower()
        )


        if (
            metric_name
            in visited_metrics
        ):
            return


        visited_metrics.add(
            metric_name
        )


        self._add_required_metrics(

            metric,

            resolved,

            existing_ids,

            visited_metrics,
        )


        self._add_required_tables(

            metric,

            resolved,

            existing_ids,
        )


    def _add_required_metrics(
        self,
        metric: MetricMetadata,
        resolved: list[
            RetrievalCandidate
        ],
        existing_ids: set[str],
        visited_metrics: set[str],
    ):

        for dependency_name in (
            metric.required_metrics
        ):

            dependency = (
                self.metadata_index
                .metrics
                .get(
                    dependency_name.lower()
                )
            )


            if dependency is None:
                continue


            dependency_id = (
                f"metric_{dependency.name}"
            )


            if (
                dependency_id
                not in existing_ids
            ):

                resolved.append(

                    RetrievalCandidate(

                        object_id=
                            dependency_id,

                        object_type=
                            "metric",

                        object_name=
                            dependency.name,

                        score=
                            1.0,

                        source=
                            "dependency",
                    )
                )


                existing_ids.add(
                    dependency_id
                )


            self._resolve_metric(

                metric=
                    dependency,

                resolved=
                    resolved,

                existing_ids=
                    existing_ids,

                visited_metrics=
                    visited_metrics,
            )


    def _add_required_tables(
        self,
        metric: MetricMetadata,
        resolved: list[
            RetrievalCandidate
        ],
        existing_ids: set[str],
    ):

        for table_name in (
            metric.required_tables
        ):

            table = (
                self.metadata_index
                .get_table(
                    table_name
                )
            )


            if table is None:
                continue


            table_id = (
                f"table_"
                f"{table.qualified_name}"
            )


            if (
                table_id
                in existing_ids
            ):
                continue


            resolved.append(

                RetrievalCandidate(

                    object_id=
                        table_id,

                    object_type=
                        "table",

                    object_name=
                        table.name,

                    score=
                        1.0,

                    source=
                        "dependency",
                )
            )


            existing_ids.add(
                table_id
            )