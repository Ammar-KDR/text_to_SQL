from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str = ""
    RUNTIME_DATABASE_URL: str = ""

    llm_provider: str = "lmstudio"

    llm_model: str = ""

    llm_base_url: str = ""

    llm_api_key: str = "lm-studio"

    llm_temperature: float = 0.0

    llm_max_tokens: int = 1200

    embedding_provider: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()