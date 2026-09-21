from abc import ABC, abstractmethod
from .id_generator import generate_document_id


class VectorStore(ABC):
    """
    Abstract interface for vector storage systems.

    Allows replacing Qdrant with another
    vector database without changing retrieval logic.
    """


    @abstractmethod
    def create_collection(
        self,
    ):
        pass



    @abstractmethod
    def upsert(
        self,
        documents,
        vectors,
    ):
        pass



    @abstractmethod
    def search(
        self,
        vector,
        limit: int = 5,
    ):
        pass



    @abstractmethod
    def delete_collection(
        self,
    ):
        pass


from qdrant_client import QdrantClient

from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
)

from textSQL.vectorstore.base import (
    VectorStore,
)

from textSQL.embeddings.model import (
    EmbeddingDocument,
)



class QdrantVectorStore(VectorStore):


    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "metadata_embeddings",
        vector_size: int = 384,
    ):

        self.client = QdrantClient(
            host=host,
            port=port,
        )


        self.collection_name = collection_name

        self.vector_size = vector_size



    def collection_exists(self) -> bool:

        collections = (
            self.client
            .get_collections()
            .collections
        )


        return any(
            collection.name
            == self.collection_name
            for collection in collections
        )



    def create_collection(self):

        if self.collection_exists():

            return


        self.client.create_collection(

            collection_name=self.collection_name,

            vectors_config=VectorParams(

                size=self.vector_size,

                distance=Distance.COSINE,

            ),
        )



    def upsert(
        self,
        documents: list[EmbeddingDocument],
        vectors: list[list[float]],
    ):

        if not self.collection_exists():

            self.create_collection()



        points = []


        for document, vector in zip(
            documents,
            vectors,
        ):

            points.append(

                PointStruct(

                    
                    id=generate_document_id(document.id),

                    vector=vector,

                    payload={

                        "object_type":
                            document.object_type,

                        "object_name":
                            document.object_name,

                        **document.metadata,

                        "content":
                            document.content,

                    },
                )
            )


        self.client.upsert(

            collection_name=self.collection_name,

            points=points,

        )



    def search(
        self,
        vector: list[float],
        limit: int = 5,
    ):


        if not self.collection_exists():

            return []


        results = self.client.query_points(

            collection_name=self.collection_name,

            query=vector,

            limit=limit,

        ).points


        return results



    def delete_collection(self):

        if not self.collection_exists():

            return


        self.client.delete_collection(

            collection_name=self.collection_name,

        )