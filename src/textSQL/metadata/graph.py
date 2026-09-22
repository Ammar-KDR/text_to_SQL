from collections import (
    defaultdict,
    deque,
)

from textSQL.metadata.models import (
    RelationshipMetadata,
)


class SchemaGraph:


    def __init__(self):

        self.nodes: set[str] = set()

        self.edges: dict[
            str,
            list[RelationshipMetadata],
        ] = defaultdict(list)


    def add_table(
        self,
        table_name: str,
    ):

        self.nodes.add(
            table_name
        )


    def add_relationship(
        self,
        relationship: RelationshipMetadata,
    ):


            # --------------------------------------------------
            # Synthetic many-to-many relationships describe
            # semantic connectivity but are not physical SQL
            # join edges.
            #
            # Example:
            #
            # customers <-> campaigns
            #
            # actually requires:
            #
            # customers
            #     <- customer_campaigns
            #     -> campaigns
            #
            # Keeping the synthetic edge out of the join graph
            # prevents SQL generation from skipping the
            # junction table.
            # --------------------------------------------------

        if (
            relationship.relationship_type
            ==
            "many-to-many"

            and

            relationship.through_table
            is not None
        ):

            return
        
        source = (
            relationship
            .source_qualified_name
        )

        target = (
            relationship
            .target_qualified_name
        )


        self.nodes.add(source)

        self.nodes.add(target)


        self.edges[
            source
        ].append(
            relationship
        )

        self.edges[
            target
        ].append(
            relationship
        )


    def find_path(
        self,
        start_table: str,
        target_table: str,
    ):

        if (
            start_table
            not in self.nodes
        ):

            return None


        if (
            target_table
            not in self.nodes
        ):

            return None


        if (
            start_table
            ==
            target_table
        ):

            return []


        queue = deque([

            (
                start_table,
                [],
            )

        ])


        visited = {
            start_table
        }


        while queue:

            current, path = (
                queue.popleft()
            )


            for relationship in (
                self.edges[current]
            ):

                source = (
                    relationship
                    .source_qualified_name
                )

                target = (
                    relationship
                    .target_qualified_name
                )


                if source == current:

                    neighbor = target

                else:

                    neighbor = source


                if neighbor in visited:
                    continue


                new_path = (

                    path

                    +

                    [
                        relationship
                    ]
                )


                if (
                    neighbor
                    ==
                    target_table
                ):

                    return new_path


                visited.add(
                    neighbor
                )


                queue.append(

                    (
                        neighbor,
                        new_path,
                    )

                )


        return None


def build_schema_graph(
    relationships: list[
        RelationshipMetadata
    ],
    tables: list[str],
):

    graph = SchemaGraph()


    for table in tables:

        graph.add_table(
            table
        )


    for relationship in relationships:

        graph.add_relationship(
            relationship
        )


    return graph