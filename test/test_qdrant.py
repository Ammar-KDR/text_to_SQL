import pytest


from textSQL.vectorstore.qdrant import (
    QdrantVectorStore,
)


from textSQL.embeddings.model import (
    EmbeddingDocument,
)



@pytest.fixture
def vector_store():

    store = QdrantVectorStore(

        collection_name=
        "test_metadata_embeddings",

        vector_size=3,

    )


    store.delete_collection()


    return store



def test_collection_created(
    vector_store,
):

    assert (
        vector_store.collection_exists()
        is False
    )


    vector_store.create_collection()


    assert (
        vector_store.collection_exists()
        is True
    )



def test_create_collection_is_idempotent(
    vector_store,
):

    vector_store.create_collection()

    vector_store.create_collection()


    assert (
        vector_store.collection_exists()
        is True
    )



def test_upsert_creates_collection_if_missing(
    vector_store,
):

    document = EmbeddingDocument(

        id="metric_revenue",

        content=
        "Revenue metric",

        object_type="metric",

        object_name="revenue",

        metadata={
            "domain": "sales"
        }

    )


    vector_store.upsert(

        [document],

        [
            [
                0.1,
                0.2,
                0.3
            ]
        ]

    )


    assert (
        vector_store.collection_exists()
        is True
    )



def test_delete_missing_collection_is_safe(
    vector_store,
):

    vector_store.delete_collection()


    assert True



def test_duplicate_upsert_updates_same_point(
    vector_store,
):

    document = EmbeddingDocument(

        id="metric_revenue",

        content=
        "Revenue metric",

        object_type="metric",

        object_name="revenue",

    )


    vector = [
        [
            0.1,
            0.2,
            0.3
        ]
    ]


    vector_store.upsert(
        [document],
        vector,
    )


    vector_store.upsert(
        [document],
        vector,
    )


    results = vector_store.search(

        vector[0],

        limit=10,

    )


    assert len(results) == 1