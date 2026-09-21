from textSQL.indexing.vector_indexer import (
    VectorIndexer,
)


class FakeEmbeddingService:


    def create_embeddings(
        self,
        metadata,
    ):

        return (
            ["doc1"],
            [
                [
                    0.1,
                    0.2,
                    0.3,
                ]
            ],
        )



class FakeVectorStore:


    def __init__(self):

        self.documents = None

        self.vectors = None



    def upsert(
        self,
        documents,
        vectors,
    ):

        self.documents = documents

        self.vectors = vectors



def test_vector_indexer():

    embedding_service = (
        FakeEmbeddingService()
    )


    vector_store = (
        FakeVectorStore()
    )


    indexer = VectorIndexer(

        embedding_service,

        vector_store,

    )


    indexer.index(
        metadata=None
    )


    assert (
        vector_store.documents
        == ["doc1"]
    )


    assert (
        vector_store.vectors[0]
        ==
        [
            0.1,
            0.2,
            0.3,
        ]
    )