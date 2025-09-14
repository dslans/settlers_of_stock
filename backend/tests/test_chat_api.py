"""
Integration tests for Chat API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import json

from main import app
from app.services.chat_service import ChatResponse, ChatMessage, UserPreferences
from app.services.vertex_ai_service import AnalysisResult

class TestChatAPI:
    """Test cases for Chat API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user_token(self):
        """Mock JWT token for authenticated user"""
        return "Bearer mock_jwt_token"
    
    @pytest.fixture
    def mock_auth_dependency(self):
        """Mock authentication dependency"""
        with patch('app.api.chat.get_current_user') as mock_auth:
            mock_auth.return_value = {"sub": "test_user_123", "email": "test@example.com"}
            yield mock_auth
    
    @pytest.fixture
    def mock_chat_service(self):
        """Mock chat service"""
        with patch('app.api.chat.chat_service') as mock_service:
            yield mock_service
    
    def test_send_chat_message_success(self, client, mock_auth_dependency, mock_chat_service):
        """Test successful chat message sending"""
        # Mock chat service response
        mock_response = ChatResponse(
            message="AAPL is a strong buy with 85% confidence...",
            analysis_data={"symbol": "AAPL", "recommendation": "BUY", "confidence": 85},
            suggestions=["What are the risks?", "Compare to competitors"]
        )
        mock_chat_service.process_message = AsyncMock(return_value=mock_response)
        
        # Test request
        response = client.post(
            "/api/v1/chat",
            json={"message": "What do you think about AAPL?"},
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "AAPL is a strong buy with 85% confidence..."
        assert data["analysis_data"]["symbol"] == "AAPL"
        assert len(data["suggestions"]) == 2
        
        # Verify service was called
        mock_chat_service.process_message.assert_called_once()
    
    def test_send_chat_message_with_analysis_data(self, client, mock_auth_dependency, mock_chat_service):
        """Test chat message with analysis data"""
        # Mock chat service response
        mock_response = ChatResponse(
            message="Based on the analysis, AAPL shows strong fundamentals...",
            analysis_data={"symbol": "AAPL", "recommendation": "BUY", "confidence": 85}
        )
        mock_chat_service.process_message = AsyncMock(return_value=mock_response)
        
        # Test request with analysis data
        analysis_data = {
            "symbol": "AAPL",
            "recommendation": "BUY",
            "confidence": 85,
            "reasoning": ["Strong fundamentals"],
            "risks": ["Market volatility"]
        }
        
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Analyze this stock",
                "analysis_data": analysis_data
            },
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "AAPL" in data["message"]
        
        # Verify service was called with analysis result
        mock_chat_service.process_message.assert_called_once()
        call_args = mock_chat_service.process_message.call_args
        assert call_args[1]["analysis_result"] is not None
        assert call_args[1]["analysis_result"].symbol == "AAPL"
    
    def test_send_chat_message_invalid_analysis_data(self, client, mock_auth_dependency, mock_chat_service):
        """Test chat message with invalid analysis data"""
        # Mock chat service response (should still work without analysis data)
        mock_response = ChatResponse(message="I can help you with stock analysis...")
        mock_chat_service.process_message = AsyncMock(return_value=mock_response)
        
        # Test request with invalid analysis data
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Tell me about stocks",
                "analysis_data": {"invalid": "data"}
            },
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Should still succeed but without analysis data
        assert response.status_code == 200
        
        # Verify service was called without analysis result
        call_args = mock_chat_service.process_message.call_args
        assert call_args[1]["analysis_result"] is None
    
    def test_send_chat_message_service_error(self, client, mock_auth_dependency, mock_chat_service):
        """Test chat message when service fails"""
        # Mock service error
        mock_chat_service.process_message = AsyncMock(side_effect=Exception("Service error"))
        
        # Test request
        response = client.post(
            "/api/v1/chat",
            json={"message": "Test message"},
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Should return 500 error
        assert response.status_code == 500
        data = response.json()
        assert "Failed to process chat message" in data["detail"]
    
    def test_get_chat_history_success(self, client, mock_auth_dependency, mock_chat_service):
        """Test successful chat history retrieval"""
        # Mock chat history
        mock_messages = [
            ChatMessage(
                id="msg_1",
                user_id="test_user_123",
                type="user",
                content="Hello"
            ),
            ChatMessage(
                id="msg_2",
                user_id="test_user_123",
                type="assistant",
                content="Hi there!"
            )
        ]
        mock_chat_service.get_chat_history = AsyncMock(return_value=mock_messages)
        
        # Test request
        response = client.get(
            "/api/v1/chat/history",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 2
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][1]["content"] == "Hi there!"
    
    def test_get_chat_history_with_limit(self, client, mock_auth_dependency, mock_chat_service):
        """Test chat history retrieval with limit"""
        mock_chat_service.get_chat_history = AsyncMock(return_value=[])
        
        # Test request with limit
        response = client.get(
            "/api/v1/chat/history?limit=10",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        
        # Verify service was called with correct limit
        mock_chat_service.get_chat_history.assert_called_with("test_user_123", 10)
    
    def test_clear_chat_history_success(self, client, mock_auth_dependency, mock_chat_service):
        """Test successful chat history clearing"""
        mock_chat_service.clear_conversation = AsyncMock()
        
        # Test request
        response = client.delete(
            "/api/v1/chat/history",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "cleared successfully" in data["message"]
        
        # Verify service was called
        mock_chat_service.clear_conversation.assert_called_with("test_user_123")
    
    def test_get_user_preferences_success(self, client, mock_auth_dependency, mock_chat_service):
        """Test successful user preferences retrieval"""
        # Mock preferences
        mock_prefs = UserPreferences(
            risk_tolerance="moderate",
            investment_horizon="medium",
            preferred_analysis=["fundamental", "technical"]
        )
        mock_chat_service.get_user_preferences = AsyncMock(return_value=mock_prefs)
        
        # Test request
        response = client.get(
            "/api/v1/chat/preferences",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["risk_tolerance"] == "moderate"
        assert data["investment_horizon"] == "medium"
        assert "fundamental" in data["preferred_analysis"]
    
    def test_update_user_preferences_success(self, client, mock_auth_dependency, mock_chat_service):
        """Test successful user preferences update"""
        # Mock current and updated preferences
        current_prefs = UserPreferences(risk_tolerance="moderate")
        updated_prefs = UserPreferences(risk_tolerance="aggressive")
        
        mock_chat_service.get_user_preferences = AsyncMock(return_value=current_prefs)
        mock_chat_service.update_user_preferences = AsyncMock()
        
        # Test request
        response = client.put(
            "/api/v1/chat/preferences",
            json={"risk_tolerance": "aggressive"},
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["risk_tolerance"] == "aggressive"
        
        # Verify service was called
        mock_chat_service.update_user_preferences.assert_called_once()
    
    def test_explain_technical_indicator_success(self, client, mock_auth_dependency, mock_chat_service):
        """Test successful technical indicator explanation"""
        # Mock vertex AI service
        mock_vertex_ai = Mock()
        mock_vertex_ai.explain_technical_indicator = AsyncMock(
            return_value="The RSI of 70 indicates that AAPL may be overbought..."
        )
        mock_chat_service.vertex_ai = mock_vertex_ai
        mock_chat_service.get_conversation_context = AsyncMock()
        
        # Test request
        response = client.post(
            "/api/v1/chat/explain/RSI?value=70.0&symbol=AAPL",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "RSI" in data["explanation"]
        assert "overbought" in data["explanation"]
    
    def test_get_market_summary_success(self, client, mock_auth_dependency, mock_chat_service):
        """Test successful market summary generation"""
        # Mock vertex AI service
        mock_vertex_ai = Mock()
        mock_vertex_ai.generate_market_summary = AsyncMock(
            return_value="The market is showing mixed signals today..."
        )
        mock_chat_service.vertex_ai = mock_vertex_ai
        mock_chat_service.get_conversation_context = AsyncMock()
        
        # Test request
        response = client.get(
            "/api/v1/chat/market-summary",
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "mixed signals" in data["summary"]
    
    def test_chat_health_check_success(self, client, mock_chat_service):
        """Test chat service health check"""
        # Mock vertex AI service
        mock_vertex_ai = Mock()
        mock_vertex_ai.get_active_sessions_count.return_value = 5
        mock_chat_service.vertex_ai = mock_vertex_ai
        
        # Test request (no auth required for health check)
        response = client.get("/api/v1/chat/health")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "chat"
        assert data["active_sessions"] == 5
        assert "timestamp" in data
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to protected endpoints"""
        # Test without authorization header
        response = client.post(
            "/api/v1/chat",
            json={"message": "Test message"}
        )
        
        # Should return 401 or 403 (depending on auth implementation)
        assert response.status_code in [401, 403]
    
    def test_invalid_request_data(self, client, mock_auth_dependency):
        """Test invalid request data validation"""
        # Test with missing required field
        response = client.post(
            "/api/v1/chat",
            json={},  # Missing 'message' field
            headers={"Authorization": "Bearer mock_token"}
        )
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert "error" in data or "detail" in data