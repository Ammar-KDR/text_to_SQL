from pydantic import BaseModel, Field



class EmbeddingDocument(BaseModel):

    id: str

    content: str

    object_type: str

    object_name: str

    metadata: dict = Field(
        default_factory=dict
    )