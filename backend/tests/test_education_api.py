"""
Tests for educational API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from main import app
from app.models.education import (
    ConceptType, DifficultyLevel,
    EducationalConceptResponse, ConceptExplanationResponse
)


class TestEducationAPI:
    """Test cases for education API endpoints"""

    @pytest.fixture
    def client(self):
        """Test client for FastAPI app"""
        return TestClient(app)

    @pytest.fixture
    def mock_education_service(self):
        """Mock education service"""
        service = Mock()
        service.search_concepts = AsyncMock()
        service.get_concept_by_name = AsyncMock()
        service.get_contextual_explanation = AsyncMock()
        service.extract_concepts_from_text = AsyncMock()
        service.get_learning_path_suggestions = AsyncMock()
        service.track_user_progress = AsyncMock()
        service.get_user_progress = AsyncMock()
        return service

    @pytest.fixture
    def sample_concept_response(self):
        """Sample concept response for testing"""
        return EducationalConceptResponse(
            id=1,
            name="RSI (Relative Strength Index)",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER,
            short_description="Momentum oscillator",
            detailed_explanation="RSI measures momentum...",
            practical_example="If RSI is 75...",
            formula="RSI = 100 - (100 / (1 + RS))",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            related_concepts=[]
        )

    @pytest.fixture
    def sample_explanation_response(self, sample_concept_response):
        """Sample explanation response for testing"""
        return ConceptExplanationResponse(
            concept=sample_concept_response,
            contextual_explanation="RSI is a momentum indicator that helps...",
            related_suggestions=[],
            next_learning_steps=["Practice with charts", "Learn MACD"]
        )

    def test_search_concepts_success(self, client, mock_education_service, sample_concept_response):
        """Test successful concept search"""
        # Setup
        mock_education_service.search_concepts.return_value = [sample_concept_response]
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get("/api/v1/education/concepts/search?query=RSI")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "RSI (Relative Strength Index)"
        mock_education_service.search_concepts.assert_called_once()

    def test_search_concepts_with_filters(self, client, mock_education_service, sample_concept_response):
        """Test concept search with type and difficulty filters"""
        # Setup
        mock_education_service.search_concepts.return_value = [sample_concept_response]
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get(
                "/api/v1/education/concepts/search"
                "?query=indicator"
                "&concept_type=technical_indicator"
                "&difficulty_level=beginner"
                "&limit=5"
            )

        # Assert
        assert response.status_code == 200
        mock_education_service.search_concepts.assert_called_once_with(
            query="indicator",
            concept_type=ConceptType.TECHNICAL_INDICATOR,
            difficulty_level=DifficultyLevel.BEGINNER,
            limit=5
        )

    def test_search_concepts_error(self, client, mock_education_service):
        """Test concept search with service error"""
        # Setup
        mock_education_service.search_concepts.side_effect = Exception("Service error")
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get("/api/v1/education/concepts/search?query=RSI")

        # Assert
        assert response.status_code == 500
        assert "Error searching concepts" in response.json()["detail"]

    def test_get_concept_success(self, client, mock_education_service, sample_concept_response):
        """Test successful concept retrieval"""
        # Setup
        mock_education_service.get_concept_by_name.return_value = sample_concept_response
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get("/api/v1/education/concepts/RSI")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RSI (Relative Strength Index)"
        mock_education_service.get_concept_by_name.assert_called_once_with("RSI")

    def test_get_concept_not_found(self, client, mock_education_service):
        """Test concept retrieval when concept not found"""
        # Setup
        mock_education_service.get_concept_by_name.return_value = None
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get("/api/v1/education/concepts/NonExistent")

        # Assert
        assert response.status_code == 404
        assert "Concept not found" in response.json()["detail"]

    def test_explain_concept_success(self, client, mock_education_service, sample_explanation_response):
        """Test successful concept explanation"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = sample_explanation_response
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.post(
                "/api/v1/education/explain",
                json={
                    "concept_name": "RSI",
                    "context": "AAPL analysis",
                    "user_level": "beginner"
                }
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["concept"]["name"] == "RSI (Relative Strength Index)"
        assert "momentum indicator" in data["contextual_explanation"]
        assert len(data["next_learning_steps"]) == 2

    def test_explain_concept_not_found(self, client, mock_education_service):
        """Test concept explanation when concept not found"""
        # Setup
        mock_education_service.get_contextual_explanation.return_value = None
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.post(
                "/api/v1/education/explain",
                json={"concept_name": "NonExistent"}
            )

        # Assert
        assert response.status_code == 404
        assert "Concept not found" in response.json()["detail"]

    def test_extract_concepts_success(self, client, mock_education_service):
        """Test successful concept extraction from text"""
        # Setup
        mock_education_service.extract_concepts_from_text.return_value = ["RSI", "MACD"]
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.post(
                "/api/v1/education/extract-concepts",
                params={"text": "The RSI and MACD indicators show bullish momentum"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["concepts"] == ["RSI", "MACD"]

    def test_get_learning_path_suggestions_success(self, client, mock_education_service):
        """Test successful learning path suggestions"""
        # Setup
        suggestions = [
            "Start with basic market concepts",
            "Learn fundamental ratios",
            "Understand technical indicators"
        ]
        mock_education_service.get_learning_path_suggestions.return_value = suggestions
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get(
                "/api/v1/education/learning-paths/suggestions"
                "?user_level=beginner"
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == suggestions

    def test_get_learning_path_suggestions_with_interests(self, client, mock_education_service):
        """Test learning path suggestions with interests"""
        # Setup
        mock_education_service.get_learning_path_suggestions.return_value = ["Suggestion 1"]
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get(
                "/api/v1/education/learning-paths/suggestions"
                "?user_level=intermediate"
                "&interests=technical_indicator"
                "&interests=fundamental_ratio"
            )

        # Assert
        assert response.status_code == 200
        mock_education_service.get_learning_path_suggestions.assert_called_once_with(
            user_level=DifficultyLevel.INTERMEDIATE,
            interests=[ConceptType.TECHNICAL_INDICATOR, ConceptType.FUNDAMENTAL_RATIO]
        )

    def test_track_learning_progress_success(self, client, mock_education_service):
        """Test successful learning progress tracking"""
        # Setup
        from app.models.education import UserLearningProgressResponse
        progress_response = Mock(spec=UserLearningProgressResponse)
        mock_education_service.track_user_progress.return_value = progress_response
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            with patch('app.api.education.get_current_user', return_value=Mock(id=1)):
                # Execute
                response = client.post(
                    "/api/v1/education/progress/1"
                    "?completed=true"
                    "&difficulty_rating=4"
                )

        # Assert
        assert response.status_code == 200
        mock_education_service.track_user_progress.assert_called_once_with(
            user_id=1,
            concept_id=1,
            completed=True,
            difficulty_rating=4
        )

    def test_get_user_progress_success(self, client, mock_education_service):
        """Test successful user progress retrieval"""
        # Setup
        mock_education_service.get_user_progress.return_value = []
        
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            with patch('app.api.education.get_current_user', return_value=Mock(id=1)):
                # Execute
                response = client.get("/api/v1/education/progress")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_education_service.get_user_progress.assert_called_once_with(1)

    def test_get_concept_types_success(self, client):
        """Test getting available concept types"""
        # Execute
        response = client.get("/api/v1/education/concepts/types")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "technical_indicator" in data
        assert "fundamental_ratio" in data
        assert "market_concept" in data

    def test_get_difficulty_levels_success(self, client):
        """Test getting available difficulty levels"""
        # Execute
        response = client.get("/api/v1/education/difficulty-levels")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "beginner" in data
        assert "intermediate" in data
        assert "advanced" in data

    def test_invalid_concept_type_filter(self, client, mock_education_service):
        """Test search with invalid concept type"""
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get(
                "/api/v1/education/concepts/search"
                "?query=test"
                "&concept_type=invalid_type"
            )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_invalid_difficulty_level_filter(self, client, mock_education_service):
        """Test search with invalid difficulty level"""
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            # Execute
            response = client.get(
                "/api/v1/education/concepts/search"
                "?query=test"
                "&difficulty_level=invalid_level"
            )

        # Assert
        assert response.status_code == 422  # Validation error

    def test_invalid_difficulty_rating(self, client, mock_education_service):
        """Test tracking progress with invalid difficulty rating"""
        with patch('app.api.education.get_education_service', return_value=mock_education_service):
            with patch('app.api.education.get_current_user', return_value=Mock(id=1)):
                # Execute
                response = client.post(
                    "/api/v1/education/progress/1"
                    "?difficulty_rating=10"  # Invalid rating (should be 1-5)
                )

        # Assert
        assert response.status_code == 422  # Validation error