import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

class TestHealthEndpoints:
    """Test suite for health and status endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns expected response."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Settlers of Stock API is running"
        assert data["version"] == "1.0.0"
        assert "docs" in data

    def test_health_check_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert data["status"] == "healthy"
        assert data["service"] == "settlers-of-stock-api"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)

    def test_status_endpoint(self):
        """Test the detailed status endpoint."""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert data["status"] == "operational"
        assert data["service"] == "settlers-of-stock-api"
        assert data["version"] == "1.0.0"
        assert data["environment"] == "development"
        assert "uptime" in data
        assert "dependencies" in data
        
        # Verify dependencies structure
        dependencies = data["dependencies"]
        assert "database" in dependencies
        assert "redis" in dependencies
        assert "external_apis" in dependencies
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)

class TestCORSMiddleware:
    """Test CORS middleware configuration."""
    
    def test_cors_preflight_request(self):
        """Test CORS preflight request handling."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers

    def test_cors_actual_request(self):
        """Test actual CORS request with allowed origin."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"

class TestErrorHandling:
    """Test error handling and exception responses."""
    
    def test_404_not_found(self):
        """Test 404 error handling for non-existent endpoints."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        data = response.json()
        # FastAPI default 404 response format
        assert "detail" in data
        assert data["detail"] == "Not Found"

    def test_method_not_allowed(self):
        """Test 405 error handling for unsupported methods."""
        response = client.post("/health")
        assert response.status_code == 405
        data = response.json()
        # FastAPI default 405 response format
        assert "detail" in data
        assert data["detail"] == "Method Not Allowed"

class TestRequestLogging:
    """Test request logging middleware."""
    
    @patch('main.logger')
    def test_request_logging(self, mock_logger):
        """Test that requests are properly logged."""
        response = client.get("/health")
        assert response.status_code == 200
        
        # Verify logging calls were made
        mock_logger.info.assert_called()
        
        # Check that request and response were logged
        log_calls = [call.args[0] for call in mock_logger.info.call_args_list]
        request_logged = any("Request: GET" in call for call in log_calls)
        response_logged = any("Response: 200" in call for call in log_calls)
        
        assert request_logged, "Request should be logged"
        assert response_logged, "Response should be logged"

class TestApplicationLifecycle:
    """Test application startup and shutdown events."""
    
    def test_startup_logging(self):
        """Test that startup events are configured."""
        # Since startup events happen when the app is created, 
        # we can't easily mock the logger after the fact.
        # Instead, we verify that the startup event handler exists
        startup_handlers = [handler for handler in app.router.on_startup]
        assert len(startup_handlers) > 0, "Startup event handler should be registered"

class TestResponseModels:
    """Test response model validation."""
    
    def test_health_response_model(self):
        """Test health response follows the expected model."""
        response = client.get("/health")
        data = response.json()
        
        # Verify all required fields are present
        required_fields = ["status", "service", "version", "timestamp", "environment"]
        for field in required_fields:
            assert field in data, f"Field '{field}' missing from health response"

    def test_status_response_model(self):
        """Test status response follows the expected model."""
        response = client.get("/status")
        data = response.json()
        
        # Verify all required fields are present
        required_fields = ["status", "service", "version", "timestamp", "environment", "uptime", "dependencies"]
        for field in required_fields:
            assert field in data, f"Field '{field}' missing from status response"