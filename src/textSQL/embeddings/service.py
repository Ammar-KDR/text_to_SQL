from textSQL.metadata.models import DatabaseMetadata

from .builder import (
    MetadataEmbeddingBuilder,
)

from .encoder import (
    EmbeddingEncoder,
)

from .model import (
    EmbeddingDocument,
)


class EmbeddingService:


    def __init__(
        self,
        encoder: EmbeddingEncoder,
    ):

        self.encoder = encoder



    def create_embeddings(
        self,
        metadata: DatabaseMetadata,
    ):

        documents = (
            MetadataEmbeddingBuilder(
                metadata
            )
            .build()
        )


        vectors = self.encoder.encode(
            [
                document.content
                for document in documents
            ]
        )


        return documents, vectors