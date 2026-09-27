import pytest
from pydantic import ValidationError

from textSQL.generation.models import (
    GenerationStatus,
    SQLGenerationResult,
)


def test_generated_result_is_valid():

    result = SQLGenerationResult(

        status=GenerationStatus.GENERATED,

        sql=(
            "SELECT COUNT(*) "
            "FROM public.customers;"
        ),

        explanation=(
            "Counts rows from the retrieved "
            "customers table."
        ),

        tables_used=[
            "public.customers"
        ],

        columns_used=[],
    )


    assert (
        result.status
        == GenerationStatus.GENERATED
    )

    assert result.sql is not None


def test_generated_result_requires_sql():

    with pytest.raises(
        ValidationError
    ):

        SQLGenerationResult(

            status=GenerationStatus.GENERATED,

            sql=None,

            explanation=(
                "Generated successfully."
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
            "is ambiguous."
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


def test_clarification_result_cannot_contain_sql():

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
                "How should best customers "
                "be measured?"
            ),
        )


def test_clarification_requires_question():

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

            clarification_question=None,
        )


def test_unanswerable_result_is_valid():

    result = SQLGenerationResult(

        status=(
            GenerationStatus.UNANSWERABLE
        ),

        sql=None,

        explanation=(
            "The retrieved schema does not "
            "contain product lineage for "
            "customer events."
        ),
    )


    assert result.sql is None

    assert (
        result.status
        == GenerationStatus.UNANSWERABLE
    )


def test_unanswerable_result_cannot_contain_sql():

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
                "Required product lineage "
                "is unavailable."
            ),
        )