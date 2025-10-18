"""
Configuration management for Text2Dataset application
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    # Application settings
    APP_NAME: str = "Text2Dataset"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # Database settings
    MONGODB_URI: Optional[str] = os.getenv("MONGODB_URI")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "text2dataset")
    
    # Security settings
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    SESSION_TIMEOUT: int = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # File upload settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_FILE_EXTENSIONS: set = {'.txt', '.pdf', '.docx', '.doc'}
    
    # Processing settings
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "1000000"))  # 1MB
    MIN_TEXT_LENGTH: int = int(os.getenv("MIN_TEXT_LENGTH", "10"))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # API settings
    API_RATE_LIMIT: int = int(os.getenv("API_RATE_LIMIT", "100"))  # requests per minute
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # Cache settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings."""
        errors = []
        
        if not cls.SECRET_KEY or cls.SECRET_KEY == "your-secret-key-here":
            errors.append("SECRET_KEY must be set to a secure value")
        
        if cls.PASSWORD_MIN_LENGTH < 6:
            errors.append("PASSWORD_MIN_LENGTH must be at least 6")
        
        if cls.MAX_FILE_SIZE > 50 * 1024 * 1024:  # 50MB
            errors.append("MAX_FILE_SIZE cannot exceed 50MB")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True

# Create global settings instance
settings = Settings()

# Validate configuration on import
try:
    settings.validate_config()
except ValueError as e:
    print(f"Warning: {e}")
