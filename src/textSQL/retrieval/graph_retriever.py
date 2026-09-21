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

        self.metadata_index = metadata_index

        self.graph = graph



    def retrieve(
        self,
        candidates: list[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:


        tables = [

            candidate.object_name

            for candidate in candidates

            if candidate.object_type == "table"

        ]


        relationships = []


        for i, source in enumerate(tables):

            for target in tables[i + 1:]:


                path = self.graph.find_path(
                    source,
                    target,
                )


                if not path:

                    continue


                for relationship in path:

                    relationship_id = (
                        "relationship_"
                        f"{relationship.source_table}_"
                        f"{relationship.target_table}"
                    )


                    relationships.append(

                        RetrievalCandidate(

                            object_id=
                            relationship_id,

                            object_type=
                            "relationship",

                            object_name=
                            relationship_id,

                            score=1.0,

                            source=
                            "graph",

                        )
                    )


        return relationships