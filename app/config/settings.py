"""
MSBot Configuration Settings
Centralized configuration management using Pydantic Settings
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Microsoft Teams Bot Configuration
    microsoft_app_id: str = Field(default="", env="MICROSOFT_APP_ID")
    microsoft_app_password: str = Field(default="", env="MICROSOFT_APP_PASSWORD")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=3978, env="PORT")
    
    # HTTPS Configuration
    https_enabled: bool = Field(default=True, env="HTTPS_ENABLED")
    ssl_cert_path: str = Field(default="./certs/cert.pem", env="SSL_CERT_PATH")
    ssl_key_path: str = Field(default="./certs/key.pem", env="SSL_KEY_PATH")
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def validate_bot_config(self) -> bool:
        """Validate that required bot configuration is present"""
        if not self.microsoft_app_id or not self.microsoft_app_password:
            return False
        return True
    
    def get_base_url(self) -> str:
        """Get the base URL for the bot"""
        protocol = "https" if self.https_enabled else "http"
        return f"{protocol}://{self.host}:{self.port}"

# Global settings instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Get application settings (singleton pattern)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings