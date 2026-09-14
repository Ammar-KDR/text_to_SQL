from abc import ABC, abstractmethod


class LLMClient(ABC):
    """
    Abstract interface for all LLM providers.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        Generate a response from the language model.

        Args:
            prompt:
                Input prompt.

        Returns:
            Generated text.
        """
        pass