from abc import ABC, abstractmethod

from pydantic import BaseModel


class LLMClient(ABC):
    """
    Provider-independent interface for LLM generation.
    """

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[BaseModel] | None = None,
    ) -> str:
        """
        Generate a model response.

        Args:
            system_prompt:
                Stable model instructions.

            user_prompt:
                Request-specific content.

            response_schema:
                Optional Pydantic model describing
                the required structured output.

        Returns:
            Raw generated response text.
        """
        pass