"""
Tests for educational service functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.education_service import EducationService
from app.services.vertex_ai_service import VertexAIService
from app.models.education import (
    EducationalConcept, ConceptType, DifficultyLevel,
    EducationalConceptResponse, ConceptExplanationResponse
)


class TestEducationService:
    """Test cases for EducationService"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_vertex_ai_service(self):
        """Mock Vertex AI service"""
        mock_service = Mock(spec=VertexAIService)
        mock_service.generate_content = AsyncMock(return_value="Mock AI explanation")
        return mock_service

    @pytest.fixture
    def education_service(self, mock_db_session, mock_vertex_ai_service):
        """Create education service with mocked dependencies"""
        with patch.object(EducationService, '_initialize_default_concepts'):
            service = EducationService(mock_db_session, mock_vertex_ai_service)
            return service

    @pytest.fixture
    def sample_concept(self):
        """Sample educational concept for testing"""
        return EducationalConcept(
            id=1,
            name="RSI (Relative Strength Index)",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER,
            short_description="Momentum oscillator that measures speed and change of price movements",
            detailed_explanation="RSI is a momentum oscillator that ranges from 0 to 100...",
            practical_example="If Apple's RSI is 75, it suggests the stock may be overbought...",
            formula="RSI = 100 - (100 / (1 + RS))",
            interpretation_guide="RSI > 70: Potentially overbought...",
            common_mistakes="Don't rely solely on RSI for trading decisions...",
            keywords="momentum, overbought, oversold, oscillator",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    async def test_get_concept_by_name_found(self, education_service, mock_db_session, sample_concept):
        """Test getting concept by name when concept exists"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_concept

        # Execute
        result = await education_service.get_concept_by_name("RSI")

        # Assert
        assert result is not None
        assert result.name == "RSI (Relative Strength Index)"
        assert result.concept_type == ConceptType.TECHNICAL_INDICATOR
        mock_db_session.query.assert_called_once_with(EducationalConcept)

    async def test_get_concept_by_name_not_found(self, education_service, mock_db_session):
        """Test getting concept by name when concept doesn't exist"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        # Execute
        result = await education_service.get_concept_by_name("NonExistent")

        # Assert
        assert result is None

    async def test_search_concepts_with_query(self, education_service, mock_db_session, sample_concept):
        """Test searching concepts with text query"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_concept]

        # Execute
        results = await education_service.search_concepts("RSI", limit=5)

        # Assert
        assert len(results) == 1
        assert results[0].name == "RSI (Relative Strength Index)"

    async def test_search_concepts_with_filters(self, education_service, mock_db_session, sample_concept):
        """Test searching concepts with type and difficulty filters"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_concept]

        # Execute
        results = await education_service.search_concepts(
            "indicator",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER
        )

        # Assert
        assert len(results) == 1
        assert results[0].concept_type == ConceptType.TECHNICAL_INDICATOR

    async def test_get_contextual_explanation(self, education_service, mock_db_session, sample_concept):
        """Test getting contextual explanation for a concept"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_concept

        with patch.object(education_service, '_get_related_concepts', return_value=[]):
            with patch.object(education_service, '_generate_learning_steps', return_value=["Step 1", "Step 2"]):
                # Execute
                result = await education_service.get_contextual_explanation(
                    "RSI", 
                    context="AAPL analysis",
                    user_level=DifficultyLevel.BEGINNER
                )

        # Assert
        assert result is not None
        assert isinstance(result, ConceptExplanationResponse)
        assert result.concept.name == "RSI (Relative Strength Index)"
        assert len(result.next_learning_steps) == 2

    async def test_generate_contextual_explanation_with_ai(self, education_service, mock_vertex_ai_service):
        """Test AI-generated contextual explanation"""
        # Setup
        concept = EducationalConceptResponse(
            id=1,
            name="RSI",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER,
            short_description="Test description",
            detailed_explanation="Test explanation",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Execute
        result = await education_service._generate_contextual_explanation(
            concept, "AAPL analysis", DifficultyLevel.BEGINNER
        )

        # Assert
        assert result == "Mock AI explanation"
        mock_vertex_ai_service.generate_content.assert_called_once()

    async def test_generate_contextual_explanation_fallback(self, education_service, mock_vertex_ai_service):
        """Test fallback when AI generation fails"""
        # Setup
        mock_vertex_ai_service.generate_content.side_effect = Exception("AI service error")
        concept = EducationalConceptResponse(
            id=1,
            name="RSI",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER,
            short_description="Test description",
            detailed_explanation="Test explanation",
            practical_example="Test example",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Execute
        result = await education_service._generate_contextual_explanation(
            concept, "AAPL analysis", DifficultyLevel.BEGINNER
        )

        # Assert
        assert "Test explanation" in result
        assert "Test example" in result

    async def test_extract_concepts_from_text(self, education_service, mock_db_session, sample_concept):
        """Test extracting concepts from text"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_concept]

        # Execute
        text = "The RSI indicator shows momentum and overbought conditions"
        concepts = await education_service.extract_concepts_from_text(text)

        # Assert
        assert "RSI (Relative Strength Index)" in concepts

    async def test_extract_concepts_from_text_keywords(self, education_service, mock_db_session, sample_concept):
        """Test extracting concepts from text using keywords"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_concept]

        # Execute
        text = "The stock is showing overbought conditions"
        concepts = await education_service.extract_concepts_from_text(text)

        # Assert
        assert "RSI (Relative Strength Index)" in concepts

    @pytest.mark.asyncio
    async def test_get_learning_path_suggestions_beginner(self, education_service):
        """Test learning path suggestions for beginners"""
        # Execute
        suggestions = await education_service.get_learning_path_suggestions(
            DifficultyLevel.BEGINNER
        )

        # Assert
        assert len(suggestions) > 0
        assert any("basic" in suggestion.lower() for suggestion in suggestions)
        assert any("market cap" in suggestion.lower() for suggestion in suggestions)

    async def test_get_learning_path_suggestions_intermediate(self, education_service):
        """Test learning path suggestions for intermediate users"""
        # Execute
        suggestions = await education_service.get_learning_path_suggestions(
            DifficultyLevel.INTERMEDIATE
        )

        # Assert
        assert len(suggestions) > 0
        assert any("advanced" in suggestion.lower() for suggestion in suggestions)
        assert any("macd" in suggestion.lower() for suggestion in suggestions)

    async def test_get_learning_path_suggestions_advanced(self, education_service):
        """Test learning path suggestions for advanced users"""
        # Execute
        suggestions = await education_service.get_learning_path_suggestions(
            DifficultyLevel.ADVANCED
        )

        # Assert
        assert len(suggestions) > 0
        assert any("custom" in suggestion.lower() for suggestion in suggestions)
        assert any("quantitative" in suggestion.lower() for suggestion in suggestions)

    def test_generate_learning_steps_beginner(self, education_service):
        """Test generating learning steps for beginners"""
        # Setup
        concept = EducationalConceptResponse(
            id=1,
            name="RSI",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER,
            short_description="Test",
            detailed_explanation="Test",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Execute
        steps = education_service._generate_learning_steps(concept, DifficultyLevel.BEGINNER)

        # Assert
        assert len(steps) == 3
        assert any("practice" in step.lower() for step in steps)

    def test_generate_learning_steps_intermediate(self, education_service):
        """Test generating learning steps for intermediate users"""
        # Setup
        concept = EducationalConceptResponse(
            id=1,
            name="RSI",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            short_description="Test",
            detailed_explanation="Test",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Execute
        steps = education_service._generate_learning_steps(concept, DifficultyLevel.INTERMEDIATE)

        # Assert
        assert len(steps) == 3
        assert any("combine" in step.lower() for step in steps)

    def test_generate_learning_steps_advanced(self, education_service):
        """Test generating learning steps for advanced users"""
        # Setup
        concept = EducationalConceptResponse(
            id=1,
            name="RSI",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.ADVANCED,
            short_description="Test",
            detailed_explanation="Test",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Execute
        steps = education_service._generate_learning_steps(concept, DifficultyLevel.ADVANCED)

        # Assert
        assert len(steps) == 3
        assert any("develop" in step.lower() for step in steps)

    def test_initialize_default_concepts_empty_db(self, mock_db_session, mock_vertex_ai_service):
        """Test initialization of default concepts when database is empty"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.count.return_value = 0

        # Execute
        service = EducationService(mock_db_session, mock_vertex_ai_service)

        # Assert
        assert mock_db_session.add.call_count > 0  # Should add default concepts
        mock_db_session.commit.assert_called_once()

    def test_initialize_default_concepts_existing_data(self, mock_db_session, mock_vertex_ai_service):
        """Test initialization when concepts already exist"""
        # Setup
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query
        mock_query.count.return_value = 5  # Existing concepts

        # Execute
        service = EducationService(mock_db_session, mock_vertex_ai_service)

        # Assert
        mock_db_session.add.assert_not_called()  # Should not add concepts
        mock_db_session.commit.assert_not_called()


class TestEducationServiceIntegration:
    """Integration tests for education service"""

    async def test_full_explanation_workflow(self):
        """Test complete workflow from concept search to explanation"""
        # This would be an integration test with real database
        # For now, just ensure the workflow structure is correct
        pass

    async def test_concept_extraction_accuracy(self):
        """Test accuracy of concept extraction from various text types"""
        # This would test with real financial text samples
        pass

    async def test_ai_explanation_quality(self):
        """Test quality and relevance of AI-generated explanations"""
        # This would test with real AI service
        pass