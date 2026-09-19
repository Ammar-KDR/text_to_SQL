from .models import DatabaseMetadata,SchemaMetadata,TableMetadata,ColumnMetadata,RelationshipMetadata
from sqlalchemy import inspect
from .relationship_inference import infer_relationships

from textSQL.metadata.relationship_inference import (
    infer_relationships
)
from textSQL.metadata.cardinality_inference import (
    infer_cardinality
)
from textSQL.metadata.graph import build_schema_graph
from textSQL.metadata.relationship_normalization import normalize_relationships
def extract_database_metadata(
    engine,
    config: dict
) -> DatabaseMetadata:

    inspector = inspect(engine)

    schemas = extract_schemas(
        inspector,
        config
    )


    all_tables = []

    for schema in schemas:
        all_tables.extend(
            schema.tables
        )
    relationships = infer_relationships(
    all_tables
)
    relationships = normalize_relationships(
    relationships
)
    all_table_names = [
    table.name
    for schema in schemas
    for table in schema.tables
    ]

    graph = build_schema_graph(
    relationships,
    all_table_names
)
    relationships = [
    infer_cardinality(
        relationship,
        all_tables
    )
    for relationship in relationships
        ]


    return DatabaseMetadata(

        database_name=engine.url.database,

        schemas=schemas,

        relationships=relationships,
        graph=graph

    )

def extract_schemas(
    inspector,
    config
) -> list[SchemaMetadata]:

    schemas = []

    available_schemas = (
        inspector.get_schema_names()
    )

    for schema_name in available_schemas:

        if schema_name in config["excluded_schemas"]:
            continue


        schema_config = (
            config["schemas"]
            .get(schema_name, {})
        )


        tables = extract_tables(
            inspector,
            schema_name,
            config
        )


        schemas.append(
            SchemaMetadata(
                name=schema_name,

                schema_type=
                schema_config.get(
                    "type",
                    "unknown"
                ),

                description=
                schema_config.get(
                    "description"
                ),

                tables=tables
            )
        )

    return schemas

def extract_tables(
    inspector,
    schema_name,
    config
) -> list[TableMetadata]:


    tables = []

    table_names = (
        inspector.get_table_names(
            schema=schema_name
        )
    )
    excluded_tables = config.get(
    "excluded_tables",
    []
)


    


    for table_name in table_names:

        if table_name in excluded_tables:
                continue
        columns = extract_columns(
            inspector,
            table_name,
            schema_name,
            
        )


        relationships = extract_relationships(
            inspector,
            table_name,
            schema_name,
            
        )

        primary_keys=[
    column.name
    for column in columns
    if column.is_primary_key
]
        tables.append(
            TableMetadata(
                name=table_name,
                columns=columns,
                relationships=relationships,
                primary_keys=primary_keys
            )
        )


    return tables


def extract_columns(
    inspector,
    table_name: str,
    schema_name: str
) -> list[ColumnMetadata]:

    columns = []


    raw_columns = inspector.get_columns(
        table_name,
        schema=schema_name
    )


    primary_key_info = (
        inspector.get_pk_constraint(
            table_name,
            schema=schema_name
        )
    )


    primary_keys = set(
        primary_key_info.get(
            "constrained_columns",
            []
        )
    )


    unique_constraints = (
        inspector.get_unique_constraints(
            table_name,
            schema=schema_name
        )
    )


    unique_columns = set()


    for constraint in unique_constraints:

        unique_columns.update(
            constraint.get(
                "column_names",
                []
            )
        )


    for column in raw_columns:

        column_name = column["name"]

        columns.append(

            ColumnMetadata(

                name=column_name,

                data_type=str(
                    column["type"]
                ),

                nullable=column["nullable"],

                is_primary_key=
                column_name in primary_keys,

                is_unique=
                column_name in unique_columns

            )
        )


    return columns


def extract_relationships(
    inspector,
    table_name,
    schema_name
) -> list[RelationshipMetadata]:

    relationships = []


    foreign_keys = (
        inspector.get_foreign_keys(
            table_name,
            schema=schema_name
        )
    )


    for fk in foreign_keys:

        relationships.append(
            RelationshipMetadata(
    source_table=table_name,

    target_table=fk["referred_table"],

    relationship_type="foreign_key",

    source_cardinality="unknown",

    target_cardinality="unknown",

    foreign_keys=[
        fk["constrained_columns"][0]
    ]
))


    return relationships