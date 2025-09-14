"""
Tests for Risk Assessment Service.

This module contains comprehensive tests for the risk assessment functionality
including individual stock risk analysis, portfolio risk assessment,
correlation analysis, and scenario modeling.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
from datetime import datetime, timedelta

from app.services.risk_assessment import (
    RiskAssessmentService, RiskAssessmentException, MarketCondition,
    RiskCategory, RiskMetric, CorrelationData, ScenarioResult, PortfolioRisk
)
from app.models.analysis import RiskLevel
from app.models.stock import MarketData
from app.models.fundamental import FundamentalData
from app.models.technical import TechnicalData, TrendDirection, TimeFrame


class TestRiskAssessmentService:
    """Test cases for RiskAssessmentService."""
    
    @pytest.fixture
    def risk_service(self):
        """Create a RiskAssessmentService instance for testing."""
        mock_data_service = Mock()
        return RiskAssessmentService(data_service=mock_data_service)
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        return MarketData(
            symbol="AAPL",
            price=Decimal("150.00"),
            change=Decimal("2.50"),
            change_percent=Decimal("0.017"),
            volume=75000000,
            high_52_week=Decimal("180.00"),
            low_52_week=Decimal("120.00"),
            avg_volume=80000000,
            market_cap=2500000000000,
            pe_ratio=Decimal("25.5"),
            timestamp=datetime.now()
        )
    
    @pytest.fixture
    def sample_fundamental_data(self):
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
    def sample_technical_data(self):
        """Create sample technical data for testing."""
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
            support_levels=[],
            resistance_levels=[],
            trend_direction=TrendDirection.BULLISH,
            timestamp=datetime.now(),
            data_points=252
        )

    @pytest.mark.asyncio
    async def test_assess_stock_risk_basic(self, risk_service, sample_market_data):
        """Test basic stock risk assessment."""
        # Mock data service
        risk_service.data_service.get_market_data = AsyncMock(return_value=sample_market_data)
        
        # Mock internal methods
        risk_service._calculate_risk_metrics = AsyncMock(return_value=[
            RiskMetric(
                name="Volatility Risk",
                value=0.25,
                risk_level=RiskLevel.MODERATE,
                description="Moderate volatility risk",
                impact="Medium",
                mitigation="Consider position sizing"
            )
        ])
        risk_service._analyze_correlations = AsyncMock(return_value=None)
        risk_service._perform_scenario_analysis = AsyncMock(return_value=None)
        
        # Test assessment
        result = await risk_service.assess_stock_risk("AAPL", include_correlation=False, include_scenarios=False)
        
        assert result['symbol'] == 'AAPL'
        assert result['overall_risk_level'] in ['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']
        assert 'risk_score' in result
        assert 'risk_metrics' in result
        assert 'risk_warnings' in result
        assert 'mitigation_suggestions' in result
        assert 'assessment_timestamp' in result

    @pytest.mark.asyncio
    async def test_assess_stock_risk_with_all_data(self, risk_service, sample_market_data, 
                                                  sample_fundamental_data, sample_technical_data):
        """Test stock risk assessment with all data types."""
        # Mock data service
        risk_service.data_service.get_market_data = AsyncMock(return_value=sample_market_data)
        
        # Test assessment with all data
        result = await risk_service.assess_stock_risk(
            "AAPL", 
            market_data=sample_market_data,
            fundamental_data=sample_fundamental_data,
            technical_data=sample_technical_data,
            include_correlation=True,
            include_scenarios=True
        )
        
        assert result['symbol'] == 'AAPL'
        assert len(result['risk_metrics']) > 0
        assert result['correlation_data'] is not None
        assert result['scenario_analysis'] is not None

    @pytest.mark.asyncio
    async def test_assess_portfolio_risk(self, risk_service):
        """Test portfolio risk assessment."""
        positions = [
            {'symbol': 'AAPL', 'quantity': 100, 'value': 15000, 'sector': 'Technology'},
            {'symbol': 'GOOGL', 'quantity': 50, 'value': 12000, 'sector': 'Technology'},
            {'symbol': 'JNJ', 'quantity': 75, 'value': 10000, 'sector': 'Healthcare'}
        ]
        
        # Mock individual stock assessments
        mock_assessment = {
            'overall_risk_level': 'MODERATE',
            'risk_score': 50,
            'risk_metrics': [],
            'correlation_data': None,
            'scenario_analysis': None,
            'risk_warnings': [],
            'mitigation_suggestions': [],
            'assessment_timestamp': datetime.now().isoformat()
        }
        
        risk_service.assess_stock_risk = AsyncMock(return_value=mock_assessment)
        
        # Test portfolio assessment
        result = await risk_service.assess_portfolio_risk(positions)
        
        assert isinstance(result, PortfolioRisk)
        assert result.total_value == Decimal('37000')
        assert len(result.positions) == 3
        assert result.overall_risk_level in ['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']
        assert 0 <= result.diversification_score <= 100
        assert 0 <= result.concentration_risk <= 1
        assert 0 <= result.correlation_risk <= 1

    def test_calculate_volatility_risk_low(self, risk_service, sample_market_data, sample_technical_data):
        """Test volatility risk calculation for low volatility."""
        sample_technical_data.atr = Decimal("1.50")  # Low ATR
        
        result = asyncio.run(risk_service._calculate_volatility_risk(
            "AAPL", sample_market_data, sample_technical_data
        ))
        
        assert result is not None
        assert result.name == "Volatility Risk"
        assert result.risk_level == RiskLevel.LOW
        assert result.value < 0.15  # Low volatility threshold

    def test_calculate_volatility_risk_high(self, risk_service, sample_market_data, sample_technical_data):
        """Test volatility risk calculation for high volatility."""
        sample_technical_data.atr = Decimal("6.00")  # High ATR
        
        result = asyncio.run(risk_service._calculate_volatility_risk(
            "AAPL", sample_market_data, sample_technical_data
        ))
        
        assert result is not None
        assert result.name == "Volatility Risk"
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        assert result.value > 0.25  # High volatility threshold

    def test_calculate_liquidity_risk_high_volume(self, risk_service, sample_market_data):
        """Test liquidity risk calculation for high volume stock."""
        sample_market_data.avg_volume = 50000000  # High volume
        
        result = risk_service._calculate_liquidity_risk(sample_market_data)
        
        assert result is not None
        assert result.name == "Liquidity Risk"
        assert result.risk_level == RiskLevel.LOW
        assert result.value == 50000000

    def test_calculate_liquidity_risk_low_volume(self, risk_service, sample_market_data):
        """Test liquidity risk calculation for low volume stock."""
        sample_market_data.avg_volume = 50000  # Low volume
        
        result = risk_service._calculate_liquidity_risk(sample_market_data)
        
        assert result is not None
        assert result.name == "Liquidity Risk"
        assert result.risk_level == RiskLevel.VERY_HIGH
        assert result.value == 50000

    def test_calculate_fundamental_risks_healthy(self, risk_service, sample_fundamental_data):
        """Test fundamental risk calculation for healthy company."""
        # Set healthy fundamental metrics
        sample_fundamental_data.debt_to_equity = Decimal("0.25")  # Low debt
        sample_fundamental_data.profit_margin = Decimal("0.20")   # High margin
        sample_fundamental_data.free_cash_flow = 50000000000      # Positive FCF
        
        results = risk_service._calculate_fundamental_risks(sample_fundamental_data)
        
        assert len(results) >= 3  # Should have debt, profitability, and cash flow risks
        
        # Check debt risk is low
        debt_risk = next((r for r in results if r.name == "Debt Risk"), None)
        assert debt_risk is not None
        assert debt_risk.risk_level == RiskLevel.LOW
        
        # Check profitability risk is low
        profit_risk = next((r for r in results if r.name == "Profitability Risk"), None)
        assert profit_risk is not None
        assert profit_risk.risk_level == RiskLevel.LOW
        
        # Check cash flow risk is low
        cf_risk = next((r for r in results if r.name == "Cash Flow Risk"), None)
        assert cf_risk is not None
        assert cf_risk.risk_level == RiskLevel.LOW

    def test_calculate_fundamental_risks_unhealthy(self, risk_service, sample_fundamental_data):
        """Test fundamental risk calculation for unhealthy company."""
        # Set unhealthy fundamental metrics
        sample_fundamental_data.debt_to_equity = Decimal("2.50")   # High debt
        sample_fundamental_data.profit_margin = Decimal("-0.05")   # Negative margin
        sample_fundamental_data.free_cash_flow = -10000000000      # Negative FCF
        
        results = risk_service._calculate_fundamental_risks(sample_fundamental_data)
        
        assert len(results) >= 3
        
        # Check debt risk is high
        debt_risk = next((r for r in results if r.name == "Debt Risk"), None)
        assert debt_risk is not None
        assert debt_risk.risk_level == RiskLevel.VERY_HIGH
        
        # Check profitability risk is high
        profit_risk = next((r for r in results if r.name == "Profitability Risk"), None)
        assert profit_risk is not None
        assert profit_risk.risk_level == RiskLevel.VERY_HIGH
        
        # Check cash flow risk is high
        cf_risk = next((r for r in results if r.name == "Cash Flow Risk"), None)
        assert cf_risk is not None
        assert cf_risk.risk_level == RiskLevel.HIGH

    def test_calculate_technical_risks_normal_rsi(self, risk_service, sample_technical_data, sample_market_data):
        """Test technical risk calculation with normal RSI."""
        sample_technical_data.rsi = Decimal("50.0")  # Normal RSI
        
        results = risk_service._calculate_technical_risks(sample_technical_data, sample_market_data)
        
        momentum_risk = next((r for r in results if r.name == "Momentum Risk"), None)
        assert momentum_risk is not None
        assert momentum_risk.risk_level == RiskLevel.LOW

    def test_calculate_technical_risks_extreme_rsi(self, risk_service, sample_technical_data, sample_market_data):
        """Test technical risk calculation with extreme RSI."""
        sample_technical_data.rsi = Decimal("85.0")  # Overbought RSI
        
        results = risk_service._calculate_technical_risks(sample_technical_data, sample_market_data)
        
        momentum_risk = next((r for r in results if r.name == "Momentum Risk"), None)
        assert momentum_risk is not None
        assert momentum_risk.risk_level == RiskLevel.HIGH

    def test_calculate_position_risk_near_high(self, risk_service, sample_market_data):
        """Test position risk calculation when near 52-week high."""
        sample_market_data.price = Decimal("178.00")  # Near 52-week high of 180
        
        result = risk_service._calculate_position_risk(sample_market_data)
        
        assert result is not None
        assert result.name == "52-Week Position Risk"
        assert result.risk_level == RiskLevel.MODERATE
        assert result.value > 0.9  # Should be > 90% of range

    def test_calculate_position_risk_near_low(self, risk_service, sample_market_data):
        """Test position risk calculation when near 52-week low."""
        sample_market_data.price = Decimal("122.00")  # Near 52-week low of 120
        
        result = risk_service._calculate_position_risk(sample_market_data)
        
        assert result is not None
        assert result.name == "52-Week Position Risk"
        assert result.risk_level == RiskLevel.HIGH
        assert result.value < 0.1  # Should be < 10% of range

    def test_determine_overall_risk_level_low(self, risk_service):
        """Test overall risk level determination for low risk metrics."""
        metrics = [
            RiskMetric("Test1", 0.1, RiskLevel.LOW, "Low risk", "Low", "Mitigation"),
            RiskMetric("Test2", 0.2, RiskLevel.LOW, "Low risk", "Low", "Mitigation")
        ]
        
        result = risk_service._determine_overall_risk_level(metrics)
        assert result == RiskLevel.LOW

    def test_determine_overall_risk_level_high(self, risk_service):
        """Test overall risk level determination for high risk metrics."""
        metrics = [
            RiskMetric("Test1", 0.8, RiskLevel.HIGH, "High risk", "High", "Mitigation"),
            RiskMetric("Test2", 0.9, RiskLevel.HIGH, "High risk", "High", "Mitigation")
        ]
        
        result = risk_service._determine_overall_risk_level(metrics)
        assert result == RiskLevel.VERY_HIGH  # Multiple high risks

    def test_determine_overall_risk_level_very_high(self, risk_service):
        """Test overall risk level determination for very high risk metrics."""
        metrics = [
            RiskMetric("Test1", 0.95, RiskLevel.VERY_HIGH, "Very high risk", "High", "Mitigation")
        ]
        
        result = risk_service._determine_overall_risk_level(metrics)
        assert result == RiskLevel.VERY_HIGH

    def test_calculate_risk_score(self, risk_service):
        """Test risk score calculation."""
        metrics = [
            RiskMetric("Test1", 0.3, RiskLevel.MODERATE, "Moderate risk", "Medium", "Mitigation"),
            RiskMetric("Test2", 0.7, RiskLevel.HIGH, "High risk", "High", "Mitigation")
        ]
        
        score = risk_service._calculate_risk_score(metrics)
        assert 0 <= score <= 100
        assert score > 40  # Should be above moderate due to high risk metric

    def test_generate_risk_warnings(self, risk_service):
        """Test risk warning generation."""
        metrics = [
            RiskMetric("High Risk Test", 0.8, RiskLevel.HIGH, "High risk description", "High", "Mitigation"),
            RiskMetric("Low Risk Test", 0.2, RiskLevel.LOW, "Low risk description", "Low", "Mitigation")
        ]
        
        warnings = risk_service._generate_risk_warnings(metrics, RiskLevel.HIGH)
        
        assert len(warnings) >= 2  # Overall warning + high risk metric warning
        assert any("HIGH RISK" in warning for warning in warnings)
        assert any("High Risk Test" in warning for warning in warnings)

    def test_generate_mitigation_suggestions(self, risk_service):
        """Test mitigation suggestion generation."""
        metrics = [
            RiskMetric("High Risk Test", 0.8, RiskLevel.HIGH, "High risk", "High", "Test mitigation"),
            RiskMetric("Low Risk Test", 0.2, RiskLevel.LOW, "Low risk", "Low", "Low mitigation")
        ]
        
        suggestions = risk_service._generate_mitigation_suggestions(metrics, RiskLevel.HIGH)
        
        assert len(suggestions) > 0
        assert any("position size" in suggestion.lower() for suggestion in suggestions)
        assert any("Test mitigation" in suggestion for suggestion in suggestions)

    def test_calculate_diversification_score_single_position(self, risk_service):
        """Test diversification score for single position."""
        positions = [{'weight': 1.0}]
        
        score = risk_service._calculate_diversification_score(positions)
        assert score == 0  # Single position should have 0 diversification

    def test_calculate_diversification_score_well_diversified(self, risk_service):
        """Test diversification score for well-diversified portfolio."""
        positions = [
            {'weight': 0.08} for _ in range(12)  # 12 positions, each ~8%
        ]
        
        score = risk_service._calculate_diversification_score(positions)
        assert score >= 80  # Should be well diversified

    def test_calculate_concentration_risk_concentrated(self, risk_service):
        """Test concentration risk for concentrated portfolio."""
        positions = [
            {'weight': 0.8},  # 80% in one position
            {'weight': 0.2}   # 20% in another
        ]
        
        risk = risk_service._calculate_concentration_risk(positions)
        assert risk > 0.6  # Should be high concentration risk

    def test_calculate_concentration_risk_diversified(self, risk_service):
        """Test concentration risk for diversified portfolio."""
        positions = [
            {'weight': 0.1} for _ in range(10)  # 10 equal positions
        ]
        
        risk = risk_service._calculate_concentration_risk(positions)
        assert risk < 0.2  # Should be low concentration risk

    @pytest.mark.asyncio
    async def test_analyze_correlations(self, risk_service):
        """Test correlation analysis."""
        result = await risk_service._analyze_correlations("AAPL")
        
        assert isinstance(result, CorrelationData)
        assert result.symbol == "AAPL"
        assert result.benchmark == "SPY"
        assert -1 <= result.correlation <= 1
        assert result.beta > 0
        assert 0 <= result.r_squared <= 1

    @pytest.mark.asyncio
    async def test_perform_scenario_analysis(self, risk_service, sample_market_data):
        """Test scenario analysis."""
        correlation_data = CorrelationData(
            symbol="AAPL",
            benchmark="SPY",
            correlation=0.75,
            beta=1.2,
            r_squared=0.56,
            period_days=252,
            last_updated=datetime.now()
        )
        
        results = await risk_service._perform_scenario_analysis("AAPL", sample_market_data, correlation_data)
        
        assert len(results) == len(MarketCondition)
        
        for result in results:
            assert isinstance(result, ScenarioResult)
            assert result.scenario in MarketCondition
            assert -1 <= result.expected_return <= 1  # Reasonable return range
            assert result.worst_case_return <= result.expected_return <= result.best_case_return
            assert 0 <= result.probability <= 1

    @pytest.mark.asyncio
    async def test_assess_stock_risk_invalid_symbol(self, risk_service):
        """Test stock risk assessment with invalid symbol."""
        risk_service.data_service.get_market_data = AsyncMock(side_effect=Exception("Invalid symbol"))
        
        with pytest.raises(RiskAssessmentException) as exc_info:
            await risk_service.assess_stock_risk("INVALID")
        
        assert exc_info.value.error_type == "ASSESSMENT_FAILED"
        assert "INVALID" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_assess_portfolio_risk_empty_portfolio(self, risk_service):
        """Test portfolio risk assessment with empty portfolio."""
        with pytest.raises(RiskAssessmentException) as exc_info:
            await risk_service.assess_portfolio_risk([])
        
        assert "empty" in exc_info.value.message.lower()

    def test_get_scenario_description(self, risk_service):
        """Test scenario description generation."""
        description = risk_service._get_scenario_description(MarketCondition.BULL_MARKET, 0.20)
        
        assert "bull market" in description.lower()
        assert "20.0%" in description

    @pytest.mark.asyncio
    async def test_calculate_historical_volatility(self, risk_service):
        """Test historical volatility calculation."""
        # This is a placeholder implementation, so we just test it returns a reasonable value
        volatility = await risk_service._calculate_historical_volatility("AAPL")
        
        assert volatility is not None
        assert 0 < volatility < 2  # Reasonable volatility range (0-200%)

    def test_determine_portfolio_risk_level_high_risk_positions(self, risk_service):
        """Test portfolio risk level determination with high-risk positions."""
        position_risks = [
            {
                'weight': 0.6,
                'risk_assessment': {'overall_risk_level': 'HIGH'}
            },
            {
                'weight': 0.4,
                'risk_assessment': {'overall_risk_level': 'MODERATE'}
            }
        ]
        
        result = risk_service._determine_portfolio_risk_level(position_risks, 0.3, 0.5)
        assert result == RiskLevel.HIGH  # High weight in high-risk position

    def test_determine_portfolio_risk_level_concentrated(self, risk_service):
        """Test portfolio risk level determination with high concentration."""
        position_risks = [
            {
                'weight': 0.5,
                'risk_assessment': {'overall_risk_level': 'LOW'}
            },
            {
                'weight': 0.5,
                'risk_assessment': {'overall_risk_level': 'LOW'}
            }
        ]
        
        result = risk_service._determine_portfolio_risk_level(position_risks, 0.9, 0.3)
        assert result == RiskLevel.VERY_HIGH  # High concentration risk

    def test_generate_portfolio_risk_metrics(self, risk_service):
        """Test portfolio risk metrics generation."""
        position_risks = []
        concentration_risk = 0.7
        correlation_risk = 0.6
        diversification_score = 40
        
        metrics = risk_service._generate_portfolio_risk_metrics(
            position_risks, concentration_risk, correlation_risk, diversification_score
        )
        
        assert len(metrics) == 3  # Concentration, correlation, and diversification
        
        # Check concentration risk metric
        concentration_metric = next((m for m in metrics if m.name == "Concentration Risk"), None)
        assert concentration_metric is not None
        assert concentration_metric.risk_level == RiskLevel.HIGH  # 0.7 is high
        
        # Check correlation risk metric
        correlation_metric = next((m for m in metrics if m.name == "Correlation Risk"), None)
        assert correlation_metric is not None
        assert correlation_metric.risk_level == RiskLevel.MODERATE  # 0.6 is moderate
        
        # Check diversification risk metric
        diversification_metric = next((m for m in metrics if m.name == "Diversification Risk"), None)
        assert diversification_metric is not None
        assert diversification_metric.risk_level == RiskLevel.MODERATE  # 40 score is moderate


class TestRiskAssessmentIntegration:
    """Integration tests for risk assessment functionality."""
    
    @pytest.mark.asyncio
    async def test_full_stock_assessment_workflow(self):
        """Test complete stock assessment workflow."""
        # This would be an integration test with real data services
        # For now, we'll test the workflow with mocked services
        
        mock_data_service = Mock()
        mock_data_service.get_market_data = AsyncMock(return_value=MarketData(
            symbol="AAPL",
            price=Decimal("150.00"),
            change=Decimal("2.50"),
            change_percent=Decimal("0.017"),
            volume=75000000,
            high_52_week=Decimal("180.00"),
            low_52_week=Decimal("120.00"),
            avg_volume=80000000,
            timestamp=datetime.now()
        ))
        
        risk_service = RiskAssessmentService(data_service=mock_data_service)
        
        # Test full assessment
        result = await risk_service.assess_stock_risk("AAPL")
        
        # Verify complete result structure
        required_keys = [
            'symbol', 'overall_risk_level', 'risk_score', 'risk_metrics',
            'correlation_data', 'scenario_analysis', 'risk_warnings',
            'mitigation_suggestions', 'assessment_timestamp', 'data_sources'
        ]
        
        for key in required_keys:
            assert key in result
        
        # Verify data types and ranges
        assert result['symbol'] == 'AAPL'
        assert result['overall_risk_level'] in ['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']
        assert 0 <= result['risk_score'] <= 100
        assert isinstance(result['risk_metrics'], list)
        assert isinstance(result['risk_warnings'], list)
        assert isinstance(result['mitigation_suggestions'], list)

    @pytest.mark.asyncio
    async def test_portfolio_assessment_workflow(self):
        """Test complete portfolio assessment workflow."""
        mock_data_service = Mock()
        risk_service = RiskAssessmentService(data_service=mock_data_service)
        
        # Mock individual stock assessments
        mock_assessment = {
            'overall_risk_level': 'MODERATE',
            'risk_score': 50,
            'risk_metrics': [],
            'correlation_data': None,
            'scenario_analysis': None,
            'risk_warnings': [],
            'mitigation_suggestions': [],
            'assessment_timestamp': datetime.now().isoformat()
        }
        
        risk_service.assess_stock_risk = AsyncMock(return_value=mock_assessment)
        
        positions = [
            {'symbol': 'AAPL', 'quantity': 100, 'value': 15000, 'sector': 'Technology'},
            {'symbol': 'MSFT', 'quantity': 80, 'value': 20000, 'sector': 'Technology'},
            {'symbol': 'JNJ', 'quantity': 150, 'value': 25000, 'sector': 'Healthcare'}
        ]
        
        result = await risk_service.assess_portfolio_risk(positions)
        
        # Verify portfolio assessment structure
        assert isinstance(result, PortfolioRisk)
        assert result.total_value == Decimal('60000')
        assert len(result.positions) == 3
        assert result.overall_risk_level in ['LOW', 'MODERATE', 'HIGH', 'VERY_HIGH']
        assert 0 <= result.diversification_score <= 100
        assert 0 <= result.concentration_risk <= 1
        assert 0 <= result.correlation_risk <= 1
        assert len(result.risk_metrics) > 0
        
        # Verify position weights sum to 1
        total_weight = sum(pos['weight'] for pos in result.positions)
        assert abs(total_weight - 1.0) < 0.01  # Allow for floating point errors