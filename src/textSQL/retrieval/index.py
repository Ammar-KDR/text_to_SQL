from collections import defaultdict

from textSQL.metadata.models import (
    DatabaseMetadata,
    TableMetadata,
    ColumnMetadata,
    MetricMetadata,
)

from textSQL.metadata.graph import SchemaGraph



class MetadataIndex:


    def __init__(
        self,
        metadata: DatabaseMetadata,
        graph: SchemaGraph,
    ):

        self.metadata = metadata

        self.graph = graph


        self.tables: dict[str, TableMetadata] = {}

        self.columns: dict[str, list[ColumnMetadata]] = defaultdict(list)

        self.metrics: dict[str, MetricMetadata] = {}
        self.metric_aliases: dict[str, MetricMetadata] = {}
        self.objects: dict[str, object] = {}


        self._build()



    def _build(self):

        self._index_tables()

        self._index_columns()

        self._index_metrics()

        self._index_relationships()



    def _index_tables(self):

        for schema in self.metadata.schemas:

            for table in schema.tables:

                self.tables[
                    table.name
                ] = table


                self.objects[
                    f"table_{table.name}"
                ] = table



    def _index_columns(self):

        for table in self.tables.values():

            for column in table.columns:

                self.columns[
                    column.name.lower()
                ].append(
                    column
                )



    def _index_metrics(self):

        # Metrics are currently not nested
        # inside SchemaMetadata,
        # they are separate metadata objects

        # Placeholder until we decide
        # where metrics are loaded from

        for metric in self.metadata.metrics:
            self.metrics[metric.name.lower()]=metric

            self.objects[
                f"metric_{metric.name}"
            ] = metric

        
            for synonym in metric.synonyms:

                self.metric_aliases[
                    synonym.lower()
                ] = metric

    def _index_relationships(
            self,
        ):

        for relationship in self.metadata.relationships:

            relationship_id = (
                f"relationship_"
                f"{relationship.source_table}_"
                f"{relationship.target_table}"
            )


            self.objects[
                relationship_id
            ] = relationship

    def get_object(
    self,
    object_id: str,
):

        return self.objects.get(
            object_id
        )

    