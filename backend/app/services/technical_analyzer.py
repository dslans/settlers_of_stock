"""
Technical Analysis Engine for stock analysis.
Provides comprehensive technical analysis including moving averages, momentum indicators,
Bollinger Bands, and support/resistance level detection using TA-Lib.
"""

import talib
import yfinance as yf
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel

from ..models.technical import (
    TechnicalData, TimeFrame, TrendDirection, SignalStrength,
    TechnicalIndicator, SupportResistanceLevel
)
from ..models.stock import Stock
from .data_aggregation import DataAggregationService, DataAggregationException


# Configure logging
logger = logging.getLogger(__name__)


class TechnicalAnalysisException(Exception):
    """Custom exception for technical analysis errors."""
    
    def __init__(self, message: str, error_type: str = "ANALYSIS_ERROR", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class TechnicalSignal(BaseModel):
    """Technical analysis signal result."""
    
    indicator: str
    signal: SignalStrength
    value: Optional[Decimal]
    description: str
    confidence: int  # 0-100


class MultiTimeframeAnalysis(BaseModel):
    """Multi-timeframe technical analysis result."""
    
    symbol: str
    analyses: Dict[str, TechnicalData]  # timeframe -> analysis
    consensus_signal: SignalStrength
    trend_alignment: bool
    key_levels: Dict[str, List[SupportResistanceLevel]]
    analysis_timestamp: datetime


class TechnicalAnalyzer:
    """
    Comprehensive technical analysis engine using TA-Lib.
    
    Provides moving averages, momentum indicators, Bollinger Bands,
    support/resistance detection, and multi-timeframe analysis.
    """
    
    def __init__(self, data_service: Optional[DataAggregationService] = None):
        """Initialize the technical analyzer."""
        self.data_service = data_service or DataAggregationService()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Timeframe to yfinance period mapping
        self.timeframe_periods = {
            TimeFrame.ONE_DAY: "1d",
            TimeFrame.ONE_WEEK: "5d", 
            TimeFrame.ONE_MONTH: "1mo",
            TimeFrame.THREE_MONTHS: "3mo",
            TimeFrame.SIX_MONTHS: "6mo",
            TimeFrame.ONE_YEAR: "1y",
            TimeFrame.TWO_YEARS: "2y"
        }
        
        # Timeframe to data interval mapping
        self.timeframe_intervals = {
            TimeFrame.ONE_DAY: "5m",
            TimeFrame.ONE_WEEK: "1h",
            TimeFrame.ONE_MONTH: "1d",
            TimeFrame.THREE_MONTHS: "1d",
            TimeFrame.SIX_MONTHS: "1d",
            TimeFrame.ONE_YEAR: "1d",
            TimeFrame.TWO_YEARS: "1wk"
        }
    
    async def analyze_technical(self, symbol: str, timeframe: TimeFrame = TimeFrame.ONE_DAY) -> TechnicalData:
        """
        Perform comprehensive technical analysis for a stock.
        
        Args:
            symbol: Stock ticker symbol
            timeframe: Analysis timeframe
            
        Returns:
            TechnicalData with calculated indicators and analysis
            
        Raises:
            TechnicalAnalysisException: If analysis cannot be performed
        """
        symbol = symbol.upper().strip()
        
        try:
            # Fetch historical price data
            price_data = await self._fetch_price_data(symbol, timeframe)
            
            if price_data.empty or len(price_data) < 50:
                raise TechnicalAnalysisException(
                    f"Insufficient price data for {symbol} ({len(price_data)} periods)",
                    error_type="INSUFFICIENT_DATA",
                    suggestions=[
                        "Try a different timeframe",
                        "Check if symbol is actively traded",
                        "Verify symbol exists"
                    ]
                )
            
            # Calculate technical indicators
            technical_data = await self._calculate_all_indicators(symbol, price_data, timeframe)
            
            # Detect support and resistance levels
            support_levels, resistance_levels = self._detect_support_resistance(price_data)
            technical_data.support_levels = support_levels
            technical_data.resistance_levels = resistance_levels
            
            # Determine overall trend and signal
            technical_data.trend_direction = self._determine_trend(technical_data, price_data)
            technical_data.overall_signal = self._calculate_overall_signal(technical_data, price_data)
            
            # Set metadata
            technical_data.data_points = len(price_data)
            technical_data.timestamp = datetime.now()
            
            logger.info(f"Successfully analyzed technical indicators for {symbol} ({timeframe})")
            return technical_data
            
        except Exception as e:
            logger.error(f"Failed to analyze technical indicators for {symbol}: {e}")
            if isinstance(e, TechnicalAnalysisException):
                raise e
            raise TechnicalAnalysisException(
                f"Unable to perform technical analysis for {symbol}: {str(e)}",
                error_type="CALCULATION_ERROR",
                suggestions=[
                    "Check if market data is available",
                    "Try a different timeframe",
                    "Verify symbol is correct"
                ]
            )
    
    async def analyze_multi_timeframe(self, symbol: str, timeframes: List[TimeFrame] = None) -> MultiTimeframeAnalysis:
        """
        Perform multi-timeframe technical analysis.
        
        Args:
            symbol: Stock ticker symbol
            timeframes: List of timeframes to analyze (default: [1D, 1W, 1M])
            
        Returns:
            MultiTimeframeAnalysis with consensus signals and trend alignment
        """
        if timeframes is None:
            timeframes = [TimeFrame.ONE_DAY, TimeFrame.ONE_WEEK, TimeFrame.ONE_MONTH]
        
        try:
            # Analyze each timeframe concurrently
            tasks = []
            for tf in timeframes:
                task = asyncio.create_task(self._safe_analyze_technical(symbol, tf))
                tasks.append((tf.value, task))
            
            # Collect results
            analyses = {}
            for tf_name, task in tasks:
                try:
                    result = await task
                    if result:
                        analyses[tf_name] = result
                except Exception as e:
                    logger.warning(f"Failed to analyze {symbol} for timeframe {tf_name}: {e}")
            
            if not analyses:
                raise TechnicalAnalysisException(
                    f"No technical analysis data available for {symbol}",
                    error_type="NO_DATA"
                )
            
            # Calculate consensus signal and trend alignment
            consensus_signal = self._calculate_consensus_signal(analyses)
            trend_alignment = self._check_trend_alignment(analyses)
            
            # Aggregate key levels across timeframes
            key_levels = self._aggregate_key_levels(analyses)
            
            return MultiTimeframeAnalysis(
                symbol=symbol,
                analyses=analyses,
                consensus_signal=consensus_signal,
                trend_alignment=trend_alignment,
                key_levels=key_levels,
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Failed multi-timeframe analysis for {symbol}: {e}")
            if isinstance(e, TechnicalAnalysisException):
                raise e
            raise TechnicalAnalysisException(
                f"Unable to perform multi-timeframe analysis for {symbol}: {str(e)}",
                error_type="MULTI_TIMEFRAME_ERROR"
            )
    
    # Moving Average Calculations
    
    def calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Simple Moving Average using TA-Lib."""
        return talib.SMA(prices, timeperiod=period)
    
    def calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average using TA-Lib."""
        return talib.EMA(prices, timeperiod=period)
    
    # Momentum Indicators
    
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Relative Strength Index using TA-Lib."""
        return talib.RSI(prices, timeperiod=period)
    
    def calculate_macd(self, prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate MACD using TA-Lib."""
        macd, macd_signal, macd_histogram = talib.MACD(prices, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        return macd, macd_signal, macd_histogram
    
    # Bollinger Bands
    
    def calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculate Bollinger Bands using TA-Lib."""
        upper, middle, lower = talib.BBANDS(prices, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev, matype=0)
        return upper, middle, lower
    
    # Volume Indicators
    
    def calculate_obv(self, prices: np.ndarray, volumes: np.ndarray) -> np.ndarray:
        """Calculate On-Balance Volume using TA-Lib."""
        return talib.OBV(prices, volumes)
    
    # Volatility Indicators
    
    def calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """Calculate Average True Range using TA-Lib."""
        return talib.ATR(high, low, close, timeperiod=period)
    
    # Private helper methods
    
    async def _fetch_price_data(self, symbol: str, timeframe: TimeFrame) -> pd.DataFrame:
        """Fetch historical price data from yfinance."""
        loop = asyncio.get_event_loop()
        
        def _fetch_sync():
            ticker = yf.Ticker(symbol)
            period = self.timeframe_periods[timeframe]
            interval = self.timeframe_intervals[timeframe]
            
            # Fetch more data for longer timeframes to ensure sufficient history
            if timeframe in [TimeFrame.ONE_YEAR, TimeFrame.TWO_YEARS]:
                period = "5y"  # Get 5 years of data for better analysis
            elif timeframe in [TimeFrame.THREE_MONTHS, TimeFrame.SIX_MONTHS]:
                period = "2y"  # Get 2 years of data
            
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                raise ValueError(f"No price data available for {symbol}")
            
            # Ensure we have the required columns
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            return data
        
        return await loop.run_in_executor(self.executor, _fetch_sync)
    
    async def _calculate_all_indicators(self, symbol: str, price_data: pd.DataFrame, timeframe: TimeFrame) -> TechnicalData:
        """Calculate all technical indicators for the given price data."""
        loop = asyncio.get_event_loop()
        
        def _calculate_sync():
            # Convert to numpy arrays for TA-Lib
            close_prices = price_data['Close'].values.astype(float)
            high_prices = price_data['High'].values.astype(float)
            low_prices = price_data['Low'].values.astype(float)
            volumes = price_data['Volume'].values.astype(float)
            
            # Initialize technical data
            tech_data = TechnicalData(symbol=symbol, timeframe=timeframe)
            
            # Moving Averages
            sma_20 = self.calculate_sma(close_prices, 20)
            sma_50 = self.calculate_sma(close_prices, 50)
            sma_200 = self.calculate_sma(close_prices, 200)
            ema_12 = self.calculate_ema(close_prices, 12)
            ema_26 = self.calculate_ema(close_prices, 26)
            
            # Get latest values (handle NaN)
            tech_data.sma_20 = self._safe_decimal(sma_20[-1]) if not np.isnan(sma_20[-1]) else None
            tech_data.sma_50 = self._safe_decimal(sma_50[-1]) if not np.isnan(sma_50[-1]) else None
            tech_data.sma_200 = self._safe_decimal(sma_200[-1]) if not np.isnan(sma_200[-1]) else None
            tech_data.ema_12 = self._safe_decimal(ema_12[-1]) if not np.isnan(ema_12[-1]) else None
            tech_data.ema_26 = self._safe_decimal(ema_26[-1]) if not np.isnan(ema_26[-1]) else None
            
            # Momentum Indicators
            rsi = self.calculate_rsi(close_prices)
            macd, macd_signal, macd_histogram = self.calculate_macd(close_prices)
            
            tech_data.rsi = self._safe_decimal(rsi[-1]) if not np.isnan(rsi[-1]) else None
            tech_data.macd = self._safe_decimal(macd[-1]) if not np.isnan(macd[-1]) else None
            tech_data.macd_signal = self._safe_decimal(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else None
            tech_data.macd_histogram = self._safe_decimal(macd_histogram[-1]) if not np.isnan(macd_histogram[-1]) else None
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(close_prices)
            
            tech_data.bollinger_upper = self._safe_decimal(bb_upper[-1]) if not np.isnan(bb_upper[-1]) else None
            tech_data.bollinger_middle = self._safe_decimal(bb_middle[-1]) if not np.isnan(bb_middle[-1]) else None
            tech_data.bollinger_lower = self._safe_decimal(bb_lower[-1]) if not np.isnan(bb_lower[-1]) else None
            
            # Volume Indicators
            volume_sma = self.calculate_sma(volumes, 20)
            obv = self.calculate_obv(close_prices, volumes)
            
            tech_data.volume_sma = int(volume_sma[-1]) if not np.isnan(volume_sma[-1]) else None
            tech_data.obv = int(obv[-1]) if not np.isnan(obv[-1]) else None
            
            # Volatility
            atr = self.calculate_atr(high_prices, low_prices, close_prices)
            tech_data.atr = self._safe_decimal(atr[-1]) if not np.isnan(atr[-1]) else None
            
            return tech_data
        
        return await loop.run_in_executor(self.executor, _calculate_sync)
    
    def _detect_support_resistance(self, price_data: pd.DataFrame, window: int = 20, min_touches: int = 2) -> Tuple[List[SupportResistanceLevel], List[SupportResistanceLevel]]:
        """Detect support and resistance levels using local minima/maxima."""
        try:
            high_prices = price_data['High'].values
            low_prices = price_data['Low'].values
            close_prices = price_data['Close'].values
            dates = price_data.index
            
            # Find local minima (potential support) and maxima (potential resistance)
            support_candidates = []
            resistance_candidates = []
            
            # Use a rolling window to find local extremes
            for i in range(window, len(close_prices) - window):
                # Check for local minimum (support)
                if low_prices[i] == min(low_prices[i-window:i+window+1]):
                    support_candidates.append({
                        'price': low_prices[i],
                        'date': dates[i],
                        'index': i
                    })
                
                # Check for local maximum (resistance)
                if high_prices[i] == max(high_prices[i-window:i+window+1]):
                    resistance_candidates.append({
                        'price': high_prices[i],
                        'date': dates[i],
                        'index': i
                    })
            
            # Group similar levels and count touches
            support_levels = self._group_and_score_levels(support_candidates, close_prices, 'support', min_touches)
            resistance_levels = self._group_and_score_levels(resistance_candidates, close_prices, 'resistance', min_touches)
            
            # Sort by strength and return top levels
            support_levels.sort(key=lambda x: x.strength, reverse=True)
            resistance_levels.sort(key=lambda x: x.strength, reverse=True)
            
            return support_levels[:5], resistance_levels[:5]  # Return top 5 of each
            
        except Exception as e:
            logger.warning(f"Failed to detect support/resistance levels: {e}")
            return [], []
    
    def _group_and_score_levels(self, candidates: List[Dict], prices: np.ndarray, level_type: str, min_touches: int) -> List[SupportResistanceLevel]:
        """Group similar price levels and calculate their strength."""
        if not candidates:
            return []
        
        # Group candidates by similar price levels (within 1% of each other)
        grouped_levels = []
        tolerance = 0.01  # 1% tolerance
        
        for candidate in candidates:
            price = candidate['price']
            added_to_group = False
            
            # Try to add to existing group
            for group in grouped_levels:
                group_price = group['price']
                if abs(price - group_price) / group_price <= tolerance:
                    group['candidates'].append(candidate)
                    group['price'] = (group['price'] * len(group['candidates']) + price) / (len(group['candidates']) + 1)
                    added_to_group = True
                    break
            
            # Create new group if not added to existing
            if not added_to_group:
                grouped_levels.append({
                    'price': price,
                    'candidates': [candidate]
                })
        
        # Convert to SupportResistanceLevel objects
        levels = []
        for group in grouped_levels:
            touches = len(group['candidates'])
            if touches >= min_touches:
                # Calculate strength based on touches and recency
                strength = min(10, touches * 2)  # Base strength from touches
                
                # Boost strength for recent touches
                recent_touches = sum(1 for c in group['candidates'] if len(prices) - c['index'] <= 50)
                if recent_touches > 0:
                    strength += min(3, recent_touches)
                
                # Get most recent touch
                most_recent = max(group['candidates'], key=lambda x: x['index'])
                
                level = SupportResistanceLevel(
                    level=Decimal(str(round(group['price'], 2))),
                    strength=strength,
                    type=level_type,
                    touches=touches,
                    last_touch=most_recent['date']
                )
                levels.append(level)
        
        return levels
    
    def _determine_trend(self, tech_data: TechnicalData, price_data: pd.DataFrame) -> TrendDirection:
        """Determine overall trend direction based on multiple indicators."""
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        current_price = Decimal(str(price_data['Close'].iloc[-1]))
        
        # Moving average trend
        if tech_data.sma_20 and tech_data.sma_50:
            total_signals += 1
            if tech_data.sma_20 > tech_data.sma_50:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Price vs moving averages
        if tech_data.sma_20:
            total_signals += 1
            if current_price > tech_data.sma_20:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # MACD trend
        if tech_data.macd and tech_data.macd_signal:
            total_signals += 1
            if tech_data.macd > tech_data.macd_signal:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # RSI trend (not overbought/oversold)
        if tech_data.rsi:
            if 30 < tech_data.rsi < 70:  # Only count if not in extreme zones
                total_signals += 1
                if tech_data.rsi > 50:
                    bullish_signals += 1
                else:
                    bearish_signals += 1
        
        # Determine trend based on signal majority
        if total_signals == 0:
            return TrendDirection.UNKNOWN
        
        bullish_ratio = bullish_signals / total_signals
        
        if bullish_ratio >= 0.7:
            return TrendDirection.BULLISH
        elif bullish_ratio <= 0.3:
            return TrendDirection.BEARISH
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_overall_signal(self, tech_data: TechnicalData, price_data: pd.DataFrame) -> SignalStrength:
        """Calculate overall technical signal strength."""
        current_price = Decimal(str(price_data['Close'].iloc[-1]))
        score = tech_data.calculate_technical_score(current_price)
        
        # Convert score to signal strength
        if score >= 80:
            return SignalStrength.STRONG_BUY
        elif score >= 65:
            return SignalStrength.BUY
        elif score >= 55:
            return SignalStrength.WEAK_BUY
        elif score >= 45:
            return SignalStrength.NEUTRAL
        elif score >= 35:
            return SignalStrength.WEAK_SELL
        elif score >= 20:
            return SignalStrength.SELL
        else:
            return SignalStrength.STRONG_SELL
    
    async def _safe_analyze_technical(self, symbol: str, timeframe: TimeFrame) -> Optional[TechnicalData]:
        """Safely analyze technical data without raising exceptions."""
        try:
            return await self.analyze_technical(symbol, timeframe)
        except Exception as e:
            logger.warning(f"Failed to analyze {symbol} for {timeframe}: {e}")
            return None
    
    def _calculate_consensus_signal(self, analyses: Dict[str, TechnicalData]) -> SignalStrength:
        """Calculate consensus signal across multiple timeframes."""
        if not analyses:
            return SignalStrength.NEUTRAL
        
        # Weight signals by timeframe importance (longer timeframes have more weight)
        timeframe_weights = {
            TimeFrame.ONE_DAY.value: 1,
            TimeFrame.ONE_WEEK.value: 2,
            TimeFrame.ONE_MONTH.value: 3,
            TimeFrame.THREE_MONTHS.value: 4,
            TimeFrame.SIX_MONTHS.value: 4,
            TimeFrame.ONE_YEAR.value: 5,
            TimeFrame.TWO_YEARS.value: 5
        }
        
        signal_scores = {
            SignalStrength.STRONG_SELL: -3,
            SignalStrength.SELL: -2,
            SignalStrength.WEAK_SELL: -1,
            SignalStrength.NEUTRAL: 0,
            SignalStrength.WEAK_BUY: 1,
            SignalStrength.BUY: 2,
            SignalStrength.STRONG_BUY: 3
        }
        
        weighted_score = 0
        total_weight = 0
        
        for timeframe, analysis in analyses.items():
            weight = timeframe_weights.get(timeframe, 1)
            score = signal_scores.get(analysis.overall_signal, 0)
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            return SignalStrength.NEUTRAL
        
        avg_score = weighted_score / total_weight
        
        # Convert back to signal strength
        if avg_score >= 2.5:
            return SignalStrength.STRONG_BUY
        elif avg_score >= 1.5:
            return SignalStrength.BUY
        elif avg_score >= 0.5:
            return SignalStrength.WEAK_BUY
        elif avg_score >= -0.5:
            return SignalStrength.NEUTRAL
        elif avg_score >= -1.5:
            return SignalStrength.WEAK_SELL
        elif avg_score >= -2.5:
            return SignalStrength.SELL
        else:
            return SignalStrength.STRONG_SELL
    
    def _check_trend_alignment(self, analyses: Dict[str, TechnicalData]) -> bool:
        """Check if trends are aligned across timeframes."""
        if len(analyses) < 2:
            return True  # Single timeframe is always "aligned"
        
        trends = [analysis.trend_direction for analysis in analyses.values()]
        
        # Count trend directions
        trend_counts = {}
        for trend in trends:
            trend_counts[trend] = trend_counts.get(trend, 0) + 1
        
        # Consider aligned if majority (>50%) agree
        max_count = max(trend_counts.values())
        return max_count / len(trends) > 0.5
    
    def _aggregate_key_levels(self, analyses: Dict[str, TechnicalData]) -> Dict[str, List[SupportResistanceLevel]]:
        """Aggregate support and resistance levels across timeframes."""
        all_support = []
        all_resistance = []
        
        for analysis in analyses.values():
            all_support.extend(analysis.support_levels)
            all_resistance.extend(analysis.resistance_levels)
        
        # Group similar levels across timeframes
        key_support = self._consolidate_levels(all_support, 'support')
        key_resistance = self._consolidate_levels(all_resistance, 'resistance')
        
        return {
            'support': key_support[:3],  # Top 3 support levels
            'resistance': key_resistance[:3]  # Top 3 resistance levels
        }
    
    def _consolidate_levels(self, levels: List[SupportResistanceLevel], level_type: str) -> List[SupportResistanceLevel]:
        """Consolidate similar levels from different timeframes."""
        if not levels:
            return []
        
        # Group levels within 2% of each other
        tolerance = 0.02
        consolidated = []
        
        for level in levels:
            added_to_group = False
            
            for existing in consolidated:
                price_diff = abs(float(level.level) - float(existing.level)) / float(existing.level)
                if price_diff <= tolerance:
                    # Merge levels - take higher strength and more recent touch
                    if level.strength > existing.strength:
                        existing.strength = level.strength
                    if level.last_touch and (not existing.last_touch or level.last_touch > existing.last_touch):
                        existing.last_touch = level.last_touch
                    existing.touches += level.touches
                    added_to_group = True
                    break
            
            if not added_to_group:
                consolidated.append(level)
        
        # Sort by strength
        consolidated.sort(key=lambda x: x.strength, reverse=True)
        return consolidated
    
    def _safe_decimal(self, value: float) -> Optional[Decimal]:
        """Safely convert float to Decimal, handling NaN and infinity."""
        if np.isnan(value) or np.isinf(value):
            return None
        return Decimal(str(round(value, 4)))