"""
Tests for Sector Analysis Service.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime

from app.services.sector_analyzer import SectorAnalyzer, SectorAnalysisException
from app.models.sector import (
    SectorCategory, SectorPerformance, IndustryPerformance, 
    SectorRotationSignal, TrendDirection, RotationPhase
)
from app.models.stock import MarketData
from app.services.data_aggregation import DataAggregationService


class TestSectorAnalyzer:
    """Test cases for SectorAnalyzer service."""
    
    @pytest.fixture
    def mock_data_service(self):
        """Create mock data aggregation service."""
        service = Mock(spec=DataAggregationService)
        service.get_market_data = AsyncMock()
        service.get_stock_info = AsyncMock()
        return service
    
    @pytest.fixture
    def sector_analyzer(self, mock_data_service):
        """Create SectorAnalyzer instance with mocked dependencies."""
        return SectorAnalyzer(data_service=mock_data_service)
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        return MarketData(
            symbol="AAPL",
            price=Decimal("150.00"),
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

    @pytest.mark.asyncio
    async def test_analyze_single_sector_success(self, sector_analyzer, mock_data_service, sample_market_data):
        """Test successful single sector analysis."""
        # Setup mock responses
        mock_data_service.get_market_data.return_value = sample_market_data
        
        # Test the private method directly
        result = await sector_analyzer._analyze_single_sector(SectorCategory.TECHNOLOGY)
        
        # Verify result
        assert result is not None
        assert result.sector == SectorCategory.TECHNOLOGY
        assert isinstance(result.performance_1m, Decimal)
        assert isinstance(result.momentum_score, int)
        assert result.momentum_score >= 0
        assert result.momentum_score <= 100
        
        # Verify data service was called
        assert mock_data_service.get_market_data.call_count > 0

    @pytest.mark.asyncio
    async def test_analyze_single_sector_no_data(self, sector_analyzer, mock_data_service):
        """Test sector analysis when no market data is available."""
        # Setup mock to return no data
        mock_data_service.get_market_data.side_effect = Exception("No data available")
        
        # Test the private method
        result = await sector_analyzer._analyze_single_sector(SectorCategory.TECHNOLOGY)
        
        # Should return None when no data available
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_all_sectors_success(self, sector_analyzer, mock_data_service, sample_market_data):
        """Test successful analysis of all sectors."""
        # Setup mock responses
        mock_data_service.get_market_data.return_value = sample_market_data
        
        # Mock the _analyze_single_sector method to return sample data
        with patch.object(sector_analyzer, '_analyze_single_sector') as mock_analyze:
            mock_analyze.return_value = SectorPerformance(
                sector=SectorCategory.TECHNOLOGY,
                performance_1d=Decimal("1.0"),
                performance_1w=Decimal("2.0"),
                performance_1m=Decimal("5.0"),
                performance_3m=Decimal("10.0"),
                performance_6m=Decimal("15.0"),
                performance_1y=Decimal("20.0"),
                performance_ytd=Decimal("12.0"),
                relative_performance_1m=Decimal("1.0"),
                relative_performance_3m=Decimal("2.0"),
                relative_performance_1y=Decimal("3.0"),
                trend_direction=TrendDirection.UP,
                trend_strength=70,
                momentum_score=75,
                market_cap=1000000000000,
                avg_volume=1000000000,
                pe_ratio=Decimal("25.0"),
                pb_ratio=Decimal("3.0"),
                performance_rank_1m=1,
                performance_rank_3m=1,
                performance_rank_1y=1,
                volatility=Decimal("20.0"),
                beta=Decimal("1.0"),
                dividend_yield=Decimal("2.0")
            )
            
            result = await sector_analyzer.analyze_all_sectors()
            
            # Verify result structure
            assert result is not None
            assert len(result.sector_performances) > 0
            assert len(result.top_performers_1m) <= 3
            assert len(result.top_performers_3m) <= 3
            assert len(result.top_performers_1y) <= 3
            assert isinstance(result.rotation_signals, list)
            assert result.market_trend in [t.value for t in TrendDirection]
            assert result.market_phase in [p.value for p in RotationPhase]

    @pytest.mark.asyncio
    async def test_analyze_all_sectors_no_data(self, sector_analyzer, mock_data_service):
        """Test analysis when no sector data is available."""
        # Mock to return None for all sectors
        with patch.object(sector_analyzer, '_analyze_single_sector') as mock_analyze:
            mock_analyze.return_value = None
            
            with pytest.raises(SectorAnalysisException) as exc_info:
                await sector_analyzer.analyze_all_sectors()
            
            assert exc_info.value.error_type == "NO_DATA"
            assert "Failed to analyze any sectors" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_analyze_sector_industries_success(self, sector_analyzer, mock_data_service, sample_market_data):
        """Test successful industry analysis within a sector."""
        # Setup mock responses
        mock_data_service.get_market_data.return_value = sample_market_data
        
        # Mock sector analysis
        with patch.object(sector_analyzer, '_analyze_single_sector') as mock_sector:
            mock_sector.return_value = SectorPerformance(
                sector=SectorCategory.TECHNOLOGY,
                performance_1d=Decimal("1.0"),
                performance_1w=Decimal("2.0"),
                performance_1m=Decimal("5.0"),
                performance_3m=Decimal("10.0"),
                performance_6m=Decimal("15.0"),
                performance_1y=Decimal("20.0"),
                performance_ytd=Decimal("12.0"),
                relative_performance_1m=Decimal("1.0"),
                relative_performance_3m=Decimal("2.0"),
                relative_performance_1y=Decimal("3.0"),
                trend_direction=TrendDirection.UP,
                trend_strength=70,
                momentum_score=75,
                market_cap=1000000000000,
                avg_volume=1000000000,
                pe_ratio=Decimal("25.0"),
                pb_ratio=Decimal("3.0"),
                performance_rank_1m=1,
                performance_rank_3m=1,
                performance_rank_1y=1,
                volatility=Decimal("20.0"),
                beta=Decimal("1.0"),
                dividend_yield=Decimal("2.0")
            )
            
            result = await sector_analyzer.analyze_sector_industries(SectorCategory.TECHNOLOGY)
            
            # Verify result structure
            assert result is not None
            assert result.sector == SectorCategory.TECHNOLOGY
            assert isinstance(result.industries, list)
            assert isinstance(result.top_performing_industries, list)
            assert isinstance(result.best_value_industries, list)
            assert isinstance(result.highest_growth_industries, list)
            assert result.sector_summary is not None

    @pytest.mark.asyncio
    async def test_compare_sectors_success(self, sector_analyzer, mock_data_service):
        """Test successful sector comparison."""
        # Mock sector analysis
        with patch.object(sector_analyzer, '_analyze_single_sector') as mock_analyze:
            mock_analyze.return_value = SectorPerformance(
                sector=SectorCategory.TECHNOLOGY,
                performance_1d=Decimal("1.0"),
                performance_1w=Decimal("2.0"),
                performance_1m=Decimal("5.0"),
                performance_3m=Decimal("10.0"),
                performance_6m=Decimal("15.0"),
                performance_1y=Decimal("20.0"),
                performance_ytd=Decimal("12.0"),
                relative_performance_1m=Decimal("1.0"),
                relative_performance_3m=Decimal("2.0"),
                relative_performance_1y=Decimal("3.0"),
                trend_direction=TrendDirection.UP,
                trend_strength=70,
                momentum_score=75,
                market_cap=1000000000000,
                avg_volume=1000000000,
                pe_ratio=Decimal("25.0"),
                pb_ratio=Decimal("3.0"),
                performance_rank_1m=1,
                performance_rank_3m=1,
                performance_rank_1y=1,
                volatility=Decimal("20.0"),
                beta=Decimal("1.0"),
                dividend_yield=Decimal("2.0")
            )
            
            sectors = [SectorCategory.TECHNOLOGY, SectorCategory.HEALTHCARE]
            result = await sector_analyzer.compare_sectors(sectors, "3m")
            
            # Verify result structure
            assert result is not None
            assert result.sectors == sectors
            assert result.timeframe == "3m"
            assert len(result.performance_ranking) == len(sectors)
            assert len(result.valuation_ranking) == len(sectors)
            assert len(result.momentum_ranking) == len(sectors)
            assert result.winner in [s.value for s in sectors]
            assert result.best_value in [s.value for s in sectors]
            assert result.strongest_momentum in [s.value for s in sectors]
            assert isinstance(result.key_insights, list)
            assert isinstance(result.recommendations, list)

    def test_calculate_trend_direction(self, sector_analyzer):
        """Test trend direction calculation."""
        # Test strong uptrend
        performance_metrics = {
            '3m': Decimal('20.0'),
            '1m': Decimal('8.0')
        }
        trend = sector_analyzer._calculate_trend_direction(performance_metrics)
        assert trend == TrendDirection.STRONG_UP
        
        # Test uptrend
        performance_metrics = {
            '3m': Decimal('8.0'),
            '1m': Decimal('2.0')
        }
        trend = sector_analyzer._calculate_trend_direction(performance_metrics)
        assert trend == TrendDirection.UP
        
        # Test sideways
        performance_metrics = {
            '3m': Decimal('2.0'),
            '1m': Decimal('1.0')
        }
        trend = sector_analyzer._calculate_trend_direction(performance_metrics)
        assert trend == TrendDirection.SIDEWAYS
        
        # Test downtrend
        performance_metrics = {
            '3m': Decimal('-8.0'),
            '1m': Decimal('-2.0')
        }
        trend = sector_analyzer._calculate_trend_direction(performance_metrics)
        assert trend == TrendDirection.DOWN
        
        # Test strong downtrend
        performance_metrics = {
            '3m': Decimal('-20.0'),
            '1m': Decimal('-8.0')
        }
        trend = sector_analyzer._calculate_trend_direction(performance_metrics)
        assert trend == TrendDirection.STRONG_DOWN

    def test_calculate_trend_strength(self, sector_analyzer):
        """Test trend strength calculation."""
        performance_metrics = {
            '1m': Decimal('10.0'),
            '3m': Decimal('15.0')
        }
        strength = sector_analyzer._calculate_trend_strength(performance_metrics)
        assert isinstance(strength, int)
        assert 0 <= strength <= 100

    def test_calculate_momentum_score(self, sector_analyzer):
        """Test momentum score calculation."""
        performance_metrics = {
            '1w': Decimal('5.0'),
            '1m': Decimal('8.0'),
            '3m': Decimal('12.0')
        }
        momentum = sector_analyzer._calculate_momentum_score(performance_metrics)
        assert isinstance(momentum, int)
        assert 0 <= momentum <= 100

    @pytest.mark.asyncio
    async def test_calculate_sector_metrics(self, sector_analyzer, sample_market_data):
        """Test sector metrics calculation."""
        market_data_list = [sample_market_data]
        
        metrics = await sector_analyzer._calculate_sector_metrics(market_data_list)
        
        assert 'market_cap' in metrics
        assert 'avg_volume' in metrics
        assert 'pe_ratio' in metrics
        assert 'volatility' in metrics
        assert 'beta' in metrics
        assert 'dividend_yield' in metrics
        
        assert metrics['market_cap'] == sample_market_data.market_cap
        assert isinstance(metrics['volatility'], Decimal)
        assert isinstance(metrics['beta'], Decimal)

    @pytest.mark.asyncio
    async def test_calculate_industry_metrics(self, sector_analyzer, sample_market_data):
        """Test industry metrics calculation."""
        market_data_list = [sample_market_data]
        
        metrics = await sector_analyzer._calculate_industry_metrics(market_data_list)
        
        assert 'market_cap' in metrics
        assert 'pe_ratio' in metrics
        assert 'pb_ratio' in metrics
        assert 'roe' in metrics
        assert 'profit_margin' in metrics
        assert 'revenue_growth' in metrics
        assert 'earnings_growth' in metrics
        
        assert metrics['market_cap'] == sample_market_data.market_cap
        assert isinstance(metrics['pe_ratio'], Decimal)

    def test_determine_market_trend(self, sector_analyzer, sample_sector_performance):
        """Test market trend determination."""
        sector_performances = [sample_sector_performance]
        
        trend = sector_analyzer._determine_market_trend(sector_performances)
        
        assert trend in [t for t in TrendDirection]

    def test_determine_market_phase(self, sector_analyzer, sample_sector_performance):
        """Test market phase determination."""
        sector_performances = [sample_sector_performance]
        
        phase = sector_analyzer._determine_market_phase(sector_performances)
        
        assert phase in [p for p in RotationPhase]

    def test_determine_volatility_regime(self, sector_analyzer, sample_sector_performance):
        """Test volatility regime determination."""
        sector_performances = [sample_sector_performance]
        
        regime = sector_analyzer._determine_volatility_regime(sector_performances)
        
        assert regime in ["low", "normal", "elevated", "high"]

    @pytest.mark.asyncio
    async def test_identify_rotation_signals(self, sector_analyzer, sample_sector_performance):
        """Test rotation signal identification."""
        # Create multiple sector performances with different momentum scores
        sector_performances = [
            sample_sector_performance,
            SectorPerformance(
                sector=SectorCategory.ENERGY,
                performance_1d=Decimal("-0.5"),
                performance_1w=Decimal("-1.0"),
                performance_1m=Decimal("-2.0"),
                performance_3m=Decimal("-5.0"),
                performance_6m=Decimal("-8.0"),
                performance_1y=Decimal("-10.0"),
                performance_ytd=Decimal("-6.0"),
                relative_performance_1m=Decimal("-1.0"),
                relative_performance_3m=Decimal("-2.0"),
                relative_performance_1y=Decimal("-3.0"),
                trend_direction=TrendDirection.DOWN,
                trend_strength=30,
                momentum_score=25,  # Low momentum
                market_cap=500000000000,
                avg_volume=500000000,
                pe_ratio=Decimal("15.0"),
                pb_ratio=Decimal("2.0"),
                performance_rank_1m=10,
                performance_rank_3m=10,
                performance_rank_1y=10,
                volatility=Decimal("30.0"),
                beta=Decimal("1.5"),
                dividend_yield=Decimal("4.0")
            )
        ]
        
        signals = await sector_analyzer._identify_rotation_signals(sector_performances)
        
        assert isinstance(signals, list)
        # Should identify rotation from low momentum to high momentum sector
        if signals:
            signal = signals[0]
            assert isinstance(signal, SectorRotationSignal)
            assert signal.from_sector in [s.sector for s in sector_performances]
            assert signal.to_sector in [s.sector for s in sector_performances]
            assert 0 <= signal.signal_strength <= 100
            assert 0 <= signal.confidence <= 100

    def test_generate_comparison_insights(self, sector_analyzer):
        """Test comparison insights generation."""
        sector_performances = {
            SectorCategory.TECHNOLOGY: SectorPerformance(
                sector=SectorCategory.TECHNOLOGY,
                performance_1d=Decimal("1.0"),
                performance_1w=Decimal("2.0"),
                performance_1m=Decimal("5.0"),
                performance_3m=Decimal("10.0"),
                performance_6m=Decimal("15.0"),
                performance_1y=Decimal("20.0"),
                performance_ytd=Decimal("12.0"),
                relative_performance_1m=Decimal("1.0"),
                relative_performance_3m=Decimal("2.0"),
                relative_performance_1y=Decimal("3.0"),
                trend_direction=TrendDirection.UP,
                trend_strength=70,
                momentum_score=75,
                market_cap=1000000000000,
                avg_volume=1000000000,
                pe_ratio=Decimal("25.0"),
                pb_ratio=Decimal("3.0"),
                performance_rank_1m=1,
                performance_rank_3m=1,
                performance_rank_1y=1,
                volatility=Decimal("20.0"),
                beta=Decimal("1.0"),
                dividend_yield=Decimal("2.0")
            )
        }
        
        insights = sector_analyzer._generate_comparison_insights(sector_performances, "3m")
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        for insight in insights:
            assert isinstance(insight, str)
            assert len(insight) > 0

    def test_generate_comparison_recommendations(self, sector_analyzer):
        """Test comparison recommendations generation."""
        sector_performances = {}
        performance_ranking = [{'sector': SectorCategory.TECHNOLOGY}]
        valuation_ranking = [{'sector': SectorCategory.HEALTHCARE}]
        
        recommendations = sector_analyzer._generate_comparison_recommendations(
            sector_performances, performance_ranking, valuation_ranking
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        for recommendation in recommendations:
            assert isinstance(recommendation, str)
            assert len(recommendation) > 0