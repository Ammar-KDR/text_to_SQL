from textSQL.retrieval.model import (
    RetrievalCandidate,
)

from .index import (
    MetadataIndex,
)

from textSQL.metadata.graph import (
    SchemaGraph,
)


class GraphRetriever:


    def __init__(
        self,
        metadata_index: MetadataIndex,
        graph: SchemaGraph,
    ):

        self.metadata_index = (
            metadata_index
        )

        self.graph = graph


    def retrieve(
    self,
    candidates: list[RetrievalCandidate],
) -> list[RetrievalCandidate]:

        tables = [

            self._table_identity(
                candidate
            )

            for candidate
            in candidates

            if (
                candidate.object_type
                ==
                "table"
            )
        ]


        # Remove duplicate table identities
        # while preserving their order.
        tables = list(
            dict.fromkeys(
                tables
            )
        )


        relationship_candidates = {}


        for i, source in enumerate(
            tables
        ):

            for target in tables[
                i + 1:
            ]:

                path = (
                    self.graph
                    .find_path(
                        source,
                        target,
                    )
                )


                if not path:
                    continue


                for relationship in path:

                    relationship_id = (
                        relationship.object_id
                    )


                    # The same edge may occur
                    # in multiple table-pair paths.
                    #
                    # It must only become one
                    # retrieval candidate.
                    if (
                        relationship_id
                        in relationship_candidates
                    ):
                        continue


                    relationship_candidates[
                        relationship_id
                    ] = RetrievalCandidate(

                        object_id=
                            relationship_id,

                        object_type=
                            "relationship",

                        object_name=(

                            f"{relationship.source_qualified_name}"
                            f" -> "
                            f"{relationship.target_qualified_name}"

                        ),

                        score=
                            1.0,

                        source=
                            "graph",
                    )


        return list(
            relationship_candidates.values()
        )


    def _table_identity(
        self,
        candidate: RetrievalCandidate,
    ) -> str:

        prefix = "table_"


        if (
            candidate.object_id
            .startswith(prefix)
        ):

            return (
                candidate.object_id[
                    len(prefix):
                ]
            )


        return candidate.object_name