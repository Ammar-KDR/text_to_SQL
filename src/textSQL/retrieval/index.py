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

        self.table_aliases: dict[
            str,
            list[TableMetadata],
        ] = defaultdict(list)

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

                if table.schema_name is None:
                    table.schema_name = schema.name
                
                qualified_name = (
                    table.qualified_name.lower()
                )


                self.tables[
                    qualified_name
                ] = table
                
                self.table_aliases[
                    table.name.lower()
                ].append(
                    table
                )


                self.objects[
                    f"table_{table.qualified_name}"
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

        for relationship in (
            self.metadata.relationships
        ):

            self.objects[
                relationship.object_id
            ] = relationship

    def get_object(
    self,
    object_id: str,
):

        return self.objects.get(
            object_id
        )


    def get_table(
    self,
    table_name: str,
) -> TableMetadata | None:

        normalized = table_name.lower()

        # Exact qualified lookup first
        table = self.tables.get(
            normalized
        )

        if table is not None:
            return table

        # Fall back to bare name only
        # when it resolves uniquely
        matches = self.table_aliases.get(
            normalized,
            [],
        )

        if len(matches) == 1:
            return matches[0]

        return None