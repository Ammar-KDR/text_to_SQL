from pydantic import ValidationError

from textSQL.generation.context_builder import (
    GenerationContextBuilder,
)

from textSQL.generation.context_formatter import (
    ContextFormatter,
)

from textSQL.generation.prompt_builder import (
    PromptBuilder,
)

from textSQL.generation.models import (
    GenerationContext,
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

from textSQL.retrieval.model import (
    RetrievedContext,
)

from .output_normalizer import GenerationOutputNormalizer
class SQLGenerator:
    """
    Orchestrates grounded SQL generation.

    This class does not retrieve schema,
    validate SQL ASTs, execute SQL, or
    verify query results.
    """


    def __init__(
        self,
        llm_client: LLMClient,
        context_builder: (GenerationContextBuilder| None) = None,
        context_formatter: (ContextFormatter| None) = None,
        prompt_builder: (PromptBuilder| None) = None,
        output_normalizer:(GenerationOutputNormalizer| None) = None,
        
    ):

        self.llm_client = llm_client

        self.context_builder = (
            context_builder
            or GenerationContextBuilder()
        )

        self.context_formatter = (
            context_formatter
            or ContextFormatter()
        )

        self.prompt_builder = (
            prompt_builder
            or PromptBuilder()
        )
        self.output_normalizer = (
        output_normalizer
        or GenerationOutputNormalizer()
    )


    def generate(
        self,
        retrieved_context: RetrievedContext,
    ) -> SQLGenerationResult:

        generation_context = (
            self.context_builder
            .build(
                retrieved_context
            )
        )


        formatted_context = (
            self.context_formatter
            .format(
                generation_context
            )
        )


        prompt = (
            self.prompt_builder
            .build(
                question=(
                    retrieved_context.question
                ),
                formatted_context=(
                    formatted_context
                ),
            )
        )


        raw_response = (
            self.llm_client
            .generate(
                system_prompt=(
                    prompt.system_prompt
                ),
                user_prompt=(
                    prompt.user_prompt
                ),
                response_schema=(
                    SQLGenerationResult
                ),
            )
        )

        normalized_response = (
            self.output_normalizer
            .normalize(
                raw_response
            )
        )


        result = (
            self._parse_result(
                normalized_response
            )
        )


        self._validate_grounding(
            result=result,
            context=generation_context,
        )


        return result




    def _parse_result(
        self,
        raw_response: str,
    ) -> SQLGenerationResult:

        try:

            return (
                SQLGenerationResult
                .model_validate_json(
                    raw_response
                )
            )

        except ValidationError as exc:

            raise (
                InvalidStructuredOutputError(

                    message=(
                        "LLM returned invalid "
                        "structured generation output."
                    ),

                    raw_response=(
                        raw_response
                    ),

                    validation_errors=(
                        exc.errors()
                    ),
                )
            ) from exc


    def _validate_grounding(
        self,
        result: SQLGenerationResult,
        context: GenerationContext,
    ) -> None:

        if (
            result.status
            != GenerationStatus.GENERATED
        ):
            return


        allowed_tables = {

            table.qualified_name

            for table
            in context.tables
        }


        declared_tables = set(
            result.tables_used
        )


        unknown_tables = (
            declared_tables
            -
            allowed_tables
        )


        if unknown_tables:

            raise GenerationGroundingError(

                "Generated result declared "
                "tables outside the retrieved "
                "generation context: "
                +
                ", ".join(
                    sorted(
                        unknown_tables
                    )
                )
            )


        allowed_columns = {

            (
                f"{table.qualified_name}."
                f"{column.name}"
            )

            for table
            in context.tables

            for column
            in table.columns
        }


        declared_columns = set(
            result.columns_used
        )


        unknown_columns = (
            declared_columns
            -
            allowed_columns
        )


        if unknown_columns:

            raise GenerationGroundingError(

                "Generated result declared "
                "columns outside the retrieved "
                "generation context: "
                +
                ", ".join(
                    sorted(
                        unknown_columns
                    )
                )
            )