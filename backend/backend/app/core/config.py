from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./farmgrid.db"
    secret_key: str = "change-this-in-production"
    access_token_expire_minutes: int = 1440
    frontend_origin: str = "http://localhost:5173"
    openweather_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
