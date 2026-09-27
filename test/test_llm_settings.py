import pytest
from pydantic import ValidationError

from textSQL.config.settings import (
    Settings,
)


# ============================================================
# DEFAULT SETTINGS
# ============================================================


def test_default_llm_provider():

    settings = Settings(
        _env_file=None,
    )


    assert (
        settings.llm_provider
        ==
        "lmstudio"
    )


def test_default_temperature_is_deterministic():

    settings = Settings(
        _env_file=None,
    )


    assert (
        settings.llm_temperature
        ==
        0.0
    )


def test_default_max_tokens():

    settings = Settings(
        _env_file=None,
    )


    assert (
        settings.llm_max_tokens
        ==
        1200
    )


def test_default_api_key_supports_local_provider():

    settings = Settings(
        _env_file=None,
    )


    assert (
        settings.llm_api_key
        ==
        "lm-studio"
    )


# ============================================================
# EXPLICIT CONFIGURATION
# ============================================================


def test_llm_configuration_can_be_overridden():

    settings = Settings(

        _env_file=None,

        llm_provider="openai",

        llm_model="example-model",

        llm_base_url=(
            "https://example.test/v1"
        ),

        llm_api_key="secret",

        llm_temperature=0.1,

        llm_max_tokens=2048,
    )


    assert (
        settings.llm_provider
        ==
        "openai"
    )

    assert (
        settings.llm_model
        ==
        "example-model"
    )

    assert (
        settings.llm_base_url
        ==
        "https://example.test/v1"
    )

    assert (
        settings.llm_api_key
        ==
        "secret"
    )

    assert (
        settings.llm_temperature
        ==
        0.1
    )

    assert (
        settings.llm_max_tokens
        ==
        2048
    )


# ============================================================
# ENVIRONMENT VARIABLE CONFIGURATION
# ============================================================


def test_llm_settings_load_from_environment(
    monkeypatch,
):

    monkeypatch.setenv(
        "LLM_PROVIDER",
        "lmstudio",
    )

    monkeypatch.setenv(
        "LLM_MODEL",
        "local-model",
    )

    monkeypatch.setenv(
        "LLM_BASE_URL",
        "http://localhost:1234/v1",
    )

    monkeypatch.setenv(
        "LLM_API_KEY",
        "lm-studio",
    )

    monkeypatch.setenv(
        "LLM_TEMPERATURE",
        "0.0",
    )

    monkeypatch.setenv(
        "LLM_MAX_TOKENS",
        "1500",
    )


    settings = Settings(
        _env_file=None,
    )


    assert (
        settings.llm_provider
        ==
        "lmstudio"
    )

    assert (
        settings.llm_model
        ==
        "local-model"
    )

    assert (
        settings.llm_base_url
        ==
        "http://localhost:1234/v1"
    )

    assert (
        settings.llm_api_key
        ==
        "lm-studio"
    )

    assert (
        settings.llm_temperature
        ==
        0.0
    )

    assert (
        settings.llm_max_tokens
        ==
        1500
    )


# ============================================================
# TYPE VALIDATION
# ============================================================


def test_temperature_is_parsed_as_float():

    settings = Settings(

        _env_file=None,

        llm_temperature="0.1",
    )


    assert (
        settings.llm_temperature
        ==
        0.1
    )

    assert isinstance(
        settings.llm_temperature,
        float,
    )


def test_max_tokens_is_parsed_as_integer():

    settings = Settings(

        _env_file=None,

        llm_max_tokens="1600",
    )


    assert (
        settings.llm_max_tokens
        ==
        1600
    )

    assert isinstance(
        settings.llm_max_tokens,
        int,
    )


def test_invalid_temperature_type_fails():

    with pytest.raises(
        ValidationError
    ):

        Settings(

            _env_file=None,

            llm_temperature=(
                "not-a-number"
            ),
        )


def test_invalid_max_tokens_type_fails():

    with pytest.raises(
        ValidationError
    ):

        Settings(

            _env_file=None,

            llm_max_tokens=(
                "not-an-integer"
            ),
        )