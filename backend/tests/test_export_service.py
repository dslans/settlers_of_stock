"""
Tests for export service functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO

from app.services.export_service import ExportService
from app.models.analysis import AnalysisResult, AnalysisType, Recommendation, RiskLevel, PriceTarget
from app.models.sentiment import SentimentAnalysisResult, SentimentData, TrendDirection


@pytest.fixture
def export_service():
    """Create export service instance for testing."""
    with patch('app.services.export_service.redis.Redis'), \
         patch('app.services.export_service.storage.Client'):
        service = ExportService()
        return service


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
        strengths=[
            "Strong financial position with low debt",
            "Consistent revenue growth",
            "Technical indicators showing bullish momentum"
        ],
        weaknesses=[
            "High valuation compared to peers",
            "Dependence on iPhone sales"
        ],
        risks=[
            "Market volatility",
            "Regulatory challenges",
            "Supply chain disruptions"
        ],
        opportunities=[
            "Services revenue growth",
            "Expansion in emerging markets",
            "New product categories"
        ],
        price_targets=[
            PriceTarget(
                target=165.00,
                timeframe="3M",
                confidence=75,
                rationale="Based on P/E expansion and earnings growth"
            ),
            PriceTarget(
                target=180.00,
                timeframe="1Y",
                confidence=65,
                rationale="Long-term growth trajectory and market expansion"
            )
        ],
        risk_level=RiskLevel.MODERATE,
        risk_factors={
            "volatility": 0.25,
            "beta": 1.2,
            "debt_ratio": 0.3
        },
        analysis_timestamp=datetime.now(),
        data_freshness={
            "fundamental": datetime.now(),
            "technical": datetime.now()
        }
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


class TestExportService:
    """Test cases for ExportService."""

    @pytest.mark.asyncio
    async def test_generate_pdf_report(self, export_service, sample_analysis_result, sample_sentiment_result):
        """Test PDF report generation."""
        # Generate PDF
        pdf_bytes = await export_service.generate_pdf_report(
            analysis_result=sample_analysis_result,
            sentiment_result=sample_sentiment_result,
            include_charts=True,
            user_id="test_user"
        )
        
        # Verify PDF was generated
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        
        # Verify PDF header
        assert pdf_bytes.startswith(b'%PDF')

    @pytest.mark.asyncio
    async def test_generate_pdf_report_without_sentiment(self, export_service, sample_analysis_result):
        """Test PDF report generation without sentiment data."""
        # Generate PDF without sentiment
        pdf_bytes = await export_service.generate_pdf_report(
            analysis_result=sample_analysis_result,
            sentiment_result=None,
            include_charts=False,
            user_id="test_user"
        )
        
        # Verify PDF was generated
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b'%PDF')

    @pytest.mark.asyncio
    async def test_create_shareable_link(self, export_service, sample_analysis_result, sample_sentiment_result):
        """Test shareable link creation."""
        # Mock Redis operations
        export_service.redis_client.setex = Mock()
        
        # Create shareable link
        link_id = await export_service.create_shareable_link(
            analysis_result=sample_analysis_result,
            sentiment_result=sample_sentiment_result,
            user_id="test_user",
            expires_in_hours=24
        )
        
        # Verify link ID was generated
        assert isinstance(link_id, str)
        assert len(link_id) > 0
        
        # Verify Redis was called
        export_service.redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_shared_analysis(self, export_service, sample_analysis_result):
        """Test retrieving shared analysis."""
        # Mock Redis operations
        share_data = {
            "analysis": sample_analysis_result.dict(),
            "sentiment": None,
            "created_at": datetime.now().isoformat(),
            "created_by": "test_user",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "view_count": 0
        }
        
        export_service.redis_client.get = Mock(return_value=json.dumps(share_data, default=str))
        export_service.redis_client.setex = Mock()
        export_service.redis_client.ttl = Mock(return_value=86400)  # 24 hours
        
        # Get shared analysis
        result = await export_service.get_shared_analysis("test_link_id")
        
        # Verify result
        assert result is not None
        assert result["analysis"]["symbol"] == "AAPL"
        assert result["view_count"] == 1  # Should be incremented
        
        # Verify Redis operations
        export_service.redis_client.get.assert_called_once_with("share:test_link_id")
        export_service.redis_client.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_shared_analysis_not_found(self, export_service):
        """Test retrieving non-existent shared analysis."""
        # Mock Redis operations
        export_service.redis_client.get = Mock(return_value=None)
        
        # Get shared analysis
        result = await export_service.get_shared_analysis("nonexistent_link_id")
        
        # Verify result
        assert result is None

    @pytest.mark.asyncio
    async def test_export_data_csv(self, export_service, sample_analysis_result, sample_sentiment_result):
        """Test CSV data export."""
        # Export to CSV
        csv_content = await export_service.export_data_csv(
            analysis_result=sample_analysis_result,
            sentiment_result=sample_sentiment_result
        )
        
        # Verify CSV content
        assert isinstance(csv_content, str)
        assert len(csv_content) > 0
        
        # Check CSV structure
        lines = csv_content.strip().split('\n')
        assert len(lines) > 1  # Header + at least one data row
        
        # Check header
        header = lines[0]
        assert 'Symbol' in header
        assert 'Recommendation' in header
        assert 'Confidence' in header
        
        # Check data row
        data_row = lines[1]
        assert 'AAPL' in data_row
        assert 'BUY' in data_row

    @pytest.mark.asyncio
    async def test_export_data_json(self, export_service, sample_analysis_result, sample_sentiment_result):
        """Test JSON data export."""
        # Export to JSON
        json_content = await export_service.export_data_json(
            analysis_result=sample_analysis_result,
            sentiment_result=sample_sentiment_result,
            include_metadata=True
        )
        
        # Verify JSON content
        assert isinstance(json_content, str)
        assert len(json_content) > 0
        
        # Parse JSON
        data = json.loads(json_content)
        
        # Verify structure
        assert "analysis" in data
        assert "sentiment" in data
        assert "export_metadata" in data
        
        # Verify analysis data
        assert data["analysis"]["symbol"] == "AAPL"
        assert data["analysis"]["recommendation"] == "BUY"
        assert data["analysis"]["confidence"] == 78
        
        # Verify metadata
        assert data["export_metadata"]["format"] == "json"
        assert data["export_metadata"]["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_export_data_json_without_metadata(self, export_service, sample_analysis_result):
        """Test JSON data export without metadata."""
        # Export to JSON without metadata
        json_content = await export_service.export_data_json(
            analysis_result=sample_analysis_result,
            sentiment_result=None,
            include_metadata=False
        )
        
        # Parse JSON
        data = json.loads(json_content)
        
        # Verify structure
        assert "analysis" in data
        assert "sentiment" in data
        assert "export_metadata" not in data
        
        # Verify sentiment is None
        assert data["sentiment"] is None

    @pytest.mark.asyncio
    async def test_delete_shared_link(self, export_service):
        """Test deleting a shared link."""
        # Mock Redis operations
        share_data = {
            "created_by": "test_user",
            "analysis": {"symbol": "AAPL"}
        }
        
        export_service.redis_client.get = Mock(return_value=json.dumps(share_data))
        export_service.redis_client.delete = Mock(return_value=1)  # 1 key deleted
        
        # Delete shared link
        result = await export_service.delete_shared_link("test_link_id", "test_user")
        
        # Verify result
        assert result is True
        
        # Verify Redis operations
        export_service.redis_client.get.assert_called_once_with("share:test_link_id")
        export_service.redis_client.delete.assert_called_once_with("share:test_link_id")

    @pytest.mark.asyncio
    async def test_delete_shared_link_unauthorized(self, export_service):
        """Test deleting a shared link without permission."""
        # Mock Redis operations
        share_data = {
            "created_by": "other_user",
            "analysis": {"symbol": "AAPL"}
        }
        
        export_service.redis_client.get = Mock(return_value=json.dumps(share_data))
        
        # Try to delete shared link as different user
        result = await export_service.delete_shared_link("test_link_id", "test_user")
        
        # Verify result
        assert result is False
        
        # Verify Redis delete was not called
        export_service.redis_client.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_shared_link_not_found(self, export_service):
        """Test deleting a non-existent shared link."""
        # Mock Redis operations
        export_service.redis_client.get = Mock(return_value=None)
        export_service.redis_client.delete = Mock(return_value=0)  # 0 keys deleted
        
        # Try to delete non-existent shared link
        result = await export_service.delete_shared_link("nonexistent_link_id", "test_user")
        
        # Verify result
        assert result is False

    @pytest.mark.asyncio
    async def test_save_export_file_local(self, export_service):
        """Test saving export file locally."""
        # Mock cloud storage to fail
        export_service.storage_client = None
        
        # Test content
        content = b"test file content"
        filename = "test_export.pdf"
        
        # Save file
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = await export_service.save_export_file(content, filename)
            
            # Verify result
            assert isinstance(result, str)
            assert filename in result
            
            # Verify file was written
            mock_file.write.assert_called_once_with(content)

    @pytest.mark.asyncio
    async def test_get_user_exports_empty(self, export_service):
        """Test getting user exports when none exist."""
        # Get user exports
        exports = await export_service.get_user_exports("test_user", 10)
        
        # Verify result
        assert isinstance(exports, list)
        assert len(exports) == 0


class TestExportServiceErrors:
    """Test error handling in ExportService."""

    @pytest.mark.asyncio
    async def test_generate_pdf_report_error(self, export_service, sample_analysis_result):
        """Test PDF generation error handling."""
        # Mock ReportLab to raise an exception
        with patch('app.services.export_service.SimpleDocTemplate') as mock_doc:
            mock_doc.side_effect = Exception("PDF generation failed")
            
            # Try to generate PDF
            with pytest.raises(Exception) as exc_info:
                await export_service.generate_pdf_report(sample_analysis_result)
            
            assert "PDF generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_shareable_link_redis_error(self, export_service, sample_analysis_result):
        """Test shareable link creation with Redis error."""
        # Mock Redis to raise an exception
        export_service.redis_client.setex = Mock(side_effect=Exception("Redis error"))
        
        # Try to create shareable link
        with pytest.raises(Exception) as exc_info:
            await export_service.create_shareable_link(sample_analysis_result)
        
        assert "Redis error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_export_data_csv_error(self, export_service, sample_analysis_result):
        """Test CSV export error handling."""
        # Mock csv module to raise an exception
        with patch('app.services.export_service.csv.writer') as mock_writer:
            mock_writer.side_effect = Exception("CSV generation failed")
            
            # Try to export CSV
            with pytest.raises(Exception) as exc_info:
                await export_service.export_data_csv(sample_analysis_result)
            
            assert "CSV generation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_export_data_json_error(self, export_service, sample_analysis_result):
        """Test JSON export error handling."""
        # Mock json module to raise an exception
        with patch('app.services.export_service.json.dumps') as mock_dumps:
            mock_dumps.side_effect = Exception("JSON serialization failed")
            
            # Try to export JSON
            with pytest.raises(Exception) as exc_info:
                await export_service.export_data_json(sample_analysis_result)
            
            assert "JSON serialization failed" in str(exc_info.value)