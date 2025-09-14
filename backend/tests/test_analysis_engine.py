"""
Tests for the Analysis Engine.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timedelta

from backend.app.services.analysis_engine import AnalysisEngine, AnalysisEngineException
from backend.app.services.fundamental_analyzer import FundamentalAnalyzer
from backend.app.services.technical_analyzer import TechnicalAnalyzer
from backend.app.services.data_aggregation import DataAggregationService
from backend.app.models.analysis import (
    AnalysisResult, AnalysisType, Recommendation, RiskLevel, 
    PriceTarget, CombinedAnalysis
)
from backend.app.models.fundamental import FundamentalData
from backend.app.models.technical import (
    TechnicalData, TimeFrame, TrendDirection, SignalStrength,
    SupportResistanceLevel
)
from backend.app.models.stock import MarketData


class TestAnalysisEngine:
    """Test cases for the AnalysisEngine class."""
    
    @pytest.fixture
    def mock_data_service(self):
        """Mock data aggregation service."""
        service = Mock(spec=DataAggregationService)
        service.get_market_data = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_fundamental_analyzer(self):
        """Mock fundamental analyzer."""
        analyzer = Mock(spec=FundamentalAnalyzer)
        analyzer.analyze_fundamentals = AsyncMock()
        return analyzer
    
    @pytest.fixture
    def mock_technical_analyzer(self):
        """Mock technical analyzer."""
        analyzer = Mock(spec=TechnicalAnalyzer)
        analyzer.analyze_technical = AsyncMock()
        return analyzer
    
    @pytest.fixture
    def analysis_engine(self, mock_data_service, mock_fundamental_analyzer, mock_technical_analyzer):
        """Create analysis engine with mocked dependencies."""
        return AnalysisEngine(
            fundamental_analyzer=mock_fundamental_analyzer,
            technical_analyzer=mock_technical_analyzer,
            data_service=mock_data_service
        )
    
    @pytest.fixture
    def sample_market_data(self):
        """Sample market data for testing."""
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
            pe_ratio=Decimal("25.5")
        )
    
    @pytest.fixture
    def sample_fundamental_data(self):
        """Sample fundamental data for testing."""
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
    def sample_technical_data(self):
        """Sample technical data for testing."""
        return TechnicalData(
            symbol="AAPL",
            timeframe=TimeFrame.ONE_DAY,
            sma_20=Decimal("148.50"),
            sma_50=Decimal("145.20"),
            sma_200=Decimal("140.80"),
            ema_12=Decimal("149.10"),
            ema_26=Decimal("147.30"),
            rsi=Decimal("65.5"),
            macd=Decimal("1.25"),
            macd_signal=Decimal("0.85"),
            macd_histogram=Decimal("0.40"),
            bollinger_upper=Decimal("152.00"),
            bollinger_lower=Decimal("144.00"),
            bollinger_middle=Decimal("148.00"),
            volume_sma=75000000,
            obv=1250000000,
            atr=Decimal("2.45"),
            support_levels=[
                SupportResistanceLevel(
                    level=Decimal("145.00"),
                    strength=8,
                    type="support",
                    touches=3,
                    last_touch=datetime.now() - timedelta(days=5)
                )
            ],
            resistance_levels=[
                SupportResistanceLevel(
                    level=Decimal("155.00"),
                    strength=7,
                    type="resistance",
                    touches=2,
                    last_touch=datetime.now() - timedelta(days=2)
                )
            ],
            trend_direction=TrendDirection.BULLISH,
            overall_signal=SignalStrength.BUY,
            data_points=252
        )


class TestAnalysisEngineBasicFunctionality(TestAnalysisEngine):
    """Test basic functionality of the analysis engine."""
    
    @pytest.mark.asyncio
    async def test_analyze_stock_success(
        self, 
        analysis_engine, 
        mock_data_service,
        mock_fundamental_analyzer,
        mock_technical_analyzer,
        sample_market_data,
        sample_fundamental_data,
        sample_technical_data
    ):
        """Test successful stock analysis with both fundamental and technical data."""
        # Setup mocks
        mock_data_service.get_market_data.return_value = sample_market_data
        mock_fundamental_analyzer.analyze_fundamentals.return_value = sample_fundamental_data
        mock_technical_analyzer.analyze_technical.return_value = sample_technical_data
        
        # Perform analysis
        result = await analysis_engine.analyze_stock("AAPL")
        
        # Verify result
        assert isinstance(result, AnalysisResult)
        assert result.symbol == "AAPL"
        assert result.analysis_type == AnalysisType.COMBINED
        assert result.recommendation in [r for r in Recommendation]
        assert 0 <= result.confidence <= 100
        assert 0 <= result.overall_score <= 100
        assert result.fundamental_score is not None
        assert result.technical_score is not None
        assert len(result.strengths) > 0
        assert len(result.risks) > 0
        assert result.risk_level in [r for r in RiskLevel]
        assert result.fundamental_data == sample_fundamental_data
        assert result.technical_data == sample_technical_data
        
        # Verify mocks were called
        mock_data_service.get_market_data.assert_called_once_with("AAPL")
        mock_fundamental_analyzer.analyze_fundamentals.assert_called_once_with("AAPL")
        mock_technical_analyzer.analyze_technical.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_stock_fundamental_only(
        self,
        analysis_engine,
        mock_data_service,
        mock_fundamental_analyzer,
        mock_technical_analyzer,
        sample_market_data,
        sample_fundamental_data
    ):
        """Test analysis with only fundamental data available."""
        # Setup mocks
        mock_data_service.get_market_data.return_value = sample_market_data
        mock_fundamental_analyzer.analyze_fundamentals.return_value = sample_fundamental_data
        mock_technical_analyzer.analyze_technical.return_value = None
        
        # Perform analysis
        result = await analysis_engine.analyze_stock("AAPL", include_technical=False)
        
        # Verify result
        assert isinstance(result, AnalysisResult)
        assert result.symbol == "AAPL"
        assert result.fundamental_score is not None
        assert result.technical_score is None
        assert result.fundamental_data == sample_fundamental_data
        assert result.technical_data is None
    
    @pytest.mark.asyncio
    async def test_analyze_stock_technical_only(
        self,
        analysis_engine,
        mock_data_service,
        mock_fundamental_analyzer,
        mock_technical_analyzer,
        sample_market_data,
        sample_technical_data
    ):
        """Test analysis with only technical data available."""
        # Setup mocks
        mock_data_service.get_market_data.return_value = sample_market_data
        mock_fundamental_analyzer.analyze_fundamentals.return_value = None
        mock_technical_analyzer.analyze_technical.return_value = sample_technical_data
        
        # Perform analysis
        result = await analysis_engine.analyze_stock("AAPL", include_fundamental=False)
        
        # Verify result
        assert isinstance(result, AnalysisResult)
        assert result.symbol == "AAPL"
        assert result.fundamental_score is None
        assert result.technical_score is not None
        assert result.fundamental_data is None
        assert result.technical_data == sample_technical_data
    
    @pytest.mark.asyncio
    async def test_analyze_stock_no_data_available(
        self,
        analysis_engine,
        mock_data_service,
        mock_fundamental_analyzer,
        mock_technical_analyzer
    ):
        """Test analysis when no data is available."""
        # Setup mocks to return None
        mock_data_service.get_market_data.return_value = None
        mock_fundamental_analyzer.analyze_fundamentals.return_value = None
        mock_technical_analyzer.analyze_technical.return_value = None
        
        # Expect exception
        with pytest.raises(AnalysisEngineException) as exc_info:
            await analysis_engine.analyze_stock("INVALID")
        
        assert exc_info.value.error_type == "NO_DATA"
        assert "No analysis data available" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_analyze_stock_invalid_symbol(
        self,
        analysis_engine,
        mock_data_service,
        mock_fundamental_analyzer,
        mock_technical_analyzer
    ):
        """Test analysis with invalid symbol."""
        # Setup mocks to raise exceptions
        mock_data_service.get_market_data.side_effect = Exception("Invalid symbol")
        mock_fundamental_analyzer.analyze_fundamentals.side_effect = Exception("Invalid symbol")
        mock_technical_analyzer.analyze_technical.side_effect = Exception("Invalid symbol")
        
        # Expect exception
        with pytest.raises(AnalysisEngineException):
            await analysis_engine.analyze_stock("INVALID")


class TestRecommendationGeneration(TestAnalysisEngine):
    """Test recommendation generation logic."""
    
    def test_score_to_recommendation_mapping(self, analysis_engine):
        """Test score to recommendation mapping."""
        # Test all recommendation thresholds
        assert analysis_engine._score_to_recommendation(90) == Recommendation.STRONG_BUY
        assert analysis_engine._score_to_recommendation(85) == Recommendation.STRONG_BUY
        assert analysis_engine._score_to_recommendation(75) == Recommendation.BUY
        assert analysis_engine._score_to_recommendation(70) == Recommendation.BUY
        assert analysis_engine._score_to_recommendation(55) == Recommendation.HOLD
        assert analysis_engine._score_to_recommendation(45) == Recommendation.HOLD
        assert analysis_engine._score_to_recommendation(35) == Recommendation.SELL
        assert analysis_engine._score_to_recommendation(30) == Recommendation.SELL
        assert analysis_engine._score_to_recommendation(15) == Recommendation.STRONG_SELL
        assert analysis_engine._score_to_recommendation(0) == Recommendation.STRONG_SELL
    
    def test_calculate_combined_score(self, analysis_engine, sample_fundamental_data, sample_technical_data):
        """Test combined score calculation."""
        # Create combined analysis with both fundamental and technical data
        combined = CombinedAnalysis(
            symbol="AAPL",
            fundamental_analysis=sample_fundamental_data,
            technical_analysis=sample_technical_data,
            market_data={"price": 150.00}
        )
        
        score = analysis_engine._calculate_combined_score(combined)
        
        # Score should be between 0 and 100
        assert 0 <= score <= 100
        assert isinstance(score, int)
    
    def test_calculate_confidence_with_aligned_signals(self, analysis_engine):
        """Test confidence calculation with aligned signals."""
        combined = CombinedAnalysis(
            symbol="AAPL",
            fundamental_signal="buy",
            technical_signal=SignalStrength.BUY,
            signals_aligned=True
        )
        
        confidence = analysis_engine._calculate_confidence(combined)
        
        # Should have higher confidence with aligned signals
        assert confidence >= 60  # Base + alignment bonus
        assert 0 <= confidence <= 100
    
    def test_calculate_confidence_with_misaligned_signals(self, analysis_engine):
        """Test confidence calculation with misaligned signals."""
        combined = CombinedAnalysis(
            symbol="AAPL",
            fundamental_signal="buy",
            technical_signal=SignalStrength.SELL,
            signals_aligned=False
        )
        
        confidence = analysis_engine._calculate_confidence(combined)
        
        # Should have lower confidence with misaligned signals
        assert confidence <= 50  # Base - misalignment penalty
        assert 0 <= confidence <= 100


class TestPriceTargetGeneration(TestAnalysisEngine):
    """Test price target generation."""
    
    @pytest.mark.asyncio
    async def test_generate_price_targets(
        self,
        analysis_engine,
        sample_fundamental_data,
        sample_technical_data
    ):
        """Test price target generation with both analyses."""
        combined = CombinedAnalysis(
            symbol="AAPL",
            fundamental_analysis=sample_fundamental_data,
            technical_analysis=sample_technical_data
        )
        
        current_price = Decimal("150.00")
        targets = await analysis_engine.generate_price_targets("AAPL", combined, current_price)
        
        # Should generate multiple targets
        assert len(targets) > 0
        
        for target in targets:
            assert isinstance(target, PriceTarget)
            assert target.target > 0
            assert 0 <= target.confidence <= 100
            assert target.timeframe in ['3M', '6M', '1Y']
            assert len(target.rationale) > 0
    
    def test_calculate_technical_target(self, analysis_engine, sample_technical_data):
        """Test technical-based price target calculation."""
        current_price = Decimal("150.00")
        target = analysis_engine._calculate_technical_target(
            current_price, 
            sample_technical_data, 
            "3M"
        )
        
        assert target is not None
        assert isinstance(target, PriceTarget)
        assert target.target > 0
        assert target.timeframe == "3M"
        assert 30 <= target.confidence <= 90
    
    def test_calculate_fundamental_target(self, analysis_engine, sample_fundamental_data):
        """Test fundamental-based price target calculation."""
        current_price = Decimal("150.00")
        target = analysis_engine._calculate_fundamental_target(
            current_price,
            sample_fundamental_data,
            "1Y"
        )
        
        assert target is not None
        assert isinstance(target, PriceTarget)
        assert target.target > 0
        assert target.timeframe == "1Y"
        assert 30 <= target.confidence <= 90


class TestRiskAssessment(TestAnalysisEngine):
    """Test risk assessment functionality."""
    
    @pytest.mark.asyncio
    async def test_assess_risk_level_low_risk(
        self,
        analysis_engine,
        sample_market_data
    ):
        """Test risk assessment for low-risk stock."""
        # Create low-risk fundamental data
        low_risk_fundamental = FundamentalData(
            symbol="AAPL",
            pe_ratio=Decimal("15.0"),  # Reasonable P/E
            debt_to_equity=Decimal("0.20"),  # Low debt
            profit_margin=Decimal("0.25"),  # High margins
            free_cash_flow=1000000000,  # Positive cash flow
            quarter="Q4",
            year=2024
        )
        
        # Create low-risk technical data
        low_risk_technical = TechnicalData(
            symbol="AAPL",
            timeframe=TimeFrame.ONE_DAY,
            trend_direction=TrendDirection.BULLISH,
            rsi=Decimal("55.0"),  # Neutral RSI
            atr=Decimal("1.50")  # Low volatility
        )
        
        combined = CombinedAnalysis(
            symbol="AAPL",
            fundamental_analysis=low_risk_fundamental,
            technical_analysis=low_risk_technical
        )
        
        risk_level, risk_factors = await analysis_engine.assess_risk_level(
            "AAPL", 
            combined, 
            sample_market_data
        )
        
        assert risk_level in [RiskLevel.LOW, RiskLevel.MODERATE]
        assert isinstance(risk_factors, dict)
        assert 'overall_risk_score' in risk_factors
    
    @pytest.mark.asyncio
    async def test_assess_risk_level_high_risk(
        self,
        analysis_engine,
        sample_market_data
    ):
        """Test risk assessment for high-risk stock."""
        # Create high-risk fundamental data
        high_risk_fundamental = FundamentalData(
            symbol="RISKY",
            pe_ratio=Decimal("50.0"),  # High P/E
            debt_to_equity=Decimal("2.0"),  # High debt
            profit_margin=Decimal("-0.05"),  # Negative margins
            free_cash_flow=-500000000,  # Negative cash flow
            quarter="Q4",
            year=2024
        )
        
        # Create high-risk technical data
        high_risk_technical = TechnicalData(
            symbol="RISKY",
            timeframe=TimeFrame.ONE_DAY,
            trend_direction=TrendDirection.BEARISH,
            rsi=Decimal("85.0"),  # Overbought
            atr=Decimal("8.00")  # High volatility
        )
        
        combined = CombinedAnalysis(
            symbol="RISKY",
            fundamental_analysis=high_risk_fundamental,
            technical_analysis=high_risk_technical
        )
        
        risk_level, risk_factors = await analysis_engine.assess_risk_level(
            "RISKY", 
            combined, 
            sample_market_data
        )
        
        assert risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        assert isinstance(risk_factors, dict)
        assert risk_factors['overall_risk_score'] > 50


class TestStrengthsWeaknessesAnalysis(TestAnalysisEngine):
    """Test strengths and weaknesses analysis."""
    
    def test_analyze_strengths_weaknesses_strong_fundamentals(
        self,
        analysis_engine,
        sample_fundamental_data
    ):
        """Test analysis with strong fundamental data."""
        combined = CombinedAnalysis(
            symbol="AAPL",
            fundamental_analysis=sample_fundamental_data
        )
        
        strengths, weaknesses = analysis_engine._analyze_strengths_weaknesses(combined)
        
        assert len(strengths) > 0
        assert any("return on equity" in s.lower() for s in strengths)
        assert any("debt" in s.lower() for s in strengths)
    
    def test_analyze_strengths_weaknesses_weak_fundamentals(self, analysis_engine):
        """Test analysis with weak fundamental data."""
        weak_fundamental = FundamentalData(
            symbol="WEAK",
            pe_ratio=Decimal("45.0"),  # High P/E
            roe=Decimal("0.03"),  # Low ROE
            debt_to_equity=Decimal("1.5"),  # High debt
            profit_margin=Decimal("0.01"),  # Low margins
            revenue_growth=Decimal("-0.10"),  # Declining revenue
            quarter="Q4",
            year=2024
        )
        
        combined = CombinedAnalysis(
            symbol="WEAK",
            fundamental_analysis=weak_fundamental
        )
        
        strengths, weaknesses = analysis_engine._analyze_strengths_weaknesses(combined)
        
        assert len(weaknesses) > 0
        assert any("debt" in w.lower() for w in weaknesses)
        assert any("revenue" in w.lower() for w in weaknesses)
    
    def test_analyze_strengths_weaknesses_technical_bullish(
        self,
        analysis_engine,
        sample_technical_data
    ):
        """Test analysis with bullish technical data."""
        combined = CombinedAnalysis(
            symbol="AAPL",
            technical_analysis=sample_technical_data,
            market_data={"price": 150.00}
        )
        
        strengths, weaknesses = analysis_engine._analyze_strengths_weaknesses(combined)
        
        assert len(strengths) > 0
        assert any("bullish" in s.lower() for s in strengths)


class TestRisksOpportunitiesAnalysis(TestAnalysisEngine):
    """Test risks and opportunities analysis."""
    
    def test_analyze_risks_opportunities_basic(self, analysis_engine):
        """Test basic risks and opportunities analysis."""
        combined = CombinedAnalysis(symbol="AAPL")
        
        risks, opportunities = analysis_engine._analyze_risks_opportunities(combined)
        
        # Should always include basic market risks
        assert len(risks) > 0
        assert any("market volatility" in r.lower() for r in risks)
        assert any("interest rate" in r.lower() for r in risks)
    
    def test_analyze_risks_opportunities_with_data(
        self,
        analysis_engine,
        sample_fundamental_data,
        sample_technical_data
    ):
        """Test risks and opportunities with actual data."""
        combined = CombinedAnalysis(
            symbol="AAPL",
            fundamental_analysis=sample_fundamental_data,
            technical_analysis=sample_technical_data
        )
        
        risks, opportunities = analysis_engine._analyze_risks_opportunities(combined)
        
        assert len(risks) > 0
        assert len(opportunities) > 0
        
        # Should include growth opportunities from strong revenue growth
        assert any("revenue growth" in o.lower() for o in opportunities)
        
        # Should include cash generation opportunity
        assert any("cash generation" in o.lower() for o in opportunities)


class TestEdgeCases(TestAnalysisEngine):
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_analyze_stock_with_partial_data_failure(
        self,
        analysis_engine,
        mock_data_service,
        mock_fundamental_analyzer,
        mock_technical_analyzer,
        sample_market_data,
        sample_fundamental_data
    ):
        """Test analysis when some data sources fail."""
        # Setup mocks - fundamental succeeds, technical fails
        mock_data_service.get_market_data.return_value = sample_market_data
        mock_fundamental_analyzer.analyze_fundamentals.return_value = sample_fundamental_data
        mock_technical_analyzer.analyze_technical.side_effect = Exception("Technical analysis failed")
        
        # Should still succeed with partial data
        result = await analysis_engine.analyze_stock("AAPL")
        
        assert isinstance(result, AnalysisResult)
        assert result.fundamental_data is not None
        assert result.technical_data is None
    
    def test_calculate_combined_score_no_data(self, analysis_engine):
        """Test combined score calculation with no data."""
        combined = CombinedAnalysis(symbol="AAPL")
        
        score = analysis_engine._calculate_combined_score(combined)
        
        # Should return neutral score
        assert score == 50
    
    @pytest.mark.asyncio
    async def test_generate_price_targets_no_data(self, analysis_engine):
        """Test price target generation with no data."""
        combined = CombinedAnalysis(symbol="AAPL")
        current_price = Decimal("150.00")
        
        targets = await analysis_engine.generate_price_targets("AAPL", combined, current_price)
        
        # Should return empty list
        assert targets == []
    
    def test_calculate_technical_target_no_resistance(self, analysis_engine):
        """Test technical target calculation with no resistance levels."""
        tech_data = TechnicalData(
            symbol="AAPL",
            timeframe=TimeFrame.ONE_DAY,
            trend_direction=TrendDirection.BULLISH,
            resistance_levels=[]  # No resistance levels
        )
        
        current_price = Decimal("150.00")
        target = analysis_engine._calculate_technical_target(current_price, tech_data, "3M")
        
        # Should still generate a target based on trend
        assert target is not None
        assert target.target > current_price  # Should be higher due to bullish trend


if __name__ == "__main__":
    pytest.main([__file__])