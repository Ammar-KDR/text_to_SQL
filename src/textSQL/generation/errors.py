class GenerationError(Exception):
    """
    Base error for SQL-generation failures.
    """

    pass


class InvalidStructuredOutputError(
    GenerationError
):
    """
    Raised when the LLM response cannot be
    parsed into SQLGenerationResult.
    """

    pass


class GenerationGroundingError(
    GenerationError
):
    """
    Raised when the model declares database
    objects that were not supplied in the
    approved GenerationContext.
    """

    pass
class InvalidStructuredOutputError(
    GenerationError
):

    def __init__(
        self,
        message: str,
        raw_response: str,
        validation_errors=None,
    ):

        super().__init__(
            message
        )

        self.raw_response = (
            raw_response
        )

        self.validation_errors = (
            validation_errors
        )