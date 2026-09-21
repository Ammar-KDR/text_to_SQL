from textSQL.metadata.models import (
    DatabaseMetadata,
)

from textSQL.embeddings.service import (
    EmbeddingService,
)

from textSQL.vectorstore.base import (
    VectorStore,
)



class VectorIndexer:
    """
    Builds the vector index from database metadata.

    Flow:

    DatabaseMetadata
            |
            ↓
    EmbeddingService
            |
            ↓
    Documents + Vectors
            |
            ↓
    VectorStore
    """


    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ):

        self.embedding_service = embedding_service

        self.vector_store = vector_store



    def index(
        self,
        metadata: DatabaseMetadata,
    ):

        documents, vectors = (
            self.embedding_service
            .create_embeddings(
                metadata
            )
        )


        self.vector_store.upsert(
            documents,
            vectors,
        )