from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LaunchGuard AI"
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-haiku-4-5-20251001-v1:0"
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
