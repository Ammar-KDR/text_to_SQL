from dataclasses import (
    dataclass,
)

from textSQL.generation.generator import (
    SQLGenerator,
)

from textSQL.generation.models import (
    GenerationStatus,
    SQLGenerationResult,
)

from textSQL.retrieval.model import (
    RetrievedContext,
)

from textSQL.validation.models import (
    SQLValidationResult,
    SQLValidationStatus,
)

from textSQL.validation.sql_validator import (
    SQLValidator,
)


@dataclass(
    frozen=True
)
class SQLGenerationWorkflowResult:
    """
    Final result of generation + deterministic
    validation + optional single repair.

    final_validation is None when the final
    generation does not contain SQL, such as
    CLARIFICATION_REQUIRED or UNANSWERABLE.
    """

    final_generation: (
        SQLGenerationResult
    )

    final_validation: (
        SQLValidationResult
        | None
    )

    repair_attempted: bool


class SQLGenerationOrchestrator:
    """
    Coordinates:

        GenerationContext construction
            ↓
        SQL generation
            ↓
        deterministic validation
            ↓
        at most one repair
            ↓
        deterministic re-validation

    Important invariants:

    - GenerationContext is built exactly once.
    - The exact same GenerationContext object is
      used by generation, validation, repair, and
      re-validation.
    - VALID SQL is never repaired.
    - BLOCKED SQL is never repaired.
    - INVALID SQL may be repaired exactly once.
    - A failed repair is never repaired again.
    - Non-generated states are never validated.
    """


    def __init__(
        self,
        generator: SQLGenerator,
        validator: SQLValidator,
    ):

        self.generator = generator

        self.validator = validator


    def generate_and_validate(
        self,
        retrieved_context: RetrievedContext,
    ) -> SQLGenerationWorkflowResult:

        # ====================================================
        # 1. BUILD GENERATION CONTEXT EXACTLY ONCE
        # ====================================================

        generation_context = (
            self.generator
            .build_context(
                retrieved_context
            )
        )


        # ====================================================
        # 2. INITIAL GENERATION
        # ====================================================

        generation_result = (
            self.generator
            .generate_from_context(

                question=(
                    retrieved_context.question
                ),

                generation_context=(
                    generation_context
                ),
            )
        )


        # ====================================================
        # 3. NON-SQL GENERATION STATES
        # ====================================================

        if (
            generation_result.status
            !=
            GenerationStatus.GENERATED
        ):

            return (
                SQLGenerationWorkflowResult(

                    final_generation=(
                        generation_result
                    ),

                    final_validation=None,

                    repair_attempted=False,
                )
            )


        # SQLGenerationResult guarantees SQL exists
        # whenever status == GENERATED.

        assert (
            generation_result.sql
            is not None
        )


        # ====================================================
        # 4. INITIAL VALIDATION
        # ====================================================

        validation_result = (
            self.validator
            .validate(

                sql=(
                    generation_result.sql
                ),

                context=(
                    generation_context
                ),
            )
        )


        # ====================================================
        # 5. VALID → STOP
        # ====================================================

        if (
            validation_result.status
            ==
            SQLValidationStatus.VALID
        ):

            return (
                SQLGenerationWorkflowResult(

                    final_generation=(
                        generation_result
                    ),

                    final_validation=(
                        validation_result
                    ),

                    repair_attempted=False,
                )
            )


        # ====================================================
        # 6. BLOCKED → STOP
        # ====================================================

        if (
            validation_result.status
            ==
            SQLValidationStatus.BLOCKED
        ):

            return (
                SQLGenerationWorkflowResult(

                    final_generation=(
                        generation_result
                    ),

                    final_validation=(
                        validation_result
                    ),

                    repair_attempted=False,
                )
            )


        # ====================================================
        # 7. INVALID → EXACTLY ONE REPAIR
        # ====================================================

        repaired_result = (
            self.generator
            .repair_from_context(

                question=(
                    retrieved_context.question
                ),

                generation_context=(
                    generation_context
                ),

                previous_result=(
                    generation_result
                ),

                validation_result=(
                    validation_result
                ),
            )
        )


        # ====================================================
        # 8. REPAIR MAY RETURN NON-SQL STATE
        # ====================================================

        if (
            repaired_result.status
            !=
            GenerationStatus.GENERATED
        ):

            return (
                SQLGenerationWorkflowResult(

                    final_generation=(
                        repaired_result
                    ),

                    final_validation=None,

                    repair_attempted=True,
                )
            )


        assert (
            repaired_result.sql
            is not None
        )


        # ====================================================
        # 9. VALIDATE REPAIR EXACTLY ONCE
        # ====================================================

        repaired_validation = (
            self.validator
            .validate(

                sql=(
                    repaired_result.sql
                ),

                context=(
                    generation_context
                ),
            )
        )


        # ====================================================
        # 10. STOP UNCONDITIONALLY
        # ====================================================
        #
        # There is deliberately no conditional repair here.
        #
        # repaired_validation may be:
        #
        #     VALID
        #     INVALID
        #     BLOCKED
        #
        # All three are terminal after the single repair.

        return (
            SQLGenerationWorkflowResult(

                final_generation=(
                    repaired_result
                ),

                final_validation=(
                    repaired_validation
                ),

                repair_attempted=True,
            )
        )