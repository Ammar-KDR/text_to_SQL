from textSQL.retrieval.query_encoder import (
    QueryEncoder,
)

from textSQL.embeddings.encoder import (
    EmbeddingEncoder,
)



class FakeEncoder(EmbeddingEncoder):


    def encode(
        self,
        texts: list[str],
    ):

        return [
            [
                0.1,
                0.2,
                0.3,
            ]
            for _ in texts
        ]



def test_query_encoder():

    encoder = QueryEncoder(
        FakeEncoder()
    )


    vector = encoder.encode_query(
        "show revenue"
    )


    assert vector == [
        0.1,
        0.2,
        0.3,
    ]



def test_query_encoder_returns_single_vector():

    encoder = QueryEncoder(
        FakeEncoder()
    )


    vector = encoder.encode_query(
        "customers"
    )


    assert isinstance(
        vector,
        list,
    )

    assert len(vector) == 3