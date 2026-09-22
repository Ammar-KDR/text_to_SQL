from textSQL.retrieval.model import (
    FusedCandidate,
    RetrievalTrace,
    RetrievedContext,
    JoinPath,
)

from .index import (
    MetadataIndex,
)

from textSQL.metadata.models import (
    TableMetadata,
    MetricMetadata,
    RelationshipMetadata,
)


class ContextBuilder:


    def __init__(
        self,
        metadata_index: MetadataIndex,
    ):

        self.metadata_index = (
            metadata_index
        )


    def build(
        self,
        question: str,
        candidates: list[FusedCandidate],
    ) -> RetrievedContext:

        tables = []

        metrics = []

        relationships = []

        trace = []


        for candidate in candidates:

            metadata_object = (
                self.metadata_index
                .get_object(
                    candidate.object_id
                )
            )


            if metadata_object is None:
                continue


            if isinstance(
                metadata_object,
                TableMetadata,
            ):

                self._append_unique_table(
                    tables,
                    metadata_object,
                )


            elif isinstance(
                metadata_object,
                MetricMetadata,
            ):

                metrics.append(
                    metadata_object
                )


            elif isinstance(
                metadata_object,
                RelationshipMetadata,
            ):

                self._append_unique_relationship(
                    relationships,
                    metadata_object,
                )


            trace.append(

                RetrievalTrace(

                    object_type=
                        candidate.object_type,

                    object_name=
                        candidate.object_name,

                    score=
                        candidate.rrf_score,

                )
            )


        join_paths = (
            self._build_join_paths(
                tables
            )
        )


        # A multi-hop path may contain an
        # intermediate table that was not
        # originally a retrieval candidate.
        #
        # Example:
        #
        # A -> B -> C
        #
        # If only A and C were retrieved,
        # B still needs to be available to
        # SQL generation.

        self._include_join_path_tables(
            tables,
            join_paths,
        )


        # Relationships contained inside
        # deterministic join paths should
        # also be represented in the final
        # relationship context.

        self._include_join_path_relationships(
            relationships,
            join_paths,
        )


        return RetrievedContext(

            question=question,

            tables=tables,

            metrics=metrics,

            relationships=relationships,

            join_paths=join_paths,

            trace=trace,

        )


    def _build_join_paths(
        self,
        tables: list[TableMetadata],
    ) -> list[JoinPath]:

        join_paths = []

        seen_paths = set()


        table_names = []

        seen_tables = set()


        for table in tables:

            qualified_name = (
                table.qualified_name
            )

            if qualified_name in seen_tables:
                continue


            seen_tables.add(
                qualified_name
            )

            table_names.append(
                qualified_name
            )


        for index, source in enumerate(
            table_names
        ):

            for target in table_names[
                index + 1:
            ]:

                relationships = (
                    self.metadata_index
                    .graph
                    .find_path(
                        source,
                        target,
                    )
                )


                if not relationships:
                    continue


                ordered_tables = (
                    self._ordered_path_tables(
                        source,
                        relationships,
                    )
                )


                path_key = (

                    tuple(
                        ordered_tables
                    ),

                    tuple(
                        relationship.object_id
                        for relationship
                        in relationships
                    ),
                )


                if path_key in seen_paths:
                    continue


                seen_paths.add(
                    path_key
                )


                join_paths.append(

                    JoinPath(

                        tables=
                            ordered_tables,

                        relationships=
                            relationships,

                    )
                )


        return join_paths


    def _ordered_path_tables(
        self,
        start_table: str,
        relationships: list[
            RelationshipMetadata
        ],
    ) -> list[str]:

        tables = [
            start_table
        ]

        current = (
            start_table
        )


        for relationship in relationships:

            source = (
                relationship
                .source_qualified_name
            )

            target = (
                relationship
                .target_qualified_name
            )


            if source == current:

                next_table = target


            elif target == current:

                next_table = source


            else:

                raise ValueError(

                    "Invalid schema graph path: "
                    f"relationship "
                    f"'{relationship.object_id}' "
                    f"is not connected to "
                    f"'{current}'"
                )


            tables.append(
                next_table
            )

            current = (
                next_table
            )


        return tables


    def _include_join_path_tables(
        self,
        tables: list[TableMetadata],
        join_paths: list[JoinPath],
    ):

        existing = {

            table.qualified_name

            for table in tables
        }


        for join_path in join_paths:

            for table_name in (
                join_path.tables
            ):

                if table_name in existing:
                    continue


                table = (
                    self.metadata_index
                    .get_table(
                        table_name
                    )
                )


                if table is None:
                    continue


                tables.append(
                    table
                )

                existing.add(
                    table_name
                )


    def _include_join_path_relationships(
        self,
        relationships: list[
            RelationshipMetadata
        ],
        join_paths: list[JoinPath],
    ):

        existing = {

            relationship.object_id

            for relationship
            in relationships
        }


        for join_path in join_paths:

            for relationship in (
                join_path.relationships
            ):

                if (
                    relationship.object_id
                    in existing
                ):
                    continue


                relationships.append(
                    relationship
                )

                existing.add(
                    relationship.object_id
                )


    def _append_unique_table(
        self,
        tables: list[TableMetadata],
        table: TableMetadata,
    ):

        existing = {

            item.qualified_name

            for item in tables
        }


        if (
            table.qualified_name
            not in existing
        ):

            tables.append(
                table
            )


    def _append_unique_relationship(
        self,
        relationships: list[
            RelationshipMetadata
        ],
        relationship: RelationshipMetadata,
    ):

        existing = {

            item.object_id

            for item
            in relationships
        }


        if (
            relationship.object_id
            not in existing
        ):

            relationships.append(
                relationship
            )