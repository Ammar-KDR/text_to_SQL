from abc import ABC, abstractmethod


class VectorStore(ABC):


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
        limit: int,
    ):
        pass