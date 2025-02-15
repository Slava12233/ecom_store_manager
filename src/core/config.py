"""
Configuration management for the application.
"""
import os
from pydantic import BaseSettings, HttpUrl, SecretStr

class Settings(BaseSettings):
    # WooCommerce Settings
    WC_STORE_URL: HttpUrl
    WC_CONSUMER_KEY: str
    WC_CONSUMER_SECRET: SecretStr

    # OpenAI Settings
    OPENAI_API_KEY: SecretStr

    # Telegram Settings
    TELEGRAM_BOT_TOKEN: SecretStr

    # Database Settings
    DATABASE_URL: str = "sqlite:///./ecom_store.db"

    # Application Settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Additional Settings
    MAX_PRODUCTS_FETCH: int = 10
    ENABLE_CACHE: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 