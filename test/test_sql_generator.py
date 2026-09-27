import pytest

from textSQL.generation.generator import (
    SQLGenerator,
)

from textSQL.generation.models import (
    GenerationStatus,
    SQLGenerationResult,
)

from textSQL.generation.errors import (
    InvalidStructuredOutputError,
    GenerationGroundingError,
)

from textSQL.llm.client import (
    LLMClient,
)

from textSQL.llm.errors import (
    LLMProviderError,
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
    JoinPath,
    RetrievalTrace,
)


# ============================================================
# FAKE LLM CLIENT
# ============================================================


class FakeLLMClient(LLMClient):

    def __init__(
        self,
        response: str | None = None,
        error: Exception | None = None,
    ):

        self.response = response

        self.error = error

        self.calls = []


    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema=None,
    ) -> str:

        self.calls.append(
            {
                "system_prompt":
                    system_prompt,

                "user_prompt":
                    user_prompt,

                "response_schema":
                    response_schema,
            }
        )


        if self.error is not None:
            raise self.error


        return self.response


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def fact_sales_table():

    return TableMetadata(

        name="fact_sales",

        schema_name="warehouse",

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
            ),
        ],
    )


@pytest.fixture
def dim_customer_table():

    return TableMetadata(

        name="dim_customer",

        schema_name="warehouse",

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
    )


@pytest.fixture
def revenue_metric():

    return MetricMetadata(

        name="revenue",

        description=(
            "Net merchandise revenue."
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
                "Use the analytical "
                "sales fact for revenue."
            )
        ],

        forbidden_sources=[
            "orders"
        ],

        synonyms=[
            "sales"
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

                score=0.05,
            )
        ],
    )


# ============================================================
# HELPERS
# ============================================================


def build_generated_response():

    return """
    {
        "status": "generated",
        "sql": "SELECT dc.customer_name, SUM(fs.revenue) AS revenue FROM warehouse.fact_sales AS fs JOIN warehouse.dim_customer AS dc ON fs.customer_key = dc.customer_key GROUP BY dc.customer_name;",
        "explanation": "Uses the retrieved revenue metric and the supplied customer relationship.",
        "tables_used": [
            "warehouse.fact_sales",
            "warehouse.dim_customer"
        ],
        "columns_used": [
            "warehouse.fact_sales.revenue",
            "warehouse.fact_sales.customer_key",
            "warehouse.dim_customer.customer_key",
            "warehouse.dim_customer.customer_name"
        ],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


# ============================================================
# SUCCESSFUL GENERATION
# ============================================================


def test_generator_returns_typed_result(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    generator = SQLGenerator(
        llm_client=llm
    )


    result = generator.generate(
        retrieved_context
    )


    assert isinstance(
        result,
        SQLGenerationResult,
    )


    assert (
        result.status
        ==
        GenerationStatus.GENERATED
    )


    assert result.sql is not None


def test_generator_preserves_generated_sql(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    result = (
        SQLGenerator(llm)
        .generate(
            retrieved_context
        )
    )


    assert (
        "warehouse.fact_sales"
        in result.sql
    )

    assert (
        "warehouse.dim_customer"
        in result.sql
    )


# ============================================================
# LLM INVOCATION
# ============================================================


def test_generator_calls_llm_once(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    SQLGenerator(
        llm
    ).generate(
        retrieved_context
    )


    assert len(
        llm.calls
    ) == 1


def test_generator_requests_sql_generation_schema(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    SQLGenerator(
        llm
    ).generate(
        retrieved_context
    )


    call = llm.calls[0]


    assert (
        call["response_schema"]
        is SQLGenerationResult
    )


def test_generator_sends_question_to_user_prompt(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    SQLGenerator(
        llm
    ).generate(
        retrieved_context
    )


    call = llm.calls[0]


    assert (
        retrieved_context.question
        in call["user_prompt"]
    )


def test_generator_sends_grounded_context(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    SQLGenerator(
        llm
    ).generate(
        retrieved_context
    )


    prompt = (
        llm.calls[0]
        ["user_prompt"]
    )


    assert (
        "warehouse.fact_sales"
        in prompt
    )

    assert (
        "warehouse.dim_customer"
        in prompt
    )

    assert (
        "customer_key"
        in prompt
    )


def test_generator_does_not_send_retrieval_trace(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    SQLGenerator(
        llm
    ).generate(
        retrieved_context
    )


    prompt = (
        llm.calls[0]
        ["user_prompt"]
    )


    assert (
        '"trace"'
        not in prompt
    )

    assert (
        "0.05"
        not in prompt
    )


# ============================================================
# CLARIFICATION
# ============================================================


def test_generator_returns_clarification():

    context = RetrievedContext(

        question=(
            "Who are our best customers?"
        )
    )


    response = """
    {
        "status": "clarification_required",
        "sql": null,
        "explanation": "Best customers can be measured using different business metrics.",
        "tables_used": [],
        "columns_used": [],
        "assumptions": [],
        "clarification_question": "How should best customers be measured?",
        "clarification_options": [
            "revenue",
            "profit",
            "order frequency"
        ]
    }
    """


    result = (
        SQLGenerator(
            FakeLLMClient(
                response=response
            )
        )
        .generate(
            context
        )
    )


    assert (
        result.status
        ==
        GenerationStatus
        .CLARIFICATION_REQUIRED
    )

    assert result.sql is None

    assert (
        result.clarification_question
        ==
        "How should best customers be measured?"
    )


# ============================================================
# UNANSWERABLE
# ============================================================


def test_generator_returns_unanswerable():

    context = RetrievedContext(

        question=(
            "Which exact product "
            "was viewed most often?"
        )
    )


    response = """
    {
        "status": "unanswerable",
        "sql": null,
        "explanation": "The supplied context does not contain product lineage for customer events.",
        "tables_used": [],
        "columns_used": [],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


    result = (
        SQLGenerator(
            FakeLLMClient(
                response=response
            )
        )
        .generate(
            context
        )
    )


    assert (
        result.status
        ==
        GenerationStatus.UNANSWERABLE
    )

    assert result.sql is None


# ============================================================
# MALFORMED STRUCTURED OUTPUT
# ============================================================


@pytest.mark.parametrize(
    "response",
    [
        "not json",
        "",
        "{",
        '{"status":"generated"}',
        '{"status":"something_invalid"}',
    ],
)
def test_invalid_structured_output_is_rejected(
    retrieved_context,
    response,
):

    llm = FakeLLMClient(
        response=response
    )


    generator = SQLGenerator(
        llm
    )


    with pytest.raises(
        InvalidStructuredOutputError
    ):

        generator.generate(
            retrieved_context
        )


def test_invalid_output_preserves_validation_cause(
    retrieved_context,
):

    llm = FakeLLMClient(
        response="not json"
    )


    with pytest.raises(
        InvalidStructuredOutputError
    ) as error:

        SQLGenerator(
            llm
        ).generate(
            retrieved_context
        )


    assert (
        error.value.__cause__
        is not None
    )


# ============================================================
# PROVIDER FAILURE
# ============================================================


def test_provider_failure_propagates_cleanly(
    retrieved_context,
):

    provider_error = (
        LLMProviderError(
            "LLM provider request failed."
        )
    )


    llm = FakeLLMClient(
        error=provider_error
    )


    with pytest.raises(
        LLMProviderError
    ) as error:

        SQLGenerator(
            llm
        ).generate(
            retrieved_context
        )


    assert (
        error.value
        is provider_error
    )


# ============================================================
# TABLE GROUNDING
# ============================================================


def test_allowed_declared_tables_pass(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    result = (
        SQLGenerator(
            llm
        )
        .generate(
            retrieved_context
        )
    )


    assert (
        "warehouse.fact_sales"
        in result.tables_used
    )


def test_unknown_declared_table_is_rejected(
    retrieved_context,
):

    response = """
    {
        "status": "generated",
        "sql": "SELECT * FROM warehouse.sales_summary;",
        "explanation": "Uses sales summary.",
        "tables_used": [
            "warehouse.sales_summary"
        ],
        "columns_used": [],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


    generator = SQLGenerator(

        FakeLLMClient(
            response=response
        )
    )


    with pytest.raises(
        GenerationGroundingError,
        match=(
            "warehouse.sales_summary"
        ),
    ):

        generator.generate(
            retrieved_context
        )


def test_multiple_unknown_tables_are_reported(
    retrieved_context,
):

    response = """
    {
        "status": "generated",
        "sql": "SELECT 1;",
        "explanation": "Test.",
        "tables_used": [
            "warehouse.fake_sales",
            "public.fake_customers"
        ],
        "columns_used": [],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


    with pytest.raises(
        GenerationGroundingError
    ) as error:

        SQLGenerator(

            FakeLLMClient(
                response=response
            )

        ).generate(
            retrieved_context
        )


    message = str(
        error.value
    )


    assert (
        "warehouse.fake_sales"
        in message
    )

    assert (
        "public.fake_customers"
        in message
    )


# ============================================================
# COLUMN GROUNDING
# ============================================================


def test_allowed_declared_columns_pass(
    retrieved_context,
):

    result = (
        SQLGenerator(

            FakeLLMClient(
                response=(
                    build_generated_response()
                )
            )

        ).generate(
            retrieved_context
        )
    )


    assert (
        "warehouse.fact_sales.revenue"
        in result.columns_used
    )


def test_unknown_declared_column_is_rejected(
    retrieved_context,
):

    response = """
    {
        "status": "generated",
        "sql": "SELECT fs.total_revenue FROM warehouse.fact_sales AS fs;",
        "explanation": "Uses revenue.",
        "tables_used": [
            "warehouse.fact_sales"
        ],
        "columns_used": [
            "warehouse.fact_sales.total_revenue"
        ],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


    with pytest.raises(
        GenerationGroundingError,
        match=(
            "warehouse.fact_sales.total_revenue"
        ),
    ):

        SQLGenerator(

            FakeLLMClient(
                response=response
            )

        ).generate(
            retrieved_context
        )


# ============================================================
# NON-GENERATED STATES DO NOT RUN GROUNDING CHECK
# ============================================================


def test_clarification_does_not_require_declared_objects():

    context = RetrievedContext(

        question=(
            "Who are our best customers?"
        )
    )


    response = """
    {
        "status": "clarification_required",
        "sql": null,
        "explanation": "The ranking metric is ambiguous.",
        "tables_used": [],
        "columns_used": [],
        "assumptions": [],
        "clarification_question": "How should customers be ranked?",
        "clarification_options": [
            "revenue",
            "profit"
        ]
    }
    """


    result = (
        SQLGenerator(

            FakeLLMClient(
                response=response
            )

        ).generate(
            context
        )
    )


    assert (
        result.status
        ==
        GenerationStatus
        .CLARIFICATION_REQUIRED
    )


def test_unanswerable_does_not_require_declared_objects():

    context = RetrievedContext(

        question=(
            "Which product page "
            "was viewed most?"
        )
    )


    response = """
    {
        "status": "unanswerable",
        "sql": null,
        "explanation": "Required product lineage is unavailable.",
        "tables_used": [],
        "columns_used": [],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


    result = (
        SQLGenerator(

            FakeLLMClient(
                response=response
            )

        ).generate(
            context
        )
    )


    assert (
        result.status
        ==
        GenerationStatus.UNANSWERABLE
    )


# ============================================================
# IMPORTANT DAY 6 LIMITATION
# ============================================================


def test_day6_does_not_parse_sql_for_hidden_hallucinations(
    retrieved_context,
):

    """
    This intentionally documents the Day 6
    architectural boundary.

    The model declares an allowed table but
    the SQL itself references a fake table.

    Day 6 does NOT inspect SQL syntax or ASTs.
    Day 7 must detect this.
    """

    response = """
    {
        "status": "generated",
        "sql": "SELECT * FROM warehouse.fake_sales;",
        "explanation": "Test boundary.",
        "tables_used": [
            "warehouse.fact_sales"
        ],
        "columns_used": [],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


    result = (
        SQLGenerator(

            FakeLLMClient(
                response=response
            )

        ).generate(
            retrieved_context
        )
    )


    assert (
        result.status
        ==
        GenerationStatus.GENERATED
    )


    assert (
        "warehouse.fake_sales"
        in result.sql
    )


# ============================================================
# NO EXECUTION RESPONSIBILITY
# ============================================================


def test_generator_only_returns_sql_and_does_not_execute(
    retrieved_context,
):

    """
    SQLGenerator has no database/session/engine
    dependency.

    Successful generation ends by returning
    SQLGenerationResult.
    """

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    generator = SQLGenerator(
        llm_client=llm
    )


    result = generator.generate(
        retrieved_context
    )


    assert isinstance(
        result,
        SQLGenerationResult,
    )

    assert result.sql is not None

    assert len(
        llm.calls
    ) == 1


# ============================================================
# COMPLETE DAY 6 GENERATION FLOW
# ============================================================


def test_complete_generation_pipeline(
    retrieved_context,
):

    llm = FakeLLMClient(
        response=(
            build_generated_response()
        )
    )


    generator = SQLGenerator(
        llm
    )


    result = generator.generate(
        retrieved_context
    )


    # Final typed result.

    assert isinstance(
        result,
        SQLGenerationResult,
    )


    assert (
        result.status
        ==
        GenerationStatus.GENERATED
    )


    # Grounded declared objects.

    assert (
        result.tables_used
        ==
        [
            "warehouse.fact_sales",
            "warehouse.dim_customer",
        ]
    )


    assert (
        "warehouse.fact_sales.revenue"
        in result.columns_used
    )


    # LLM called exactly once.

    assert len(
        llm.calls
    ) == 1


    call = (
        llm.calls[0]
    )


    # Structured-output contract supplied.

    assert (
        call["response_schema"]
        is SQLGenerationResult
    )


    # Stable policy is separate.

    assert (
        "PostgreSQL"
        in call["system_prompt"]
    )


    assert (
        "read-only"
        in call["system_prompt"]
    )


    # Question and database knowledge
    # are request-specific.

    assert (
        retrieved_context.question
        in call["user_prompt"]
    )


    assert (
        "warehouse.fact_sales"
        in call["user_prompt"]
    )


    # Retrieval internals remain hidden.

    assert (
        '"trace"'
        not in call["user_prompt"]
    )

