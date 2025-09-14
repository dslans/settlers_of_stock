"""
Unit tests for the Fundamental Analysis Engine.
Tests financial ratio calculations, company health assessment, and industry comparisons.
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from app.services.fundamental_analyzer import (
    FundamentalAnalyzer, 
    FundamentalAnalysisException,
    HealthRating,
    CompanyHealth,
    IndustryComparison
)
from app.models.fundamental import FundamentalData
from app.models.stock import Stock
from app.services.data_aggregation import DataAggregationService


# Global fixtures
@pytest.fixture
def mock_data_service():
    """Create a mock data aggregation service."""
    return Mock(spec=DataAggregationService)

@pytest.fixture
def sample_fundamental_data():
    """Create sample fundamental data for testing."""
    return FundamentalData(
        symbol="AAPL",
        pe_ratio=Decimal("25.5"),
        pb_ratio=Decimal("8.2"),
        roe=Decimal("0.28"),
        debt_to_equity=Decimal("0.45"),
        revenue_growth=Decimal("0.08"),
        profit_margin=Decimal("0.23"),
        eps=Decimal("6.15"),
        dividend=Decimal("0.92"),
        dividend_yield=Decimal("0.006"),
        book_value=Decimal("18.5"),
        revenue=394328000000,
        net_income=99803000000,
        total_debt=132480000000,
        total_equity=62146000000,
        free_cash_flow=84726000000,
        quarter="Q4",
        year=2024
    )

@pytest.fixture
def sample_stock_info():
    """Create sample stock info for testing."""
    return Stock(
        symbol="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3000000000000,
        last_updated=datetime.now()
    )


class TestFundamentalAnalyzer:
    """Test suite for FundamentalAnalyzer class."""
    pass


class TestFinancialRatioCalculations:
    """Test financial ratio calculation methods."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for ratio testing."""
        return FundamentalAnalyzer()
    
    def test_calculate_pe_ratio_valid(self, analyzer):
        """Test P/E ratio calculation with valid inputs."""
        price = Decimal("150.00")
        eps = Decimal("6.00")
        
        result = analyzer.calculate_pe_ratio(price, eps)
        
        assert result == Decimal("25.00")
    
    def test_calculate_pe_ratio_zero_eps(self, analyzer):
        """Test P/E ratio calculation with zero EPS."""
        price = Decimal("150.00")
        eps = Decimal("0.00")
        
        result = analyzer.calculate_pe_ratio(price, eps)
        
        assert result is None
    
    def test_calculate_pe_ratio_negative_eps(self, analyzer):
        """Test P/E ratio calculation with negative EPS."""
        price = Decimal("150.00")
        eps = Decimal("-2.00")
        
        result = analyzer.calculate_pe_ratio(price, eps)
        
        assert result is None
    
    def test_calculate_pb_ratio_valid(self, analyzer):
        """Test P/B ratio calculation with valid inputs."""
        price = Decimal("150.00")
        book_value = Decimal("20.00")
        
        result = analyzer.calculate_pb_ratio(price, book_value)
        
        assert result == Decimal("7.50")
    
    def test_calculate_pb_ratio_zero_book_value(self, analyzer):
        """Test P/B ratio calculation with zero book value."""
        price = Decimal("150.00")
        book_value = Decimal("0.00")
        
        result = analyzer.calculate_pb_ratio(price, book_value)
        
        assert result is None
    
    def test_calculate_roe_valid(self, analyzer):
        """Test ROE calculation with valid inputs."""
        net_income = 100000000
        total_equity = 500000000
        
        result = analyzer.calculate_roe(net_income, total_equity)
        
        assert result == Decimal("0.2000")
    
    def test_calculate_roe_zero_equity(self, analyzer):
        """Test ROE calculation with zero equity."""
        net_income = 100000000
        total_equity = 0
        
        result = analyzer.calculate_roe(net_income, total_equity)
        
        assert result is None
    
    def test_calculate_debt_to_equity_valid(self, analyzer):
        """Test debt-to-equity ratio calculation with valid inputs."""
        total_debt = 200000000
        total_equity = 500000000
        
        result = analyzer.calculate_debt_to_equity(total_debt, total_equity)
        
        assert result == Decimal("0.40")
    
    def test_calculate_debt_to_equity_no_debt(self, analyzer):
        """Test debt-to-equity ratio calculation with no debt."""
        total_debt = 0
        total_equity = 500000000
        
        result = analyzer.calculate_debt_to_equity(total_debt, total_equity)
        
        assert result == Decimal("0.00")
    
    def test_calculate_debt_to_equity_zero_equity(self, analyzer):
        """Test debt-to-equity ratio calculation with zero equity."""
        total_debt = 200000000
        total_equity = 0
        
        result = analyzer.calculate_debt_to_equity(total_debt, total_equity)
        
        assert result is None
    
    def test_calculate_current_ratio_valid(self, analyzer):
        """Test current ratio calculation with valid inputs."""
        current_assets = 300000000
        current_liabilities = 200000000
        
        result = analyzer.calculate_current_ratio(current_assets, current_liabilities)
        
        assert result == Decimal("1.50")
    
    def test_calculate_quick_ratio_valid(self, analyzer):
        """Test quick ratio calculation with valid inputs."""
        current_assets = 300000000
        inventory = 50000000
        current_liabilities = 200000000
        
        result = analyzer.calculate_quick_ratio(current_assets, inventory, current_liabilities)
        
        assert result == Decimal("1.25")
    
    def test_calculate_roa_valid(self, analyzer):
        """Test ROA calculation with valid inputs."""
        net_income = 100000000
        total_assets = 1000000000
        
        result = analyzer.calculate_roa(net_income, total_assets)
        
        assert result == Decimal("0.1000")
    
    def test_calculate_gross_margin_valid(self, analyzer):
        """Test gross margin calculation with valid inputs."""
        gross_profit = 200000000
        revenue = 500000000
        
        result = analyzer.calculate_gross_margin(gross_profit, revenue)
        
        assert result == Decimal("0.4000")
    
    def test_calculate_operating_margin_valid(self, analyzer):
        """Test operating margin calculation with valid inputs."""
        operating_income = 150000000
        revenue = 500000000
        
        result = analyzer.calculate_operating_margin(operating_income, revenue)
        
        assert result == Decimal("0.3000")


class TestCompanyHealthAssessment:
    """Test company health assessment functionality."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for health testing."""
        return FundamentalAnalyzer()
    
    def test_calculate_health_score_excellent_company(self, analyzer):
        """Test health score calculation for excellent company."""
        data = FundamentalData(
            symbol="AAPL",
            pe_ratio=Decimal("20.0"),
            pb_ratio=Decimal("5.0"),
            roe=Decimal("0.25"),  # 25% ROE
            debt_to_equity=Decimal("0.20"),  # Low debt
            revenue_growth=Decimal("0.20"),  # 20% growth
            profit_margin=Decimal("0.25"),  # 25% margin
            free_cash_flow=100000000,  # Positive FCF
            dividend_yield=Decimal("0.03"),  # 3% yield
            quarter="Q4",
            year=2024
        )
        
        score, strengths, weaknesses, key_metrics = analyzer._calculate_health_score(data)
        
        assert score >= 80  # Should be excellent
        assert len(strengths) > len(weaknesses)
        assert "Excellent ROE" in " ".join(strengths)
        assert "Low debt-to-equity" in " ".join(strengths)
        assert "Strong revenue growth" in " ".join(strengths)
    
    def test_calculate_health_score_poor_company(self, analyzer):
        """Test health score calculation for poor company."""
        data = FundamentalData(
            symbol="POOR",
            pe_ratio=Decimal("50.0"),  # High P/E
            pb_ratio=Decimal("15.0"),  # High P/B
            roe=Decimal("0.02"),  # Low ROE
            debt_to_equity=Decimal("2.0"),  # Very high debt
            revenue_growth=Decimal("-0.10"),  # Declining revenue
            profit_margin=Decimal("0.01"),  # Low margin
            free_cash_flow=-50000000,  # Negative FCF
            quarter="Q4",
            year=2024
        )
        
        score, strengths, weaknesses, key_metrics = analyzer._calculate_health_score(data)
        
        assert score <= 50  # Should be poor
        assert len(weaknesses) > len(strengths)
        assert "Low ROE" in " ".join(weaknesses)
        assert "Very high debt-to-equity" in " ".join(weaknesses)
        assert "Declining revenue" in " ".join(weaknesses)
    
    @pytest.mark.asyncio
    async def test_assess_company_health_success(self, analyzer, sample_fundamental_data):
        """Test successful company health assessment."""
        with patch.object(analyzer, 'analyze_fundamentals', return_value=sample_fundamental_data):
            result = await analyzer.assess_company_health("AAPL")
            
            assert isinstance(result, CompanyHealth)
            assert result.symbol == "AAPL"
            assert 0 <= result.overall_score <= 100
            assert result.rating in [r.value for r in HealthRating]
            assert isinstance(result.strengths, list)
            assert isinstance(result.weaknesses, list)
            assert isinstance(result.key_metrics, dict)
    
    @pytest.mark.asyncio
    async def test_assess_company_health_failure(self, analyzer):
        """Test company health assessment failure."""
        with patch.object(analyzer, 'analyze_fundamentals', side_effect=Exception("Data error")):
            with pytest.raises(FundamentalAnalysisException) as exc_info:
                await analyzer.assess_company_health("INVALID")
            
            assert exc_info.value.error_type == "ASSESSMENT_ERROR"


class TestIndustryComparison:
    """Test industry comparison functionality."""
    
    def get_analyzer_with_mock(self, mock_data_service):
        """Create analyzer with mocked data service."""
        return FundamentalAnalyzer(data_service=mock_data_service)
    
    @pytest.fixture
    def peer_data(self):
        """Create sample peer data for testing."""
        return {
            "AAPL": FundamentalData(
                symbol="AAPL", pe_ratio=Decimal("25.0"), pb_ratio=Decimal("8.0"),
                roe=Decimal("0.28"), debt_to_equity=Decimal("0.45"),
                profit_margin=Decimal("0.23"), revenue_growth=Decimal("0.08"),
                quarter="Q4", year=2024
            ),
            "MSFT": FundamentalData(
                symbol="MSFT", pe_ratio=Decimal("30.0"), pb_ratio=Decimal("10.0"),
                roe=Decimal("0.35"), debt_to_equity=Decimal("0.30"),
                profit_margin=Decimal("0.30"), revenue_growth=Decimal("0.12"),
                quarter="Q4", year=2024
            ),
            "GOOGL": FundamentalData(
                symbol="GOOGL", pe_ratio=Decimal("20.0"), pb_ratio=Decimal("5.0"),
                roe=Decimal("0.20"), debt_to_equity=Decimal("0.10"),
                profit_margin=Decimal("0.20"), revenue_growth=Decimal("0.15"),
                quarter="Q4", year=2024
            )
        }
    
    def test_calculate_industry_averages(self, mock_data_service, peer_data):
        """Test industry average calculation."""
        analyzer = self.get_analyzer_with_mock(mock_data_service)
        averages = analyzer._calculate_industry_averages(peer_data)
        
        assert "pe_ratio" in averages
        assert "roe" in averages
        assert "debt_to_equity" in averages
        
        # Check calculated averages
        expected_pe_avg = (25.0 + 30.0 + 20.0) / 3
        assert abs(averages["pe_ratio"] - expected_pe_avg) < 0.01
        
        expected_roe_avg = (0.28 + 0.35 + 0.20) / 3
        assert abs(averages["roe"] - expected_roe_avg) < 0.01
    
    def test_calculate_percentile_rankings(self, mock_data_service, peer_data):
        """Test percentile ranking calculation."""
        analyzer = self.get_analyzer_with_mock(mock_data_service)
        rankings = analyzer._calculate_percentile_rankings("AAPL", peer_data)
        
        assert "roe" in rankings
        assert "pe_ratio" in rankings
        
        # AAPL has middle ROE (0.28), should be around 66th percentile (2 out of 3 companies have lower ROE)
        assert 60 <= rankings["roe"] <= 70
        
        # AAPL has middle P/E (25.0), should be around 66th percentile for "lower is better" (2 out of 3 have higher P/E)
        assert 60 <= rankings["pe_ratio"] <= 70
    
    def test_determine_relative_performance(self, mock_data_service, peer_data):
        """Test relative performance determination."""
        analyzer = self.get_analyzer_with_mock(mock_data_service)
        industry_averages = {
            "pe_ratio": 25.0,
            "roe": 0.28,
            "debt_to_equity": 0.28
        }
        
        performance = analyzer._determine_relative_performance("AAPL", peer_data, industry_averages)
        
        assert "pe_ratio" in performance
        assert "roe" in performance
        assert "debt_to_equity" in performance
        
        # AAPL's metrics are close to averages, so should be "At Average"
        assert performance["pe_ratio"] == "At Average"
        assert performance["roe"] == "At Average"
    
    @pytest.mark.asyncio
    async def test_compare_to_industry_success(self, mock_data_service, sample_stock_info, peer_data):
        """Test successful industry comparison."""
        analyzer = self.get_analyzer_with_mock(mock_data_service)
        analyzer.data_service.get_stock_info = AsyncMock(return_value=sample_stock_info)
        
        with patch.object(analyzer, '_fetch_peer_fundamentals', return_value=peer_data):
            result = await analyzer.compare_to_industry("AAPL")
            
            assert isinstance(result, IndustryComparison)
            assert result.symbol == "AAPL"
            assert result.industry == "Technology"
            assert isinstance(result.peer_symbols, list)
            assert isinstance(result.percentile_rankings, dict)
            assert isinstance(result.industry_averages, dict)
            assert isinstance(result.relative_performance, dict)


class TestFundamentalAnalysisIntegration:
    """Test integration scenarios and error handling."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer for integration testing."""
        return FundamentalAnalyzer()
    
    @pytest.mark.asyncio
    async def test_analyze_fundamentals_with_yfinance_mock(self, analyzer):
        """Test fundamental analysis with mocked yfinance data."""
        mock_yf_data = {
            'symbol': 'AAPL',
            'trailingPE': 25.5,
            'priceToBook': 8.2,
            'returnOnEquity': 0.28,
            'debtToEquity': 0.45,
            'revenueGrowth': 0.08,
            'profitMargins': 0.23,
            'trailingEps': 6.15,
            'dividendRate': 0.92,
            'dividendYield': 0.006,
            'bookValue': 18.5,
            'totalRevenue': 394328000000,
            'netIncomeToCommon': 99803000000,
            'totalDebt': 132480000000,
            'totalStockholderEquity': 62146000000,
            'freeCashflow': 84726000000
        }
        
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.info = mock_yf_data
            
            result = await analyzer.analyze_fundamentals("AAPL")
            
            assert isinstance(result, FundamentalData)
            assert result.symbol == "AAPL"
            assert result.pe_ratio == Decimal("25.5")
            assert result.roe == Decimal("0.28")
    
    @pytest.mark.asyncio
    async def test_analyze_fundamentals_invalid_symbol(self, analyzer):
        """Test fundamental analysis with invalid symbol."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.return_value.info = {}
            
            with pytest.raises(FundamentalAnalysisException) as exc_info:
                await analyzer.analyze_fundamentals("INVALID")
            
            assert exc_info.value.error_type == "DATA_ERROR"
    
    @pytest.mark.asyncio
    async def test_safe_fetch_fundamentals_error_handling(self, analyzer):
        """Test safe fundamental fetching with error handling."""
        with patch.object(analyzer, 'analyze_fundamentals', side_effect=Exception("Network error")):
            result = await analyzer._safe_fetch_fundamentals("AAPL")
            
            assert result is None
    
    def test_industry_peers_mapping(self, analyzer):
        """Test industry peer mapping functionality."""
        assert "Technology" in analyzer.industry_peers
        assert "AAPL" in analyzer.industry_peers["Technology"]
        assert "MSFT" in analyzer.industry_peers["Technology"]
        
        assert "Financial Services" in analyzer.industry_peers
        assert "JPM" in analyzer.industry_peers["Financial Services"]


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer for edge case testing."""
        return FundamentalAnalyzer()
    
    def test_health_score_with_missing_data(self, analyzer):
        """Test health score calculation with missing data."""
        data = FundamentalData(
            symbol="TEST",
            quarter="Q4",
            year=2024
            # Most fields are None
        )
        
        score, strengths, weaknesses, key_metrics = analyzer._calculate_health_score(data)
        
        assert 0 <= score <= 100
        assert isinstance(strengths, list)
        assert isinstance(weaknesses, list)
        assert isinstance(key_metrics, dict)
    
    def test_percentile_rankings_single_company(self, analyzer):
        """Test percentile rankings with single company."""
        peer_data = {
            "AAPL": FundamentalData(
                symbol="AAPL", pe_ratio=Decimal("25.0"),
                quarter="Q4", year=2024
            )
        }
        
        rankings = analyzer._calculate_percentile_rankings("AAPL", peer_data)
        
        # With single company, should be 100th percentile
        if "pe_ratio" in rankings:
            assert rankings["pe_ratio"] == 100.0
    
    def test_industry_averages_empty_data(self, analyzer):
        """Test industry averages with empty data."""
        peer_data = {}
        
        averages = analyzer._calculate_industry_averages(peer_data)
        
        assert isinstance(averages, dict)
        assert len(averages) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])