from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Polymarket
    POLYMARKET_GAMMA_URL: str = "https://gamma-api.polymarket.com"
    POLYMARKET_CLOB_URL: str = "https://clob.polymarket.com"

    # External APIs
    TAVILY_API_KEY: str | None = None
    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USER_AGENT: str = "PolyTerminal/1.0"
    TOKEN_COMPANY_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    WOODWIDE_API_KEY: str | None = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # App Settings
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
