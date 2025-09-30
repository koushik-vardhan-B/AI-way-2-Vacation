from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = ["*"]
    
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