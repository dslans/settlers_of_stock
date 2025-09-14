import pytest
from unittest.mock import patch
from app.core.config import Settings, get_settings

class TestSettings:
    """Test configuration settings."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()
        
        assert settings.API_V1_STR == "/api/v1"
        assert settings.PROJECT_NAME == "Settlers of Stock"
        assert settings.environment == "development"
        assert settings.debug is True
        assert settings.GCP_REGION == "us-central1"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        
    def test_cors_origins_default(self):
        """Test default CORS origins configuration."""
        settings = Settings()
        
        expected_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ]
        
        assert settings.cors_origins == expected_origins
        
    def test_allowed_hosts_default(self):
        """Test default allowed hosts configuration."""
        settings = Settings()
        
        expected_hosts = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
            "testserver"  # For FastAPI TestClient
        ]
        
        assert settings.allowed_hosts == expected_hosts

    @patch.dict('os.environ', {
        'ENVIRONMENT': 'production',
        'DEBUG': 'false',
        'SECRET_KEY': 'test-secret-key'
    })
    def test_environment_override(self):
        """Test that environment variables override defaults."""
        settings = Settings()
        
        assert settings.environment == "production"
        assert settings.debug is False
        assert settings.SECRET_KEY == "test-secret-key"

    def test_get_settings_cached(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should be the same instance due to lru_cache
        assert settings1 is settings2

class TestConfigurationValidation:
    """Test configuration validation and edge cases."""
    
    def test_optional_fields_none(self):
        """Test that optional fields can be None."""
        settings = Settings()
        
        # These should be None by default
        assert settings.DATABASE_URL is None
        assert settings.REDIS_URL is None
        assert settings.GCP_PROJECT_ID is None
        assert settings.ALPHA_VANTAGE_API_KEY is None
        assert settings.NEWS_API_KEY is None

    @patch.dict('os.environ', {
        'DATABASE_URL': 'postgresql://user:pass@localhost/db',
        'REDIS_URL': 'redis://localhost:6379',
        'GCP_PROJECT_ID': 'test-project-123'
    })
    def test_optional_fields_with_values(self):
        """Test optional fields when provided via environment."""
        settings = Settings()
        
        assert settings.DATABASE_URL == "postgresql://user:pass@localhost/db"
        assert settings.REDIS_URL == "redis://localhost:6379"
        assert settings.GCP_PROJECT_ID == "test-project-123"