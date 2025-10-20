from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DollarClub Trading Platform"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/dollarclub"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"
    
    # IBKR OAuth (secondary integration)
    IBKR_CLIENT_ID: str = ""
    IBKR_CLIENT_SECRET: str = ""
    IBKR_REDIRECT_URI: str = "http://localhost:8000/auth/ibkr/connect"
    IBKR_AUTH_URL: str = "https://api.ibkr.com/v1/portal/iserver/auth/oauth"
    IBKR_TOKEN_URL: str = "https://api.ibkr.com/v1/portal/iserver/auth/token"
    IBKR_API_BASE: str = "https://api.ibkr.com/v1/portal/iserver"
    
    # Script execution
    MAX_SCRIPT_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_EXECUTION_TIME: int = 3600  # 1 hour
    MAX_CONCURRENT_SCRIPTS: int = 5
    
    # File storage
    SCRIPTS_DIR: str = "scripts"
    UPLOAD_DIR: str = "uploads"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.SCRIPTS_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
