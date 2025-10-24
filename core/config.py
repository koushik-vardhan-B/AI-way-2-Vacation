from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["*"]
    # ADD THESE NEW DATABASE SETTINGS:
    DATABASE_URL: str = "sqlite:///./travel_planner.db"
    DATABASE_ECHO: bool = False  # Set True for SQL query logging
    
    # ADD THESE AUTH SETTINGS:
    SECRET_KEY: str = "change-this-to-a-random-secret-key-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # API Keys
    API_KEY: str = "test-api-key"
    GOOGLE_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: str
    GPLACES_API_KEY: str
    FOURSQUARE_API_KEY: str
    TAVILY_API_KEY: str  # Changed from TAVILAY_API_KEY to match expected name
    OPENWEATHERMAP_API_KEY: str
    EXCHANGE_RATE_API_KEY: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "travel_planner.log"
    
    # Paths
    OUTPUT_DIR: str = "./output"
    GRAPHS_DIR: str = "./graphs"
    LOGS_DIR: str = "./logs"


    #SMTP
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "anone3877@gmail.com"
    SMTP_PASSWORD: str = "pgxg nhtd rody fzco"
    FROM_EMAIL: str = "anone3877@gmail.com"
    FRONTEND_URL: str="http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

def validate_environment() -> None:
    """Validate required environment variables are set"""
    required_vars = [
        "GOOGLE_API_KEY",
        "GROQ_API_KEY",
        "GPLACES_API_KEY",
        "FOURSQUARE_API_KEY",
        "TAVILY_API_KEY",
        "OPENWEATHERMAP_API_KEY",
        "EXCHANGE_RATE_API_KEY"
    ]
    
    settings = get_settings()
    missing_vars = []
    
    for var in required_vars:
        if not getattr(settings, var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Singleton instance
_settings = None

def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def clear_settings_cache():
    """Clear the settings cache to force reload"""
    global _settings
    _settings = None