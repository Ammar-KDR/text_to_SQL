from textSQL.config.settings import (
    Settings,
    settings,
)

from textSQL.llm.client import (
    LLMClient,
)

from textSQL.llm.openai_compatible import (
    OpenAICompatibleLLMClient,
)


def build_llm_client(
    config: Settings = settings,
) -> LLMClient:

    provider = (
        config.llm_provider
        .strip()
        .lower()
    )


    if provider not in {
        "lmstudio",
        "openai",
    }:

        raise ValueError(
            "Unsupported LLM provider: "
            f"{config.llm_provider}"
        )


    if not config.llm_model:

        raise ValueError(
            "LLM model must be configured."
        )


    if (
        provider == "lmstudio"
        and
        not config.llm_base_url
    ):

        raise ValueError(
            "LM Studio requires "
            "llm_base_url."
        )


    return OpenAICompatibleLLMClient(

        model=(
            config.llm_model
        ),

        base_url=(
            config.llm_base_url
            or None
        ),

        api_key=(
            config.llm_api_key
        ),

        temperature=(
            config.llm_temperature
        ),

        max_tokens=(
            config.llm_max_tokens
        ),
    )