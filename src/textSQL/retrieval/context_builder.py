from textSQL.retrieval.model import (
    FusedCandidate,
    RetrievalTrace,
    RetrievedContext
)



from .index import (
    MetadataIndex,
)

from textSQL.metadata.models import (
    TableMetadata,
    MetricMetadata,
    RelationshipMetadata,
)



class ContextBuilder:


    def __init__(
        self,
        metadata_index: MetadataIndex,
    ):

        self.metadata_index = metadata_index



    def build(
        self,
        question: str,
        candidates: list[FusedCandidate],
    ) -> RetrievedContext:


        tables = []

        metrics = []

        relationships = []

        trace = []


        for candidate in candidates:


            metadata_object = (
                self.metadata_index
                .get_object(
                    candidate.object_id
                )
            )


            if metadata_object is None:

                continue



            if isinstance(
                metadata_object,
                TableMetadata,
            ):

                tables.append(
                    metadata_object
                )


            elif isinstance(
                metadata_object,
                MetricMetadata,
            ):

                metrics.append(
                    metadata_object
                )


            elif isinstance(
                metadata_object,
                RelationshipMetadata,
            ):

                relationships.append(
                    metadata_object
                )



            trace.append(

                RetrievalTrace(

                    object_type=
                    candidate.object_type,

                    object_name=
                    candidate.object_name,

                    score=
                    candidate.rrf_score,

                )

            )


        return RetrievedContext(

            question=question,

            tables=tables,

            metrics=metrics,

            relationships=relationships,

            join_paths=[],

            trace=trace,

        )