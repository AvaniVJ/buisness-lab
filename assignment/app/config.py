from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Knowledge Brain"
    database_path: str = "data/knowledge.db"
    sitemap_url: str = "https://support.brilliantdirectories.com/support/sitemap.xml"
    user_agent: str = "KnowledgeBrainCapstone/1.0 (polite educational crawler)"
    request_delay_seconds: float = 1.0
    max_concurrency: int = 2
    request_timeout_seconds: float = 20.0
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    claude_model: str = "claude-3-5-haiku-latest"
    anthropic_api_key: str | None = None
    refresh_hour_utc: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
