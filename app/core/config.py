from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Stocks REST API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    HTTP_REQUEST_TIMEOUT: int = 10

    DATABASE_URL: str = "./sql_app.db"
    POLYGON_API_KEY: SecretStr

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


# Instantiate the settings object
settings = Settings()
