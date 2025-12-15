from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:die@0.0.0.0:5432/db"

    SECRET_KEY: str = "91164f112606672942e9a66658649af033c501586b348f226d2f56b2e23bb135"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CODEFORCES_API_URL: str = "https://codeforces.com/api"

    LLM_API_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "gemma3:270m"
    #LLM_MODEL: str = "deepseek-r1:8b"

    # ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_HOSTS: List[str] = ["*"]

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()
