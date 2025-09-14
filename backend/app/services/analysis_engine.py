"""
Combined Analysis and Recommendation Engine.

This module provides the main AnalysisEngine class that combines fundamental and technical
analysis to generate comprehensive investment recommendations with confidence scoring,
reasoning, risk assessment, and price targets.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from concurrent.futures import ThreadPoolExecutor

from ..models.analysis import (
    AnalysisResult, AnalysisType, Recommendation, RiskLevel, 
    PriceTarget, CombinedAnalysis
)
from ..models.fundamental import FundamentalData
from ..models.technical import TechnicalData, SignalStrength, TrendDirection
from ..models.stock import MarketData
from .fundamental_analyzer import FundamentalAnalyzer, FundamentalAnalysisException
from .technical_analyzer import TechnicalAnalyzer, TechnicalAnalysisException
from .sentiment_analyzer import SentimentAnalyzer
from .data_aggregation import DataAggregationService, DataAggregationException


# Configure logging
logger = logging.getLogger(__name__)


class AnalysisEngineException(Exception):
    """Custom exception for analysis engine errors."""
    
    def __init__(self, message: str, error_type: str = "ANALYSIS_ERROR", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class AnalysisEngine:
    """
    Combined Analysis and Recommendation Engine.
    
    Integrates fundamental and technical analysis to provide comprehensive
    investment recommendations with confidence scoring, risk assessment,
    and price targets.
    """
    
    def __init__(
        self,
        fundamental_analyzer: Optional[FundamentalAnalyzer] = None,
        technical_analyzer: Optional[TechnicalAnalyzer] = None,
        sentiment_analyzer: Optional[SentimentAnalyzer] = None,
        data_service: Optional[DataAggregationService] = None
    ):
        """Initialize the analysis engine with required services."""
        self.data_service = data_service or DataAggregationService()
        self.fundamental_analyzer = fundamental_analyzer or FundamentalAnalyzer(self.data_service)
        self.technical_analyzer = technical_analyzer or TechnicalAnalyzer(self.data_service)
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Recommendation thresholds
        self.recommendation_thresholds = {
            Recommendation.STRONG_BUY: 85,
            Recommendation.BUY: 70,
            Recommendation.HOLD: 45,
            Recommendation.SELL: 30,
            Recommendation.STRONG_SELL: 0
        }
        
        # Risk level thresholds based on various factors
        self.risk_thresholds = {
            'volatility': {'low': 0.15, 'moderate': 0.25, 'high': 0.40},
            'debt_ratio': {'low': 0.30, 'moderate': 0.60, 'high': 1.00},
            'pe_ratio': {'low': 15, 'moderate': 25, 'high': 40}
        }
    
    async def analyze_stock(
        self, 
        symbol: str, 
        include_fundamental: bool = True,
        include_technical: bool = True,
        include_sentiment: bool = True,
        timeframe: str = "1D"
    ) -> AnalysisResult:
        """
        Perform comprehensive stock analysis combining fundamental, technical, and sentiment analysis.
        
        Args:
            symbol: Stock ticker symbol
            include_fundamental: Whether to include fundamental analysis
            include_technical: Whether to include technical analysis
            include_sentiment: Whether to include sentiment analysis
            timeframe: Technical analysis timeframe
            
        Returns:
            AnalysisResult with comprehensive analysis and recommendation
            
        Raises:
            AnalysisEngineException: If analysis cannot be performed
        """
        symbol = symbol.upper().strip()
        
        try:
            logger.info(f"Starting comprehensive analysis for {symbol}")
            
            # Fetch current market data
            market_data = await self._safe_get_market_data(symbol)
            
            # Perform analyses concurrently
            tasks = []
            
            if include_fundamental:
                tasks.append(('fundamental', self._safe_fundamental_analysis(symbol)))
            
            if include_technical:
                from ..models.technical import TimeFrame
                tf = getattr(TimeFrame, timeframe.replace('D', '_DAY').replace('W', '_WEEK').replace('M', '_MONTH').replace('Y', '_YEAR'), TimeFrame.ONE_DAY)
                tasks.append(('technical', self._safe_technical_analysis(symbol, tf)))
            
            if include_sentiment:
                tasks.append(('sentiment', self._safe_sentiment_analysis(symbol)))
            
            # Wait for all analyses to complete
            results = {}
            for analysis_type, task in tasks:
                try:
                    result = await task
                    if result:
                        results[analysis_type] = result
                except Exception as e:
                    logger.warning(f"Failed {analysis_type} analysis for {symbol}: {e}")
            
            if not results:
                raise AnalysisEngineException(
                    f"No analysis data available for {symbol}",
                    error_type="NO_DATA",
                    suggestions=[
                        "Check if symbol exists and is actively traded",
                        "Try again later if data sources are temporarily unavailable",
                        "Verify symbol format is correct"
                    ]
                )
            
            # Combine analyses and generate recommendation
            combined_analysis = self._combine_analyses(symbol, results, market_data)
            analysis_result = await self._generate_recommendation(combined_analysis)
            
            logger.info(f"Completed analysis for {symbol}: {analysis_result.recommendation} ({analysis_result.confidence}%)")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            if isinstance(e, AnalysisEngineException):
                raise e
            raise AnalysisEngineException(
                f"Unable to analyze {symbol}: {str(e)}",
                error_type="ANALYSIS_FAILED",
                suggestions=[
                    "Check symbol exists and is valid",
                    "Ensure market data is available",
                    "Try again later"
                ]
            )
    
    async def generate_price_targets(
        self, 
        symbol: str, 
        combined_analysis: CombinedAnalysis,
        current_price: Decimal
    ) -> List[PriceTarget]:
        """
        Generate price targets for different timeframes.
        
        Args:
            symbol: Stock ticker symbol
            combined_analysis: Combined analysis data
            current_price: Current stock price
            
        Returns:
            List of PriceTarget objects for different timeframes
        """
        targets = []
        
        try:
            # Short-term target (3 months) - primarily technical
            if combined_analysis.technical_analysis:
                short_term_target = self._calculate_technical_target(
                    current_price, 
                    combined_analysis.technical_analysis,
                    timeframe="3M"
                )
                if short_term_target:
                    targets.append(short_term_target)
            
            # Medium-term target (6 months) - balanced approach
            medium_term_target = self._calculate_balanced_target(
                current_price,
                combined_analysis,
                timeframe="6M"
            )
            if medium_term_target:
                targets.append(medium_term_target)
            
            # Long-term target (1 year) - primarily fundamental
            if combined_analysis.fundamental_analysis:
                long_term_target = self._calculate_fundamental_target(
                    current_price,
                    combined_analysis.fundamental_analysis,
                    timeframe="1Y"
                )
                if long_term_target:
                    targets.append(long_term_target)
            
        except Exception as e:
            logger.warning(f"Failed to generate price targets for {symbol}: {e}")
        
        return targets
    
    async def assess_risk_level(
        self, 
        symbol: str, 
        combined_analysis: CombinedAnalysis,
        market_data: Optional[MarketData] = None
    ) -> Tuple[RiskLevel, Dict[str, Any]]:
        """
        Assess overall risk level and detailed risk factors.
        
        Args:
            symbol: Stock ticker symbol
            combined_analysis: Combined analysis data
            market_data: Current market data
            
        Returns:
            Tuple of (RiskLevel, risk_factors_dict)
        """
        risk_factors = {}
        risk_score = 0  # 0 = low risk, 100 = very high risk
        
        try:
            # Fundamental risk factors
            if combined_analysis.fundamental_analysis:
                fund_data = combined_analysis.fundamental_analysis
                
                # Debt risk
                if fund_data.debt_to_equity is not None:
                    debt_ratio = float(fund_data.debt_to_equity)
                    risk_factors['debt_ratio'] = debt_ratio
                    
                    if debt_ratio > self.risk_thresholds['debt_ratio']['high']:
                        risk_score += 25
                    elif debt_ratio > self.risk_thresholds['debt_ratio']['moderate']:
                        risk_score += 15
                    elif debt_ratio > self.risk_thresholds['debt_ratio']['low']:
                        risk_score += 5
                
                # Valuation risk
                if fund_data.pe_ratio:
                    pe_ratio = float(fund_data.pe_ratio)
                    risk_factors['pe_ratio'] = pe_ratio
                    
                    if pe_ratio > self.risk_thresholds['pe_ratio']['high']:
                        risk_score += 20
                    elif pe_ratio > self.risk_thresholds['pe_ratio']['moderate']:
                        risk_score += 10
                
                # Profitability risk
                if fund_data.profit_margin:
                    margin = float(fund_data.profit_margin)
                    risk_factors['profit_margin'] = margin
                    
                    if margin < 0:  # Negative margins
                        risk_score += 30
                    elif margin < 0.05:  # Very low margins
                        risk_score += 15
                
                # Cash flow risk
                if fund_data.free_cash_flow is not None:
                    risk_factors['free_cash_flow'] = fund_data.free_cash_flow
                    if fund_data.free_cash_flow < 0:
                        risk_score += 20
            
            # Technical risk factors
            if combined_analysis.technical_analysis:
                tech_data = combined_analysis.technical_analysis
                
                # Volatility risk (using ATR as proxy)
                if tech_data.atr and market_data:
                    atr_percent = float(tech_data.atr) / float(market_data.price)
                    risk_factors['volatility'] = atr_percent
                    
                    if atr_percent > self.risk_thresholds['volatility']['high']:
                        risk_score += 25
                    elif atr_percent > self.risk_thresholds['volatility']['moderate']:
                        risk_score += 15
                    elif atr_percent > self.risk_thresholds['volatility']['low']:
                        risk_score += 5
                
                # Trend risk
                if tech_data.trend_direction == TrendDirection.BEARISH:
                    risk_score += 15
                elif tech_data.trend_direction == TrendDirection.SIDEWAYS:
                    risk_score += 5
                
                # RSI extremes
                if tech_data.rsi:
                    rsi = float(tech_data.rsi)
                    risk_factors['rsi'] = rsi
                    if rsi > 80 or rsi < 20:  # Extreme levels
                        risk_score += 10
            
            # Market data risk factors
            if market_data:
                # 52-week position risk
                if market_data.high_52_week and market_data.low_52_week:
                    week_52_position = (market_data.price - market_data.low_52_week) / (market_data.high_52_week - market_data.low_52_week)
                    risk_factors['week_52_position'] = float(week_52_position)
                    
                    if week_52_position > 0.9:  # Near 52-week high
                        risk_score += 10
                    elif week_52_position < 0.1:  # Near 52-week low
                        risk_score += 15
            
            # Determine risk level
            if risk_score >= 75:
                risk_level = RiskLevel.VERY_HIGH
            elif risk_score >= 50:
                risk_level = RiskLevel.HIGH
            elif risk_score >= 25:
                risk_level = RiskLevel.MODERATE
            else:
                risk_level = RiskLevel.LOW
            
            risk_factors['overall_risk_score'] = risk_score
            
        except Exception as e:
            logger.warning(f"Failed to assess risk for {symbol}: {e}")
            risk_level = RiskLevel.MODERATE  # Default to moderate risk
            risk_factors['error'] = str(e)
        
        return risk_level, risk_factors
    
    # Private helper methods
    
    async def _safe_get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Safely get market data without raising exceptions."""
        try:
            return await self.data_service.get_market_data(symbol)
        except Exception as e:
            logger.warning(f"Failed to get market data for {symbol}: {e}")
            return None
    
    async def _safe_fundamental_analysis(self, symbol: str) -> Optional[FundamentalData]:
        """Safely perform fundamental analysis without raising exceptions."""
        try:
            return await self.fundamental_analyzer.analyze_fundamentals(symbol)
        except Exception as e:
            logger.warning(f"Failed fundamental analysis for {symbol}: {e}")
            return None
    
    async def _safe_technical_analysis(self, symbol: str, timeframe) -> Optional[TechnicalData]:
        """Safely perform technical analysis without raising exceptions."""
        try:
            return await self.technical_analyzer.analyze_technical(symbol, timeframe)
        except Exception as e:
            logger.warning(f"Failed technical analysis for {symbol}: {e}")
            return None
    
    async def _safe_sentiment_analysis(self, symbol: str):
        """Safely perform sentiment analysis without raising exceptions."""
        try:
            return await self.sentiment_analyzer.analyze_stock_sentiment(symbol)
        except Exception as e:
            logger.warning(f"Failed sentiment analysis for {symbol}: {e}")
            return None
    
    def _combine_analyses(
        self, 
        symbol: str, 
        results: Dict[str, Any], 
        market_data: Optional[MarketData]
    ) -> CombinedAnalysis:
        """Combine fundamental, technical, and sentiment analysis results."""
        fundamental_data = results.get('fundamental')
        technical_data = results.get('technical')
        sentiment_data = results.get('sentiment')
        
        # Determine signals
        fundamental_signal = None
        if fundamental_data:
            health_score = fundamental_data.calculate_health_score()
            if health_score:
                if health_score >= 80:
                    fundamental_signal = 'strong_buy'
                elif health_score >= 65:
                    fundamental_signal = 'buy'
                elif health_score >= 45:
                    fundamental_signal = 'hold'
                elif health_score >= 30:
                    fundamental_signal = 'sell'
                else:
                    fundamental_signal = 'strong_sell'
        
        technical_signal = technical_data.overall_signal if technical_data else None
        
        # Create combined analysis
        combined = CombinedAnalysis(
            symbol=symbol,
            fundamental_analysis=fundamental_data,
            technical_analysis=technical_data,
            market_data=market_data.dict() if market_data else None,
            fundamental_signal=fundamental_signal,
            technical_signal=technical_signal
        )
        
        # Calculate signal alignment
        combined.signals_aligned = combined.calculate_signal_alignment()
        
        # Calculate combined score
        combined.combined_score = self._calculate_combined_score(combined)
        
        # Determine conviction level
        if combined.signals_aligned:
            combined.conviction_level = "High" if combined.combined_score >= 70 else "Moderate"
        else:
            combined.conviction_level = "Low"
        
        return combined
    
    def _calculate_combined_score(self, combined: CombinedAnalysis) -> int:
        """Calculate combined analysis score."""
        scores = []
        weights = []
        
        # Fundamental score
        if combined.fundamental_analysis:
            fund_score = combined.fundamental_analysis.calculate_health_score()
            if fund_score:
                scores.append(fund_score)
                weights.append(0.6)  # 60% weight for fundamental
        
        # Technical score
        if combined.technical_analysis and combined.market_data:
            current_price = Decimal(str(combined.market_data.get('price', 0)))
            tech_score = combined.technical_analysis.calculate_technical_score(current_price)
            scores.append(tech_score)
            weights.append(0.4)  # 40% weight for technical
        
        if not scores:
            return 50  # Neutral score
        
        # Calculate weighted average
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        total_weight = sum(weights)
        
        return int(weighted_sum / total_weight) if total_weight > 0 else 50
    
    async def _generate_recommendation(self, combined: CombinedAnalysis) -> AnalysisResult:
        """Generate comprehensive recommendation from combined analysis."""
        symbol = combined.symbol
        
        # Determine recommendation based on combined score
        recommendation = self._score_to_recommendation(combined.combined_score or 50)
        
        # Calculate confidence based on signal alignment and data quality
        confidence = self._calculate_confidence(combined)
        
        # Generate strengths, weaknesses, risks, and opportunities
        strengths, weaknesses = self._analyze_strengths_weaknesses(combined)
        risks, opportunities = self._analyze_risks_opportunities(combined)
        
        # Generate price targets
        current_price = None
        if combined.market_data:
            current_price = Decimal(str(combined.market_data.get('price', 0)))
        
        price_targets = []
        if current_price:
            price_targets = await self.generate_price_targets(symbol, combined, current_price)
        
        # Assess risk level
        risk_level, risk_factors = await self.assess_risk_level(symbol, combined)
        
        # Create analysis result
        result = AnalysisResult(
            symbol=symbol,
            analysis_type=AnalysisType.COMBINED,
            recommendation=recommendation,
            confidence=confidence,
            overall_score=combined.combined_score or 50,
            fundamental_score=combined.fundamental_analysis.calculate_health_score() if combined.fundamental_analysis else None,
            technical_score=combined.technical_analysis.calculate_technical_score(current_price) if combined.technical_analysis and current_price else None,
            strengths=strengths,
            weaknesses=weaknesses,
            risks=risks,
            opportunities=opportunities,
            price_targets=price_targets,
            risk_level=risk_level,
            risk_factors=risk_factors,
            fundamental_data=combined.fundamental_analysis,
            technical_data=combined.technical_analysis,
            analysis_timestamp=datetime.now(),
            data_freshness={
                'fundamental': combined.fundamental_analysis.last_updated if combined.fundamental_analysis else None,
                'technical': combined.technical_analysis.timestamp if combined.technical_analysis else None,
                'market': datetime.now()
            }
        )
        
        return result
    
    def _score_to_recommendation(self, score: int) -> Recommendation:
        """Convert combined score to recommendation."""
        for recommendation, threshold in self.recommendation_thresholds.items():
            if score >= threshold:
                return recommendation
        return Recommendation.STRONG_SELL
    
    def _calculate_confidence(self, combined: CombinedAnalysis) -> int:
        """Calculate confidence level based on analysis quality and alignment."""
        base_confidence = 50
        
        # Boost confidence if signals are aligned
        if combined.signals_aligned:
            base_confidence += 20
        else:
            base_confidence -= 10
        
        # Boost confidence based on data availability
        if combined.fundamental_analysis and combined.technical_analysis:
            base_confidence += 15  # Both analyses available
        elif combined.fundamental_analysis or combined.technical_analysis:
            base_confidence += 5   # One analysis available
        
        # Boost confidence based on data quality
        if combined.fundamental_analysis:
            # Check if key fundamental metrics are available
            key_metrics = [
                combined.fundamental_analysis.pe_ratio,
                combined.fundamental_analysis.roe,
                combined.fundamental_analysis.debt_to_equity,
                combined.fundamental_analysis.profit_margin
            ]
            available_metrics = sum(1 for metric in key_metrics if metric is not None)
            base_confidence += min(10, available_metrics * 2)
        
        if combined.technical_analysis:
            # Check technical data quality
            if combined.technical_analysis.data_points >= 100:
                base_confidence += 5
            if combined.technical_analysis.support_levels or combined.technical_analysis.resistance_levels:
                base_confidence += 5
        
        return max(0, min(100, base_confidence))
    
    def _analyze_strengths_weaknesses(self, combined: CombinedAnalysis) -> Tuple[List[str], List[str]]:
        """Analyze strengths and weaknesses from combined data."""
        strengths = []
        weaknesses = []
        
        # Fundamental strengths/weaknesses
        if combined.fundamental_analysis:
            fund = combined.fundamental_analysis
            
            # ROE analysis
            if fund.roe:
                if fund.roe >= Decimal('0.20'):
                    strengths.append(f"Excellent return on equity of {fund.roe:.1%}")
                elif fund.roe >= Decimal('0.15'):
                    strengths.append(f"Strong return on equity of {fund.roe:.1%}")
                elif fund.roe < Decimal('0.05'):
                    weaknesses.append(f"Low return on equity of {fund.roe:.1%}")
            
            # Debt analysis
            if fund.debt_to_equity is not None:
                if fund.debt_to_equity <= Decimal('0.30'):
                    strengths.append(f"Conservative debt level (D/E: {fund.debt_to_equity:.2f})")
                elif fund.debt_to_equity > Decimal('1.00'):
                    weaknesses.append(f"High debt burden (D/E: {fund.debt_to_equity:.2f})")
            
            # Profitability analysis
            if fund.profit_margin:
                if fund.profit_margin >= Decimal('0.20'):
                    strengths.append(f"High profit margins of {fund.profit_margin:.1%}")
                elif fund.profit_margin < Decimal('0.02'):
                    weaknesses.append(f"Low profit margins of {fund.profit_margin:.1%}")
            
            # Growth analysis
            if fund.revenue_growth:
                if fund.revenue_growth >= Decimal('0.15'):
                    strengths.append(f"Strong revenue growth of {fund.revenue_growth:.1%}")
                elif fund.revenue_growth < Decimal('-0.05'):
                    weaknesses.append(f"Declining revenue ({fund.revenue_growth:.1%})")
            
            # Valuation analysis
            if fund.pe_ratio:
                if fund.pe_ratio > Decimal('35'):
                    weaknesses.append(f"High valuation (P/E: {fund.pe_ratio:.1f})")
                elif Decimal('10') <= fund.pe_ratio <= Decimal('20'):
                    strengths.append(f"Reasonable valuation (P/E: {fund.pe_ratio:.1f})")
        
        # Technical strengths/weaknesses
        if combined.technical_analysis:
            tech = combined.technical_analysis
            
            # Trend analysis
            if tech.trend_direction == TrendDirection.BULLISH:
                strengths.append("Bullish technical trend")
            elif tech.trend_direction == TrendDirection.BEARISH:
                weaknesses.append("Bearish technical trend")
            
            # RSI analysis
            if tech.rsi:
                if 30 <= tech.rsi <= 70:
                    strengths.append("RSI in healthy range")
                elif tech.rsi > 80:
                    weaknesses.append("Overbought conditions (RSI > 80)")
                elif tech.rsi < 20:
                    weaknesses.append("Oversold conditions (RSI < 20)")
            
            # Moving average analysis
            if tech.sma_20 and tech.sma_50 and combined.market_data:
                current_price = Decimal(str(combined.market_data.get('price', 0)))
                if current_price > tech.sma_20 > tech.sma_50:
                    strengths.append("Price above key moving averages")
                elif current_price < tech.sma_20 < tech.sma_50:
                    weaknesses.append("Price below key moving averages")
        
        return strengths, weaknesses
    
    def _analyze_risks_opportunities(self, combined: CombinedAnalysis) -> Tuple[List[str], List[str]]:
        """Analyze risks and opportunities from combined data."""
        risks = []
        opportunities = []
        
        # Market risks
        risks.extend([
            "Market volatility and economic uncertainty",
            "Interest rate changes affecting valuations",
            "Sector-specific regulatory changes"
        ])
        
        # Fundamental-based risks and opportunities
        if combined.fundamental_analysis:
            fund = combined.fundamental_analysis
            
            # High debt risk
            if fund.debt_to_equity and fund.debt_to_equity > Decimal('0.80'):
                risks.append("High debt levels may limit financial flexibility")
            
            # Valuation risk
            if fund.pe_ratio and fund.pe_ratio > Decimal('30'):
                risks.append("High valuation may limit upside potential")
            
            # Growth opportunities
            if fund.revenue_growth and fund.revenue_growth > Decimal('0.10'):
                opportunities.append("Strong revenue growth momentum")
            
            # Cash generation opportunity
            if fund.free_cash_flow and fund.free_cash_flow > 0:
                opportunities.append("Strong cash generation for reinvestment")
        
        # Technical-based risks and opportunities
        if combined.technical_analysis:
            tech = combined.technical_analysis
            
            # Support/resistance opportunities
            if tech.support_levels:
                opportunities.append("Strong technical support levels identified")
            
            if tech.resistance_levels:
                risks.append("Technical resistance levels may limit upside")
            
            # Volatility considerations
            if tech.atr and combined.market_data:
                current_price = Decimal(str(combined.market_data.get('price', 0)))
                atr_percent = tech.atr / current_price
                if atr_percent > Decimal('0.05'):  # > 5% daily range
                    risks.append("High volatility increases trading risk")
        
        return risks, opportunities
    
    def _calculate_technical_target(
        self, 
        current_price: Decimal, 
        technical_data: TechnicalData,
        timeframe: str
    ) -> Optional[PriceTarget]:
        """Calculate technical-based price target."""
        try:
            target_price = current_price
            confidence = 50
            rationale = "Technical analysis based target"
            
            # Use resistance levels for upside targets
            if technical_data.resistance_levels:
                nearest_resistance = min(
                    technical_data.resistance_levels,
                    key=lambda r: abs(r.level - current_price)
                )
                if nearest_resistance.level > current_price:
                    target_price = nearest_resistance.level
                    confidence = min(80, 50 + nearest_resistance.strength * 3)
                    rationale = f"Target based on resistance level at ${nearest_resistance.level}"
            
            # Adjust based on trend
            if technical_data.trend_direction == TrendDirection.BULLISH:
                target_price *= Decimal('1.10')  # 10% upside for bullish trend
                confidence += 10
                rationale += " with bullish trend support"
            elif technical_data.trend_direction == TrendDirection.BEARISH:
                target_price *= Decimal('0.95')  # 5% downside for bearish trend
                confidence -= 10
                rationale += " adjusted for bearish trend"
            
            # Use Bollinger Bands if available
            if technical_data.bollinger_upper and current_price < technical_data.bollinger_upper:
                bb_target = technical_data.bollinger_upper
                if bb_target > target_price:
                    target_price = bb_target
                    rationale = f"Target based on Bollinger Band upper limit"
            
            return PriceTarget(
                target=target_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                timeframe=timeframe,
                confidence=max(30, min(90, confidence)),
                rationale=rationale
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate technical target: {e}")
            return None
    
    def _calculate_fundamental_target(
        self,
        current_price: Decimal,
        fundamental_data: FundamentalData,
        timeframe: str
    ) -> Optional[PriceTarget]:
        """Calculate fundamental-based price target."""
        try:
            target_price = current_price
            confidence = 50
            rationale = "Fundamental analysis based target"
            
            # Use P/E ratio for valuation-based target
            if fundamental_data.pe_ratio and fundamental_data.eps:
                # Assume fair P/E based on growth and quality
                fair_pe = Decimal('20')  # Base fair P/E
                
                # Adjust fair P/E based on growth
                if fundamental_data.revenue_growth:
                    if fundamental_data.revenue_growth > Decimal('0.15'):
                        fair_pe = Decimal('25')  # Higher P/E for growth
                    elif fundamental_data.revenue_growth < Decimal('0.05'):
                        fair_pe = Decimal('15')  # Lower P/E for slow growth
                
                # Adjust for quality (ROE)
                if fundamental_data.roe:
                    if fundamental_data.roe > Decimal('0.20'):
                        fair_pe += Decimal('3')  # Premium for high ROE
                    elif fundamental_data.roe < Decimal('0.10'):
                        fair_pe -= Decimal('3')  # Discount for low ROE
                
                target_price = fair_pe * fundamental_data.eps
                confidence = 70
                rationale = f"Target based on fair P/E of {fair_pe} and EPS of ${fundamental_data.eps}"
            
            # Adjust for financial health
            health_score = fundamental_data.calculate_health_score()
            if health_score:
                if health_score >= 80:
                    target_price *= Decimal('1.05')  # 5% premium for excellent health
                    confidence += 10
                elif health_score <= 40:
                    target_price *= Decimal('0.90')  # 10% discount for poor health
                    confidence -= 15
            
            return PriceTarget(
                target=target_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                timeframe=timeframe,
                confidence=max(30, min(90, confidence)),
                rationale=rationale
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate fundamental target: {e}")
            return None
    
    def _calculate_balanced_target(
        self,
        current_price: Decimal,
        combined_analysis: CombinedAnalysis,
        timeframe: str
    ) -> Optional[PriceTarget]:
        """Calculate balanced target using both fundamental and technical analysis."""
        try:
            targets = []
            
            # Get technical target
            if combined_analysis.technical_analysis:
                tech_target = self._calculate_technical_target(
                    current_price, 
                    combined_analysis.technical_analysis, 
                    timeframe
                )
                if tech_target:
                    targets.append((tech_target.target, tech_target.confidence, 0.4))  # 40% weight
            
            # Get fundamental target
            if combined_analysis.fundamental_analysis:
                fund_target = self._calculate_fundamental_target(
                    current_price,
                    combined_analysis.fundamental_analysis,
                    timeframe
                )
                if fund_target:
                    targets.append((fund_target.target, fund_target.confidence, 0.6))  # 60% weight
            
            if not targets:
                return None
            
            # Calculate weighted average
            weighted_price = sum(price * Decimal(str(weight)) for price, conf, weight in targets)
            weighted_confidence = sum(conf * weight for price, conf, weight in targets)
            total_weight = sum(weight for price, conf, weight in targets)
            
            if total_weight == 0:
                return None
            
            target_price = weighted_price / Decimal(str(total_weight))
            confidence = int(weighted_confidence / total_weight)
            
            return PriceTarget(
                target=target_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                timeframe=timeframe,
                confidence=max(30, min(90, confidence)),
                rationale="Balanced target combining fundamental and technical analysis"
            )
            
        except Exception as e:
            logger.warning(f"Failed to calculate balanced target: {e}")
            return None

# Global analysis engine instance
analysis_engine = AnalysisEngine()