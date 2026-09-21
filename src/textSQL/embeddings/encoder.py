from abc import ABC, abstractmethod
from sentence_transformers import SentenceTransformer

class EmbeddingEncoder(ABC):


    @abstractmethod
    def encode(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        pass


class BGEEncoder(EmbeddingEncoder):


    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ):

        self.model = SentenceTransformer(
            model_name
        )



    def encode(
        self,
        texts: list[str],
    ) -> list[list[float]]:


        embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
        )


        return embeddings.tolist()