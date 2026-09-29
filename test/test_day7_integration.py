from textSQL.database.connection import (
    engine,
)

from textSQL.generation.generator import (
    SQLGenerator,
)

from textSQL.generation.models import (
    GenerationStatus,
    SQLGenerationResult,
)

from textSQL.generation.orchestrator import (
    SQLGenerationOrchestrator,
)

from textSQL.llm.client import (
    LLMClient,
)

from textSQL.metadata.models import (
    ColumnMetadata,
    TableMetadata,
)

from textSQL.retrieval.model import (
    RetrievedContext,
)

from textSQL.validation.executor import (
    ReadOnlySQLExecutor,
)

from textSQL.validation.models import (
    SQLValidationStatus,
)

from textSQL.validation.sql_validator import (
    SQLValidator,
)


# ============================================================
# DETERMINISTIC FAKE LLM
# ============================================================


class SequenceLLMClient(
    LLMClient
):

    def __init__(
        self,
        responses: list[str],
    ):

        self.responses = list(
            responses
        )

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


        if not self.responses:

            raise AssertionError(
                "LLM called more times "
                "than expected."
            )


        return self.responses.pop(0)


# ============================================================
# RETRIEVED CONTEXT
# ============================================================


def build_registered_customers_context():

    customers = TableMetadata(

        name="customers",

        schema_name="public",

        primary_keys=[
            "customer_id"
        ],

        columns=[

            ColumnMetadata(

                name="customer_id",

                data_type="BIGINT",

                nullable=False,

                is_primary_key=True,
            ),

            ColumnMetadata(

                name="user_id",

                data_type="BIGINT",

                nullable=True,
            ),
        ],
    )


    return RetrievedContext(

        question=(
            "How many customers "
            "are registered?"
        ),

        tables=[
            customers
        ],

        relationships=[],

        metrics=[],

        join_paths=[],

        trace=[],
    )


# ============================================================
# GENERATION RESPONSES
# ============================================================


def valid_generation_response():

    return """
    {
        "status": "generated",
        "sql": "SELECT COUNT(*) AS count FROM public.customers WHERE user_id IS NOT NULL;",
        "explanation": "GENERATED: Registered customers are customers whose user_id is not null.",
        "tables_used": [
            "public.customers"
        ],
        "columns_used": [
            "public.customers.user_id"
        ],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


def invalid_generation_response():

    return """
    {
        "status": "generated",
        "sql": "SELECT COUNT(*) AS count FROM public.customers WHERE fake_status = 'registered';",
        "explanation": "GENERATED: Counts registered customers.",
        "tables_used": [
            "public.customers"
        ],
        "columns_used": [
            "public.customers.user_id"
        ],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


def repaired_generation_response():

    return """
    {
        "status": "generated",
        "sql": "SELECT COUNT(*) AS count FROM public.customers WHERE user_id IS NOT NULL;",
        "explanation": "GENERATED: Corrected the query to use the retrieved user_id registration rule.",
        "tables_used": [
            "public.customers"
        ],
        "columns_used": [
            "public.customers.user_id"
        ],
        "assumptions": [],
        "clarification_question": null,
        "clarification_options": []
    }
    """


# ============================================================
# HELPERS
# ============================================================


def build_validator():

    return SQLValidator(

        engine=engine,

        # Integration-test ceilings only.
        #
        # These values are intentionally generous so this
        # test verifies pipeline integration rather than
        # calibrating production planner policy.

        max_total_cost=(
            1_000_000_000
        ),

        max_plan_rows=(
            10_000_000
        ),

        max_rows=500,

        max_joins=6,

        max_subquery_depth=3,
    )


# ============================================================
# VALID FIRST GENERATION
# ============================================================


def test_day7_valid_generation_to_execution():

    llm = SequenceLLMClient(
        responses=[
            valid_generation_response()
        ]
    )


    generator = SQLGenerator(
        llm_client=llm
    )


    validator = (
        build_validator()
    )


    workflow = (
        SQLGenerationOrchestrator(

            generator=generator,

            validator=validator,
        )
    )


    workflow_result = (
        workflow
        .generate_and_validate(

            build_registered_customers_context()
        )
    )


    # --------------------------------------------------------
    # GENERATION
    # --------------------------------------------------------

    assert (
        workflow_result
        .final_generation
        .status
        ==
        GenerationStatus.GENERATED
    )


    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    assert (
        workflow_result
        .final_validation
        is not None
    )


    assert (
        workflow_result
        .final_validation
        .status
        ==
        SQLValidationStatus.VALID
    )


    assert (
        workflow_result
        .repair_attempted
        is False
    )


    safe_sql = (
        workflow_result
        .final_validation
        .safe_sql
    )


    assert (
        safe_sql
        is not None
    )


    assert (
        "LIMIT 500"
        in safe_sql.upper()
    )


    # --------------------------------------------------------
    # EXECUTION
    # --------------------------------------------------------

    execution = (

        ReadOnlySQLExecutor(
            engine
        )

        .execute(
            safe_sql
        )
    )


    assert (
        execution.row_count
        ==
        1
    )


    assert (
        "count"
        in execution.columns
    )


    assert (
        isinstance(
            execution.rows[0][
                "count"
            ],
            int,
        )
    )


    # One initial LLM generation only.
    assert (
        len(llm.calls)
        ==
        1
    )


# ============================================================
# INVALID → REPAIR → VALID → EXECUTE
# ============================================================


def test_day7_invalid_generation_repairs_once_and_executes():

    llm = SequenceLLMClient(

        responses=[

            invalid_generation_response(),

            repaired_generation_response(),
        ]
    )


    generator = SQLGenerator(
        llm_client=llm
    )


    validator = (
        build_validator()
    )


    workflow_result = (

        SQLGenerationOrchestrator(

            generator=generator,

            validator=validator,
        )

        .generate_and_validate(

            build_registered_customers_context()
        )
    )


    # --------------------------------------------------------
    # REPAIR OCCURRED
    # --------------------------------------------------------

    assert (
        workflow_result
        .repair_attempted
        is True
    )


    assert (
        len(llm.calls)
        ==
        2
    )


    # --------------------------------------------------------
    # REPAIRED GENERATION
    # --------------------------------------------------------

    assert (
        workflow_result
        .final_generation
        .status
        ==
        GenerationStatus.GENERATED
    )


    assert (
        "user_id IS NOT NULL"
        in
        workflow_result
        .final_generation
        .sql
    )


    # --------------------------------------------------------
    # FINAL VALIDATION
    # --------------------------------------------------------

    assert (
        workflow_result
        .final_validation
        is not None
    )


    assert (
        workflow_result
        .final_validation
        .status
        ==
        SQLValidationStatus.VALID
    )


    safe_sql = (
        workflow_result
        .final_validation
        .safe_sql
    )


    assert (
        safe_sql
        is not None
    )


    # --------------------------------------------------------
    # REAL EXECUTION
    # --------------------------------------------------------

    execution = (

        ReadOnlySQLExecutor(
            engine
        )

        .execute(
            safe_sql
        )
    )


    assert (
        execution.row_count
        ==
        1
    )


    assert (
        "count"
        in execution.columns
    )