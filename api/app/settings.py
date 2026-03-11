from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "TrendIt API"
    environment: str = "dev"

    database_url: str = "postgresql://trendit:trendit@localhost:5432/trendit"

    # Alpha Vantage configuration
    alpha_vantage_api_key: str | None = None
    alpha_vantage_base_url: str = "https://www.alphavantage.co/query"

    # LLM adapter wiring (you'll provide these later)
    llm_provider: str = "openai"  # openai | anthropic
    llm_api_key: str | None = None


settings = Settings()

