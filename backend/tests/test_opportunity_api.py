"""
Tests for the investment opportunity search API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from app.main import app
from app.models.opportunity import (
    OpportunitySearchFilters, InvestmentOpportunity, OpportunitySearchResult,
    OpportunityScore, OpportunityType, RiskLevel, MarketCapCategory
)


class TestOpportunityAPI:
    """Test cases for opportunity search API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def sample_opportunity(self):
        """Sample investment opportunity for testing."""
        return InvestmentOpportunity(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            current_price=Decimal("150.25"),
            market_cap=2500000000000,
            volume=75000000,
            opportunity_types=[OpportunityType.UNDERVALUED],
            risk_level=RiskLevel.MODERATE,
            scores=OpportunityScore(
                overall_score=85,
                fundamental_score=90,
                technical_score=80,
                value_score=85,
                quality_score=90,
                momentum_score=75
            ),
            key_metrics={"pe_ratio": 25.5, "roe": 0.31},
            reasons=["Strong fundamentals", "Attractive valuation"],
            risks=["Market volatility"],
            catalysts=["Earnings growth"],
            price_target_short=Decimal("165.00"),
            price_target_medium=Decimal("175.00"),
            price_target_long=Decimal("190.00")
        )
    
    @pytest.fixture
    def sample_search_result(self, sample_opportunity):
        """Sample search result for testing."""
        return OpportunitySearchResult(
            opportunities=[sample_opportunity],
            total_found=1,
            filters_applied=OpportunitySearchFilters(limit=10),
            search_timestamp="2024-01-15T10:30:00Z",
            execution_time_ms=1250,
            stats={"symbols_screened": 100, "symbols_analyzed": 50}
        )
    
    def test_search_opportunities_success(self, client, sample_search_result):
        """Test successful opportunity search."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            mock_instance = Mock()
            mock_instance.search_opportunities = AsyncMock(return_value=sample_search_result)
            mock_service.return_value = mock_instance
            
            request_data = {
                "filters": {
                    "market_cap_categories": ["large_cap"],
                    "sectors": ["Technology"],
                    "pe_ratio_max": 30,
                    "limit": 10
                },
                "universe": "popular"
            }
            
            response = client.post("/api/v1/opportunities/search", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data["opportunities"]) == 1
            assert data["opportunities"][0]["symbol"] == "AAPL"
            assert data["opportunities"][0]["name"] == "Apple Inc."
            assert data["opportunities"][0]["scores"]["overall_score"] == 85
            assert data["total_found"] == 1
            assert data["execution_time_ms"] == 1250
    
    def test_search_opportunities_invalid_filters(self, client):
        """Test search with invalid filters."""
        request_data = {
            "filters": {
                "market_cap_min": 10000000000,
                "market_cap_max": 5000000000,  # Invalid: max < min
                "limit": 10
            }
        }
        
        response = client.post("/api/v1/opportunities/search", json=request_data)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_quick_search_success(self, client):
        """Test successful quick search."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            mock_instance = Mock()
            mock_quick_result = {
                "opportunities": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "current_price": 150.25,
                        "score": 85,
                        "opportunity_types": ["undervalued"],
                        "risk_level": "moderate",
                        "sector": "Technology",
                        "market_cap": 2500000000000
                    }
                ],
                "total_found": 1,
                "search_time_ms": 500
            }
            mock_instance.search_opportunities = AsyncMock()
            mock_service.return_value = mock_instance
            
            # Mock the quick search conversion
            with patch('app.services.opportunity.quickSearchOpportunities') as mock_quick:
                mock_quick.return_value = mock_quick_result
                
                response = client.get(
                    "/api/v1/opportunities/quick-search",
                    params={
                        "opportunity_types": ["undervalued"],
                        "max_risk": "moderate",
                        "limit": 10
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert len(data["opportunities"]) == 1
                assert data["opportunities"][0]["symbol"] == "AAPL"
                assert data["total_found"] == 1
    
    def test_get_opportunity_details_success(self, client, sample_opportunity):
        """Test getting opportunity details for a specific symbol."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            mock_instance = Mock()
            mock_instance.get_opportunity_details = AsyncMock(return_value=sample_opportunity)
            mock_service.return_value = mock_instance
            
            response = client.get("/api/v1/opportunities/details/AAPL")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["symbol"] == "AAPL"
            assert data["name"] == "Apple Inc."
            assert data["scores"]["overall_score"] == 85
            assert len(data["reasons"]) == 2
            assert len(data["risks"]) == 1
    
    def test_get_opportunity_details_not_found(self, client):
        """Test getting details for non-existent symbol."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            from app.services.opportunity_search import OpportunitySearchException
            
            mock_instance = Mock()
            mock_instance.get_opportunity_details = AsyncMock(
                side_effect=OpportunitySearchException(
                    "Symbol not found",
                    error_type="INVALID_SYMBOL"
                )
            )
            mock_service.return_value = mock_instance
            
            response = client.get("/api/v1/opportunities/details/INVALID")
            
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"] is True
            assert "not found" in data["detail"]["message"].lower()
    
    def test_get_sector_opportunities_success(self, client, sample_opportunity):
        """Test getting sector opportunities."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            mock_instance = Mock()
            mock_instance.get_sector_opportunities = AsyncMock(return_value=[sample_opportunity])
            mock_service.return_value = mock_instance
            
            response = client.get(
                "/api/v1/opportunities/sector/Technology",
                params={"limit": 10, "min_market_cap": 1000000000}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 1
            assert data[0]["symbol"] == "AAPL"
            assert data[0]["sector"] == "Technology"
    
    def test_get_trending_opportunities_success(self, client, sample_opportunity):
        """Test getting trending opportunities."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            mock_instance = Mock()
            mock_instance.get_trending_opportunities = AsyncMock(return_value=[sample_opportunity])
            mock_service.return_value = mock_instance
            
            response = client.get(
                "/api/v1/opportunities/trending",
                params={"timeframe": "1d", "limit": 20}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 1
            assert data[0]["symbol"] == "AAPL"
    
    def test_get_trending_opportunities_invalid_timeframe(self, client):
        """Test trending opportunities with invalid timeframe."""
        response = client.get(
            "/api/v1/opportunities/trending",
            params={"timeframe": "invalid", "limit": 20}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_get_filter_options_success(self, client):
        """Test getting filter options."""
        response = client.get("/api/v1/opportunities/filters/options")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "opportunity_types" in data
        assert "risk_levels" in data
        assert "market_cap_categories" in data
        assert "popular_sectors" in data
        assert "timeframes" in data
        assert "sort_options" in data
        assert "sort_orders" in data
        
        # Check some expected values
        assert "undervalued" in data["opportunity_types"]
        assert "growth" in data["opportunity_types"]
        assert "low" in data["risk_levels"]
        assert "moderate" in data["risk_levels"]
        assert "large_cap" in data["market_cap_categories"]
        assert "Technology" in data["popular_sectors"]
    
    def test_validate_filters_success(self, client):
        """Test filter validation with valid filters."""
        filters = {
            "market_cap_min": 1000000000,
            "market_cap_max": 10000000000,
            "pe_ratio_max": 25,
            "roe_min": 0.15,
            "limit": 20
        }
        
        response = client.post("/api/v1/opportunities/filters/validate", json=filters)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is True
        assert len(data["issues"]) == 0
        assert data["filter_count"] > 0
    
    def test_validate_filters_with_issues(self, client):
        """Test filter validation with invalid filters."""
        filters = {
            "market_cap_min": 10000000000,
            "market_cap_max": 5000000000,  # Invalid: max < min
            "pe_ratio_min": 30,
            "pe_ratio_max": 20,  # Invalid: min > max
            "limit": 20
        }
        
        response = client.post("/api/v1/opportunities/filters/validate", json=filters)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["valid"] is False
        assert len(data["issues"]) > 0
        assert any("market_cap" in issue for issue in data["issues"])
        assert any("pe_ratio" in issue for issue in data["issues"])
    
    def test_search_opportunities_service_error(self, client):
        """Test search when service raises an error."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            from app.services.opportunity_search import OpportunitySearchException
            
            mock_instance = Mock()
            mock_instance.search_opportunities = AsyncMock(
                side_effect=OpportunitySearchException(
                    "Search failed",
                    error_type="SEARCH_FAILED",
                    suggestions=["Try with fewer filters"]
                )
            )
            mock_service.return_value = mock_instance
            
            request_data = {
                "filters": {"limit": 10},
                "universe": "popular"
            }
            
            response = client.post("/api/v1/opportunities/search", json=request_data)
            
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["error"] is True
            assert "Search failed" in data["detail"]["message"]
            assert len(data["detail"]["suggestions"]) > 0
    
    def test_search_opportunities_unexpected_error(self, client):
        """Test search when an unexpected error occurs."""
        with patch('app.api.opportunities.get_opportunity_service') as mock_service:
            mock_instance = Mock()
            mock_instance.search_opportunities = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_service.return_value = mock_instance
            
            request_data = {
                "filters": {"limit": 10},
                "universe": "popular"
            }
            
            response = client.post("/api/v1/opportunities/search", json=request_data)
            
            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"] is True
            assert "Internal server error" in data["detail"]["message"]