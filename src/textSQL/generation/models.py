from enum import Enum

from pydantic import BaseModel, Field, model_validator


## Generation Results

from enum import Enum

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class GenerationStatus(
    str,
    Enum,
):

    GENERATED = "generated"

    CLARIFICATION_REQUIRED = (
        "clarification_required"
    )

    UNANSWERABLE = "unanswerable"


class SQLGenerationResult(
    BaseModel
):

    status: GenerationStatus

    sql: str | None = None

    explanation: str

    tables_used: list[str] = Field(
        default_factory=list
    )

    columns_used: list[str] = Field(
        default_factory=list
    )

    assumptions: list[str] = Field(
        default_factory=list
    )

    clarification_question: (
        str | None
    ) = None

    clarification_options: list[str] = (
        Field(
            default_factory=list
        )
    )


    @model_validator(
        mode="after"
    )
    def validate_state(
        self,
    ):

        # ====================================================
        # GENERATED
        # ====================================================

        if (
            self.status
            ==
            GenerationStatus.GENERATED
        ):

            if not self.sql:

                raise ValueError(
                    "Generated result must "
                    "contain SQL."
                )


            normalized_sql = (
                self.sql
                .strip()
                .upper()
            )


            if normalized_sql in {
                "UNANSWERABLE",
                "CLARIFICATION_REQUIRED",
                "GENERATED",
            }:

                raise ValueError(
                    "Generated result must "
                    "contain actual SQL, not "
                    "a generation status label."
                )


            if (
                self.clarification_question
                is not None
            ):

                raise ValueError(
                    "Generated result cannot "
                    "contain a clarification "
                    "question."
                )


            if (
                self.clarification_options
            ):

                raise ValueError(
                    "Generated result cannot "
                    "contain clarification "
                    "options."
                )


        # ====================================================
        # CLARIFICATION REQUIRED
        # ====================================================

        elif (
            self.status
            ==
            GenerationStatus
            .CLARIFICATION_REQUIRED
        ):

            if self.sql is not None:

                raise ValueError(
                    "Clarification result "
                    "cannot contain SQL."
                )


            if not (
                self.clarification_question
            ):

                raise ValueError(
                    "Clarification result must "
                    "contain a clarification "
                    "question."
                )


            if self.tables_used:

                raise ValueError(
                    "Clarification result "
                    "cannot declare tables used."
                )


            if self.columns_used:

                raise ValueError(
                    "Clarification result "
                    "cannot declare columns used."
                )


        # ====================================================
        # UNANSWERABLE
        # ====================================================

        elif (
            self.status
            ==
            GenerationStatus.UNANSWERABLE
        ):

            if self.sql is not None:

                raise ValueError(
                    "Unanswerable result "
                    "cannot contain SQL."
                )


            if (
                self.clarification_question
                is not None
            ):

                raise ValueError(
                    "Unanswerable result "
                    "cannot contain a "
                    "clarification question."
                )


            if self.clarification_options:

                raise ValueError(
                    "Unanswerable result "
                    "cannot contain "
                    "clarification options."
                )


            if self.tables_used:

                raise ValueError(
                    "Unanswerable result "
                    "cannot declare tables used."
                )


            if self.columns_used:

                raise ValueError(
                    "Unanswerable result "
                    "cannot declare columns used."
                )


        return self







## Generation Context

class GenerationColumnContext(BaseModel):

    name: str

    data_type: str

    nullable: bool

    is_primary_key: bool = False

    is_unique: bool = False

    description: str | None = None

    business_meaning: str | None = None
    
    allowed_values: list[str] = Field(
    default_factory=list
)

class GenerationTableContext(BaseModel):

    qualified_name: str

    description: str | None = None

    business_role: str | None = None

    primary_keys: list[str] = Field(
        default_factory=list
    )

    columns: list[
        GenerationColumnContext
    ] = Field(
        default_factory=list
    )

class GenerationJoinCondition(BaseModel):

    source_column: str

    target_column: str

class GenerationRelationshipContext(BaseModel):

    relationship_id: str

    source_table: str

    target_table: str

    relationship_type: str

    source_cardinality: str

    target_cardinality: str

    through_table: str | None = None

    join_conditions: list[
        GenerationJoinCondition
    ] = Field(
        default_factory=list
    )

    business_meaning: str | None = None


class GenerationJoinPathContext(BaseModel):

    tables: list[str] = Field(
        default_factory=list
    )

    relationship_ids: list[str] = Field(
        default_factory=list
    )

class GenerationMetricContext(BaseModel):

    name: str

    description: str

    domain: str

    formula: str

    authoritative_source: str | None = None

    required_tables: list[str] = Field(
        default_factory=list
    )

    required_columns: list[str] = Field(
        default_factory=list
    )

    required_metrics: list[str] = Field(
        default_factory=list
    )

    business_rules: list[str] = Field(
        default_factory=list
    )

    forbidden_sources: list[str] = Field(
        default_factory=list
    )


class GenerationTemporalConstraint(
    BaseModel
):

    phrase: str

    column: str

    start_expression: str

    end_expression: str

    start_inclusive: bool = True

    end_inclusive: bool = False

class GenerationContext(BaseModel):

    tables: list[
        GenerationTableContext
    ] = Field(
        default_factory=list
    )

    relationships: list[
        GenerationRelationshipContext
    ] = Field(
        default_factory=list
    )

    join_paths: list[
        GenerationJoinPathContext
    ] = Field(
        default_factory=list
    )

    metrics: list[
        GenerationMetricContext
    ] = Field(
        default_factory=list
    )

    temporal_constraints: list[
        GenerationTemporalConstraint
    ] = Field(
        default_factory=list
    )

## Generation Prompts

class GenerationPrompt(BaseModel):

    system_prompt: str

    user_prompt: str