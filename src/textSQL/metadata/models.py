from pydantic import BaseModel
from pydantic import Field



class ColumnMetadata(BaseModel):

    name: str

    data_type: str

    nullable: bool

    is_primary_key: bool = False

    is_unique: bool = False

    description: str | None = None

    business_meaning: str | None = None

class RelationshipMetadata(BaseModel):

    source_table: str

    target_table: str

    relationship_type: str

    source_cardinality: str

    target_cardinality: str

    source_optional: bool = False

    target_optional: bool = False

    through_table: str | None = None

    foreign_keys: list[str] = Field(
        default_factory=list
    )

    reasoning: str | None = None
    confidence: float | None = None
    
    description: str | None = None

    business_meaning: str | None = None

class TableMetadata(BaseModel):

    name: str

    description: str | None = None

    business_role: str | None = None

    columns: list[ColumnMetadata] = Field(default_factory=list)

    relationships: list[RelationshipMetadata] = Field(
        default_factory=list
    )

    primary_keys: list[str] = Field(
        default_factory=list
    )

class SchemaMetadata(BaseModel):

    name: str

    schema_type: str

    description: str | None = None

    tables: list[TableMetadata] = Field(
        default_factory=list
    )

class DatabaseMetadata(BaseModel):

    database_name: str

    
    schemas: list[SchemaMetadata] = Field(
        default_factory=list
    )
    relationships: list[RelationshipMetadata]

    graph: object | None = None

class MetricMetadata(BaseModel):

    name: str

    description: str

    formula: str

    authoritative_source: str | None = None

    required_tables: list[str] = Field(default_factory=list)

    required_columns: list[str] = Field(default_factory=list)

    business_rules: list[str] = Field(default_factory=list)

    forbidden_sources: list[str] = Field(default_factory=list)

