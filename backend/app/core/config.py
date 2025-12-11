from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings."""

    # OpenAI / OpenRouter
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Demo mode (bypasses LLM for testing)
    demo_mode: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/cox_automotive.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: str = '["http://localhost:3000", "http://localhost:5173", "http://localhost:3001"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.cors_origins)

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
