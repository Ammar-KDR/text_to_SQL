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

class JoinConditionMetadata(BaseModel):

    source_schema: str | None = None

    source_table: str

    source_column: str

    target_schema: str | None = None

    target_table: str

    target_column: str


    @property
    def source_qualified_column(self) -> str:

        if self.source_schema:

            return (
                f"{self.source_schema}."
                f"{self.source_table}."
                f"{self.source_column}"
            )

        return (
            f"{self.source_table}."
            f"{self.source_column}"
        )


    @property
    def target_qualified_column(self) -> str:

        if self.target_schema:

            return (
                f"{self.target_schema}."
                f"{self.target_table}."
                f"{self.target_column}"
            )

        return (
            f"{self.target_table}."
            f"{self.target_column}"
        )

class RelationshipMetadata(BaseModel):

    source_table: str

    target_table: str

    source_schema: str | None = None

    target_schema: str | None = None

    relationship_type: str

    source_cardinality: str

    target_cardinality: str

    source_optional: bool = False

    target_optional: bool = False

    through_table: str | None = None

    through_schema: str | None = None

    foreign_keys: list[str] = Field(
        default_factory=list
    )

    join_conditions: list[
        JoinConditionMetadata
    ] = Field(
        default_factory=list
    )

    reasoning: str | None = None

    confidence: float | None = None

    description: str | None = None

    business_meaning: str | None = None


    @property
    def source_qualified_name(self) -> str:

        if self.source_schema:

            return (
                f"{self.source_schema}."
                f"{self.source_table}"
            )

        return self.source_table


    @property
    def target_qualified_name(self) -> str:

        if self.target_schema:

            return (
                f"{self.target_schema}."
                f"{self.target_table}"
            )

        return self.target_table


    @property
    def through_qualified_name(
        self
    ) -> str | None:

        if self.through_table is None:
            return None

        if self.through_schema:

            return (
                f"{self.through_schema}."
                f"{self.through_table}"
            )

        return self.through_table
    @property
    def object_id(self) -> str:

        base = (
            f"relationship_"
            f"{self.source_qualified_name}__"
            f"{self.target_qualified_name}"
        )

        if not self.join_conditions:
            return base


        join_signature = "__".join(

            sorted(

                f"{condition.source_qualified_column}"
                f"="
                f"{condition.target_qualified_column}"

                for condition
                in self.join_conditions
            )
        )


        return (
            f"{base}__"
            f"{join_signature}"
        )

class TableMetadata(BaseModel):

    name: str

    schema_name: str | None = None
    description: str | None = None

    business_role: str | None = None

    columns: list[ColumnMetadata] = Field(default_factory=list)

    relationships: list[RelationshipMetadata] = Field(
        default_factory=list
    )

    primary_keys: list[str] = Field(
        default_factory=list
    )

    @property
    def qualified_name(self) -> str:

        if self.schema_name:
            return (
                f"{self.schema_name}."
                f"{self.name}"
            )

        return self.name

class SchemaMetadata(BaseModel):

    name: str

    schema_type: str

    description: str | None = None

    tables: list[TableMetadata] = Field(
        default_factory=list
    )
class MetricMetadata(BaseModel):

    name: str

    description: str

    domain: str

    formula: str

    authoritative_source: str | None = None

    required_tables: list[str] = Field(default_factory=list)

    required_columns: list[str] = Field(default_factory=list)

    required_metrics: list[str] = Field(default_factory=list)

    business_rules: list[str] = Field(default_factory=list)

    forbidden_sources: list[str] = Field(default_factory=list)

    synonyms: list[str]

    
class DatabaseMetadata(BaseModel):

    database_name: str

    
    schemas: list[SchemaMetadata] = Field(
        default_factory=list
    )
    relationships: list[RelationshipMetadata]
    metrics: list[MetricMetadata]

    graph: object | None = Field(
        default=None,
        exclude=True,
    )



