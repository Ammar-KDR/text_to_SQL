from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    DATABASE_URL: str = ""

    llm_provider: str = "lmstudio"

    llm_model: str = ""

    llm_base_url: str = ""

    embedding_provider: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()