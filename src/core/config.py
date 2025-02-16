"""
Configuration management for the application.
"""
import os
from pydantic import BaseSettings, HttpUrl, SecretStr
from typing import Optional

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "sandbox"  # או 'production'
    
    # WooCommerce Configuration
    WC_STORE_URL: str
    WC_CONSUMER_KEY: str
    WC_CONSUMER_SECRET: SecretStr
    WP_USERNAME: str
    WP_PASSWORD: SecretStr
    
    # Sandbox Configuration
    SANDBOX_WC_STORE_URL: Optional[str] = None
    SANDBOX_WC_CONSUMER_KEY: Optional[str] = None
    SANDBOX_WC_CONSUMER_SECRET: Optional[SecretStr] = None
    SANDBOX_WP_USERNAME: Optional[str] = None
    SANDBOX_WP_PASSWORD: Optional[SecretStr] = None
    
    # API Keys
    TELEGRAM_BOT_TOKEN: SecretStr
    OPENAI_API_KEY: SecretStr
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    
    # API URLs
    OPENAI_API_URL: str
    ANTHROPIC_API_URL: Optional[str] = None
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./ecom_store.db"

    # Application Settings
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Additional Settings
    MAX_PRODUCTS_FETCH: int = 10
    ENABLE_CACHE: bool = False

    @property
    def is_sandbox(self) -> bool:
        return self.ENVIRONMENT.lower() == "sandbox"
    
    @property
    def active_store_url(self) -> str:
        return self.SANDBOX_WC_STORE_URL if self.is_sandbox else self.WC_STORE_URL
    
    @property
    def active_consumer_key(self) -> str:
        return self.SANDBOX_WC_CONSUMER_KEY if self.is_sandbox else self.WC_CONSUMER_KEY
    
    @property
    def active_consumer_secret(self) -> SecretStr:
        return self.SANDBOX_WC_CONSUMER_SECRET if self.is_sandbox else self.WC_CONSUMER_SECRET
    
    @property
    def active_wp_username(self) -> str:
        return self.SANDBOX_WP_USERNAME if self.is_sandbox else self.WP_USERNAME
    
    @property
    def active_wp_password(self) -> SecretStr:
        return self.SANDBOX_WP_PASSWORD if self.is_sandbox else self.WP_PASSWORD

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 