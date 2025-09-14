from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Settlers of Stock"
    
    # Database Configuration
    DATABASE_URL: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # GCP Configuration
    GCP_PROJECT_ID: Optional[str] = None
    GCP_REGION: str = "us-central1"
    GCP_LOCATION: str = "us-central1"  # Alias for GCP_REGION
    
    # Vertex AI Configuration
    VERTEX_AI_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "gemini-1.5-flash"
    
    # External API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    
    # Reddit API Configuration
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Email/SMTP Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_TLS: bool = True
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Testing Configuration
    TESTING_MODE: bool = False
    SKIP_EXTERNAL_APIS: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS Configuration
    cors_origins: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3001",  # Alternative React port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # Trusted hosts
    allowed_hosts: List[str] = [
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "testserver"  # For FastAPI TestClient
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        @classmethod
        def prepare_field(cls, field) -> None:
            if 'env_names' in field.field_info.extra:
                return
            return super().prepare_field(field)

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    import os
    env = os.getenv("ENVIRONMENT", "development")
    if env == "test":
        return Settings(_env_file=".env.test")
    return Settings()