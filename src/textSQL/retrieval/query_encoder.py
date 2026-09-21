from textSQL.embeddings.encoder import (
    EmbeddingEncoder,
)



class QueryEncoder:
    """
    Encodes user questions into vectors
    using the same embedding model used
    during metadata indexing.
    """


    def __init__(
        self,
        encoder: EmbeddingEncoder,
    ):

        self.encoder = encoder



    def encode_query(
        self,
        question: str,
    ) -> list[float]:

        vectors = self.encoder.encode(
            [
                question
            ]
        )


        return vectors[0]