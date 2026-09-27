import pytest

from textSQL.generation.models import (
    SQLGenerationResult,
)

from textSQL.llm.errors import (
    LLMProviderError,
)

from textSQL.llm.openai_compatible import (
    OpenAICompatibleLLMClient,
)


# ============================================================
# FAKE OPENAI RESPONSE OBJECTS
# ============================================================


class FakeMessage:

    def __init__(
        self,
        content,
    ):

        self.content = content


class FakeChoice:

    def __init__(
        self,
        content,
    ):

        self.message = FakeMessage(
            content
        )


class FakeResponse:

    def __init__(
        self,
        content,
    ):

        self.choices = [
            FakeChoice(
                content
            )
        ]


# ============================================================
# FAKE CHAT COMPLETIONS
# ============================================================


class FakeCompletions:

    def __init__(
        self,
        response_content=None,
        error=None,
    ):

        self.response_content = (
            response_content
        )

        self.error = error

        self.calls = []


    def create(
        self,
        **kwargs,
    ):

        self.calls.append(
            kwargs
        )


        if self.error is not None:

            raise self.error


        return FakeResponse(
            self.response_content
        )


class FakeChat:

    def __init__(
        self,
        completions,
    ):

        self.completions = (
            completions
        )


class FakeOpenAIClient:

    def __init__(
        self,
        completions,
    ):

        self.chat = FakeChat(
            completions
        )


# ============================================================
# HELPERS
# ============================================================


def build_client(
    monkeypatch,
    response_content=(
        '{"status":"generated",'
        '"sql":"SELECT 1;",'
        '"explanation":"Test"}'
    ),
    provider_error=None,
    base_url=(
        "http://localhost:1234/v1"
    ),
):

    completions = FakeCompletions(

        response_content=(
            response_content
        ),

        error=provider_error,
    )


    fake_openai = FakeOpenAIClient(
        completions
    )


    constructor_calls = []


    def fake_openai_constructor(
        **kwargs,
    ):

        constructor_calls.append(
            kwargs
        )

        return fake_openai


    monkeypatch.setattr(

        "textSQL.llm.openai_compatible.OpenAI",

        fake_openai_constructor,
    )


    client = (
        OpenAICompatibleLLMClient(

            model=(
                "test-model"
            ),

            base_url=base_url,

            api_key=(
                "test-key"
            ),

            temperature=0.0,

            max_tokens=1200,
        )
    )


    return (
        client,
        completions,
        constructor_calls,
    )


# ============================================================
# CLIENT CONFIGURATION
# ============================================================


def test_client_passes_api_key_and_base_url(
    monkeypatch,
):

    (
        client,
        completions,
        constructor_calls,
    ) = build_client(
        monkeypatch
    )


    assert len(
        constructor_calls
    ) == 1


    args = (
        constructor_calls[0]
    )


    assert (
        args["api_key"]
        ==
        "test-key"
    )


    assert (
        args["base_url"]
        ==
        "http://localhost:1234/v1"
    )


def test_client_omits_base_url_when_none(
    monkeypatch,
):

    (
        client,
        completions,
        constructor_calls,
    ) = build_client(

        monkeypatch,

        base_url=None,
    )


    args = (
        constructor_calls[0]
    )


    assert (
        args["api_key"]
        ==
        "test-key"
    )


    assert (
        "base_url"
        not in args
    )


def test_client_stores_generation_configuration(
    monkeypatch,
):

    (
        client,
        _,
        _,
    ) = build_client(
        monkeypatch
    )


    assert (
        client.model
        ==
        "test-model"
    )

    assert (
        client.temperature
        ==
        0.0
    )

    assert (
        client.max_tokens
        ==
        1200
    )


# ============================================================
# MESSAGE CONSTRUCTION
# ============================================================


def test_generate_sends_system_and_user_messages(
    monkeypatch,
):

    (
        client,
        completions,
        _,
    ) = build_client(
        monkeypatch
    )


    client.generate(

        system_prompt=(
            "SYSTEM RULES"
        ),

        user_prompt=(
            "USER REQUEST"
        ),
    )


    assert len(
        completions.calls
    ) == 1


    request = (
        completions.calls[0]
    )


    assert (
        request["messages"]
        ==
        [
            {
                "role": "system",
                "content":
                    "SYSTEM RULES",
            },
            {
                "role": "user",
                "content":
                    "USER REQUEST",
            },
        ]
    )


def test_generate_sends_configured_model(
    monkeypatch,
):

    (
        client,
        completions,
        _,
    ) = build_client(
        monkeypatch
    )


    client.generate(
        "system",
        "user",
    )


    request = (
        completions.calls[0]
    )


    assert (
        request["model"]
        ==
        "test-model"
    )


def test_generate_sends_low_temperature(
    monkeypatch,
):

    (
        client,
        completions,
        _,
    ) = build_client(
        monkeypatch
    )


    client.generate(
        "system",
        "user",
    )


    request = (
        completions.calls[0]
    )


    assert (
        request["temperature"]
        ==
        0.0
    )


def test_generate_sends_max_tokens(
    monkeypatch,
):

    (
        client,
        completions,
        _,
    ) = build_client(
        monkeypatch
    )


    client.generate(
        "system",
        "user",
    )


    request = (
        completions.calls[0]
    )


    assert (
        request["max_tokens"]
        ==
        1200
    )


# ============================================================
# STRUCTURED OUTPUT
# ============================================================


def test_generate_attaches_response_schema(
    monkeypatch,
):

    (
        client,
        completions,
        _,
    ) = build_client(
        monkeypatch
    )


    client.generate(

        system_prompt="system",

        user_prompt="user",

        response_schema=(
            SQLGenerationResult
        ),
    )


    request = (
        completions.calls[0]
    )


    assert (
        "response_format"
        in request
    )


    response_format = (
        request[
            "response_format"
        ]
    )


    assert (
        response_format["type"]
        ==
        "json_schema"
    )


    assert (
        response_format[
            "json_schema"
        ][
            "name"
        ]
        ==
        "SQLGenerationResult"
    )


def test_response_schema_uses_pydantic_json_schema(
    monkeypatch,
):

    (
        client,
        completions,
        _,
    ) = build_client(
        monkeypatch
    )


    client.generate(

        "system",

        "user",

        response_schema=(
            SQLGenerationResult
        ),
    )


    request = (
        completions.calls[0]
    )


    generated_schema = (

        request[
            "response_format"
        ][
            "json_schema"
        ][
            "schema"
        ]
    )


    expected_schema = (
        SQLGenerationResult
        .model_json_schema()
    )


    assert (
        generated_schema
        ==
        expected_schema
    )


def test_generate_without_schema_does_not_send_response_format(
    monkeypatch,
):

    (
        client,
        completions,
        _,
    ) = build_client(
        monkeypatch
    )


    client.generate(

        system_prompt="system",

        user_prompt="user",

        response_schema=None,
    )


    request = (
        completions.calls[0]
    )


    assert (
        "response_format"
        not in request
    )


# ============================================================
# RESPONSE HANDLING
# ============================================================


def test_generate_returns_raw_response_text(
    monkeypatch,
):

    expected = (
        '{"status":"generated",'
        '"sql":"SELECT 1;",'
        '"explanation":"Test"}'
    )


    (
        client,
        _,
        _,
    ) = build_client(

        monkeypatch,

        response_content=expected,
    )


    result = client.generate(

        system_prompt="system",

        user_prompt="user",
    )


    assert (
        result
        ==
        expected
    )


def test_client_does_not_parse_generation_result(
    monkeypatch,
):

    raw_text = (
        '{"something":"provider output"}'
    )


    (
        client,
        _,
        _,
    ) = build_client(

        monkeypatch,

        response_content=raw_text,
    )


    result = client.generate(
        "system",
        "user",
    )


    assert isinstance(
        result,
        str,
    )

    assert (
        result
        ==
        raw_text
    )


# ============================================================
# PROVIDER FAILURE HANDLING
# ============================================================


def test_provider_exception_becomes_llm_provider_error(
    monkeypatch,
):

    original_error = RuntimeError(
        "provider unavailable"
    )


    (
        client,
        _,
        _,
    ) = build_client(

        monkeypatch,

        provider_error=(
            original_error
        ),
    )


    with pytest.raises(
        LLMProviderError
    ) as error:

        client.generate(
            "system",
            "user",
        )


    assert (
        str(error.value)
        ==
        "LLM provider request failed."
    )


def test_provider_error_preserves_original_cause(
    monkeypatch,
):

    original_error = RuntimeError(
        "connection failed"
    )


    (
        client,
        _,
        _,
    ) = build_client(

        monkeypatch,

        provider_error=(
            original_error
        ),
    )


    with pytest.raises(
        LLMProviderError
    ) as error:

        client.generate(
            "system",
            "user",
        )


    assert (
        error.value.__cause__
        is original_error
    )


# ============================================================
# EMPTY RESPONSE HANDLING
# ============================================================


@pytest.mark.parametrize(
    "content",
    [
        None,
        "",
    ],
)
def test_empty_content_raises_provider_error(
    monkeypatch,
    content,
):

    (
        client,
        _,
        _,
    ) = build_client(

        monkeypatch,

        response_content=content,
    )


    with pytest.raises(
        LLMProviderError,
        match=(
            "LLM provider returned "
            "empty content."
        ),
    ):

        client.generate(
            "system",
            "user",
        )


# ============================================================
# MALFORMED PROVIDER RESPONSE
# ============================================================


def test_missing_choices_raises_provider_error(
    monkeypatch,
):

    class MalformedResponse:
        pass


    class MalformedCompletions:

        def create(
            self,
            **kwargs,
        ):

            return (
                MalformedResponse()
            )


    fake_client = (
        FakeOpenAIClient(
            MalformedCompletions()
        )
    )


    def fake_openai(
        **kwargs,
    ):

        return fake_client


    monkeypatch.setattr(

        "textSQL.llm.openai_compatible.OpenAI",

        fake_openai,
    )


    client = (
        OpenAICompatibleLLMClient(

            model="test-model",

            base_url=(
                "http://localhost:1234/v1"
            ),

            api_key="test-key",
        )
    )


    with pytest.raises(
        LLMProviderError,
        match=(
            "LLM provider returned an "
            "unexpected response."
        ),
    ):

        client.generate(
            "system",
            "user",
        )


def test_empty_choices_raises_provider_error(
    monkeypatch,
):

    class EmptyResponse:

        choices = []


    class EmptyCompletions:

        def create(
            self,
            **kwargs,
        ):

            return EmptyResponse()


    fake_client = (
        FakeOpenAIClient(
            EmptyCompletions()
        )
    )


    monkeypatch.setattr(

        "textSQL.llm.openai_compatible.OpenAI",

        lambda **kwargs:
            fake_client,
    )


    client = (
        OpenAICompatibleLLMClient(

            model="test-model",

            api_key="test-key",
        )
    )


    with pytest.raises(
        LLMProviderError,
        match=(
            "LLM provider returned an "
            "unexpected response."
        ),
    ):

        client.generate(
            "system",
            "user",
        )


# ============================================================
# PROVIDER BOUNDARY
# ============================================================


def test_complete_provider_request_boundary(
    monkeypatch,
):

    raw_result = (
        '{"status":"generated",'
        '"sql":"SELECT COUNT(*) '
        'FROM public.customers;",'
        '"explanation":"Counts customers.",'
        '"tables_used":["public.customers"],'
        '"columns_used":[],'
        '"assumptions":[],'
        '"clarification_question":null,'
        '"clarification_options":[]}'
    )


    (
        client,
        completions,
        _,
    ) = build_client(

        monkeypatch,

        response_content=raw_result,
    )


    result = client.generate(

        system_prompt=(
            "SQL generation rules"
        ),

        user_prompt=(
            "Grounded request context"
        ),

        response_schema=(
            SQLGenerationResult
        ),
    )


    assert (
        result
        ==
        raw_result
    )


    request = (
        completions.calls[0]
    )


    assert (
        request["model"]
        ==
        "test-model"
    )

    assert (
        request["temperature"]
        ==
        0.0
    )

    assert (
        request["max_tokens"]
        ==
        1200
    )

    assert (
        request["messages"][0]
        ["role"]
        ==
        "system"
    )

    assert (
        request["messages"][1]
        ["role"]
        ==
        "user"
    )

    assert (
        request[
            "response_format"
        ][
            "json_schema"
        ][
            "name"
        ]
        ==
        "SQLGenerationResult"
    )