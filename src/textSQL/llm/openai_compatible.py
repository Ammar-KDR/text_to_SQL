from pydantic import BaseModel
from openai import OpenAI

from textSQL.llm.client import (
    LLMClient,
)

from textSQL.llm.errors import (
    LLMProviderError,
)


class OpenAICompatibleLLMClient(
    LLMClient
):
    """
    LLM client for OpenAI-compatible
    Chat Completions APIs.

    This can be used with providers such as
    LM Studio or hosted OpenAI by changing
    configuration only.
    """


    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        api_key: str = "lm-studio",
        temperature: float = 0.0,
        max_tokens: int = 1200,
    ):

        self.model = model

        self.temperature = (
            temperature
        )

        self.max_tokens = (
            max_tokens
        )


        client_args = {
            "api_key": api_key,
        }


        if base_url:

            client_args[
                "base_url"
            ] = base_url


        self.client = OpenAI(
            **client_args
        )


    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: type[
            BaseModel
        ] | None = None,
    ) -> str:

        request = {

            "model":
                self.model,

            "messages": [

                {
                    "role": "system",
                    "content":
                        system_prompt,
                },

                {
                    "role": "user",
                    "content":
                        user_prompt,
                },
            ],

            "temperature":
                self.temperature,

            "max_tokens":
                self.max_tokens,
        }


        if response_schema is not None:

            request[
                "response_format"
            ] = (
                self._build_response_format(
                    response_schema
                )
            )


        try:

            response = (
                self.client
                .chat
                .completions
                .create(
                    **request
                )
            )

        except Exception as exc:

            raise LLMProviderError(
                "LLM provider request failed."
            ) from exc


        try:

            content = (
                response
                .choices[0]
                .message
                .content
            )

        except (
            AttributeError,
            IndexError,
        ) as exc:

            raise LLMProviderError(
                "LLM provider returned an "
                "unexpected response."
            ) from exc


        if not content:

            raise LLMProviderError(
                "LLM provider returned "
                "empty content."
            )


        return content


    def _build_response_format(
        self,
        response_schema: type[
            BaseModel
        ],
    ) -> dict:

        return {

            "type":
                "json_schema",

            "json_schema": {

                "name":
                    response_schema
                    .__name__,

                "schema":
                    response_schema
                    .model_json_schema(),
            },
        }