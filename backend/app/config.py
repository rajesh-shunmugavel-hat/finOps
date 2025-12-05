import os
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = os.environ.get("DATABASE_URL", "")
    openai_api_key: str = os.environ.get("OPENAI_API_KEY", "")
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
