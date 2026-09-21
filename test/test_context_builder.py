from textSQL.retrieval.context_builder import (
    ContextBuilder,
)

from textSQL.retrieval.model import (
    FusedCandidate,
)

from textSQL.metadata.models import (
    MetricMetadata,
    TableMetadata,
    ColumnMetadata,
    RelationshipMetadata,
)



class FakeMetadataIndex:


    def __init__(self):

        self.objects = {

            "metric_revenue":
            MetricMetadata(

                name="revenue",

                domain="sales",

                description=
                "Revenue generated from sales",

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

                synonyms=[
                    "sales"
                ],

            ),



            "table_fact_sales":
            TableMetadata(

                name="fact_sales",

                description=
                "Sales fact table",

                business_role=
                "Stores sales transactions",

                columns=[

                    ColumnMetadata(

                        name="amount",

                        data_type=
                        "decimal",

                        nullable=False,

                    )

                ],

            ),



            "relationship_fact_sales_dim_customer":

            RelationshipMetadata(

                source_table=
                "fact_sales",

                target_table=
                "dim_customer",

                relationship_type=
                "many-to-one",

                source_cardinality=
                "many",

                target_cardinality=
                "one",

                through_table=None,

                foreign_keys=[
                    "customer_key"
                ],

                business_meaning=
                "Connect sales to customers",

                description=
                "Sales belong to customers",

            )

        }



    def get_object(
        self,
        object_id: str,
    ):

        return self.objects.get(
            object_id
        )



def test_context_builder_creates_metric_context():


    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
        "show revenue",

        candidates=[

            FusedCandidate(

                object_id=
                "metric_revenue",

                object_type=
                "metric",

                object_name=
                "revenue",

                rrf_score=
                0.05,

                sources=[
                    "dense",
                    "dependency",
                ],

            )

        ]

    )


    assert (
        result.question
        ==
        "show revenue"
    )


    assert len(
        result.metrics
    ) == 1


    assert (
        result.metrics[0].name
        ==
        "revenue"
    )


    assert (
        len(result.tables)
        ==
        0
    )



def test_context_builder_creates_table_context():


    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
        "show sales",

        candidates=[

            FusedCandidate(

                object_id=
                "table_fact_sales",

                object_type=
                "table",

                object_name=
                "fact_sales",

                rrf_score=
                0.04,

                sources=[
                    "dependency"
                ],

            )

        ]

    )


    assert len(
        result.tables
    ) == 1


    assert (
        result.tables[0].name
        ==
        "fact_sales"
    )



def test_context_builder_creates_relationship_context():


    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
        "join sales with customers",

        candidates=[

            FusedCandidate(

                object_id=
                "relationship_fact_sales_dim_customer",

                object_type=
                "relationship",

                object_name=
                "fact_sales_dim_customer",

                rrf_score=
                0.03,

                sources=[
                    "graph"
                ],

            )

        ]

    )


    assert len(
        result.relationships
    ) == 1


    assert (
        result.relationships[0]
        .source_table
        ==
        "fact_sales"
    )


    assert (
        result.relationships[0]
        .target_table
        ==
        "dim_customer"
    )



def test_unknown_objects_are_skipped():


    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
        "unknown",

        candidates=[

            FusedCandidate(

                object_id=
                "does_not_exist",

                object_type=
                "table",

                object_name=
                "unknown",

                rrf_score=
                0.01,

                sources=[
                    "dense"
                ],

            )

        ]

    )


    assert result.tables == []

    assert result.metrics == []

    assert result.relationships == []



def test_trace_is_preserved():


    builder = ContextBuilder(
        FakeMetadataIndex()
    )


    result = builder.build(

        question=
        "show revenue",

        candidates=[

            FusedCandidate(

                object_id=
                "metric_revenue",

                object_type=
                "metric",

                object_name=
                "revenue",

                rrf_score=
                0.05,

                sources=[
                    "dense",
                    "dependency",
                ],

            )

        ]

    )


    assert len(
        result.trace
    ) == 1


    assert (
        result.trace[0].object_name
        ==
        "revenue"
    )


    assert (
        result.trace[0].score
        ==
        0.05
    )