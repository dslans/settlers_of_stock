"""
Tests for Sector Analysis API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime

from main import app
from app.services.sector_analyzer import SectorAnalyzer, SectorAnalysisException
from app.models.sector import (
    SectorCategory, SectorPerformance, SectorAnalysisResult, 
    IndustryAnalysisResult, SectorComparisonResult, SectorRotationSignal,
    TrendDirection, RotationPhase
)


class TestSectorAPI:
    """Test cases for Sector Analysis API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_sector_performance(self):
        """Create sample sector performance data."""
        return SectorPerformance(
            sector=SectorCategory.TECHNOLOGY,
            performance_1d=Decimal("1.2"),
            performance_1w=Decimal("3.5"),
            performance_1m=Decimal("8.7"),
            performance_3m=Decimal("15.2"),
            performance_6m=Decimal("22.1"),
            performance_1y=Decimal("28.5"),
            performance_ytd=Decimal("18.3"),
            relative_performance_1m=Decimal("2.1"),
            relative_performance_3m=Decimal("4.8"),
            relative_performance_1y=Decimal("8.2"),
            trend_direction=TrendDirection.UP,
            trend_strength=75,
            momentum_score=82,
            market_cap=15000000000000,
            avg_volume=2500000000,
            pe_ratio=Decimal("28.5"),
            pb_ratio=Decimal("4.2"),
            performance_rank_1m=2,
            performance_rank_3m=1,
            performance_rank_1y=3,
            volatility=Decimal("24.5"),
            beta=Decimal("1.15"),
            dividend_yield=Decimal("1.2")
        )
    
    @pytest.fixture
    def sample_analysis_result(self, sample_sector_performance):
        """Create sample sector analysis result."""
        return SectorAnalysisResult(
            sector_performances=[sample_sector_performance],
            top_performers_1m=[SectorCategory.TECHNOLOGY.value],
            top_performers_3m=[SectorCategory.TECHNOLOGY.value],
            top_performers_1y=[SectorCategory.TECHNOLOGY.value],
            bottom_performers_1m=[SectorCategory.ENERGY.value],
            bottom_performers_3m=[SectorCategory.ENERGY.value],
            bottom_performers_1y=[SectorCategory.ENERGY.value],
            rotation_signals=[],
            market_trend=TrendDirection.UP,
            market_phase=RotationPhase.MID_CYCLE,
            volatility_regime="normal",
            analysis_timestamp=datetime.now(),
            data_freshness={"sector_analysis": datetime.now()}
        )

    def test_list_sectors_success(self, client):
        """Test successful sector list retrieval."""
        response = client.get("/api/v1/sectors/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sectors" in data
        assert "total_count" in data
        assert isinstance(data["sectors"], list)
        assert data["total_count"] > 0
        
        # Check sector structure
        if data["sectors"]:
            sector = data["sectors"][0]
            assert "name" in sector
            assert "code" in sector

    @patch('app.api.sectors.get_sector_analyzer')
    def test_analyze_all_sectors_success(self, mock_get_analyzer, client, sample_analysis_result):
        """Test successful comprehensive sector analysis."""
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(return_value=sample_analysis_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sector_performances" in data
        assert "top_performers_1m" in data
        assert "rotation_signals" in data
        assert "market_trend" in data
        assert "market_phase" in data
        
        # Verify analyzer was called
        mock_analyzer.analyze_all_sectors.assert_called_once()

    @patch('app.api.sectors.get_sector_analyzer')
    def test_analyze_all_sectors_no_data(self, mock_get_analyzer, client):
        """Test sector analysis when no data is available."""
        # Setup mock to raise exception
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(
            side_effect=SectorAnalysisException(
                "Failed to analyze any sectors",
                error_type="NO_DATA",
                suggestions=["Check data sources"]
            )
        )
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/analysis")
        
        assert response.status_code == 503
        data = response.json()
        
        assert data["error"] is True
        assert "NO_DATA" in data["error_type"]

    @patch('app.api.sectors.get_sector_analyzer')
    def test_get_sector_performance_success(self, mock_get_analyzer, client, sample_analysis_result):
        """Test successful sector performance retrieval."""
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(return_value=sample_analysis_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/performance/TECHNOLOGY")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["sector"] == "Technology"
        assert "performance_1m" in data
        assert "performance_3m" in data
        assert "momentum_score" in data

    @patch('app.api.sectors.get_sector_analyzer')
    def test_get_sector_performance_not_found(self, mock_get_analyzer, client):
        """Test sector performance when sector not found."""
        # Setup mock with empty result
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(
            return_value=SectorAnalysisResult(
                sector_performances=[],
                top_performers_1m=[],
                top_performers_3m=[],
                top_performers_1y=[],
                bottom_performers_1m=[],
                bottom_performers_3m=[],
                bottom_performers_1y=[],
                rotation_signals=[],
                market_trend=TrendDirection.SIDEWAYS,
                market_phase=RotationPhase.MID_CYCLE,
                volatility_regime="normal",
                analysis_timestamp=datetime.now(),
                data_freshness={}
            )
        )
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/performance/TECHNOLOGY")
        
        assert response.status_code == 404
        data = response.json()
        
        assert data["error"] is True
        assert "SECTOR_NOT_FOUND" in data["error_type"]

    @patch('app.api.sectors.get_sector_analyzer')
    def test_analyze_sector_industries_success(self, mock_get_analyzer, client, sample_sector_performance):
        """Test successful industry analysis."""
        # Create sample industry analysis result
        industry_result = IndustryAnalysisResult(
            sector=SectorCategory.TECHNOLOGY,
            industries=[],
            top_performing_industries=["Software - Application"],
            best_value_industries=["Semiconductors"],
            highest_growth_industries=["Cloud Computing"],
            sector_summary=sample_sector_performance,
            analysis_timestamp=datetime.now()
        )
        
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_sector_industries = AsyncMock(return_value=industry_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/industries/TECHNOLOGY")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["sector"] == "Technology"
        assert "industries" in data
        assert "top_performing_industries" in data
        assert "sector_summary" in data

    @patch('app.api.sectors.get_sector_analyzer')
    def test_compare_sectors_success(self, mock_get_analyzer, client):
        """Test successful sector comparison."""
        # Create sample comparison result
        comparison_result = SectorComparisonResult(
            sectors=[SectorCategory.TECHNOLOGY, SectorCategory.HEALTHCARE],
            timeframe="3m",
            performance_ranking=[
                {"sector": "Technology", "performance": 15.2, "rank": 1},
                {"sector": "Healthcare", "performance": 8.5, "rank": 2}
            ],
            valuation_ranking=[
                {"sector": "Healthcare", "pe_ratio": 18.5, "rank": 1},
                {"sector": "Technology", "pe_ratio": 28.5, "rank": 2}
            ],
            momentum_ranking=[
                {"sector": "Technology", "momentum_score": 82, "rank": 1},
                {"sector": "Healthcare", "momentum_score": 65, "rank": 2}
            ],
            winner=SectorCategory.TECHNOLOGY,
            best_value=SectorCategory.HEALTHCARE,
            strongest_momentum=SectorCategory.TECHNOLOGY,
            key_insights=["Technology leads performance"],
            recommendations=["Consider tech allocation"],
            analysis_timestamp=datetime.now()
        )
        
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.compare_sectors = AsyncMock(return_value=comparison_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        request_data = {
            "sectors": ["TECHNOLOGY", "HEALTHCARE"],
            "timeframe": "3m",
            "metrics": ["performance", "valuation"]
        }
        
        response = client.post("/api/v1/sectors/compare", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["timeframe"] == "3m"
        assert "performance_ranking" in data
        assert "valuation_ranking" in data
        assert "winner" in data

    @patch('app.api.sectors.get_sector_analyzer')
    def test_get_rotation_signals_success(self, mock_get_analyzer, client, sample_analysis_result):
        """Test successful rotation signals retrieval."""
        # Add rotation signal to sample result
        rotation_signal = SectorRotationSignal(
            from_sector=SectorCategory.TECHNOLOGY,
            to_sector=SectorCategory.ENERGY,
            signal_strength=75,
            confidence=68,
            momentum_shift=Decimal("8.5"),
            relative_strength_change=Decimal("12.3"),
            volume_confirmation=True,
            market_phase=RotationPhase.MID_CYCLE,
            economic_driver="Rising interest rates",
            signal_date=datetime.now(),
            expected_duration="2-3 months",
            reasons=["Tech weakness", "Energy strength"],
            risks=["Geopolitical tensions"],
            last_updated=datetime.now()
        )
        sample_analysis_result.rotation_signals = [rotation_signal]
        
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(return_value=sample_analysis_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/rotation-signals?min_strength=50")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        if data:
            signal = data[0]
            assert "from_sector" in signal
            assert "to_sector" in signal
            assert "signal_strength" in signal
            assert signal["signal_strength"] >= 50

    @patch('app.api.sectors.get_sector_analyzer')
    def test_get_top_performers_success(self, mock_get_analyzer, client, sample_analysis_result):
        """Test successful top performers retrieval."""
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(return_value=sample_analysis_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/top-performers?timeframe=3m&limit=3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "top_performers_3m" in data
        assert "timeframe" in data
        assert "limit" in data
        assert data["timeframe"] == "3m"
        assert data["limit"] == 3

    @patch('app.api.sectors.get_sector_analyzer')
    def test_get_top_performers_invalid_timeframe(self, mock_get_analyzer, client, sample_analysis_result):
        """Test top performers with invalid timeframe."""
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(return_value=sample_analysis_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/top-performers?timeframe=invalid")
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["error"] is True
        assert "INVALID_TIMEFRAME" in data["error_type"]

    @patch('app.api.sectors.get_sector_analyzer')
    def test_get_sector_rankings_success(self, mock_get_analyzer, client, sample_analysis_result):
        """Test successful sector rankings retrieval."""
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(return_value=sample_analysis_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/rankings?sort_by=performance_3m&order=desc")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "rankings" in data
        assert "sort_by" in data
        assert "order" in data
        assert "total_sectors" in data
        assert data["sort_by"] == "performance_3m"
        assert data["order"] == "desc"
        
        if data["rankings"]:
            ranking = data["rankings"][0]
            assert "rank" in ranking
            assert "sector" in ranking
            assert "performance_3m" in ranking

    @patch('app.api.sectors.get_sector_analyzer')
    def test_get_sector_rankings_invalid_sort(self, mock_get_analyzer, client, sample_analysis_result):
        """Test sector rankings with invalid sort metric."""
        # Setup mock
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(return_value=sample_analysis_result)
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/rankings?sort_by=invalid_metric")
        
        assert response.status_code == 400
        data = response.json()
        
        assert data["error"] is True
        assert "INVALID_SORT_METRIC" in data["error_type"]

    def test_invalid_sector_enum(self, client):
        """Test API with invalid sector enum value."""
        response = client.get("/api/v1/sectors/performance/INVALID_SECTOR")
        
        # Should return 422 for invalid enum value
        assert response.status_code == 422

    @patch('app.api.sectors.get_sector_analyzer')
    def test_analyzer_exception_handling(self, mock_get_analyzer, client):
        """Test proper handling of analyzer exceptions."""
        # Setup mock to raise unexpected exception
        mock_analyzer = Mock(spec=SectorAnalyzer)
        mock_analyzer.analyze_all_sectors = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_get_analyzer.return_value = mock_analyzer
        
        response = client.get("/api/v1/sectors/analysis")
        
        assert response.status_code == 500
        data = response.json()
        
        assert data["error"] is True
        assert "INTERNAL_ERROR" in data["error_type"]

    def test_compare_sectors_validation(self, client):
        """Test sector comparison request validation."""
        # Test with invalid request data
        invalid_requests = [
            {},  # Missing required fields
            {"sectors": []},  # Empty sectors list
            {"sectors": ["TECHNOLOGY"]},  # Only one sector
            {"sectors": ["INVALID_SECTOR", "TECHNOLOGY"]},  # Invalid sector
        ]
        
        for invalid_request in invalid_requests:
            response = client.post("/api/v1/sectors/compare", json=invalid_request)
            assert response.status_code in [400, 422]  # Bad request or validation error

    def test_rotation_signals_parameters(self, client):
        """Test rotation signals endpoint parameter validation."""
        # Test with invalid min_strength
        response = client.get("/api/v1/sectors/rotation-signals?min_strength=150")
        
        # Should handle invalid parameter gracefully
        assert response.status_code in [200, 400, 422]

    def test_top_performers_parameters(self, client):
        """Test top performers endpoint parameter validation."""
        # Test with invalid limit
        response = client.get("/api/v1/sectors/top-performers?limit=0")
        
        # Should handle invalid parameter
        assert response.status_code in [200, 400, 422]
        
        # Test with limit too high
        response = client.get("/api/v1/sectors/top-performers?limit=20")
        
        # Should handle limit validation
        assert response.status_code in [200, 400, 422]