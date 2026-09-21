from textSQL.retrieval.retriever import (
    Retriever,
)

from textSQL.retrieval.query_encoder import (
    QueryEncoder,
)

from textSQL.embeddings.encoder import (
    EmbeddingEncoder,
)

from textSQL.metadata.models import (
    MetricMetadata,
    TableMetadata,
    ColumnMetadata,
)

from textSQL.retrieval.model import (
    RetrievedContext,
)



class FakeEncoder(EmbeddingEncoder):


    def encode(
        self,
        texts: list[str],
    ):

        return [
            [
                0.1,
                0.2,
                0.3,
            ]
            for _ in texts
        ]



class FakeQueryEncoder:


    def encode_query(
        self,
        question: str,
    ):

        return [
            0.1,
            0.2,
            0.3,
        ]



class FakeVectorResult:


    def __init__(
        self,
        metadata_id,
        object_type,
        object_name,
        score,
    ):

        self.payload = {

            "metadata_id":
                metadata_id,

            "object_type":
                object_type,

            "object_name":
                object_name,

        }

        self.score = score



class FakeVectorStore:


    def search(
        self,
        vector,
        limit,
    ):

        return [

            FakeVectorResult(

                metadata_id=
                "metric_revenue",

                object_type=
                "metric",

                object_name=
                "revenue",

                score=0.95,

            ),

            FakeVectorResult(

                metadata_id=
                "table_fact_sales",

                object_type=
                "table",

                object_name=
                "fact_sales",

                score=0.90,

            ),

        ]



class FakeMetadataIndex:


    def __init__(self):

        self.objects = {


            "metric_revenue":
            MetricMetadata(

                name="revenue",

                domain="sales",

                synonyms=[
                    "sales"
                ],

                description=
                "Revenue metric",

                formula=
                "SUM(amount)",

                authoritative_source=
                "fact_sales",

                required_tables=[
                    "fact_sales"
                ],

                required_columns=[
                    "amount"
                ],

                required_metrics=[],

                business_rules=[],

                forbidden_sources=[],

            ),


            "table_fact_sales":

            TableMetadata(

                name="fact_sales",

                description=
                "Sales fact table",

                business_role=
                "Sales source",

                columns=[

                    ColumnMetadata(

                        name="amount",

                        data_type=
                        "decimal",

                        nullable=False,

                    )

                ],

            )

        }



    def get_object(
        self,
        object_id,
    ):

        return self.objects.get(
            object_id
        )



def test_retriever_returns_context():


    retriever = Retriever(

        query_encoder=
        FakeQueryEncoder(),

        vector_store=
        FakeVectorStore(),

        metadata_index=
        FakeMetadataIndex(),

    )


    context = retriever.retrieve(

        "show revenue"

    )


    assert isinstance(
        context,
        RetrievedContext,
    )



    assert context.question == (
        "show revenue"
    )



def test_metric_is_added_to_context():


    retriever = Retriever(

        FakeQueryEncoder(),

        FakeVectorStore(),

        FakeMetadataIndex(),

    )


    context = retriever.retrieve(
        "show revenue"
    )


    assert len(
        context.metrics
    ) == 1


    assert (
        context.metrics[0].name
        ==
        "revenue"
    )



def test_table_is_added_to_context():


    retriever = Retriever(

        FakeQueryEncoder(),

        FakeVectorStore(),

        FakeMetadataIndex(),

    )


    context = retriever.retrieve(
        "show revenue"
    )


    assert len(
        context.tables
    ) == 1


    assert (
        context.tables[0].name
        ==
        "fact_sales"
    )



def test_trace_is_created():


    retriever = Retriever(

        FakeQueryEncoder(),

        FakeVectorStore(),

        FakeMetadataIndex(),

    )


    context = retriever.retrieve(
        "show revenue"
    )


    assert len(
        context.trace
    ) == 2


    assert (
        context.trace[0].score
        ==
        0.95
    )