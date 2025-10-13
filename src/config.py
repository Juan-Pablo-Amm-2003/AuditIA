import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    # Agrega más configs (e.g., embedding model path)

settings = Settings()
