"""
Tests for chat service integration with educational features.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.chat_service import ChatService, ChatResponse
from app.services.education_service import EducationService
from app.services.vertex_ai_service import VertexAIService, ConversationContext
from app.models.education import (
    EducationalConceptResponse, ConceptExplanationResponse,
    ConceptType, DifficultyLevel
)


class TestChatEducationIntegration:
    """Test cases for chat service educational integration"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock()

    @pytest.fixture
    def mock_vertex_ai_service(self):
        """Mock Vertex AI service"""
        mock_service = Mock(spec=VertexAIService)
        mock_service.generate_stock_analysis_response = AsyncMock(return_value="Stock analysis response")
        mock_service.handle_follow_up_question = AsyncMock(return_value="Follow-up response")
        return mock_service

    @pytest.fixture
    def mock_education_service(self):
        """Mock education service"""
        mock_service = Mock(spec=EducationService)
        mock_service.extract_concepts_from_text = AsyncMock(return_value=[])
        mock_service.get_contextual_explanation = AsyncMock()
        return mock_service

    @pytest.fixture
    def chat_service(self, mock_db_session, mock_vertex_ai_service, mock_education_service):
        """Create chat service with mocked dependencies"""
        with patch('app.services.chat_service.get_settings'):
            service = ChatService(testing_mode=True, db_session=mock_db_session)
            service.vertex_ai = mock_vertex_ai_service
            service.education_service = mock_education_service
            service.redis_client = None
            return service

    @pytest.fixture
    def sample_concept_response(self):
        """Sample educational concept response"""
        return EducationalConceptResponse(
            id=1,
            name="RSI (Relative Strength Index)",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER,
            short_description="Momentum oscillator",
            detailed_explanation="RSI measures momentum...",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            related_concepts=[]
        )

    @pytest.fixture
    def sample_explanation_response(self, sample_concept_response):
        """Sample explanation response"""
        return ConceptExplanationResponse(
            concept=sample_concept_response,
            contextual_explanation="RSI is a momentum indicator that helps identify overbought and oversold conditions.",
            related_suggestions=[],
            next_learning_steps=["Practice with charts", "Learn MACD"]
        )

    async def test_process_message_with_educational_concepts(
        self, chat_service, mock_education_service, sample_explanation_response
    ):
        """Test processing message that contains educational concepts"""
        # Setup
        mock_education_service.extract_concepts_from_text.return_value = ["RSI"]
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response

        # Execute
        response = await chat_service.process_message(
            user_id="test_user",
            message="What does the RSI indicator tell us about AAPL?"
        )

        # Assert
        assert isinstance(response, ChatResponse)
        assert "RSI is a momentum indicator" in response.message
        mock_education_service.extract_concepts_from_text.assert_called_once()

    async def test_process_message_educational_question(
        self, chat_service, mock_education_service, sample_explanation_response
    ):
        """Test processing direct educational question"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response

        # Execute
        response = await chat_service.process_message(
            user_id="test_user",
            message="What is RSI?"
        )

        # Assert
        assert isinstance(response, ChatResponse)
        assert "momentum indicator" in response.message
        assert "Practice with charts" in response.message

    async def test_is_educational_question_detection(self, chat_service):
        """Test detection of educational questions"""
        # Test cases
        educational_questions = [
            "What is RSI?",
            "Can you explain MACD?",
            "What does P/E ratio mean?",
            "Help me understand moving averages",
            "Define market capitalization"
        ]

        non_educational_questions = [
            "Analyze AAPL",
            "Show me the price of Tesla",
            "What's the market doing today?",
            "Buy or sell recommendation for MSFT"
        ]

        # Test educational questions
        for question in educational_questions:
            assert chat_service._is_educational_question(question), f"Should detect: {question}"

        # Test non-educational questions
        for question in non_educational_questions:
            assert not chat_service._is_educational_question(question), f"Should not detect: {question}"

    def test_extract_concept_from_question(self, chat_service):
        """Test extracting concept names from educational questions"""
        test_cases = [
            ("What is RSI?", "rsi"),
            ("Can you explain the P/E ratio?", "p/e ratio"),
            ("What does MACD mean?", "macd"),
            ("Tell me about moving averages", "moving averages"),
            ("Define market cap", "market cap")
        ]

        for question, expected_concept in test_cases:
            result = chat_service._extract_concept_from_question(question)
            assert result is not None, f"Should extract concept from: {question}"
            assert expected_concept in result.lower(), f"Expected '{expected_concept}' in '{result}'"

    async def test_handle_educational_question_success(
        self, chat_service, mock_education_service, sample_explanation_response
    ):
        """Test handling educational question successfully"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response
        context = ConversationContext(user_id="test_user")

        # Execute
        response = await chat_service._handle_educational_question(
            "What is RSI?", context
        )

        # Assert
        assert "momentum indicator" in response
        assert "Practice with charts" in response
        assert "Learn MACD" in response
        mock_education_service.get_contextual_explanation.assert_called_once()

    async def test_handle_educational_question_concept_not_found(
        self, chat_service, mock_education_service, mock_vertex_ai_service
    ):
        """Test handling educational question when concept not found"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = None
        mock_vertex_ai_service.handle_follow_up_question.return_value = "General response"
        context = ConversationContext(user_id="test_user")

        # Execute
        response = await chat_service._handle_educational_question(
            "What is unknown_concept?", context
        )

        # Assert
        assert response == "General response"
        mock_vertex_ai_service.handle_follow_up_question.assert_called_once()

    async def test_handle_educational_question_no_service(self, chat_service):
        """Test handling educational question when education service not available"""
        # Setup
        chat_service.education_service = None

        # Execute
        response = await chat_service._handle_educational_question(
            "What is RSI?", ConversationContext(user_id="test_user")
        )

        # Assert
        assert "educational service is not available" in response

    async def test_enhance_response_with_education(
        self, chat_service, mock_education_service, sample_explanation_response
    ):
        """Test enhancing response with educational explanations"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response
        original_response = "AAPL shows strong momentum with RSI at 65."
        concepts = ["RSI"]

        # Execute
        enhanced_response = await chat_service._enhance_response_with_education(
            original_response, concepts, "AAPL"
        )

        # Assert
        assert original_response in enhanced_response
        assert "Quick explanation - RSI" in enhanced_response
        assert "momentum indicator" in enhanced_response

    async def test_enhance_response_with_multiple_concepts(
        self, chat_service, mock_education_service, sample_explanation_response
    ):
        """Test enhancing response with multiple educational concepts"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response
        original_response = "Analysis shows RSI, MACD, and P/E ratio signals."
        concepts = ["RSI", "MACD", "P/E ratio"]

        # Execute
        enhanced_response = await chat_service._enhance_response_with_education(
            original_response, concepts, "AAPL"
        )

        # Assert
        assert original_response in enhanced_response
        assert "Quick explanation" in enhanced_response
        # Should mention additional concepts
        assert "P/E ratio" in enhanced_response

    async def test_enhance_response_no_education_service(self, chat_service):
        """Test enhancing response when education service not available"""
        # Setup
        chat_service.education_service = None
        original_response = "AAPL analysis"
        concepts = ["RSI"]

        # Execute
        enhanced_response = await chat_service._enhance_response_with_education(
            original_response, concepts
        )

        # Assert
        assert enhanced_response == original_response  # Should return unchanged

    async def test_enhance_response_service_error(
        self, chat_service, mock_education_service
    ):
        """Test enhancing response when education service throws error"""
        # Setup
        mock_education_service.get_contextual_explanation.side_effect = Exception("Service error")
        original_response = "AAPL analysis"
        concepts = ["RSI"]

        # Execute
        enhanced_response = await chat_service._enhance_response_with_education(
            original_response, concepts
        )

        # Assert
        assert enhanced_response == original_response  # Should return original on error

    async def test_process_message_with_analysis_and_concepts(
        self, chat_service, mock_education_service, sample_explanation_response
    ):
        """Test processing message with both analysis result and educational concepts"""
        # Setup
        from app.services.vertex_ai_service import AnalysisResult
        analysis_result = AnalysisResult(
            symbol="AAPL",
            recommendation="BUY",
            confidence=85,
            reasoning=["Strong fundamentals", "Technical breakout"],
            risks=["Market volatility"]
        )
        
        mock_education_service.extract_concepts_from_text.return_value = ["RSI"]
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response

        # Execute
        response = await chat_service.process_message(
            user_id="test_user",
            message="What's the RSI telling us about AAPL?",
            analysis_result=analysis_result
        )

        # Assert
        assert isinstance(response, ChatResponse)
        assert response.analysis_data["symbol"] == "AAPL"
        assert response.analysis_data["educational_concepts"] == ["RSI"]
        assert "momentum indicator" in response.message

    async def test_conversation_context_with_education(self, chat_service):
        """Test that educational interactions are properly stored in context"""
        # This would test context storage and retrieval
        # For now, just ensure the structure supports it
        context = ConversationContext(user_id="test_user")
        assert hasattr(context, 'user_id')

    def test_educational_suggestions_in_follow_ups(self, chat_service):
        """Test that educational concepts appear in follow-up suggestions"""
        # Setup
        from app.services.vertex_ai_service import AnalysisResult
        analysis_result = AnalysisResult(
            symbol="AAPL",
            recommendation="BUY",
            confidence=85,
            reasoning=["Strong RSI signal"],
            risks=[]
        )

        # Execute
        suggestions = chat_service._generate_follow_up_suggestions(analysis_result)

        # Assert
        assert len(suggestions) > 0
        # Should include general suggestions that could lead to educational content
        assert any("technical" in suggestion.lower() for suggestion in suggestions)

    async def test_educational_workflow_end_to_end(
        self, chat_service, mock_education_service, sample_explanation_response
    ):
        """Test complete educational workflow from question to explanation"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response

        # Execute - Ask educational question
        response1 = await chat_service.process_message(
            user_id="test_user",
            message="What is RSI?"
        )

        # Execute - Follow up question
        response2 = await chat_service.process_message(
            user_id="test_user",
            message="How do I use it for AAPL?"
        )

        # Assert
        assert "momentum indicator" in response1.message
        assert isinstance(response2, ChatResponse)
        # Both should be processed successfully