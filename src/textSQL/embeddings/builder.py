from textSQL.metadata.models import (
    DatabaseMetadata,
    MetricMetadata,
    TableMetadata,
)

from .model import (
    EmbeddingDocument,
)



class MetadataEmbeddingBuilder:


    def __init__(
        self,
        metadata: DatabaseMetadata,
    ):

        self.metadata = metadata



    def build(self) -> list[EmbeddingDocument]:

        documents = []


        documents.extend(
            self._build_metric_documents()
        )


        documents.extend(
            self._build_table_documents()
        )


        return documents



    def _build_metric_documents(
        self,
    ) -> list[EmbeddingDocument]:

        documents = []


        for metric in self.metadata.metrics:

            documents.append(

                EmbeddingDocument(

                    id=f"metric_{metric.name}",

                    object_type="metric",

                    object_name=metric.name,

                    content=self._metric_text(
                        metric
                    ),

                    metadata={

                        "domain": metric.domain,

                        "required_tables":
                            metric.required_tables,

                        "required_columns":
                            metric.required_columns,

                    }
                )
            )


        return documents



    def _metric_text(
        self,
        metric: MetricMetadata,
    ) -> str:

        return f"""
Metric:
{metric.name}

Domain:
{metric.domain}

Description:
{metric.description}

Synonyms:
{", ".join(metric.synonyms)}

Formula:
{metric.formula}

Required Tables:
{", ".join(metric.required_tables)}

Business Rules:
{", ".join(metric.business_rules)}
""".strip()



    def _build_table_documents(
        self,
    ) -> list[EmbeddingDocument]:

        documents = []


        for schema in self.metadata.schemas:

            for table in schema.tables:


                documents.append(

                    EmbeddingDocument(

                        id=f"table_{table.name}",

                        object_type="table",

                        object_name=table.name,

                        content=self._table_text(
                            table
                        ),

                        metadata={

                            "business_role":
                                table.business_role,

                            "schema":
                                schema.name,

                        }
                    )
                )


        return documents



    def _table_text(
        self,
        table: TableMetadata,
    ) -> str:


        columns = ", ".join(
            [
                column.name
                for column in table.columns
            ]
        )


        return f"""
Table:
{table.name}

Description:
{table.description}

Business Role:
{table.business_role}

Columns:
{columns}
""".strip()


    def _build_relationship_documents(
    self,
):

        documents = []

        for relationship in self.metadata.relationships:

            documents.append(
                EmbeddingDocument(

                    id=(
                        f"relationship_"
                        f"{relationship.source_table}_"
                        f"{relationship.target_table}"
                    ),

                    object_type="relationship",

                    object_name=(
                        f"{relationship.source_table}_"
                        f"{relationship.target_table}"
                    ),

                    content=self._relationship_text(
                        relationship
                    ),

                    metadata={
                        "source_table":
                            relationship.source_table,

                        "target_table":
                            relationship.target_table,

                        "relationship_type":
                            relationship.relationship_type,
                    }
                )
            )

        return documents


    def _relationship_text(
        self,
        relationship,
    ):

        return f"""
    Relationship:

    Source:
    {relationship.source_table}

    Target:
    {relationship.target_table}

    Type:
    {relationship.relationship_type}

    Foreign Keys:
    {", ".join(relationship.foreign_keys)}

    Business Meaning:
    {relationship.business_meaning}

    Description:
    {relationship.description}
    """.strip()