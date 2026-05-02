from typing import List, Union
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 1. Project Metadata
    PROJECT_NAME: str = "My FastAPI Service"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # 2. Database Settings (SQLite)
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    POLYGON_API_KEY: str = None

    # 4. Environment Management
    # This looks for a .env file in your root directory
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

# Instantiate the settings object
settings = Settings()