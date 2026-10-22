from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    anthropic_api_key: str | None = None
    claude_model: str = "claude-3-5-haiku-latest"
    knowledge_brain_url: str = "http://127.0.0.1:8000"
    database_path: str = "data/scope.db"
    hourly_rate: float = 75.0
    currency: str = "USD"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
