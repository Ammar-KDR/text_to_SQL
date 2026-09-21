from pydantic import BaseModel, Field

from textSQL.metadata.models import (
    TableMetadata,
    RelationshipMetadata,
    MetricMetadata,
)



class RetrievalTrace(BaseModel):
    """
    Debug information explaining why
    an item was retrieved.
    """

    object_type: str

    object_name: str

    score: float

    matched_terms: list[str] = Field(
        default_factory=list
    )



class JoinPath(BaseModel):
    """
    Represents a path between tables
    required for SQL generation.
    """

    tables: list[str] = Field(
        default_factory=list
    )

    relationships: list[RelationshipMetadata] = Field(
        default_factory=list
    )



class RetrievedContext(BaseModel):
    """
    Final output of the retrieval layer.

    This object is passed to the SQL generation layer.
    """

    question: str


    tables: list[TableMetadata] = Field(
        default_factory=list
    )


    relationships: list[RelationshipMetadata] = Field(
        default_factory=list
    )


    metrics: list[MetricMetadata] = Field(
        default_factory=list
    )


    join_paths: list[JoinPath] = Field(
        default_factory=list
    )


    trace: list[RetrievalTrace] = Field(
        default_factory=list
    )

class RetrievalCandidate(BaseModel):

    object_id: str

    object_type: str

    object_name: str

    score: float

    source: str






class FusedCandidate(BaseModel):


    object_id: str

    object_type: str

    object_name: str


    rrf_score: float


    sources: list[str] = Field(
        default_factory=list
    )


    original_candidates: list[
        RetrievalCandidate
    ] = Field(
        default_factory=list
    )

class RetrievedObject(BaseModel):

    object_id: str

    object_type: str

    object_name: str


    object: object


    rrf_score: float


    sources: list[str]