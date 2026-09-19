from collections import defaultdict

from textSQL.metadata.models import (
    RelationshipMetadata,
)

from collections import deque

class SchemaGraph:

    def __init__(self):

        self.nodes = set()

        self.edges = defaultdict(list)


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

        self.edges[
            relationship.source_table
        ].append(
            relationship
        )

        self.edges[
            relationship.target_table
        ].append(
            relationship
        )
    def find_path(
                self,
                start_table: str,
                target_table: str,
            ):
    
        if start_table == target_table:
            return []


        queue = deque(
            [
                (
                    start_table,
                    []
                )
            ]
        )


        visited = {
            start_table
        }


        while queue:

            current, path = queue.popleft()


            for relationship in self.edges[current]:

                if (
                    relationship.source_table
                    == current
                ):
                    neighbor = relationship.target_table

                else:
                    neighbor = relationship.source_table


                if neighbor in visited:
                    continue


                new_path = (
                    path
                    +
                    [
                        relationship
                    ]
                )


                if neighbor == target_table:

                    return new_path


                visited.add(
                    neighbor
                )


                queue.append(
                    (
                        neighbor,
                        new_path
                    )
                )


        return None


def build_schema_graph(
    relationships: list[RelationshipMetadata],
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