import pytest

from textSQL.generation.models import (
    GenerationContext,
    GenerationStatus,
    SQLGenerationResult,
)

from textSQL.generation.orchestrator import (
    SQLGenerationOrchestrator,
)

from textSQL.retrieval.model import (
    RetrievedContext,
)

from textSQL.validation.models import (
    SQLValidationResult,
    SQLValidationStatus,
    ValidationIssue,
    ValidationIssueCode,
)


# ============================================================
# HELPERS
# ============================================================


def generated_result(
    sql: str = (
        "SELECT customer_id "
        "FROM public.customers"
    ),
):

    return SQLGenerationResult(

        status=(
            GenerationStatus.GENERATED
        ),

        sql=sql,

        explanation=(
            "GENERATED: Test generation."
        ),

        tables_used=[],

        columns_used=[],

        assumptions=[],
    )


def unanswerable_result():

    return SQLGenerationResult(

        status=(
            GenerationStatus.UNANSWERABLE
        ),

        sql=None,

        explanation=(
            "UNANSWERABLE: "
            "The supplied context is insufficient."
        ),
    )


def clarification_result():

    return SQLGenerationResult(

        status=(
            GenerationStatus
            .CLARIFICATION_REQUIRED
        ),

        sql=None,

        explanation=(
            "CLARIFICATION_REQUIRED: "
            "The request is ambiguous."
        ),

        clarification_question=(
            "Which metric should be used?"
        ),

        clarification_options=[
            "revenue",
            "profit",
        ],
    )


def valid_validation(
    safe_sql: str = (
        "SELECT customer_id "
        "FROM public.customers "
        "LIMIT 500"
    ),
):

    return SQLValidationResult(

        status=(
            SQLValidationStatus.VALID
        ),

        issues=[],

        safe_sql=(
            safe_sql
        ),
    )


def invalid_validation():

    return SQLValidationResult(

        status=(
            SQLValidationStatus.INVALID
        ),

        issues=[

            ValidationIssue(

                code=(
                    ValidationIssueCode
                    .UNKNOWN_COLUMN
                ),

                message=(
                    "Unknown column."
                ),

                object_name=(
                    "public.customers.fake_column"
                ),
            )
        ],
    )


def blocked_validation():

    return SQLValidationResult(

        status=(
            SQLValidationStatus.BLOCKED
        ),

        issues=[

            ValidationIssue(

                code=(
                    ValidationIssueCode
                    .DISALLOWED_STATEMENT
                ),

                message=(
                    "Statement is blocked."
                ),
            )
        ],
    )


def retrieved_context():

    return RetrievedContext(

        question=(
            "How many customers are registered?"
        )
    )


# ============================================================
# FAKE GENERATOR
# ============================================================


class FakeGenerator:

    def __init__(
        self,
        initial_result,
        repair_result=None,
    ):

        self.initial_result = (
            initial_result
        )

        self.repair_result = (
            repair_result
        )

        self.context = (
            GenerationContext()
        )


        self.build_calls = 0

        self.generate_calls = 0

        self.repair_calls = 0


        self.generation_contexts = []

        self.repair_contexts = []

        self.repair_validation_results = []


    def build_context(
        self,
        retrieved_context,
    ):

        self.build_calls += 1

        return self.context


    def generate_from_context(
        self,
        question,
        generation_context,
    ):

        self.generate_calls += 1


        self.generation_contexts.append(
            generation_context
        )


        return self.initial_result


    def repair_from_context(
        self,
        question,
        generation_context,
        previous_result,
        validation_result,
    ):

        self.repair_calls += 1


        self.repair_contexts.append(
            generation_context
        )


        self.repair_validation_results.append(
            validation_result
        )


        if self.repair_result is None:

            raise AssertionError(
                "Unexpected repair call"
            )


        return self.repair_result


# ============================================================
# FAKE VALIDATOR
# ============================================================


class FakeValidator:

    def __init__(
        self,
        results,
    ):

        self.results = list(
            results
        )

        self.calls = 0

        self.received_sql = []

        self.received_contexts = []


    def validate(
        self,
        sql,
        context,
    ):

        self.calls += 1


        self.received_sql.append(
            sql
        )


        self.received_contexts.append(
            context
        )


        if not self.results:

            raise AssertionError(
                "Validator called more times "
                "than expected"
            )


        return self.results.pop(0)


# ============================================================
# VALID INITIAL SQL
# ============================================================


def test_valid_initial_generation_stops_without_repair():

    generator = FakeGenerator(

        initial_result=(
            generated_result()
        )
    )


    validator = FakeValidator(
        [
            valid_validation()
        ]
    )


    result = (

        SQLGenerationOrchestrator(
            generator=generator,
            validator=validator,
        )

        .generate_and_validate(
            retrieved_context()
        )
    )


    assert (
        result.final_validation.status
        ==
        SQLValidationStatus.VALID
    )


    assert (
        result.repair_attempted
        is False
    )


    assert (
        generator.build_calls
        ==
        1
    )

    assert (
        generator.generate_calls
        ==
        1
    )

    assert (
        generator.repair_calls
        ==
        0
    )

    assert (
        validator.calls
        ==
        1
    )


# ============================================================
# BLOCKED INITIAL SQL
# ============================================================


def test_blocked_initial_generation_is_never_repaired():

    generator = FakeGenerator(

        initial_result=(
            generated_result(
                "DELETE FROM public.customers"
            )
        )
    )


    validator = FakeValidator(
        [
            blocked_validation()
        ]
    )


    result = (

        SQLGenerationOrchestrator(
            generator=generator,
            validator=validator,
        )

        .generate_and_validate(
            retrieved_context()
        )
    )


    assert (
        result.final_validation.status
        ==
        SQLValidationStatus.BLOCKED
    )


    assert (
        result.repair_attempted
        is False
    )


    assert (
        generator.repair_calls
        ==
        0
    )

    assert (
        validator.calls
        ==
        1
    )


# ============================================================
# INVALID → REPAIR → VALID
# ============================================================


def test_invalid_generation_is_repaired_once():

    repaired_sql = (
        "SELECT customer_id "
        "FROM public.customers"
    )


    generator = FakeGenerator(

        initial_result=(
            generated_result(
                "SELECT fake_column "
                "FROM public.customers"
            )
        ),

        repair_result=(
            generated_result(
                repaired_sql
            )
        ),
    )


    validator = FakeValidator(
        [
            invalid_validation(),
            valid_validation(
                (
                    repaired_sql
                    +
                    " LIMIT 500"
                )
            ),
        ]
    )


    result = (

        SQLGenerationOrchestrator(
            generator=generator,
            validator=validator,
        )

        .generate_and_validate(
            retrieved_context()
        )
    )


    assert (
        result.repair_attempted
        is True
    )


    assert (
        result.final_validation.status
        ==
        SQLValidationStatus.VALID
    )


    assert (
        generator.generate_calls
        ==
        1
    )

    assert (
        generator.repair_calls
        ==
        1
    )

    assert (
        validator.calls
        ==
        2
    )


# ============================================================
# SECOND INVALID → STOP
# ============================================================


def test_second_invalid_result_stops_without_second_repair():

    generator = FakeGenerator(

        initial_result=(
            generated_result(
                "SELECT fake_column "
                "FROM public.customers"
            )
        ),

        repair_result=(
            generated_result(
                "SELECT another_fake_column "
                "FROM public.customers"
            )
        ),
    )


    validator = FakeValidator(
        [
            invalid_validation(),
            invalid_validation(),
        ]
    )


    result = (

        SQLGenerationOrchestrator(
            generator=generator,
            validator=validator,
        )

        .generate_and_validate(
            retrieved_context()
        )
    )


    assert (
        result.repair_attempted
        is True
    )


    assert (
        result.final_validation.status
        ==
        SQLValidationStatus.INVALID
    )


    assert (
        generator.generate_calls
        ==
        1
    )


    assert (
        generator.repair_calls
        ==
        1
    )


    assert (
        validator.calls
        ==
        2
    )