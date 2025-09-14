"""
Tests for export API endpoints.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from io import BytesIO

from app.main import app
from app.models.analysis import AnalysisResult, AnalysisType, Recommendation, RiskLevel, PriceTarget
from app.models.sentiment import SentimentAnalysisResult, SentimentData, TrendDirection


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create authentication headers for testing."""
    # Mock JWT token
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_analysis_result():
    """Create sample analysis result for testing."""
    return AnalysisResult(
        symbol="AAPL",
        analysis_type=AnalysisType.COMBINED,
        recommendation=Recommendation.BUY,
        confidence=78,
        overall_score=75,
        fundamental_score=80,
        technical_score=70,
        strengths=["Strong financials", "Good growth"],
        weaknesses=["High valuation"],
        risks=["Market volatility"],
        opportunities=["New markets"],
        price_targets=[
            PriceTarget(
                target=165.00,
                timeframe="3M",
                confidence=75,
                rationale="Based on fundamentals"
            )
        ],
        risk_level=RiskLevel.MODERATE,
        analysis_timestamp=datetime.now()
    )


@pytest.fixture
def sample_sentiment_result():
    """Create sample sentiment result for testing."""
    return SentimentAnalysisResult(
        symbol="AAPL",
        sentiment_data=SentimentData(
            overall_sentiment=0.6,
            news_sentiment=0.5,
            social_sentiment=0.7,
            trend_direction=TrendDirection.IMPROVING,
            trend_strength=0.8,
            confidence_score=0.75,
            data_freshness=datetime.now(),
            news_articles_count=25,
            social_posts_count=150,
            volatility=0.25
        ),
        sentiment_alerts=[],
        recent_news=[],
        analysis_timestamp=datetime.now()
    )


class TestExportAPI:
    """Test cases for export API endpoints."""

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.analysis_engine.analyze_stock')
    @patch('app.api.export.export_service.generate_pdf_report')
    def test_export_pdf_report(self, mock_generate_pdf, mock_analyze, mock_get_user, 
                              client, auth_headers, sample_analysis_result):
        """Test PDF export endpoint."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_analyze.return_value = sample_analysis_result
        mock_generate_pdf.return_value = b"fake_pdf_content"
        
        # Make request
        response = client.post(
            "/api/v1/export/pdf/AAPL",
            headers=auth_headers,
            params={"include_sentiment": True, "include_charts": True}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "AAPL" in response.headers["content-disposition"]
        assert response.content == b"fake_pdf_content"
        
        # Verify mocks were called
        mock_analyze.assert_called_once_with("AAPL")
        mock_generate_pdf.assert_called_once()

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.analysis_engine.analyze_stock')
    @patch('app.api.export.export_service.export_data_csv')
    def test_export_csv_data(self, mock_export_csv, mock_analyze, mock_get_user,
                            client, auth_headers, sample_analysis_result):
        """Test CSV export endpoint."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_analyze.return_value = sample_analysis_result
        mock_export_csv.return_value = "Symbol,Recommendation\nAAPL,BUY"
        
        # Make request
        response = client.post(
            "/api/v1/export/csv/AAPL",
            headers=auth_headers,
            params={"include_sentiment": True}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "AAPL" in response.headers["content-disposition"]
        
        # Verify mocks were called
        mock_analyze.assert_called_once_with("AAPL")
        mock_export_csv.assert_called_once()

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.analysis_engine.analyze_stock')
    @patch('app.api.export.export_service.export_data_json')
    def test_export_json_data(self, mock_export_json, mock_analyze, mock_get_user,
                             client, auth_headers, sample_analysis_result):
        """Test JSON export endpoint."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_analyze.return_value = sample_analysis_result
        mock_export_json.return_value = '{"analysis": {"symbol": "AAPL"}}'
        
        # Make request
        response = client.post(
            "/api/v1/export/json/AAPL",
            headers=auth_headers,
            params={"include_sentiment": True, "include_metadata": True}
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "AAPL" in response.headers["content-disposition"]
        
        # Verify mocks were called
        mock_analyze.assert_called_once_with("AAPL")
        mock_export_json.assert_called_once()

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.analysis_engine.analyze_stock')
    @patch('app.api.export.export_service.create_shareable_link')
    def test_create_share_link(self, mock_create_link, mock_analyze, mock_get_user,
                              client, auth_headers, sample_analysis_result):
        """Test create shareable link endpoint."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_analyze.return_value = sample_analysis_result
        mock_create_link.return_value = "test_link_id"
        
        # Request data
        request_data = {
            "symbol": "AAPL",
            "include_sentiment": True,
            "expires_in_hours": 24
        }
        
        # Make request
        response = client.post(
            "/api/v1/export/share",
            headers=auth_headers,
            json=request_data
        )
        
        # Verify response
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["link_id"] == "test_link_id"
        assert response_data["share_url"] == "/share/test_link_id"
        assert "expires_at" in response_data
        assert "created_at" in response_data
        
        # Verify mocks were called
        mock_analyze.assert_called_once_with("AAPL")
        mock_create_link.assert_called_once()

    @patch('app.api.export.export_service.get_shared_analysis')
    def test_get_shared_analysis(self, mock_get_shared, client, sample_analysis_result):
        """Test get shared analysis endpoint."""
        # Mock shared data
        shared_data = {
            "analysis": sample_analysis_result.dict(),
            "sentiment": None,
            "created_at": datetime.now().isoformat(),
            "view_count": 1,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        mock_get_shared.return_value = shared_data
        
        # Make request
        response = client.get("/api/v1/export/share/test_link_id")
        
        # Verify response
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["analysis"]["symbol"] == "AAPL"
        assert response_data["view_count"] == 1
        assert "created_at" in response_data
        assert "expires_at" in response_data
        
        # Verify mock was called
        mock_get_shared.assert_called_once_with("test_link_id")

    @patch('app.api.export.export_service.get_shared_analysis')
    def test_get_shared_analysis_not_found(self, mock_get_shared, client):
        """Test get shared analysis endpoint with non-existent link."""
        # Mock no data found
        mock_get_shared.return_value = None
        
        # Make request
        response = client.get("/api/v1/export/share/nonexistent_link_id")
        
        # Verify response
        assert response.status_code == 404
        assert "not found or expired" in response.json()["detail"]

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.export_service.delete_shared_link')
    def test_delete_share_link(self, mock_delete_link, mock_get_user, client, auth_headers):
        """Test delete shareable link endpoint."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_delete_link.return_value = True
        
        # Make request
        response = client.delete(
            "/api/v1/export/share/test_link_id",
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        
        # Verify mock was called
        mock_delete_link.assert_called_once_with("test_link_id", "test_user")

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.export_service.delete_shared_link')
    def test_delete_share_link_not_found(self, mock_delete_link, mock_get_user, client, auth_headers):
        """Test delete shareable link endpoint with non-existent link."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_delete_link.return_value = False
        
        # Make request
        response = client.delete(
            "/api/v1/export/share/test_link_id",
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.export_service.get_user_exports')
    def test_get_user_exports(self, mock_get_exports, mock_get_user, client, auth_headers):
        """Test get user exports endpoint."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_get_exports.return_value = []
        
        # Make request
        response = client.get(
            "/api/v1/export/user/exports",
            headers=auth_headers,
            params={"limit": 10}
        )
        
        # Verify response
        assert response.status_code == 200
        
        response_data = response.json()
        assert "exports" in response_data
        assert "total" in response_data
        assert response_data["total"] == 0
        
        # Verify mock was called
        mock_get_exports.assert_called_once_with("test_user", 10)

    def test_get_export_formats(self, client):
        """Test get export formats endpoint."""
        # Make request
        response = client.get("/api/v1/export/formats")
        
        # Verify response
        assert response.status_code == 200
        
        response_data = response.json()
        assert "formats" in response_data
        
        formats = response_data["formats"]
        assert len(formats) == 3  # PDF, CSV, JSON
        
        # Check format structure
        for format_info in formats:
            assert "format" in format_info
            assert "name" in format_info
            assert "description" in format_info
            assert "mime_type" in format_info
            assert "supports_charts" in format_info

    def test_health_check(self, client):
        """Test export service health check endpoint."""
        # Make request
        response = client.get("/api/v1/export/health")
        
        # Verify response
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["status"] == "healthy"
        assert response_data["service"] == "export_service"
        assert response_data["version"] == "1.0.0"


class TestExportAPIErrors:
    """Test error handling in export API endpoints."""

    @patch('app.api.export.get_current_user')
    def test_export_pdf_invalid_symbol(self, mock_get_user, client, auth_headers):
        """Test PDF export with invalid symbol."""
        # Mock user
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        
        # Make request with invalid symbol
        response = client.post(
            "/api/v1/export/pdf/INVALID_SYMBOL_TOO_LONG",
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 400
        assert "Invalid stock symbol format" in response.json()["detail"]

    @patch('app.api.export.get_current_user')
    @patch('app.api.export.analysis_engine.analyze_stock')
    def test_export_pdf_analysis_error(self, mock_analyze, mock_get_user, client, auth_headers):
        """Test PDF export with analysis error."""
        # Mock dependencies
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        mock_analyze.side_effect = Exception("Analysis failed")
        
        # Make request
        response = client.post(
            "/api/v1/export/pdf/AAPL",
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 500
        assert "Failed to generate PDF report" in response.json()["detail"]

    @patch('app.api.export.get_current_user')
    def test_create_share_link_invalid_expiration(self, mock_get_user, client, auth_headers):
        """Test create shareable link with invalid expiration time."""
        # Mock user
        mock_get_user.return_value = Mock(id="test_user", email="test@example.com")
        
        # Request data with invalid expiration
        request_data = {
            "symbol": "AAPL",
            "include_sentiment": True,
            "expires_in_hours": 200  # Too long
        }
        
        # Make request
        response = client.post(
            "/api/v1/export/share",
            headers=auth_headers,
            json=request_data
        )
        
        # Verify response
        assert response.status_code == 400
        assert "between 1 and 168 hours" in response.json()["detail"]

    def test_export_without_auth(self, client):
        """Test export endpoints without authentication."""
        # Make request without auth headers
        response = client.post("/api/v1/export/pdf/AAPL")
        
        # Verify response (should be 401 or 403 depending on auth implementation)
        assert response.status_code in [401, 403]

    @patch('app.api.export.export_service.get_shared_analysis')
    def test_get_shared_analysis_error(self, mock_get_shared, client):
        """Test get shared analysis with service error."""
        # Mock service error
        mock_get_shared.side_effect = Exception("Service error")
        
        # Make request
        response = client.get("/api/v1/export/share/test_link_id")
        
        # Verify response
        assert response.status_code == 500
        assert "Failed to retrieve shared analysis" in response.json()["detail"]