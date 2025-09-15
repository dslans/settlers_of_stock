from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache
import os
import json
from google.cloud import secretmanager

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
    
    # Skip external services for initial deployment
    SKIP_DATABASE: bool = False
    SKIP_REDIS: bool = False
    
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

def load_secret(secret_name: str, project_id: str) -> Optional[str]:
    """Load secret from Google Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Warning: Could not load secret {secret_name}: {e}")
        return None

def load_secrets_for_environment(environment: str, project_id: str) -> dict:
    """Load all secrets for the given environment."""
    secrets = {}
    
    if environment in ["production", "staging"]:
        # Load app secrets
        app_secrets_data = load_secret(f"settlers-of-stock-app-secrets-{environment}", project_id)
        if app_secrets_data:
            app_secrets = json.loads(app_secrets_data)
            secrets.update(app_secrets)
        
        # Load database URL
        database_url = load_secret(f"settlers-of-stock-database-url-{environment}", project_id)
        if database_url:
            secrets["DATABASE_URL"] = database_url
        
        # Load Redis URL
        redis_url = load_secret(f"settlers-of-stock-redis-url-{environment}", project_id)
        if redis_url:
            secrets["REDIS_URL"] = redis_url
        
        # Load API keys
        api_keys_data = load_secret(f"settlers-of-stock-api-keys-{environment}", project_id)
        if api_keys_data:
            api_keys = json.loads(api_keys_data)
            secrets["ALPHA_VANTAGE_API_KEY"] = api_keys.get("alpha_vantage", "")
            secrets["NEWS_API_KEY"] = api_keys.get("news_api", "")
        
        # Load Reddit credentials
        reddit_creds_data = load_secret(f"settlers-of-stock-reddit-credentials-{environment}", project_id)
        if reddit_creds_data:
            reddit_creds = json.loads(reddit_creds_data)
            secrets["REDDIT_CLIENT_ID"] = reddit_creds.get("client_id", "")
            secrets["REDDIT_CLIENT_SECRET"] = reddit_creds.get("client_secret", "")
        
        # Load SMTP configuration
        smtp_config_data = load_secret(f"settlers-of-stock-smtp-config-{environment}", project_id)
        if smtp_config_data:
            smtp_config = json.loads(smtp_config_data)
            secrets["SMTP_HOST"] = smtp_config.get("host", "")
            secrets["SMTP_PORT"] = smtp_config.get("port", 587)
            secrets["SMTP_USER"] = smtp_config.get("user", "")
            secrets["SMTP_PASSWORD"] = smtp_config.get("password", "")
            secrets["SMTP_TLS"] = smtp_config.get("tls", True)
    
    return secrets

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    env = os.getenv("ENVIRONMENT", "development")
    project_id = os.getenv("GCP_PROJECT_ID")
    
    # Load environment-specific .env file
    env_file = f".env.{env}" if env != "development" else ".env"
    
    # Create settings instance
    if env == "test":
        settings = Settings(_env_file=".env.test")
    else:
        settings = Settings(_env_file=env_file)
    
    # Load secrets from Google Secret Manager for production/staging
    if env in ["production", "staging"] and project_id:
        secrets = load_secrets_for_environment(env, project_id)
        
        # Override settings with secrets
        for key, value in secrets.items():
            if hasattr(settings, key.lower()):
                setattr(settings, key.lower(), value)
            elif key == "SECRET_KEY":
                settings.SECRET_KEY = value
            elif key == "DATABASE_URL":
                settings.DATABASE_URL = value
            elif key == "REDIS_URL":
                settings.REDIS_URL = value
    
    return settings