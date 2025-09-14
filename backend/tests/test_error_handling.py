import pytest
from datetime import datetime
from fastapi import HTTPException
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from unittest.mock import patch, Mock
from main import app

client = TestClient(app)

class TestExceptionHandlers:
    """Test custom exception handlers."""
    
    def test_http_exception_handler(self):
        """Test HTTP exception handling."""
        # Create a test endpoint that raises HTTPException
        @app.get("/test-http-error")
        async def test_http_error():
            raise HTTPException(status_code=400, detail="Test error message")
        
        response = client.get("/test-http-error")
        assert response.status_code == 400
        
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Test error message"
        assert data["status_code"] == 400
        assert "timestamp" in data
        
        # Verify timestamp format
        timestamp = datetime.fromisoformat(data["timestamp"])
        assert isinstance(timestamp, datetime)

    def test_validation_exception_handler(self):
        """Test validation error handling."""
        # Create a test endpoint with validation
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            required_field: str
            number_field: int
        
        @app.post("/test-validation")
        async def test_validation(data: TestModel):
            return {"message": "success"}
        
        # Send invalid data
        response = client.post("/test-validation", json={"number_field": "not_a_number"})
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Validation error"
        assert data["status_code"] == 422
        assert "details" in data
        assert "timestamp" in data

    @patch('main.logger')
    def test_general_exception_handler(self, mock_logger):
        """Test general exception handling."""
        # Create a test endpoint that raises a general exception
        @app.get("/test-general-error")
        async def test_general_error():
            raise ValueError("Test general error")
        
        response = client.get("/test-general-error")
        assert response.status_code == 500
        
        data = response.json()
        assert data["error"] is True
        assert data["message"] == "Internal server error"
        assert data["status_code"] == 500
        assert "timestamp" in data
        
        # Verify error was logged
        mock_logger.error.assert_called()

class TestErrorResponseFormat:
    """Test error response format consistency."""
    
    def test_404_error_format(self):
        """Test 404 error response format."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        data = response.json()
        required_fields = ["error", "message", "status_code", "timestamp"]
        for field in required_fields:
            assert field in data, f"Field '{field}' missing from error response"
        
        assert data["error"] is True
        assert isinstance(data["status_code"], int)

    def test_405_error_format(self):
        """Test 405 method not allowed error format."""
        response = client.post("/health")  # GET-only endpoint
        assert response.status_code == 405
        
        data = response.json()
        required_fields = ["error", "message", "status_code", "timestamp"]
        for field in required_fields:
            assert field in data, f"Field '{field}' missing from error response"

class TestLoggingBehavior:
    """Test logging behavior during error conditions."""
    
    @patch('main.logger')
    def test_http_error_logging(self, mock_logger):
        """Test that HTTP errors are properly logged."""
        @app.get("/test-logged-error")
        async def test_logged_error():
            raise HTTPException(status_code=400, detail="Test logged error")
        
        response = client.get("/test-logged-error")
        assert response.status_code == 400
        
        # Verify error was logged
        mock_logger.error.assert_called()
        log_message = mock_logger.error.call_args[0][0]
        assert "HTTP 400 error" in log_message
        assert "Test logged error" in log_message

    @patch('main.logger')
    def test_validation_error_logging(self, mock_logger):
        """Test that validation errors are properly logged."""
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            required_field: str
        
        @app.post("/test-validation-logging")
        async def test_validation_logging(data: TestModel):
            return {"message": "success"}
        
        response = client.post("/test-validation-logging", json={})
        assert response.status_code == 422
        
        # Verify validation error was logged
        mock_logger.error.assert_called()
        log_message = mock_logger.error.call_args[0][0]
        assert "Validation error" in log_message

    @patch('main.logger')
    def test_general_error_logging_with_traceback(self, mock_logger):
        """Test that general errors are logged with traceback."""
        @app.get("/test-traceback-logging")
        async def test_traceback_logging():
            raise RuntimeError("Test runtime error")
        
        response = client.get("/test-traceback-logging")
        assert response.status_code == 500
        
        # Verify error was logged with exc_info=True
        mock_logger.error.assert_called()
        call_args, call_kwargs = mock_logger.error.call_args
        assert call_kwargs.get("exc_info") is True