from textSQL.database.connection import (
    engine,
)

from textSQL.metadata.config import (
    load_metadata_config,
)

from textSQL.metadata.extractor import (
    extract_database_metadata,
)

from textSQL.embeddings.encoder import (
    BGEEncoder,
)

from textSQL.embeddings.service import (
    EmbeddingService,
)

from textSQL.indexing.vector_indexer import (
    VectorIndexer,
)

from textSQL.vectorstore.qdrant import (
    QdrantVectorStore,
)


config = load_metadata_config(
    "src/textSQL/config/metadata_config.yaml"
)


metadata = extract_database_metadata(
    engine,
    config,
)


encoder = BGEEncoder()


embedding_service = EmbeddingService(
    encoder
)


vector_store = QdrantVectorStore()


print(
    "Deleting stale metadata collection..."
)

vector_store.delete_collection()


print(
    "Rebuilding metadata index..."
)

indexer = VectorIndexer(
    embedding_service,
    vector_store,
)


indexer.index(
    metadata
)


print(
    "Metadata index rebuilt successfully."
)