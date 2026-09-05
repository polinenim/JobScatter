from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://jobscout:jobscout_local@localhost:5432/jobscout"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
