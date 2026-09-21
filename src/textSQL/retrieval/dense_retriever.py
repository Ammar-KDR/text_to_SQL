from textSQL.retrieval.query_encoder import (
    QueryEncoder,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
    RetrievalTrace,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.vectorstore.base import (
    VectorStore,
)
from textSQL.metadata.models import (
    TableMetadata,
    MetricMetadata,
    RelationshipMetadata,
)



class DenseRetriever:


    def __init__(
        self,
        query_encoder: QueryEncoder,
        vector_store: VectorStore,
        metadata_index: MetadataIndex,
    ):

        self.query_encoder = query_encoder

        self.vector_store = vector_store

        self.metadata_index = metadata_index



    def retrieve(
    self,
    question: str,
    limit: int = 5,
) -> list[RetrievalCandidate]:


        query_vector = (
            self.query_encoder
            .encode_query(question)
        )


        results = (
            self.vector_store
            .search(
                query_vector,
                limit,
            )
        )


        candidates = []


        for result in results:

            metadata_id = (
                result.payload["metadata_id"]
            )


            candidates.append(

                RetrievalCandidate(

                    object_id=metadata_id,

                    object_type=
                    result.payload["object_type"],

                    object_name=
                    result.payload["object_name"],

                    score=result.score,

                    source="dense",

                )
            )


        return candidates
   