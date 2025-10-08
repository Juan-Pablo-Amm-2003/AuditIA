import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "your-sql-server-conn-string")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret")
    # Agrega más configs (e.g., embedding model path)

settings = Settings()
