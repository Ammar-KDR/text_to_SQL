from types import SimpleNamespace

from textSQL.metadata.models import (
    DatabaseMetadata,
    SchemaMetadata,
    TableMetadata,
    ColumnMetadata,
    MetricMetadata,
)

from textSQL.metadata.graph import (
    SchemaGraph,
)

from textSQL.retrieval.index import (
    MetadataIndex,
)

from textSQL.retrieval.dependency_resolver import (
    DependencyResolver,
)

from textSQL.retrieval.model import (
    RetrievalCandidate,
)

from textSQL.embeddings.builder import (
    MetadataEmbeddingBuilder,
)

from textSQL.embeddings.model import (
    EmbeddingDocument,
)

from textSQL.vectorstore.qdrant import (
    QdrantVectorStore,
)


# ============================================================
# TEST DATA
# ============================================================


def create_test_metadata():

    fact_sales = TableMetadata(

        name="fact_sales",

        schema_name="warehouse",

        description=
        "Authoritative sales fact table",

        business_role=
        "Stores analytical sales facts",

        columns=[

            ColumnMetadata(
                name="sales_key",
                data_type="integer",
                nullable=False,
                is_primary_key=True,
            ),

            ColumnMetadata(
                name="customer_key",
                data_type="integer",
                nullable=False,
            ),

            ColumnMetadata(
                name="revenue",
                data_type="numeric",
                nullable=False,
            ),

        ],

        primary_keys=[
            "sales_key"
        ],
    )


    orders = TableMetadata(

        name="orders",

        schema_name="public",

        description=
        "Operational customer orders",

        business_role=
        "Stores transactional orders",

        columns=[

            ColumnMetadata(
                name="order_id",
                data_type="integer",
                nullable=False,
                is_primary_key=True,
            ),

            ColumnMetadata(
                name="order_status",
                data_type="varchar",
                nullable=False,
            ),

        ],

        primary_keys=[
            "order_id"
        ],
    )


    revenue = MetricMetadata(

        name="revenue",

        domain="sales",

        synonyms=[
            "sales",
            "income",
        ],

        description=
        "Net merchandise revenue",

        formula=
        "SUM(fact_sales.revenue)",

        authoritative_source=
        "fact_sales",

        required_tables=[
            "fact_sales"
        ],

        required_columns=[
            "revenue",
            "customer_key",
        ],

        required_metrics=[],

        business_rules=[
            "Prefer fact_sales as the analytical revenue source"
        ],

        forbidden_sources=[
            "payments"
        ],
    )


    return DatabaseMetadata(

        database_name="test_db",

        schemas=[

            SchemaMetadata(

                name="public",

                schema_type="OLTP",

                tables=[
                    orders
                ],
            ),

            SchemaMetadata(

                name="warehouse",

                schema_type="OLAP",

                tables=[
                    fact_sales
                ],
            ),

        ],

        relationships=[],

        metrics=[
            revenue
        ],

        graph=None,
    )


# ============================================================
# TABLE METADATA TESTS
# ============================================================


def test_table_qualified_name():

    table = TableMetadata(
        name="fact_sales",
        schema_name="warehouse",
    )

    assert (
        table.qualified_name
        ==
        "warehouse.fact_sales"
    )


def test_table_qualified_name_without_schema():

    table = TableMetadata(
        name="orders"
    )

    assert (
        table.qualified_name
        ==
        "orders"
    )


# ============================================================
# METADATA INDEX TESTS
# ============================================================


def test_tables_are_indexed_by_qualified_name():

    metadata = create_test_metadata()

    index = MetadataIndex(
        metadata,
        SchemaGraph(),
    )

    assert (
        "warehouse.fact_sales"
        in index.tables
    )

    assert (
        "public.orders"
        in index.tables
    )


def test_objects_use_schema_qualified_table_ids():

    metadata = create_test_metadata()

    index = MetadataIndex(
        metadata,
        SchemaGraph(),
    )

    fact_sales = index.get_object(
        "table_warehouse.fact_sales"
    )

    orders = index.get_object(
        "table_public.orders"
    )


    assert fact_sales is not None

    assert orders is not None


    assert (
        fact_sales.name
        ==
        "fact_sales"
    )

    assert (
        fact_sales.schema_name
        ==
        "warehouse"
    )


    assert (
        orders.name
        ==
        "orders"
    )

    assert (
        orders.schema_name
        ==
        "public"
    )


def test_unique_bare_table_name_can_resolve():

    metadata = create_test_metadata()

    index = MetadataIndex(
        metadata,
        SchemaGraph(),
    )


    table = index.get_table(
        "fact_sales"
    )


    assert table is not None

    assert (
        table.qualified_name
        ==
        "warehouse.fact_sales"
    )


def test_qualified_table_name_resolves_directly():

    metadata = create_test_metadata()

    index = MetadataIndex(
        metadata,
        SchemaGraph(),
    )


    table = index.get_table(
        "warehouse.fact_sales"
    )


    assert table is not None

    assert (
        table.schema_name
        ==
        "warehouse"
    )


# ============================================================
# COLLISION SAFETY
# ============================================================


def test_ambiguous_bare_table_name_does_not_resolve():

    public_orders = TableMetadata(
        name="orders",
        schema_name="public",
    )


    warehouse_orders = TableMetadata(
        name="orders",
        schema_name="warehouse",
    )


    metadata = DatabaseMetadata(

        database_name="test_db",

        schemas=[

            SchemaMetadata(

                name="public",

                schema_type="OLTP",

                tables=[
                    public_orders
                ],
            ),

            SchemaMetadata(

                name="warehouse",

                schema_type="OLAP",

                tables=[
                    warehouse_orders
                ],
            ),

        ],

        relationships=[],

        metrics=[],

        graph=None,
    )


    index = MetadataIndex(
        metadata,
        SchemaGraph(),
    )


    assert (
        "public.orders"
        in index.tables
    )

    assert (
        "warehouse.orders"
        in index.tables
    )


    assert (
        index.get_table(
            "orders"
        )
        is None
    )


    assert (
        index.get_table(
            "public.orders"
        )
        is not None
    )


    assert (
        index.get_table(
            "warehouse.orders"
        )
        is not None
    )


# ============================================================
# EMBEDDING DOCUMENT TESTS
# ============================================================


def test_table_embedding_uses_qualified_identity():

    metadata = create_test_metadata()

    builder = MetadataEmbeddingBuilder(
        metadata
    )


    documents = builder.build()


    table_documents = [

        document

        for document in documents

        if (
            document.object_type
            ==
            "table"
        )
    ]


    fact_sales_documents = [

        document

        for document
        in table_documents

        if (
            document.object_name
            ==
            "fact_sales"
        )
    ]


    assert (
        len(fact_sales_documents)
        ==
        1
    )


    document = (
        fact_sales_documents[0]
    )


    assert (
        document.id
        ==
        "table_warehouse.fact_sales"
    )


    assert (
        document.object_name
        ==
        "fact_sales"
    )


    assert (
        document.metadata[
            "schema"
        ]
        ==
        "warehouse"
    )


    assert (
        document.metadata[
            "qualified_name"
        ]
        ==
        "warehouse.fact_sales"
    )


    assert (
        "warehouse.fact_sales"
        in document.content
    )


# ============================================================
# DEPENDENCY RESOLVER TESTS
# ============================================================


def test_metric_dependency_uses_qualified_table_id():

    metadata = create_test_metadata()

    index = MetadataIndex(
        metadata,
        SchemaGraph(),
    )


    resolver = DependencyResolver(
        index
    )


    candidates = [

        RetrievalCandidate(

            object_id=
            "metric_revenue",

            object_type=
            "metric",

            object_name=
            "revenue",

            score=
            0.95,

            source=
            "dense",

        )

    ]


    resolved = resolver.resolve(
        candidates
    )


    table_candidates = [

        candidate

        for candidate in resolved

        if (
            candidate.object_type
            ==
            "table"
        )
    ]


    assert (
        len(table_candidates)
        ==
        1
    )


    table_candidate = (
        table_candidates[0]
    )


    assert (
        table_candidate.object_id
        ==
        "table_warehouse.fact_sales"
    )


    # Temporary behavior until
    # SchemaGraph becomes schema-aware.
    assert (
        table_candidate.object_name
        ==
        "fact_sales"
    )


# ============================================================
# QDRANT PAYLOAD TEST
# ============================================================


class FakeQdrantClient:

    def __init__(self):

        self.points = None


    def get_collections(self):

        return SimpleNamespace(

            collections=[

                SimpleNamespace(
                    name=
                    "metadata_embeddings"
                )

            ]
        )


    def upsert(
        self,
        collection_name,
        points,
    ):

        self.collection_name = (
            collection_name
        )

        self.points = points


def test_qdrant_payload_preserves_metadata_id():

    # Avoid opening a real Qdrant connection.
    store = (
        QdrantVectorStore.__new__(
            QdrantVectorStore
        )
    )


    store.client = (
        FakeQdrantClient()
    )

    store.collection_name = (
        "metadata_embeddings"
    )

    store.vector_size = 3


    document = EmbeddingDocument(

        id=
        "table_warehouse.fact_sales",

        object_type=
        "table",

        object_name=
        "fact_sales",

        content=
        "Warehouse sales fact table",

        metadata={

            "schema":
            "warehouse",

            "qualified_name":
            "warehouse.fact_sales",

        },
    )


    store.upsert(

        documents=[
            document
        ],

        vectors=[
            [
                0.1,
                0.2,
                0.3,
            ]
        ],
    )


    assert (
        store.client.points
        is not None
    )


    assert (
        len(
            store.client.points
        )
        ==
        1
    )


    payload = (
        store.client
        .points[0]
        .payload
    )


    assert (
        payload[
            "metadata_id"
        ]
        ==
        "table_warehouse.fact_sales"
    )


    assert (
        payload[
            "object_type"
        ]
        ==
        "table"
    )


    assert (
        payload[
            "object_name"
        ]
        ==
        "fact_sales"
    )


    assert (
        payload[
            "schema"
        ]
        ==
        "warehouse"
    )


    assert (
        payload[
            "qualified_name"
        ]
        ==
        "warehouse.fact_sales"
    )