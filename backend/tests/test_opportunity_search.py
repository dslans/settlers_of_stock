"""
Tests for the investment opportunity search functionality.
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.opportunity_search import OpportunitySearchService, OpportunitySearchException
from app.models.opportunity import (
    OpportunitySearchFilters, InvestmentOpportunity, OpportunityScore,
    OpportunityType, RiskLevel, MarketCapCategory
)
from app.models.stock import MarketData, Stock
from app.models.fundamental import FundamentalData
from app.models.technical import TechnicalData


class TestOpportunitySearchService:
    """Test cases for OpportunitySearchService."""
    
    @pytest.fixture
    def mock_data_service(self):
        """Mock data aggregation service."""
        mock = Mock()
        mock.get_market_data = AsyncMock()
        mock.get_stock_info = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_fundamental_analyzer(self):
        """Mock fundamental analyzer."""
        mock = Mock()
        mock.analyze_fundamentals = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_technical_analyzer(self):
        """Mock technical analyzer."""
        mock = Mock()
        mock.analyze_technical = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_analysis_engine(self):
        """Mock analysis engine."""
        mock = Mock()
        mock.analyze_stock = AsyncMock()
        return mock
    
    @pytest.fixture
    def opportunity_service(self, mock_data_service, mock_fundamental_analyzer, 
                          mock_technical_analyzer, mock_analysis_engine):
        """Create opportunity search service with mocked dependencies."""
        return OpportunitySearchService(
            data_service=mock_data_service,
            fundamental_analyzer=mock_fundamental_analyzer,
            technical_analyzer=mock_technical_analyzer,
            analysis_engine=mock_analysis_engine
        )
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing."""
        return MarketData(
            symbol="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=75000000,
            high_52_week=Decimal("180.00"),
            low_52_week=Decimal("120.00"),
            avg_volume=80000000,
            market_cap=2500000000000,
            pe_ratio=Decimal("25.5"),
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def sample_stock_info(self):
        """Sample stock info for testing."""
        return Stock(
            symbol="AAPL",
            name="Apple Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=2500000000000,
            last_updated=datetime.now()
        )
    
    @pytest.fixture
    def sample_fundamental_data(self):
        """Sample fundamental data for testing."""
        return FundamentalData(
            symbol="AAPL",
            pe_ratio=Decimal("25.5"),
            pb_ratio=Decimal("6.8"),
            roe=Decimal("0.31"),
            debt_to_equity=Decimal("0.45"),
            revenue_growth=Decimal("0.08"),
            profit_margin=Decimal("0.25"),
            eps=Decimal("6.15"),
            dividend=Decimal("0.92"),
            dividend_yield=Decimal("0.006"),
            quarter="Q4",
            year=2024,
            last_updated=datetime.now()
        )
    
    @pytest.fixture
    def sample_filters(self):
        """Sample search filters for testing."""
        return OpportunitySearchFilters(
            market_cap_categories=[MarketCapCategory.LARGE_CAP],
            sectors=["Technology"],
            pe_ratio_max=Decimal("30"),
            roe_min=Decimal("0.15"),
            opportunity_types=[OpportunityType.UNDERVALUED],
            max_risk_level=RiskLevel.MODERATE,
            limit=10
        )
    
    def test_market_cap_thresholds(self, opportunity_service):
        """Test market cap threshold definitions."""
        thresholds = opportunity_service.market_cap_thresholds
        
        assert MarketCapCategory.MEGA_CAP in thresholds
        assert MarketCapCategory.LARGE_CAP in thresholds
        assert MarketCapCategory.MID_CAP in thresholds
        assert MarketCapCategory.SMALL_CAP in thresholds
        assert MarketCapCategory.MICRO_CAP in thresholds
        
        # Check threshold values make sense
        mega_min, mega_max = thresholds[MarketCapCategory.MEGA_CAP]
        large_min, large_max = thresholds[MarketCapCategory.LARGE_CAP]
        
        assert mega_min == 200_000_000_000
        assert mega_max is None
        assert large_min == 10_000_000_000
        assert large_max == 200_000_000_000
    
    @pytest.mark.asyncio
    async def test_get_popular_symbols(self, opportunity_service):
        """Test getting popular stock symbols."""
        symbols = await opportunity_service._get_popular_symbols()
        
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" in symbols
        
        # All symbols should be strings and uppercase
        for symbol in symbols:
            assert isinstance(symbol, str)
            assert symbol.isupper()
    
    def test_passes_market_filters_market_cap(self, opportunity_service, sample_market_data):
        """Test market cap filtering logic."""
        # Test minimum market cap filter
        filters = OpportunitySearchFilters(market_cap_min=1000000000000)  # 1T
        assert opportunity_service._passes_market_filters(sample_market_data, filters)
        
        filters = OpportunitySearchFilters(market_cap_min=3000000000000)  # 3T
        assert not opportunity_service._passes_market_filters(sample_market_data, filters)
        
        # Test maximum market cap filter
        filters = OpportunitySearchFilters(market_cap_max=3000000000000)  # 3T
        assert opportunity_service._passes_market_filters(sample_market_data, filters)
        
        filters = OpportunitySearchFilters(market_cap_max=1000000000000)  # 1T
        assert not opportunity_service._passes_market_filters(sample_market_data, filters)
    
    def test_passes_market_filters_volume(self, opportunity_service, sample_market_data):
        """Test volume filtering logic."""
        # Test minimum volume filter
        filters = OpportunitySearchFilters(volume_min=50000000)
        assert opportunity_service._passes_market_filters(sample_market_data, filters)
        
        filters = OpportunitySearchFilters(volume_min=100000000)
        assert not opportunity_service._passes_market_filters(sample_market_data, filters)
        
        # Test average volume filter
        filters = OpportunitySearchFilters(avg_volume_min=70000000)
        assert opportunity_service._passes_market_filters(sample_market_data, filters)
        
        filters = OpportunitySearchFilters(avg_volume_min=90000000)
        assert not opportunity_service._passes_market_filters(sample_market_data, filters)
    
    def test_passes_fundamental_filters(self, opportunity_service, sample_fundamental_data):
        """Test fundamental filtering logic."""
        # Test P/E ratio filters
        filters = OpportunitySearchFilters(pe_ratio_max=Decimal("30"))
        assert opportunity_service._passes_fundamental_filters(sample_fundamental_data, filters)
        
        filters = OpportunitySearchFilters(pe_ratio_max=Decimal("20"))
        assert not opportunity_service._passes_fundamental_filters(sample_fundamental_data, filters)
        
        # Test ROE filter
        filters = OpportunitySearchFilters(roe_min=Decimal("0.25"))
        assert opportunity_service._passes_fundamental_filters(sample_fundamental_data, filters)
        
        filters = OpportunitySearchFilters(roe_min=Decimal("0.35"))
        assert not opportunity_service._passes_fundamental_filters(sample_fundamental_data, filters)
        
        # Test debt-to-equity filter
        filters = OpportunitySearchFilters(debt_to_equity_max=Decimal("0.50"))
        assert opportunity_service._passes_fundamental_filters(sample_fundamental_data, filters)
        
        filters = OpportunitySearchFilters(debt_to_equity_max=Decimal("0.40"))
        assert not opportunity_service._passes_fundamental_filters(sample_fundamental_data, filters)
    
    def test_calculate_opportunity_scores(self, opportunity_service, sample_market_data, 
                                        sample_fundamental_data):
        """Test opportunity score calculation."""
        # Mock fundamental data health score
        sample_fundamental_data.calculate_health_score = Mock(return_value=85)
        
        scores = opportunity_service._calculate_opportunity_scores(
            sample_market_data, sample_fundamental_data, None
        )
        
        assert isinstance(scores, OpportunityScore)
        assert 0 <= scores.overall_score <= 100
        assert scores.fundamental_score == 85
        assert scores.value_score is not None
        assert scores.quality_score is not None
        assert scores.momentum_score is not None
    
    def test_identify_opportunity_types(self, opportunity_service, sample_market_data, 
                                      sample_fundamental_data):
        """Test opportunity type identification."""
        scores = OpportunityScore(
            overall_score=80,
            fundamental_score=85,
            value_score=75,
            quality_score=85,
            momentum_score=70
        )
        
        opportunity_types = opportunity_service._identify_opportunity_types(
            sample_market_data, sample_fundamental_data, None, scores
        )
        
        assert isinstance(opportunity_types, list)
        assert len(opportunity_types) > 0
        assert all(isinstance(ot, OpportunityType) for ot in opportunity_types)
        
        # Should identify as undervalued due to high value score
        assert OpportunityType.UNDERVALUED in opportunity_types
        
        # Should identify as dividend due to high quality score
        assert OpportunityType.DIVIDEND in opportunity_types
    
    def test_assess_risk_level(self, opportunity_service, sample_market_data, 
                             sample_fundamental_data):
        """Test risk level assessment."""
        risk_level = opportunity_service._assess_risk_level(
            sample_market_data, sample_fundamental_data, None
        )
        
        assert isinstance(risk_level, RiskLevel)
        
        # Large cap with good fundamentals should be low to moderate risk
        assert risk_level in [RiskLevel.LOW, RiskLevel.MODERATE]
    
    def test_generate_reasons(self, opportunity_service, sample_market_data, 
                            sample_fundamental_data):
        """Test reason generation."""
        opportunity_types = [OpportunityType.UNDERVALUED, OpportunityType.GROWTH]
        
        reasons = opportunity_service._generate_reasons(
            sample_market_data, sample_fundamental_data, None, opportunity_types
        )
        
        assert isinstance(reasons, list)
        assert len(reasons) > 0
        assert all(isinstance(reason, str) for reason in reasons)
        
        # Should mention strong ROE
        roe_mentioned = any("return on equity" in reason.lower() for reason in reasons)
        assert roe_mentioned
    
    def test_generate_risks(self, opportunity_service, sample_market_data, 
                          sample_fundamental_data):
        """Test risk generation."""
        risks = opportunity_service._generate_risks(
            sample_market_data, sample_fundamental_data, None, RiskLevel.MODERATE
        )
        
        assert isinstance(risks, list)
        assert len(risks) > 0
        assert all(isinstance(risk, str) for risk in risks)
        
        # Should always include market volatility risk
        market_risk_mentioned = any("market volatility" in risk.lower() for risk in risks)
        assert market_risk_mentioned
    
    def test_calculate_price_targets(self, opportunity_service, sample_fundamental_data):
        """Test price target calculation."""
        current_price = Decimal("150.00")
        
        # Mock fundamental health score
        sample_fundamental_data.calculate_health_score = Mock(return_value=85)
        
        targets = opportunity_service._calculate_price_targets(
            current_price, sample_fundamental_data, None
        )
        
        assert isinstance(targets, dict)
        assert "short" in targets
        assert "medium" in targets
        assert "long" in targets
        
        # Targets should be higher than current price
        assert targets["short"] > current_price
        assert targets["medium"] > targets["short"]
        assert targets["long"] > targets["medium"]
    
    @pytest.mark.asyncio
    async def test_search_opportunities_empty_filters(self, opportunity_service):
        """Test search with minimal filters."""
        filters = OpportunitySearchFilters(limit=5)
        
        # Mock the stock universe and analysis methods
        with patch.object(opportunity_service, '_get_stock_universe') as mock_universe:
            mock_universe.return_value = ["AAPL", "MSFT"]
            
            with patch.object(opportunity_service, '_analyze_opportunities') as mock_analyze:
                mock_analyze.return_value = []
                
                result = await opportunity_service.search_opportunities(filters)
                
                assert result.total_found == 0
                assert len(result.opportunities) == 0
                assert result.filters_applied == filters
    
    @pytest.mark.asyncio
    async def test_search_opportunities_with_results(self, opportunity_service, 
                                                   sample_market_data, sample_stock_info):
        """Test search that returns results."""
        filters = OpportunitySearchFilters(limit=5)
        
        # Create a sample opportunity
        sample_opportunity = InvestmentOpportunity(
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
            catalysts=["Earnings growth"]
        )
        
        with patch.object(opportunity_service, '_get_stock_universe') as mock_universe:
            mock_universe.return_value = ["AAPL"]
            
            with patch.object(opportunity_service, '_analyze_opportunities') as mock_analyze:
                mock_analyze.return_value = [sample_opportunity]
                
                result = await opportunity_service.search_opportunities(filters)
                
                assert result.total_found == 1
                assert len(result.opportunities) == 1
                assert result.opportunities[0].symbol == "AAPL"
                assert result.opportunities[0].scores.overall_score == 85


class TestOpportunitySearchFilters:
    """Test cases for OpportunitySearchFilters model."""
    
    def test_valid_filters(self):
        """Test creating valid filters."""
        filters = OpportunitySearchFilters(
            market_cap_min=1000000000,
            market_cap_max=10000000000,
            sectors=["Technology", "Healthcare"],
            pe_ratio_max=Decimal("25"),
            roe_min=Decimal("0.15"),
            limit=20
        )
        
        assert filters.market_cap_min == 1000000000
        assert filters.market_cap_max == 10000000000
        assert filters.sectors == ["Technology", "Healthcare"]
        assert filters.pe_ratio_max == Decimal("25")
        assert filters.roe_min == Decimal("0.15")
        assert filters.limit == 20
    
    def test_invalid_market_cap_range(self):
        """Test validation of market cap range."""
        with pytest.raises(ValueError, match="market_cap_max must be greater than market_cap_min"):
            OpportunitySearchFilters(
                market_cap_min=10000000000,
                market_cap_max=5000000000
            )
    
    def test_limit_validation(self):
        """Test limit validation."""
        # Valid limits
        filters = OpportunitySearchFilters(limit=1)
        assert filters.limit == 1
        
        filters = OpportunitySearchFilters(limit=200)
        assert filters.limit == 200
        
        # Invalid limits should raise validation error
        with pytest.raises(ValueError):
            OpportunitySearchFilters(limit=0)
        
        with pytest.raises(ValueError):
            OpportunitySearchFilters(limit=201)
    
    def test_rsi_validation(self):
        """Test RSI range validation."""
        # Valid RSI values
        filters = OpportunitySearchFilters(rsi_min=Decimal("0"), rsi_max=Decimal("100"))
        assert filters.rsi_min == Decimal("0")
        assert filters.rsi_max == Decimal("100")
        
        # Invalid RSI values should raise validation error
        with pytest.raises(ValueError):
            OpportunitySearchFilters(rsi_min=Decimal("-10"))
        
        with pytest.raises(ValueError):
            OpportunitySearchFilters(rsi_max=Decimal("110"))


class TestInvestmentOpportunity:
    """Test cases for InvestmentOpportunity model."""
    
    def test_create_opportunity(self):
        """Test creating an investment opportunity."""
        opportunity = InvestmentOpportunity(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
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
            key_metrics={"pe_ratio": 25.5},
            reasons=["Strong fundamentals"],
            risks=["Market volatility"]
        )
        
        assert opportunity.symbol == "AAPL"
        assert opportunity.name == "Apple Inc."
        assert opportunity.current_price == Decimal("150.25")
        assert OpportunityType.UNDERVALUED in opportunity.opportunity_types
        assert opportunity.risk_level == RiskLevel.MODERATE
        assert opportunity.scores.overall_score == 85
    
    def test_symbol_validation(self):
        """Test symbol validation and normalization."""
        opportunity = InvestmentOpportunity(
            symbol="aapl",  # lowercase
            name="Apple Inc.",
            current_price=Decimal("150.25"),
            market_cap=2500000000000,
            volume=75000000,
            opportunity_types=[OpportunityType.UNDERVALUED],
            risk_level=RiskLevel.MODERATE,
            scores=OpportunityScore(overall_score=85),
            reasons=["Test"],
            risks=["Test"]
        )
        
        # Symbol should be converted to uppercase
        assert opportunity.symbol == "AAPL"