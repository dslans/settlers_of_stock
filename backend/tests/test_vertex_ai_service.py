"""
Tests for Vertex AI service functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from decimal import Decimal

from app.services.vertex_ai_service import (
    VertexAIService, 
    ConversationContext, 
    AnalysisResult
)

class TestVertexAIService:
    """Test cases for VertexAI service"""
    
    @pytest.fixture
    def mock_vertex_ai_service(self):
        """Create a mock VertexAI service for testing"""
        with patch('app.services.vertex_ai_service.vertexai.init'), \
             patch('app.services.vertex_ai_service.GenerativeModel') as mock_model:
            
            # Mock the model and its methods
            mock_model_instance = Mock()
            mock_model.return_value = mock_model_instance
            mock_model_instance.generate_content_async = AsyncMock()
            mock_model_instance.start_chat = Mock()
            
            service = VertexAIService(project_id="test-project")
            service.model = mock_model_instance
            
            return service, mock_model_instance
    
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
    def sample_context(self):
        """Create sample conversation context"""
        return ConversationContext(
            user_id="test_user_123",
            previous_messages=[
                {"user": "Tell me about AAPL", "assistant": "Apple is a strong stock...", "timestamp": "2024-01-01T10:00:00"}
            ],
            current_stocks=["AAPL"],
            user_preferences={"risk_tolerance": "moderate"}
        )
    
    @pytest.mark.asyncio
    async def test_generate_stock_analysis_response_success(self, mock_vertex_ai_service, sample_analysis_result, sample_context):
        """Test successful stock analysis response generation"""
        service, mock_model = mock_vertex_ai_service
        
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "Based on my analysis, AAPL is a strong buy with 85% confidence..."
        mock_model.generate_content_async.return_value = mock_response
        
        # Test the method
        result = await service.generate_stock_analysis_response(
            sample_analysis_result, 
            "What do you think about AAPL?", 
            sample_context
        )
        
        # Assertions
        assert result == "Based on my analysis, AAPL is a strong buy with 85% confidence..."
        assert mock_model.generate_content_async.called
        
        # Check that context was updated
        assert len(sample_context.previous_messages) == 2
        assert sample_context.previous_messages[-1]["user"] == "What do you think about AAPL?"
    
    @pytest.mark.asyncio
    async def test_generate_stock_analysis_response_with_chat_session(self, mock_vertex_ai_service, sample_analysis_result, sample_context):
        """Test response generation using existing chat session"""
        service, mock_model = mock_vertex_ai_service
        
        # Setup existing chat session
        mock_chat_session = Mock()
        mock_chat_session.send_message_async = AsyncMock()
        mock_response = Mock()
        mock_response.text = "Following up on our AAPL discussion..."
        mock_chat_session.send_message_async.return_value = mock_response
        
        service.chat_sessions[sample_context.user_id] = mock_chat_session
        
        # Test the method
        result = await service.generate_stock_analysis_response(
            sample_analysis_result, 
            "What about the risks?", 
            sample_context
        )
        
        # Assertions
        assert result == "Following up on our AAPL discussion..."
        assert mock_chat_session.send_message_async.called
        assert not mock_model.generate_content_async.called  # Should use chat session instead
    
    @pytest.mark.asyncio
    async def test_generate_stock_analysis_response_error_handling(self, mock_vertex_ai_service, sample_analysis_result):
        """Test error handling in response generation"""
        service, mock_model = mock_vertex_ai_service
        
        # Mock error
        mock_model.generate_content_async.side_effect = Exception("API Error")
        
        # Test the method
        result = await service.generate_stock_analysis_response(
            sample_analysis_result, 
            "What do you think about AAPL?"
        )
        
        # Should return fallback response
        assert "AAPL" in result
        assert "BUY" in result
        assert "85%" in result
        assert "informational" in result and "purposes" in result
    
    @pytest.mark.asyncio
    async def test_generate_market_summary(self, mock_vertex_ai_service):
        """Test market summary generation"""
        service, mock_model = mock_vertex_ai_service
        
        # Mock response
        mock_response = Mock()
        mock_response.text = "The market is showing mixed signals today..."
        mock_model.generate_content_async.return_value = mock_response
        
        # Sample market data
        market_data = [
            {"symbol": "AAPL", "change": 2.5, "volume": 50000000},
            {"symbol": "GOOGL", "change": -1.2, "volume": 30000000}
        ]
        
        # Test the method
        result = await service.generate_market_summary(market_data)
        
        # Assertions
        assert result == "The market is showing mixed signals today..."
        assert mock_model.generate_content_async.called
        
        # Check that prompt includes market data
        call_args = mock_model.generate_content_async.call_args[0][0]
        assert "AAPL" in call_args
        assert "GOOGL" in call_args
    
    @pytest.mark.asyncio
    async def test_explain_technical_indicator(self, mock_vertex_ai_service):
        """Test technical indicator explanation"""
        service, mock_model = mock_vertex_ai_service
        
        # Mock response
        mock_response = Mock()
        mock_response.text = "The RSI of 70 indicates that AAPL may be overbought..."
        mock_model.generate_content_async.return_value = mock_response
        
        # Test the method
        result = await service.explain_technical_indicator("RSI", 70.0, "AAPL")
        
        # Assertions
        assert result == "The RSI of 70 indicates that AAPL may be overbought..."
        assert mock_model.generate_content_async.called
        
        # Check prompt content
        call_args = mock_model.generate_content_async.call_args[0][0]
        assert "RSI" in call_args
        assert "70" in call_args
        assert "AAPL" in call_args
    
    @pytest.mark.asyncio
    async def test_handle_follow_up_question(self, mock_vertex_ai_service, sample_context):
        """Test follow-up question handling"""
        service, mock_model = mock_vertex_ai_service
        
        # Mock response
        mock_response = Mock()
        mock_response.text = "Regarding the risks we discussed for AAPL..."
        mock_model.generate_content_async.return_value = mock_response
        
        # Test the method
        result = await service.handle_follow_up_question("What about the risks?", sample_context)
        
        # Assertions
        assert result == "Regarding the risks we discussed for AAPL..."
        assert mock_model.generate_content_async.called
        
        # Check that context was updated
        assert len(sample_context.previous_messages) == 2
        assert sample_context.previous_messages[-1]["user"] == "What about the risks?"
    
    @pytest.mark.asyncio
    async def test_handle_follow_up_with_existing_session(self, mock_vertex_ai_service, sample_context):
        """Test follow-up handling with existing chat session"""
        service, mock_model = mock_vertex_ai_service
        
        # Setup existing chat session
        mock_chat_session = Mock()
        mock_chat_session.send_message_async = AsyncMock()
        mock_response = Mock()
        mock_response.text = "Building on our previous discussion..."
        mock_chat_session.send_message_async.return_value = mock_response
        
        service.chat_sessions[sample_context.user_id] = mock_chat_session
        
        # Test the method
        result = await service.handle_follow_up_question("Tell me more", sample_context)
        
        # Assertions
        assert result == "Building on our previous discussion..."
        assert mock_chat_session.send_message_async.called
    
    def test_build_analysis_prompt(self, mock_vertex_ai_service, sample_analysis_result, sample_context):
        """Test analysis prompt building"""
        service, _ = mock_vertex_ai_service
        
        prompt = service._build_analysis_prompt(
            sample_analysis_result, 
            "What do you think about AAPL?", 
            sample_context
        )
        
        # Check prompt contains key information
        assert "AAPL" in prompt
        assert "BUY" in prompt
        assert "85%" in prompt
        assert "Strong fundamentals" in prompt
        assert "Market volatility" in prompt
        assert "moderate" in prompt  # risk tolerance from context
        assert "What do you think about AAPL?" in prompt
    
    def test_get_fallback_response(self, mock_vertex_ai_service, sample_analysis_result):
        """Test fallback response generation"""
        service, _ = mock_vertex_ai_service
        
        result = service._get_fallback_response(sample_analysis_result, "Tell me about AAPL")
        
        # Check fallback contains key information
        assert "AAPL" in result
        assert "BUY" in result
        assert "85%" in result
        assert "Strong fundamentals" in result
        assert "informational" in result and "purposes" in result
    
    def test_clear_chat_session(self, mock_vertex_ai_service):
        """Test chat session clearing"""
        service, _ = mock_vertex_ai_service
        
        # Add a session
        service.chat_sessions["test_user"] = Mock()
        assert "test_user" in service.chat_sessions
        
        # Clear it
        service.clear_chat_session("test_user")
        assert "test_user" not in service.chat_sessions
    
    def test_get_active_sessions_count(self, mock_vertex_ai_service):
        """Test active sessions count"""
        service, _ = mock_vertex_ai_service
        
        # Initially empty
        assert service.get_active_sessions_count() == 0
        
        # Add sessions
        service.chat_sessions["user1"] = Mock()
        service.chat_sessions["user2"] = Mock()
        
        assert service.get_active_sessions_count() == 2
    
    def test_initialization_without_project_id(self):
        """Test that initialization fails without project ID"""
        with patch('app.services.vertex_ai_service.get_settings') as mock_settings:
            mock_settings.return_value.GCP_PROJECT_ID = None
            
            with pytest.raises(ValueError, match="GCP_PROJECT_ID must be set"):
                VertexAIService()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_market_summary(self, mock_vertex_ai_service):
        """Test error handling in market summary generation"""
        service, mock_model = mock_vertex_ai_service
        
        # Mock error
        mock_model.generate_content_async.side_effect = Exception("API Error")
        
        # Test the method
        result = await service.generate_market_summary([])
        
        # Should return error message
        assert "having trouble accessing market data" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_in_technical_explanation(self, mock_vertex_ai_service):
        """Test error handling in technical indicator explanation"""
        service, mock_model = mock_vertex_ai_service
        
        # Mock error
        mock_model.generate_content_async.side_effect = Exception("API Error")
        
        # Test the method
        result = await service.explain_technical_indicator("RSI", 70.0, "AAPL")
        
        # Should return fallback explanation
        assert "RSI" in result
        assert "70" in result
        assert "AAPL" in result
        assert "technical measure" in result