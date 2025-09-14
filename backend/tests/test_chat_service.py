"""
Tests for Chat service functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

from app.services.chat_service import (
    ChatService, 
    ChatMessage, 
    ChatResponse, 
    UserPreferences
)
from app.services.vertex_ai_service import AnalysisResult, ConversationContext

class TestChatService:
    """Test cases for Chat service"""
    
    @pytest.fixture
    def mock_chat_service(self):
        """Create a mock chat service for testing"""
        with patch('app.services.chat_service.VertexAIService') as mock_vertex_ai, \
             patch('app.services.chat_service.redis.Redis') as mock_redis:
            
            # Mock VertexAI service
            mock_vertex_ai_instance = Mock()
            mock_vertex_ai_instance.generate_stock_analysis_response = AsyncMock()
            mock_vertex_ai_instance.handle_follow_up_question = AsyncMock()
            mock_vertex_ai_instance.clear_chat_session = Mock()
            mock_vertex_ai.return_value = mock_vertex_ai_instance
            
            # Mock Redis client
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.get.return_value = None
            mock_redis_instance.setex = Mock()
            mock_redis_instance.lpush = Mock()
            mock_redis_instance.ltrim = Mock()
            mock_redis_instance.expire = Mock()
            mock_redis_instance.pipeline.return_value = mock_redis_instance
            mock_redis_instance.execute = Mock()
            mock_redis_instance.lrange.return_value = []
            mock_redis_instance.delete = Mock()
            mock_redis.return_value = mock_redis_instance
            
            service = ChatService()
            service.vertex_ai = mock_vertex_ai_instance
            service.redis_client = mock_redis_instance
            
            return service, mock_vertex_ai_instance, mock_redis_instance
    
    @pytest.fixture
    def sample_analysis_result(self):
        """Create sample analysis result for testing"""
        return AnalysisResult(
            symbol="AAPL",
            recommendation="BUY",
            confidence=85,
            reasoning=["Strong fundamentals", "Positive technical indicators"],
            risks=["Market volatility", "Regulatory concerns"],
            targets={"short_term": 180.0, "medium_term": 200.0},
            analysis_type="combined"
        )
    
    @pytest.fixture
    def sample_chat_message(self):
        """Create sample chat message"""
        return ChatMessage(
            id="msg_123",
            user_id="user_123",
            type="user",
            content="Tell me about AAPL"
        )
    
    @pytest.mark.asyncio
    async def test_process_message_with_analysis(self, mock_chat_service, sample_analysis_result):
        """Test processing message with analysis result"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Mock VertexAI response
        mock_vertex_ai.generate_stock_analysis_response.return_value = "AAPL is a strong buy with 85% confidence..."
        
        # Test the method
        result = await service.process_message(
            "user_123", 
            "What do you think about AAPL?", 
            sample_analysis_result
        )
        
        # Assertions
        assert isinstance(result, ChatResponse)
        assert result.message == "AAPL is a strong buy with 85% confidence..."
        assert result.analysis_data["symbol"] == "AAPL"
        assert result.analysis_data["recommendation"] == "BUY"
        assert result.analysis_data["confidence"] == 85
        assert len(result.suggestions) > 0
        
        # Verify VertexAI was called
        mock_vertex_ai.generate_stock_analysis_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_follow_up(self, mock_chat_service):
        """Test processing follow-up message without analysis"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Mock VertexAI response
        mock_vertex_ai.handle_follow_up_question.return_value = "Here's more information about the risks..."
        
        # Test the method
        result = await service.process_message("user_123", "What about the risks?")
        
        # Assertions
        assert isinstance(result, ChatResponse)
        assert result.message == "Here's more information about the risks..."
        assert result.analysis_data is None
        assert len(result.suggestions) > 0
        
        # Verify VertexAI was called for follow-up
        mock_vertex_ai.handle_follow_up_question.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self, mock_chat_service):
        """Test error handling in message processing"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Mock error
        mock_vertex_ai.handle_follow_up_question.side_effect = Exception("API Error")
        
        # Test the method
        result = await service.process_message("user_123", "Tell me about stocks")
        
        # Should return error response
        assert result.message_type == "error"
        assert "having trouble processing" in result.message
    
    @pytest.mark.asyncio
    async def test_get_conversation_context_existing(self, mock_chat_service):
        """Test retrieving existing conversation context"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Mock existing context in Redis
        context_data = {
            "user_id": "user_123",
            "previous_messages": [{"user": "Hello", "assistant": "Hi there!"}],
            "current_stocks": ["AAPL"],
            "analysis_history": [],
            "user_preferences": {},
            "session_start": "2024-01-01T10:00:00"
        }
        mock_redis.get.return_value = json.dumps(context_data)
        
        # Test the method
        context = await service.get_conversation_context("user_123")
        
        # Assertions
        assert context.user_id == "user_123"
        assert len(context.previous_messages) == 1
        assert "AAPL" in context.current_stocks
        
        # Verify Redis was called
        mock_redis.get.assert_called_with("chat_context:user_123")
    
    @pytest.mark.asyncio
    async def test_get_conversation_context_new(self, mock_chat_service):
        """Test creating new conversation context"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Mock no existing context
        mock_redis.get.return_value = None
        
        # Test the method
        context = await service.get_conversation_context("user_123")
        
        # Assertions
        assert context.user_id == "user_123"
        assert len(context.previous_messages) == 0
        assert len(context.current_stocks) == 0
    
    @pytest.mark.asyncio
    async def test_store_conversation_context(self, mock_chat_service):
        """Test storing conversation context"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        context = ConversationContext(user_id="user_123")
        
        # Test the method
        await service.store_conversation_context("user_123", context)
        
        # Verify Redis was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "chat_context:user_123"
        assert call_args[0][1] == 86400  # 24 hour TTL
    
    @pytest.mark.asyncio
    async def test_store_chat_message(self, mock_chat_service, sample_chat_message):
        """Test storing chat message"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Test the method
        await service.store_chat_message("user_123", sample_chat_message)
        
        # Verify Redis pipeline was used
        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once()
        mock_redis.expire.assert_called_once()
        mock_redis.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_chat_history(self, mock_chat_service):
        """Test retrieving chat history"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Mock chat history in Redis
        message_data = {
            "id": "msg_123",
            "user_id": "user_123",
            "type": "user",
            "content": "Hello",
            "timestamp": "2024-01-01T10:00:00"
        }
        mock_redis.lrange.return_value = [json.dumps(message_data)]
        
        # Test the method
        history = await service.get_chat_history("user_123", 10)
        
        # Assertions
        assert len(history) == 1
        assert history[0].content == "Hello"
        assert history[0].type == "user"
        
        # Verify Redis was called
        mock_redis.lrange.assert_called_with("chat_history:user_123", 0, 9)
    
    @pytest.mark.asyncio
    async def test_clear_conversation(self, mock_chat_service):
        """Test clearing conversation"""
        service, mock_vertex_ai, mock_redis = mock_chat_service
        
        # Test the method
        await service.clear_conversation("user_123")
        
        # Verify Redis keys were deleted
        assert mock_redis.delete.call_count == 2
        mock_redis.delete.assert_any_call("chat_context:user_123")
        mock_redis.delete.assert_any_call("chat_history:user_123")
        
        # Verify VertexAI session was cleared
        mock_vertex_ai.clear_chat_session.assert_called_with("user_123")
    
    def test_generate_follow_up_suggestions_buy(self, mock_chat_service, sample_analysis_result):
        """Test follow-up suggestions for BUY recommendation"""
        service, _, _ = mock_chat_service
        
        suggestions = service._generate_follow_up_suggestions(sample_analysis_result)
        
        # Should contain BUY-specific suggestions
        assert len(suggestions) == 4
        assert any("risks" in s.lower() for s in suggestions)
        assert any("competitors" in s.lower() for s in suggestions)
        assert any("entry point" in s.lower() for s in suggestions)
    
    def test_generate_follow_up_suggestions_sell(self, mock_chat_service):
        """Test follow-up suggestions for SELL recommendation"""
        service, _, _ = mock_chat_service
        
        sell_analysis = AnalysisResult(
            symbol="XYZ",
            recommendation="SELL",
            confidence=75,
            reasoning=["Declining fundamentals"],
            risks=["Further decline"]
        )
        
        suggestions = service._generate_follow_up_suggestions(sell_analysis)
        
        # Should contain SELL-specific suggestions
        assert any("declining" in s.lower() for s in suggestions)
        assert any("catalysts" in s.lower() for s in suggestions)
        assert any("alternatives" in s.lower() for s in suggestions)
    
    def test_generate_follow_up_suggestions_hold(self, mock_chat_service):
        """Test follow-up suggestions for HOLD recommendation"""
        service, _, _ = mock_chat_service
        
        hold_analysis = AnalysisResult(
            symbol="ABC",
            recommendation="HOLD",
            confidence=60,
            reasoning=["Mixed signals"],
            risks=["Uncertainty"]
        )
        
        suggestions = service._generate_follow_up_suggestions(hold_analysis)
        
        # Should contain HOLD-specific suggestions
        assert any("buy" in s.lower() for s in suggestions)
        assert any("hold" in s.lower() for s in suggestions)
        assert any("metrics" in s.lower() for s in suggestions)
    
    def test_generate_general_suggestions(self, mock_chat_service):
        """Test general suggestions generation"""
        service, _, _ = mock_chat_service
        
        context = ConversationContext(user_id="user_123")
        suggestions = service._generate_general_suggestions(context)
        
        # Should contain general suggestions
        assert len(suggestions) == 4
        assert any("analyze" in s.lower() for s in suggestions)
        assert any("market trends" in s.lower() for s in suggestions)
    
    def test_generate_general_suggestions_with_context(self, mock_chat_service):
        """Test general suggestions with conversation context"""
        service, _, _ = mock_chat_service
        
        context = ConversationContext(
            user_id="user_123",
            current_stocks=["AAPL", "GOOGL"]
        )
        suggestions = service._generate_general_suggestions(context)
        
        # Should include context-specific suggestions
        assert any("GOOGL" in s for s in suggestions)  # Most recent stock
        assert any("compare" in s.lower() for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_get_user_preferences_existing(self, mock_chat_service):
        """Test retrieving existing user preferences"""
        service, _, mock_redis = mock_chat_service
        
        # Mock existing preferences
        prefs_data = {
            "risk_tolerance": "aggressive",
            "investment_horizon": "long",
            "preferred_analysis": ["technical"],
            "notification_settings": {}
        }
        mock_redis.get.return_value = json.dumps(prefs_data)
        
        # Test the method
        prefs = await service.get_user_preferences("user_123")
        
        # Assertions
        assert prefs.risk_tolerance == "aggressive"
        assert prefs.investment_horizon == "long"
        assert prefs.preferred_analysis == ["technical"]
    
    @pytest.mark.asyncio
    async def test_get_user_preferences_default(self, mock_chat_service):
        """Test getting default user preferences"""
        service, _, mock_redis = mock_chat_service
        
        # Mock no existing preferences
        mock_redis.get.return_value = None
        
        # Test the method
        prefs = await service.get_user_preferences("user_123")
        
        # Should return defaults
        assert prefs.risk_tolerance == "moderate"
        assert prefs.investment_horizon == "medium"
        assert "fundamental" in prefs.preferred_analysis
        assert "technical" in prefs.preferred_analysis
    
    @pytest.mark.asyncio
    async def test_update_user_preferences(self, mock_chat_service):
        """Test updating user preferences"""
        service, _, mock_redis = mock_chat_service
        
        prefs = UserPreferences(
            risk_tolerance="conservative",
            investment_horizon="short"
        )
        
        # Test the method
        await service.update_user_preferences("user_123", prefs)
        
        # Verify Redis was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "user_prefs:user_123"
        assert call_args[0][1] == 86400 * 30  # 30 day TTL
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """Test handling Redis connection failure"""
        with patch('app.services.chat_service.VertexAIService'), \
             patch('app.services.chat_service.redis.Redis') as mock_redis:
            
            # Mock Redis connection failure
            mock_redis_instance = Mock()
            mock_redis_instance.ping.side_effect = Exception("Connection failed")
            mock_redis.return_value = mock_redis_instance
            
            # Should initialize without Redis
            service = ChatService()
            assert service.redis_client is None
    
    @pytest.mark.asyncio
    async def test_context_operations_without_redis(self, mock_chat_service):
        """Test context operations when Redis is unavailable"""
        service, _, _ = mock_chat_service
        service.redis_client = None  # Simulate no Redis
        
        # Should still work with defaults
        context = await service.get_conversation_context("user_123")
        assert context.user_id == "user_123"
        
        # Store should not fail
        await service.store_conversation_context("user_123", context)
        
        # History should return empty list
        history = await service.get_chat_history("user_123")
        assert history == []