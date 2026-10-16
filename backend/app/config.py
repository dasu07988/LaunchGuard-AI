from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LaunchGuard AI"
    aws_region: str = "us-east-1"

    # Use the active US inference profile.
    bedrock_model_id: str = (
    "us.anthropic.claude-haiku-4-5-20251001-v1:0"
)

    bedrock_max_tokens: int = 180
    bedrock_timeout_seconds: int = 15
    bedrock_enabled: bool = False

    decider_url: str = "http://127.0.0.1:8001/v1/systemone"
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()