import json

import pytest
from pydantic import ValidationError

from textSQL.generation.models import (
    GenerationStatus,
    SQLGenerationResult,
)

from textSQL.generation.context_builder import (
    GenerationContextBuilder,
)

from textSQL.generation.context_formatter import (
    ContextFormatter,
)

from textSQL.metadata.models import (
    ColumnMetadata,
    TableMetadata,
    JoinConditionMetadata,
    RelationshipMetadata,
    MetricMetadata,
)

from textSQL.retrieval.model import (
    RetrievedContext,
    RetrievalTrace,
    JoinPath,
)
from textSQL.generation.prompt_builder import (
    PromptBuilder,
)

# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def fact_sales_table():

    return TableMetadata(

        name="fact_sales",

        schema_name="warehouse",

        description=(
            "Analytical sales fact table."
        ),

        business_role=(
            "Stores sales measures "
            "at transaction grain."
        ),

        primary_keys=[
            "sales_key"
        ],

        columns=[

            ColumnMetadata(
                name="sales_key",
                data_type="BIGINT",
                nullable=False,
                is_primary_key=True,
                is_unique=True,
            ),

            ColumnMetadata(
                name="customer_key",
                data_type="INTEGER",
                nullable=False,
            ),

            ColumnMetadata(
                name="revenue",
                data_type="NUMERIC",
                nullable=False,
                business_meaning=(
                    "Net merchandise revenue."
                ),
            ),
        ],
    )


@pytest.fixture
def dim_customer_table():

    return TableMetadata(

        name="dim_customer",

        schema_name="warehouse",

        description=(
            "Analytical customer dimension."
        ),

        primary_keys=[
            "customer_key"
        ],

        columns=[

            ColumnMetadata(
                name="customer_key",
                data_type="INTEGER",
                nullable=False,
                is_primary_key=True,
                is_unique=True,
            ),

            ColumnMetadata(
                name="customer_name",
                data_type="VARCHAR",
                nullable=False,
            ),

            ColumnMetadata(
                name="country",
                data_type="VARCHAR",
                nullable=True,
            ),
        ],
    )


@pytest.fixture
def customer_relationship():

    return RelationshipMetadata(

        source_schema="warehouse",

        source_table="fact_sales",

        target_schema="warehouse",

        target_table="dim_customer",

        relationship_type="many-to-one",

        source_cardinality="many",

        target_cardinality="one",

        source_optional=False,

        target_optional=False,

        foreign_keys=[
            "customer_key"
        ],

        join_conditions=[

            JoinConditionMetadata(

                source_schema="warehouse",

                source_table="fact_sales",

                source_column="customer_key",

                target_schema="warehouse",

                target_table="dim_customer",

                target_column="customer_key",
            )
        ],

        # These are deliberately present in
        # retrieval metadata but should NOT
        # survive into GenerationContext.

        reasoning=(
            "Inferred from database "
            "foreign-key metadata."
        ),

        confidence=0.99,

        description=(
            "Internal relationship "
            "description."
        ),

        business_meaning=(
            "Each sales fact belongs "
            "to one customer."
        ),
    )


@pytest.fixture
def revenue_metric():

    return MetricMetadata(

        name="revenue",

        description=(
            "Net merchandise revenue "
            "after item discounts and "
            "refund adjustments."
        ),

        domain="sales",

        formula=(
            "SUM(fact_sales.revenue)"
        ),

        authoritative_source=(
            "fact_sales"
        ),

        required_tables=[
            "fact_sales"
        ],

        required_columns=[
            "revenue"
        ],

        required_metrics=[],

        business_rules=[
            (
                "Use warehouse fact revenue "
                "for analytical revenue."
            ),
            (
                "Revenue is adjusted "
                "for refunds."
            ),
        ],

        forbidden_sources=[
            "orders"
        ],

        synonyms=[
            "sales",
            "net sales",
        ],
    )


@pytest.fixture
def retrieved_context(
    fact_sales_table,
    dim_customer_table,
    customer_relationship,
    revenue_metric,
):

    return RetrievedContext(

        question=(
            "Show revenue by customer."
        ),

        tables=[
            fact_sales_table,
            dim_customer_table,
        ],

        relationships=[
            customer_relationship
        ],

        metrics=[
            revenue_metric
        ],

        join_paths=[

            JoinPath(

                tables=[
                    "warehouse.fact_sales",
                    "warehouse.dim_customer",
                ],

                relationships=[
                    customer_relationship
                ],
            )
        ],

        trace=[

            RetrievalTrace(

                object_type="metric",

                object_name="revenue",

                score=0.054,

                matched_terms=[
                    "revenue"
                ],
            ),

            RetrievalTrace(

                object_type="table",

                object_name="dim_customer",

                score=0.031,

                matched_terms=[
                    "customer"
                ],
            ),
        ],
    )


# ============================================================
# SQL GENERATION RESULT
# ============================================================


def test_generated_result_is_valid():

    result = SQLGenerationResult(

        status=(
            GenerationStatus.GENERATED
        ),

        sql=(
            "SELECT COUNT(*) "
            "FROM public.customers;"
        ),

        explanation=(
            "Counts customers from the "
            "retrieved customer table."
        ),

        tables_used=[
            "public.customers"
        ],

        columns_used=[],
    )


    assert (
        result.status
        ==
        GenerationStatus.GENERATED
    )

    assert result.sql is not None


def test_generated_result_requires_sql():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=(
                GenerationStatus.GENERATED
            ),

            sql=None,

            explanation=(
                "Generated query."
            ),
        )


def test_generated_result_cannot_request_clarification():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=(
                GenerationStatus.GENERATED
            ),

            sql=(
                "SELECT COUNT(*) "
                "FROM public.customers;"
            ),

            explanation=(
                "Counts customers."
            ),

            clarification_question=(
                "What do you mean?"
            ),
        )


def test_clarification_result_is_valid():

    result = SQLGenerationResult(

        status=(
            GenerationStatus
            .CLARIFICATION_REQUIRED
        ),

        sql=None,

        explanation=(
            "The meaning of best customer "
            "is materially ambiguous."
        ),

        clarification_question=(
            "How should best customers "
            "be measured?"
        ),

        clarification_options=[
            "revenue",
            "profit",
            "order frequency",
        ],
    )


    assert result.sql is None

    assert (
        result.clarification_question
        is not None
    )


def test_clarification_result_requires_question():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=(
                GenerationStatus
                .CLARIFICATION_REQUIRED
            ),

            sql=None,

            explanation=(
                "Question is ambiguous."
            ),
        )


def test_clarification_result_cannot_have_sql():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=(
                GenerationStatus
                .CLARIFICATION_REQUIRED
            ),

            sql=(
                "SELECT * "
                "FROM public.customers;"
            ),

            explanation=(
                "Question is ambiguous."
            ),

            clarification_question=(
                "How should customers "
                "be ranked?"
            ),
        )


def test_unanswerable_result_is_valid():

    result = SQLGenerationResult(

        status=(
            GenerationStatus.UNANSWERABLE
        ),

        sql=None,

        explanation=(
            "The available schema does "
            "not contain product lineage "
            "for customer events."
        ),
    )


    assert result.sql is None

    assert (
        result.status
        ==
        GenerationStatus.UNANSWERABLE
    )


def test_unanswerable_result_cannot_have_sql():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=(
                GenerationStatus.UNANSWERABLE
            ),

            sql=(
                "SELECT * "
                "FROM public.customer_events;"
            ),

            explanation=(
                "Required information "
                "is unavailable."
            ),
        )


def test_unanswerable_result_cannot_request_clarification():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=(
                GenerationStatus.UNANSWERABLE
            ),

            sql=None,

            explanation=(
                "Required information "
                "does not exist."
            ),

            clarification_question=(
                "Which product?"
            ),
        )


# ============================================================
# GENERATION CONTEXT BUILDER
# ============================================================


def test_context_builder_returns_generation_context(
    retrieved_context,
):

    builder = (
        GenerationContextBuilder()
    )

    context = builder.build(
        retrieved_context
    )


    assert len(
        context.tables
    ) == 2

    assert len(
        context.relationships
    ) == 1

    assert len(
        context.join_paths
    ) == 1

    assert len(
        context.metrics
    ) == 1


# ============================================================
# TABLE PROJECTION
# ============================================================


def test_context_builder_preserves_table_identity(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    table_names = {

        table.qualified_name

        for table
        in context.tables
    }


    assert (
        "warehouse.fact_sales"
        in table_names
    )

    assert (
        "warehouse.dim_customer"
        in table_names
    )


def test_context_builder_preserves_columns(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    fact_sales = next(

        table

        for table
        in context.tables

        if (
            table.qualified_name
            ==
            "warehouse.fact_sales"
        )
    )


    columns = {

        column.name:
            column

        for column
        in fact_sales.columns
    }


    assert "sales_key" in columns

    assert "customer_key" in columns

    assert "revenue" in columns


    assert (
        columns["sales_key"]
        .is_primary_key
        is True
    )


    assert (
        columns["revenue"]
        .data_type
        ==
        "NUMERIC"
    )


def test_context_builder_preserves_column_semantics(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    fact_sales = next(

        table

        for table
        in context.tables

        if (
            table.qualified_name
            ==
            "warehouse.fact_sales"
        )
    )


    revenue_column = next(

        column

        for column
        in fact_sales.columns

        if column.name == "revenue"
    )


    assert (
        revenue_column.business_meaning
        ==
        "Net merchandise revenue."
    )


# ============================================================
# RELATIONSHIP PROJECTION
# ============================================================


def test_context_builder_preserves_relationship(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    relationship = (
        context.relationships[0]
    )


    assert (
        relationship.source_table
        ==
        "warehouse.fact_sales"
    )

    assert (
        relationship.target_table
        ==
        "warehouse.dim_customer"
    )


    assert (
        relationship.relationship_type
        ==
        "many-to-one"
    )


def test_context_builder_preserves_exact_join_condition(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    relationship = (
        context.relationships[0]
    )


    assert (
        len(
            relationship.join_conditions
        )
        ==
        1
    )


    join = (
        relationship.join_conditions[0]
    )


    assert (
        join.source_column
        ==
        "warehouse.fact_sales.customer_key"
    )


    assert (
        join.target_column
        ==
        "warehouse.dim_customer.customer_key"
    )


def test_context_builder_preserves_cardinality(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    relationship = (
        context.relationships[0]
    )


    assert (
        relationship.source_cardinality
        ==
        "many"
    )

    assert (
        relationship.target_cardinality
        ==
        "one"
    )


def test_relationship_internal_diagnostics_are_removed(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    relationship = (
        context.relationships[0]
    )


    dumped = (
        relationship.model_dump()
    )


    assert (
        "reasoning"
        not in dumped
    )

    assert (
        "confidence"
        not in dumped
    )

    assert (
        "description"
        not in dumped
    )


# ============================================================
# JOIN PATH PROJECTION
# ============================================================


def test_context_builder_preserves_join_path(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    path = (
        context.join_paths[0]
    )


    assert (
        path.tables
        ==
        [
            "warehouse.fact_sales",
            "warehouse.dim_customer",
        ]
    )


def test_join_path_references_relationship_id(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    path = (
        context.join_paths[0]
    )

    relationship = (
        context.relationships[0]
    )


    assert (
        relationship.relationship_id
        in path.relationship_ids
    )


# ============================================================
# METRIC PROJECTION
# ============================================================


def test_context_builder_preserves_metric(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    metric = (
        context.metrics[0]
    )


    assert (
        metric.name
        ==
        "revenue"
    )

    assert (
        metric.domain
        ==
        "sales"
    )

    assert (
        metric.authoritative_source
        ==
        "fact_sales"
    )


def test_context_builder_preserves_metric_formula(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    metric = (
        context.metrics[0]
    )


    assert (
        metric.formula
        ==
        "SUM(fact_sales.revenue)"
    )


def test_context_builder_preserves_business_rules(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    metric = (
        context.metrics[0]
    )


    assert (
        "Use warehouse fact revenue "
        "for analytical revenue."
        in metric.business_rules
    )


def test_context_builder_preserves_forbidden_sources(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    metric = (
        context.metrics[0]
    )


    assert (
        "orders"
        in metric.forbidden_sources
    )


# ============================================================
# TRUST BOUNDARY
# ============================================================


def test_generation_context_does_not_include_trace(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    dumped = (
        context.model_dump()
    )


    assert (
        "trace"
        not in dumped
    )


def test_generation_context_does_not_include_question(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    dumped = (
        context.model_dump()
    )


    assert (
        "question"
        not in dumped
    )


def test_generation_context_only_has_approved_sections(
    retrieved_context,
):

    context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    assert (
        set(
            context.model_dump().keys()
        )
        ==
        {
            "tables",
            "relationships",
            "join_paths",
            "metrics",
            "temporal_constraints",
        }
    )


# ============================================================
# CONTEXT FORMATTER
# ============================================================


def test_formatter_returns_valid_json(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    assert isinstance(
        parsed,
        dict,
    )


def test_formatter_contains_all_generation_sections(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    assert "tables" in parsed

    assert "relationships" in parsed

    assert "join_paths" in parsed

    assert "metrics" in parsed


def test_formatter_contains_qualified_tables(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    table_names = {

        table["qualified_name"]

        for table
        in parsed["tables"]
    }


    assert (
        "warehouse.fact_sales"
        in table_names
    )

    assert (
        "warehouse.dim_customer"
        in table_names
    )


def test_formatter_contains_exact_join(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    join = (
        parsed[
            "relationships"
        ][0][
            "join_conditions"
        ][0]
    )


    assert (
        join["source_column"]
        ==
        "warehouse.fact_sales.customer_key"
    )


    assert (
        join["target_column"]
        ==
        "warehouse.dim_customer.customer_key"
    )


def test_formatter_contains_join_path(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    path = (
        parsed["join_paths"][0]
    )


    assert (
        path["tables"]
        ==
        [
            "warehouse.fact_sales",
            "warehouse.dim_customer",
        ]
    )


def test_formatter_contains_metric_rules(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    metric = (
        parsed["metrics"][0]
    )


    assert (
        metric["name"]
        ==
        "revenue"
    )

    assert (
        "orders"
        in metric[
            "forbidden_sources"
        ]
    )

    assert (
        len(
            metric[
                "business_rules"
            ]
        )
        >= 1
    )


def test_formatter_does_not_leak_retrieval_trace(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    assert (
        "0.054"
        not in formatted
    )

    assert (
        "0.031"
        not in formatted
    )

    assert (
        '"trace"'
        not in formatted
    )

    assert (
        '"matched_terms"'
        not in formatted
    )


def test_formatter_does_not_leak_relationship_diagnostics(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    assert (
        '"reasoning"'
        not in formatted
    )

    assert (
        '"confidence"'
        not in formatted
    )

    assert (
        "0.99"
        not in formatted
    )


# ============================================================
# OPTIONAL / EMPTY DATA
# ============================================================


def test_empty_context_formats_successfully():

    retrieved_context = (
        RetrievedContext(
            question="test",
        )
    )


    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    assert (
        parsed["tables"]
        ==
        []
    )

    assert (
        parsed["relationships"]
        ==
        []
    )

    assert (
        parsed["join_paths"]
        ==
        []
    )

    assert (
        parsed["metrics"]
        ==
        []
    )


def test_none_optional_values_are_not_serialized():

    table = TableMetadata(

        name="customers",

        schema_name="public",

        columns=[

            ColumnMetadata(
                name="customer_id",
                data_type="INTEGER",
                nullable=False,
                is_primary_key=True,
            )
        ],

        primary_keys=[
            "customer_id"
        ],
    )


    retrieved_context = (
        RetrievedContext(

            question=(
                "How many customers?"
            ),

            tables=[
                table
            ],
        )
    )


    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )


    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted
    )


    table_json = (
        parsed["tables"][0]
    )


    assert (
        "description"
        not in table_json
    )

    assert (
        "business_role"
        not in table_json
    )


# ============================================================
# COMPLETE GENERATION-CONTEXT BOUNDARY
# ============================================================


def test_complete_generation_context_boundary(
    retrieved_context,
):

    builder = (
        GenerationContextBuilder()
    )

    formatter = (
        ContextFormatter()
    )


    generation_context = (
        builder.build(
            retrieved_context
        )
    )


    formatted_context = (
        formatter.format(
            generation_context
        )
    )


    parsed = json.loads(
        formatted_context
    )


    # Trusted database objects survive.

    assert (
        parsed["tables"][0]
        ["qualified_name"]
        ==
        "warehouse.fact_sales"
    )


    assert (
        parsed["metrics"][0]
        ["name"]
        ==
        "revenue"
    )


    assert (
        parsed["relationships"][0]
        ["join_conditions"][0]
        ["source_column"]
        ==
        "warehouse.fact_sales.customer_key"
    )


    # Retrieval/debug information does not.

    assert (
        "trace"
        not in parsed
    )

    assert (
        "question"
        not in parsed
    )

    assert (
        "reasoning"
        not in (
            parsed[
                "relationships"
            ][0]
        )
    )

    assert (
        "confidence"
        not in (
            parsed[
                "relationships"
            ][0]
        )
    )

# ============================================================
# PROMPT BUILDER
# ============================================================


def test_prompt_builder_returns_typed_prompt(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )

    formatted_context = (
        ContextFormatter()
        .format(
            generation_context
        )
    )


    prompt = (
        PromptBuilder()
        .build(
            question=(
                retrieved_context.question
            ),
            formatted_context=(
                formatted_context
            ),
        )
    )


    assert (
        prompt.system_prompt
    )

    assert (
        prompt.user_prompt
    )


def test_system_prompt_specifies_postgresql():

    prompt_builder = (
        PromptBuilder()
    )


    assert (
        "PostgreSQL"
        in prompt_builder.SYSTEM_PROMPT
    )


def test_system_prompt_forbids_invention():

    system_prompt = (
        PromptBuilder.SYSTEM_PROMPT
    )


    assert (
        "Never invent tables"
        in system_prompt
    )


def test_system_prompt_requires_read_only_sql():

    system_prompt = (
        PromptBuilder.SYSTEM_PROMPT
    )


    assert (
        "read-only"
        in system_prompt
    )

    assert (
        "INSERT"
        in system_prompt
    )

    assert (
        "DELETE"
        in system_prompt
    )

    assert (
        "DROP"
        in system_prompt
    )


def test_system_prompt_defines_clarification_behavior():

    assert (
        "CLARIFICATION_REQUIRED"
        in PromptBuilder.SYSTEM_PROMPT
    )


def test_system_prompt_defines_unanswerable_behavior():

    assert (
        "UNANSWERABLE"
        in PromptBuilder.SYSTEM_PROMPT
    )


def test_system_prompt_requires_qualified_tables():

    assert (
        "fully qualified"
        in PromptBuilder.SYSTEM_PROMPT
    )


def test_user_prompt_contains_question(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )

    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )

    prompt = (
        PromptBuilder()
        .build(
            retrieved_context.question,
            formatted,
        )
    )


    assert (
        retrieved_context.question
        in prompt.user_prompt
    )


def test_user_prompt_contains_database_context(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )

    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )

    prompt = (
        PromptBuilder()
        .build(
            retrieved_context.question,
            formatted,
        )
    )


    assert (
        "warehouse.fact_sales"
        in prompt.user_prompt
    )

    assert (
        "warehouse.dim_customer"
        in prompt.user_prompt
    )

    assert (
        "revenue"
        in prompt.user_prompt
    )


def test_user_prompt_does_not_contain_retrieval_trace(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )

    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )

    prompt = (
        PromptBuilder()
        .build(
            retrieved_context.question,
            formatted,
        )
    )


    assert (
        "0.054"
        not in prompt.user_prompt
    )

    assert (
        "0.031"
        not in prompt.user_prompt
    )

    assert (
        '"trace"'
        not in prompt.user_prompt
    )


def test_question_is_separate_from_system_prompt(
    retrieved_context,
):

    generation_context = (
        GenerationContextBuilder()
        .build(
            retrieved_context
        )
    )

    formatted = (
        ContextFormatter()
        .format(
            generation_context
        )
    )

    prompt = (
        PromptBuilder()
        .build(
            retrieved_context.question,
            formatted,
        )
    )


    assert (
        retrieved_context.question
        not in prompt.system_prompt
    )

    assert (
        retrieved_context.question
        in prompt.user_prompt
    )

def test_generated_result_cannot_use_status_as_sql():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=(
                GenerationStatus.GENERATED
            ),

            sql="UNANSWERABLE",

            explanation=(
                "Required information "
                "is unavailable."
            ),
        )

def test_prompt_forbids_join_inference_without_relationship():

    assert (
        "Never infer a join"
        in PromptBuilder.SYSTEM_PROMPT
    )


def test_prompt_forbids_invented_fixed_dates():

    assert (
        "Never invent fixed calendar dates"
        in PromptBuilder.SYSTEM_PROMPT
    )


def test_prompt_requires_full_grounding_for_generated():

    assert (
        "GENERATED means the query is fully supported"
        in PromptBuilder.SYSTEM_PROMPT
    )


def test_prompt_forbids_status_inside_sql():

    assert (
        "Never place status labels"
        in PromptBuilder.SYSTEM_PROMPT
    )

from textSQL.generation.output_normalizer import GenerationOutputNormalizer

def test_normalizer_does_not_repair_incomplete_output():

    raw = """
    {
        "status": "generated"
    }
    """


    normalized = (
        GenerationOutputNormalizer()
        .normalize(raw)
    )


    data = json.loads(
        normalized
    )


    assert (
        data["status"]
        ==
        "generated"
    )

    assert (
        "explanation"
        not in data
    )

def test_normalizer_does_not_repair_invalid_status():

    raw = """
    {
        "status": "something_invalid"
    }
    """


    normalized = (
        GenerationOutputNormalizer()
        .normalize(raw)
    )


    data = json.loads(
        normalized
    )


    assert (
        data["status"]
        ==
        "something_invalid"
    )
def test_generation_context_preserves_allowed_values():

    column = ColumnMetadata(
        name="status",
        data_type="VARCHAR",
        nullable=False,
        allowed_values=[
            "state_a",
            "state_b",
        ],
    )

    table = TableMetadata(
        name="example",
        schema_name="public",
        columns=[
            column
        ],
    )

    retrieved = RetrievedContext(
        question="show state a rows",
        tables=[
            table
        ],
    )


    context = (
        GenerationContextBuilder()
        .build(
            retrieved
        )
    )


    generated_column = (
        context.tables[0]
        .columns[0]
    )


    assert (
        generated_column.allowed_values
        ==
        [
            "state_a",
            "state_b",
        ]
    )
    formatted = (
    ContextFormatter()
    .format(
        context
    )
)

    assert '"allowed_values"' in formatted
    assert '"state_a"' in formatted