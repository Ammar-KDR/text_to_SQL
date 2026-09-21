from textSQL.embeddings.service import (
    EmbeddingService,
)

from textSQL.embeddings.encoder import (
    EmbeddingEncoder,
)

from textSQL.metadata.models import (
    DatabaseMetadata,
    SchemaMetadata,
    TableMetadata,
    ColumnMetadata,
    MetricMetadata,
)



class FakeEncoder(EmbeddingEncoder):
    """
    Fake encoder used for testing.

    Avoids loading real embedding models.
    """


    def encode(
        self,
        texts: list[str],
    ) -> list[list[float]]:

        return [
            [
                0.1,
                0.2,
                0.3,
            ]
            for _ in texts
        ]



def create_test_metadata():

    revenue_metric = MetricMetadata(

        name="revenue",

        domain="sales",

        description=
        "Net revenue generated from completed sales.",

        formula=
        "SUM(fact_sales.net_amount)",

        authoritative_source=
        "fact_sales",

        required_tables=[
            "fact_sales"
        ],

        required_columns=[
            "net_amount"
        ],

        required_metrics=[],

        business_rules=[
            "Exclude cancelled orders"
        ],

        forbidden_sources=[
            "payments"
        ],

        synonyms=[
            "sales",
            "income"
        ],
    )


    sales_table = TableMetadata(

        name="fact_sales",

        description=
        "Stores finalized sales transactions.",

        business_role=
        "Authoritative sales source.",

        columns=[

            ColumnMetadata(

                name="net_amount",

                data_type="decimal",

                nullable=False,

            ),

            ColumnMetadata(

                name="customer_key",

                data_type="integer",

                nullable=False,

            ),

        ],
    )


    return DatabaseMetadata(

        database_name="test_db",

        schemas=[

            SchemaMetadata(

                name="warehouse",

                schema_type="OLAP",

                tables=[
                    sales_table
                ],

            )
        ],

        relationships=[],

        metrics=[
            revenue_metric
        ],

        graph=None,

    )



def test_embedding_service_creates_documents_and_vectors():

    metadata = create_test_metadata()


    service = EmbeddingService(

        encoder=FakeEncoder()

    )


    documents, vectors = (
        service.create_embeddings(
            metadata
        )
    )


    assert len(documents) > 0


    assert len(vectors) == len(documents)



def test_embedding_vectors_have_correct_dimension():

    metadata = create_test_metadata()


    service = EmbeddingService(

        encoder=FakeEncoder()

    )


    _, vectors = (
        service.create_embeddings(
            metadata
        )
    )


    assert len(vectors[0]) == 3



def test_metric_document_is_created():

    metadata = create_test_metadata()


    service = EmbeddingService(

        encoder=FakeEncoder()

    )


    documents, _ = (
        service.create_embeddings(
            metadata
        )
    )


    metric_documents = [

        document

        for document in documents

        if document.object_type == "metric"

    ]


    assert len(metric_documents) == 1


    metric = metric_documents[0]


    assert metric.object_name == "revenue"


    assert "Net revenue" in metric.content



def test_table_document_is_created():

    metadata = create_test_metadata()


    service = EmbeddingService(

        encoder=FakeEncoder()

    )


    documents, _ = (
        service.create_embeddings(
            metadata
        )
    )


    table_documents = [

        document

        for document in documents

        if document.object_type == "table"

    ]


    assert len(table_documents) == 1


    table = table_documents[0]


    assert table.object_name == "fact_sales"


    assert "net_amount" in table.content