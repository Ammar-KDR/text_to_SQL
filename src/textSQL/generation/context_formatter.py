from textSQL.generation.models import (
    GenerationContext,
)


class ContextFormatter:
    """
    Serializes the approved generation context
    into an LLM-readable representation.

    This class does not decide what information
    the model is allowed to receive. That decision
    belongs to GenerationContextBuilder.
    """


    def format(
        self,
        context: GenerationContext,
    ) -> str:

        return context.model_dump_json(
            indent=2,
            exclude_none=True,
            exclude_defaults=False,
        )
    