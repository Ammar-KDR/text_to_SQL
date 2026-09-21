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

        self.metadata_index = metadata_index



    def resolve(
        self,
        candidates: list[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:

        resolved = list(
            candidates
        )


        existing_ids = {
            candidate.object_id
            for candidate in resolved
        }


        for candidate in candidates:


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

                self._add_required_tables(
                    obj,
                    resolved,
                    existing_ids,
                )


        return resolved

    def _add_required_tables(
        self,
        metric: MetricMetadata,
        resolved: list[RetrievalCandidate],
        existing_ids: set[str],
    ):


        for table_name in metric.required_tables:


            table_id = (
                f"table_{table_name}"
            )


            if table_id in existing_ids:

                continue


            table = (
                self.metadata_index
                .tables
                .get(
                    table_name
                )
            )


            if table is None:

                continue


            resolved.append(

                RetrievalCandidate(

                    object_id=table_id,

                    object_type="table",

                    object_name=table_name,

                    score=1.0,

                    source="dependency",

                )
            )


            existing_ids.add(
                table_id
            )