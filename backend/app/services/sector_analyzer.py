"""
Sector Analysis Service.

This service provides comprehensive sector and industry analysis including:
- Sector performance comparison and trend analysis
- Sector rotation identification and momentum analysis
- Industry comparison with relative valuations and growth metrics
"""

import logging
import asyncio
import yfinance as yf
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from concurrent.futures import ThreadPoolExecutor
import statistics
import numpy as np

from ..models.sector import (
    SectorCategory, SectorPerformance, IndustryPerformance, SectorRotationSignal,
    SectorAnalysisResult, IndustryAnalysisResult, SectorComparisonResult,
    TrendDirection, RotationPhase
)
from ..models.stock import MarketData
from .data_aggregation import DataAggregationService, DataAggregationException


# Configure logging
logger = logging.getLogger(__name__)


class SectorAnalysisException(Exception):
    """Custom exception for sector analysis errors."""
    
    def __init__(self, message: str, error_type: str = "ANALYSIS_ERROR", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class SectorAnalyzer:
    """
    Sector Analysis Service.
    
    Provides comprehensive sector and industry analysis capabilities including
    performance comparison, rotation identification, and trend analysis.
    """
    
    def __init__(self, data_service: Optional[DataAggregationService] = None):
        """Initialize the sector analyzer."""
        self.data_service = data_service or DataAggregationService()
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        # Sector to stock mappings (representative stocks for each sector)
        self.sector_stocks = {
            SectorCategory.TECHNOLOGY: [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'NFLX',
                'ADBE', 'CRM', 'ORCL', 'INTC', 'AMD', 'QCOM', 'AVGO', 'TXN'
            ],
            SectorCategory.HEALTHCARE: [
                'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'BMY', 'MRK',
                'DHR', 'LLY', 'MDT', 'GILD', 'AMGN', 'CVS', 'CI', 'HUM'
            ],
            SectorCategory.FINANCIAL_SERVICES: [
                'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BRK-B', 'V', 'MA',
                'AXP', 'BLK', 'SPGI', 'CME', 'ICE', 'COF', 'USB'
            ],
            SectorCategory.CONSUMER_CYCLICAL: [
                'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'TJX', 'LOW',
                'BKNG', 'GM', 'F', 'MAR', 'HLT', 'YUM', 'CMG', 'ORLY'
            ],
            SectorCategory.CONSUMER_DEFENSIVE: [
                'WMT', 'PG', 'KO', 'PEP', 'COST', 'WBA', 'KR', 'SYY',
                'GIS', 'K', 'HSY', 'CPB', 'CAG', 'TSN', 'HRL', 'CLX'
            ],
            SectorCategory.COMMUNICATION_SERVICES: [
                'GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA', 'VZ', 'T', 'CHTR',
                'TMUS', 'TWTR', 'SNAP', 'PINS', 'ROKU', 'SPOT', 'ZM', 'DOCU'
            ],
            SectorCategory.INDUSTRIALS: [
                'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'FDX', 'LMT',
                'RTX', 'DE', 'EMR', 'ETN', 'ITW', 'PH', 'ROK', 'DOV'
            ],
            SectorCategory.ENERGY: [
                'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'VLO', 'PSX',
                'OXY', 'BKR', 'HAL', 'DVN', 'FANG', 'MRO', 'APA', 'HES'
            ],
            SectorCategory.UTILITIES: [
                'NEE', 'DUK', 'SO', 'D', 'AEP', 'EXC', 'XEL', 'SRE',
                'PEG', 'ED', 'FE', 'ETR', 'ES', 'AWK', 'PPL', 'CMS'
            ],
            SectorCategory.REAL_ESTATE: [
                'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'DLR', 'O',
                'SBAC', 'EXR', 'AVB', 'EQR', 'VTR', 'ESS', 'MAA', 'UDR'
            ],
            SectorCategory.MATERIALS: [
                'LIN', 'APD', 'SHW', 'FCX', 'NEM', 'ECL', 'DD', 'DOW',
                'PPG', 'NUE', 'VMC', 'MLM', 'PKG', 'IP', 'CF', 'MOS'
            ]
        }
        
        # Industry mappings within sectors
        self.sector_industries = {
            SectorCategory.TECHNOLOGY: {
                'Software - Application': ['MSFT', 'ORCL', 'CRM', 'ADBE', 'INTU'],
                'Software - Infrastructure': ['MSFT', 'ORCL', 'VMW', 'NOW', 'TEAM'],
                'Semiconductors': ['NVDA', 'INTC', 'AMD', 'QCOM', 'AVGO', 'TXN'],
                'Consumer Electronics': ['AAPL', 'TSLA'],
                'Internet Content & Information': ['GOOGL', 'META', 'NFLX'],
                'Electronic Components': ['TXN', 'ADI', 'MCHP', 'KLAC']
            },
            SectorCategory.HEALTHCARE: {
                'Drug Manufacturers - Major': ['JNJ', 'PFE', 'ABBV', 'MRK', 'LLY'],
                'Medical Devices': ['TMO', 'ABT', 'MDT', 'DHR', 'SYK'],
                'Biotechnology': ['GILD', 'AMGN', 'REGN', 'BIIB', 'VRTX'],
                'Health Insurance': ['UNH', 'CVS', 'CI', 'HUM', 'ANTM'],
                'Diagnostics & Research': ['TMO', 'DHR', 'A', 'IQV', 'LH']
            },
            SectorCategory.FINANCIAL_SERVICES: {
                'Banks - Diversified': ['JPM', 'BAC', 'WFC', 'C'],
                'Investment Banking & Brokerage': ['GS', 'MS', 'SCHW'],
                'Credit Services': ['V', 'MA', 'AXP', 'COF'],
                'Asset Management': ['BLK', 'BK', 'TROW', 'IVZ'],
                'Insurance - Diversified': ['BRK-B', 'AIG', 'TRV', 'ALL']
            }
        }
    
    async def analyze_all_sectors(self) -> SectorAnalysisResult:
        """
        Perform comprehensive analysis of all sectors.
        
        Returns:
            Complete sector analysis with performance, rankings, and rotation signals
        """
        try:
            logger.info("Starting comprehensive sector analysis")
            start_time = datetime.now()
            
            # Analyze all sectors concurrently
            sector_tasks = []
            for sector in SectorCategory:
                task = asyncio.create_task(self._analyze_single_sector(sector))
                sector_tasks.append((sector, task))
            
            # Wait for all sector analyses to complete
            sector_performances = []
            for sector, task in sector_tasks:
                try:
                    performance = await task
                    if performance:
                        sector_performances.append(performance)
                except Exception as e:
                    logger.warning(f"Failed to analyze sector {sector}: {e}")
            
            if not sector_performances:
                raise SectorAnalysisException(
                    "Failed to analyze any sectors",
                    error_type="NO_DATA",
                    suggestions=["Check data sources", "Try again later"]
                )
            
            # Sort sectors by performance for rankings
            sorted_1m = sorted(sector_performances, key=lambda x: x.performance_1m, reverse=True)
            sorted_3m = sorted(sector_performances, key=lambda x: x.performance_3m, reverse=True)
            sorted_1y = sorted(sector_performances, key=lambda x: x.performance_1y, reverse=True)
            
            # Identify rotation signals
            rotation_signals = await self._identify_rotation_signals(sector_performances)
            
            # Determine market context
            market_trend = self._determine_market_trend(sector_performances)
            market_phase = self._determine_market_phase(sector_performances)
            volatility_regime = self._determine_volatility_regime(sector_performances)
            
            result = SectorAnalysisResult(
                sector_performances=sector_performances,
                top_performers_1m=[s.sector for s in sorted_1m[:3]],
                top_performers_3m=[s.sector for s in sorted_3m[:3]],
                top_performers_1y=[s.sector for s in sorted_1y[:3]],
                bottom_performers_1m=[s.sector for s in sorted_1m[-3:]],
                bottom_performers_3m=[s.sector for s in sorted_3m[-3:]],
                bottom_performers_1y=[s.sector for s in sorted_1y[-3:]],
                rotation_signals=rotation_signals,
                market_trend=market_trend,
                market_phase=market_phase,
                volatility_regime=volatility_regime,
                data_freshness={
                    'sector_analysis': datetime.now(),
                    'market_data': datetime.now()
                }
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Sector analysis completed in {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Sector analysis failed: {e}")
            if isinstance(e, SectorAnalysisException):
                raise e
            raise SectorAnalysisException(
                f"Failed to perform sector analysis: {str(e)}",
                error_type="ANALYSIS_FAILED",
                suggestions=["Try again later", "Check data connectivity"]
            )
    
    async def analyze_sector_industries(self, sector: SectorCategory) -> IndustryAnalysisResult:
        """
        Analyze industries within a specific sector.
        
        Args:
            sector: Sector to analyze
            
        Returns:
            Industry analysis result for the sector
        """
        try:
            logger.info(f"Analyzing industries in {sector} sector")
            
            # Get sector performance
            sector_performance = await self._analyze_single_sector(sector)
            if not sector_performance:
                raise SectorAnalysisException(
                    f"Failed to get sector performance for {sector}",
                    error_type="NO_DATA"
                )
            
            # Analyze industries within the sector
            industries = self.sector_industries.get(sector, {})
            if not industries:
                logger.warning(f"No industry mapping found for {sector}")
                return IndustryAnalysisResult(
                    sector=sector,
                    industries=[],
                    top_performing_industries=[],
                    best_value_industries=[],
                    highest_growth_industries=[],
                    sector_summary=sector_performance
                )
            
            # Analyze each industry
            industry_tasks = []
            for industry_name, stocks in industries.items():
                task = asyncio.create_task(
                    self._analyze_single_industry(industry_name, sector, stocks)
                )
                industry_tasks.append((industry_name, task))
            
            industry_performances = []
            for industry_name, task in industry_tasks:
                try:
                    performance = await task
                    if performance:
                        industry_performances.append(performance)
                except Exception as e:
                    logger.warning(f"Failed to analyze industry {industry_name}: {e}")
            
            # Sort industries by different metrics
            perf_sorted = sorted(industry_performances, key=lambda x: x.performance_3m, reverse=True)
            value_sorted = sorted(
                [i for i in industry_performances if i.avg_pe_ratio],
                key=lambda x: x.avg_pe_ratio
            )
            growth_sorted = sorted(
                [i for i in industry_performances if i.revenue_growth],
                key=lambda x: x.revenue_growth, reverse=True
            )
            
            result = IndustryAnalysisResult(
                sector=sector,
                industries=industry_performances,
                top_performing_industries=[i.industry for i in perf_sorted[:3]],
                best_value_industries=[i.industry for i in value_sorted[:3]],
                highest_growth_industries=[i.industry for i in growth_sorted[:3]],
                sector_summary=sector_performance
            )
            
            logger.info(f"Analyzed {len(industry_performances)} industries in {sector}")
            return result
            
        except Exception as e:
            logger.error(f"Industry analysis failed for {sector}: {e}")
            if isinstance(e, SectorAnalysisException):
                raise e
            raise SectorAnalysisException(
                f"Failed to analyze industries in {sector}: {str(e)}",
                error_type="ANALYSIS_FAILED"
            )
    
    async def compare_sectors(
        self,
        sectors: List[SectorCategory],
        timeframe: str = "3m"
    ) -> SectorComparisonResult:
        """
        Compare performance of multiple sectors.
        
        Args:
            sectors: List of sectors to compare
            timeframe: Comparison timeframe
            
        Returns:
            Sector comparison result
        """
        try:
            logger.info(f"Comparing {len(sectors)} sectors over {timeframe}")
            
            # Analyze each sector
            sector_tasks = []
            for sector in sectors:
                task = asyncio.create_task(self._analyze_single_sector(sector))
                sector_tasks.append((sector, task))
            
            sector_performances = {}
            for sector, task in sector_tasks:
                try:
                    performance = await task
                    if performance:
                        sector_performances[sector] = performance
                except Exception as e:
                    logger.warning(f"Failed to analyze sector {sector}: {e}")
            
            if not sector_performances:
                raise SectorAnalysisException(
                    "Failed to analyze any sectors for comparison",
                    error_type="NO_DATA"
                )
            
            # Create rankings
            performance_attr = f"performance_{timeframe}"
            performance_ranking = []
            valuation_ranking = []
            momentum_ranking = []
            
            for sector, perf in sector_performances.items():
                performance_ranking.append({
                    'sector': sector,
                    'performance': getattr(perf, performance_attr, 0),
                    'rank': 0  # Will be set after sorting
                })
                
                valuation_ranking.append({
                    'sector': sector,
                    'pe_ratio': perf.pe_ratio,
                    'pb_ratio': perf.pb_ratio,
                    'rank': 0
                })
                
                momentum_ranking.append({
                    'sector': sector,
                    'momentum_score': perf.momentum_score,
                    'trend_strength': perf.trend_strength,
                    'rank': 0
                })
            
            # Sort and assign ranks
            performance_ranking.sort(key=lambda x: x['performance'], reverse=True)
            for i, item in enumerate(performance_ranking):
                item['rank'] = i + 1
            
            valuation_ranking.sort(key=lambda x: x['pe_ratio'] or 999)
            for i, item in enumerate(valuation_ranking):
                item['rank'] = i + 1
            
            momentum_ranking.sort(key=lambda x: x['momentum_score'], reverse=True)
            for i, item in enumerate(momentum_ranking):
                item['rank'] = i + 1
            
            # Determine winners
            winner = performance_ranking[0]['sector']
            best_value = valuation_ranking[0]['sector']
            strongest_momentum = momentum_ranking[0]['sector']
            
            # Generate insights
            key_insights = self._generate_comparison_insights(
                sector_performances, timeframe
            )
            recommendations = self._generate_comparison_recommendations(
                sector_performances, performance_ranking, valuation_ranking
            )
            
            result = SectorComparisonResult(
                sectors=sectors,
                timeframe=timeframe,
                performance_ranking=performance_ranking,
                valuation_ranking=valuation_ranking,
                momentum_ranking=momentum_ranking,
                winner=winner,
                best_value=best_value,
                strongest_momentum=strongest_momentum,
                key_insights=key_insights,
                recommendations=recommendations
            )
            
            logger.info(f"Sector comparison completed for {len(sectors)} sectors")
            return result
            
        except Exception as e:
            logger.error(f"Sector comparison failed: {e}")
            if isinstance(e, SectorAnalysisException):
                raise e
            raise SectorAnalysisException(
                f"Failed to compare sectors: {str(e)}",
                error_type="COMPARISON_FAILED"
            )
    
    # Private helper methods
    
    async def _analyze_single_sector(self, sector: SectorCategory) -> Optional[SectorPerformance]:
        """Analyze performance of a single sector."""
        try:
            stocks = self.sector_stocks.get(sector, [])
            if not stocks:
                logger.warning(f"No stocks defined for sector {sector}")
                return None
            
            # Get market data for all stocks in the sector
            market_data_list = []
            for symbol in stocks[:10]:  # Limit to top 10 stocks for performance
                try:
                    market_data = await self.data_service.get_market_data(symbol)
                    market_data_list.append(market_data)
                except Exception as e:
                    logger.debug(f"Failed to get data for {symbol}: {e}")
            
            if not market_data_list:
                logger.warning(f"No market data available for sector {sector}")
                return None
            
            # Calculate sector metrics
            sector_metrics = await self._calculate_sector_metrics(market_data_list)
            
            # Get historical performance (simulated for now)
            performance_metrics = self._calculate_performance_metrics(market_data_list)
            
            # Calculate trend and momentum
            trend_direction = self._calculate_trend_direction(performance_metrics)
            trend_strength = self._calculate_trend_strength(performance_metrics)
            momentum_score = self._calculate_momentum_score(performance_metrics)
            
            # Create sector performance object
            performance = SectorPerformance(
                sector=sector,
                performance_1d=performance_metrics['1d'],
                performance_1w=performance_metrics['1w'],
                performance_1m=performance_metrics['1m'],
                performance_3m=performance_metrics['3m'],
                performance_6m=performance_metrics['6m'],
                performance_1y=performance_metrics['1y'],
                performance_ytd=performance_metrics['ytd'],
                relative_performance_1m=performance_metrics['rel_1m'],
                relative_performance_3m=performance_metrics['rel_3m'],
                relative_performance_1y=performance_metrics['rel_1y'],
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                momentum_score=momentum_score,
                market_cap=sector_metrics['market_cap'],
                avg_volume=sector_metrics['avg_volume'],
                pe_ratio=sector_metrics['pe_ratio'],
                pb_ratio=sector_metrics['pb_ratio'],
                performance_rank_1m=1,  # Will be set during ranking
                performance_rank_3m=1,
                performance_rank_1y=1,
                volatility=sector_metrics['volatility'],
                beta=sector_metrics['beta'],
                dividend_yield=sector_metrics['dividend_yield']
            )
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to analyze sector {sector}: {e}")
            return None
    
    async def _analyze_single_industry(
        self,
        industry_name: str,
        sector: SectorCategory,
        stocks: List[str]
    ) -> Optional[IndustryPerformance]:
        """Analyze performance of a single industry."""
        try:
            # Get market data for industry stocks
            market_data_list = []
            for symbol in stocks:
                try:
                    market_data = await self.data_service.get_market_data(symbol)
                    market_data_list.append(market_data)
                except Exception as e:
                    logger.debug(f"Failed to get data for {symbol}: {e}")
            
            if not market_data_list:
                return None
            
            # Calculate industry metrics
            industry_metrics = await self._calculate_industry_metrics(market_data_list)
            
            # Get performance metrics
            performance_metrics = self._calculate_performance_metrics(market_data_list)
            
            performance = IndustryPerformance(
                industry=industry_name,
                sector=sector,
                performance_1d=performance_metrics['1d'],
                performance_1w=performance_metrics['1w'],
                performance_1m=performance_metrics['1m'],
                performance_3m=performance_metrics['3m'],
                performance_1y=performance_metrics['1y'],
                relative_to_sector_1m=Decimal('0'),  # Would calculate vs sector
                relative_to_sector_3m=Decimal('0'),
                relative_to_sector_1y=Decimal('0'),
                avg_pe_ratio=industry_metrics['pe_ratio'],
                avg_pb_ratio=industry_metrics['pb_ratio'],
                avg_roe=industry_metrics['roe'],
                avg_profit_margin=industry_metrics['profit_margin'],
                revenue_growth=industry_metrics['revenue_growth'],
                earnings_growth=industry_metrics['earnings_growth'],
                market_cap=industry_metrics['market_cap'],
                stock_count=len(market_data_list),
                performance_rank=1,  # Will be set during ranking
                valuation_rank=1,
                growth_rank=1
            )
            
            return performance
            
        except Exception as e:
            logger.error(f"Failed to analyze industry {industry_name}: {e}")
            return None
    
    async def _calculate_sector_metrics(self, market_data_list: List[MarketData]) -> Dict[str, Any]:
        """Calculate aggregated sector metrics."""
        if not market_data_list:
            return {}
        
        # Calculate weighted averages and totals
        total_market_cap = sum(md.market_cap or 0 for md in market_data_list)
        total_volume = sum(md.volume for md in market_data_list)
        avg_volume = int(statistics.mean(md.avg_volume or 0 for md in market_data_list if md.avg_volume))
        
        # Calculate average P/E ratio (excluding None values)
        pe_ratios = [float(md.pe_ratio) for md in market_data_list if md.pe_ratio]
        avg_pe = Decimal(str(statistics.mean(pe_ratios))) if pe_ratios else None
        
        # Simulated additional metrics
        volatility = Decimal(str(np.random.uniform(15, 35)))  # Simulated volatility
        beta = Decimal(str(np.random.uniform(0.8, 1.3)))  # Simulated beta
        dividend_yield = Decimal(str(np.random.uniform(0, 4)))  # Simulated dividend yield
        
        return {
            'market_cap': total_market_cap,
            'avg_volume': avg_volume,
            'pe_ratio': avg_pe,
            'pb_ratio': Decimal(str(np.random.uniform(1, 5))),  # Simulated
            'volatility': volatility,
            'beta': beta,
            'dividend_yield': dividend_yield
        }
    
    async def _calculate_industry_metrics(self, market_data_list: List[MarketData]) -> Dict[str, Any]:
        """Calculate aggregated industry metrics."""
        if not market_data_list:
            return {}
        
        total_market_cap = sum(md.market_cap or 0 for md in market_data_list)
        
        # Calculate average P/E ratio
        pe_ratios = [float(md.pe_ratio) for md in market_data_list if md.pe_ratio]
        avg_pe = Decimal(str(statistics.mean(pe_ratios))) if pe_ratios else None
        
        # Simulated metrics (in production, these would come from fundamental data)
        return {
            'market_cap': total_market_cap,
            'pe_ratio': avg_pe,
            'pb_ratio': Decimal(str(np.random.uniform(1, 6))),
            'roe': Decimal(str(np.random.uniform(0.05, 0.25))),
            'profit_margin': Decimal(str(np.random.uniform(0.05, 0.30))),
            'revenue_growth': Decimal(str(np.random.uniform(-0.05, 0.20))),
            'earnings_growth': Decimal(str(np.random.uniform(-0.10, 0.25)))
        }
    
    def _calculate_performance_metrics(self, market_data_list: List[MarketData]) -> Dict[str, Decimal]:
        """Calculate performance metrics for a group of stocks."""
        # In production, this would use historical price data
        # For now, we'll simulate performance based on current change data
        
        if not market_data_list:
            return {k: Decimal('0') for k in ['1d', '1w', '1m', '3m', '6m', '1y', 'ytd', 'rel_1m', 'rel_3m', 'rel_1y']}
        
        # Use current day change as basis for simulation
        avg_change = statistics.mean(float(md.change_percent) for md in market_data_list)
        
        # Simulate different timeframe performances
        performance_1d = Decimal(str(avg_change))
        performance_1w = Decimal(str(avg_change * np.random.uniform(3, 7)))
        performance_1m = Decimal(str(avg_change * np.random.uniform(8, 15)))
        performance_3m = Decimal(str(avg_change * np.random.uniform(20, 40)))
        performance_6m = Decimal(str(avg_change * np.random.uniform(35, 70)))
        performance_1y = Decimal(str(avg_change * np.random.uniform(60, 120)))
        performance_ytd = Decimal(str(avg_change * np.random.uniform(10, 30)))
        
        # Simulate relative performance (vs market)
        market_performance_1m = Decimal(str(np.random.uniform(-5, 15)))
        market_performance_3m = Decimal(str(np.random.uniform(-10, 25)))
        market_performance_1y = Decimal(str(np.random.uniform(-15, 35)))
        
        return {
            '1d': performance_1d,
            '1w': performance_1w,
            '1m': performance_1m,
            '3m': performance_3m,
            '6m': performance_6m,
            '1y': performance_1y,
            'ytd': performance_ytd,
            'rel_1m': performance_1m - market_performance_1m,
            'rel_3m': performance_3m - market_performance_3m,
            'rel_1y': performance_1y - market_performance_1y
        }
    
    def _calculate_trend_direction(self, performance_metrics: Dict[str, Decimal]) -> TrendDirection:
        """Determine trend direction based on performance."""
        perf_3m = float(performance_metrics['3m'])
        perf_1m = float(performance_metrics['1m'])
        
        if perf_3m > 15 and perf_1m > 5:
            return TrendDirection.STRONG_UP
        elif perf_3m > 5 and perf_1m > 0:
            return TrendDirection.UP
        elif perf_3m < -15 and perf_1m < -5:
            return TrendDirection.STRONG_DOWN
        elif perf_3m < -5 and perf_1m < 0:
            return TrendDirection.DOWN
        else:
            return TrendDirection.SIDEWAYS
    
    def _calculate_trend_strength(self, performance_metrics: Dict[str, Decimal]) -> int:
        """Calculate trend strength score."""
        perf_1m = abs(float(performance_metrics['1m']))
        perf_3m = abs(float(performance_metrics['3m']))
        
        # Strength based on consistency and magnitude
        strength = min(100, int((perf_1m + perf_3m) * 2))
        return max(0, strength)
    
    def _calculate_momentum_score(self, performance_metrics: Dict[str, Decimal]) -> int:
        """Calculate momentum score."""
        perf_1w = float(performance_metrics['1w'])
        perf_1m = float(performance_metrics['1m'])
        perf_3m = float(performance_metrics['3m'])
        
        # Momentum based on recent vs longer-term performance
        if perf_1w > perf_1m > perf_3m:
            momentum = 80 + min(20, int(perf_1w))
        elif perf_1w > 0 and perf_1m > 0:
            momentum = 60 + min(20, int((perf_1w + perf_1m) / 2))
        elif perf_1w > 0:
            momentum = 50 + min(10, int(perf_1w))
        else:
            momentum = max(0, 50 + int(perf_1w))
        
        return min(100, max(0, momentum))
    
    async def _identify_rotation_signals(
        self,
        sector_performances: List[SectorPerformance]
    ) -> List[SectorRotationSignal]:
        """Identify sector rotation signals."""
        signals = []
        
        # Sort by momentum change (simulated)
        momentum_sorted = sorted(sector_performances, key=lambda x: x.momentum_score, reverse=True)
        
        if len(momentum_sorted) >= 2:
            # Create rotation signal from weakest to strongest momentum
            from_sector = momentum_sorted[-1].sector
            to_sector = momentum_sorted[0].sector
            
            momentum_diff = momentum_sorted[0].momentum_score - momentum_sorted[-1].momentum_score
            
            if momentum_diff > 30:  # Significant momentum difference
                signal = SectorRotationSignal(
                    from_sector=from_sector,
                    to_sector=to_sector,
                    signal_strength=min(100, momentum_diff),
                    confidence=70,
                    momentum_shift=Decimal(str(momentum_diff)),
                    relative_strength_change=Decimal(str(momentum_diff * 0.5)),
                    volume_confirmation=True,
                    market_phase=RotationPhase.MID_CYCLE,
                    economic_driver="Market momentum shift",
                    signal_date=datetime.now() - timedelta(days=3),
                    expected_duration="1-2 months",
                    reasons=[
                        f"{to_sector} showing strong momentum",
                        f"{from_sector} losing relative strength",
                        "Volume confirming the rotation"
                    ],
                    risks=[
                        "Market volatility could reverse rotation",
                        "Economic data could change sector preferences"
                    ]
                )
                signals.append(signal)
        
        return signals
    
    def _determine_market_trend(self, sector_performances: List[SectorPerformance]) -> TrendDirection:
        """Determine overall market trend from sector performances."""
        if not sector_performances:
            return TrendDirection.SIDEWAYS
        
        avg_performance = statistics.mean(float(sp.performance_1m) for sp in sector_performances)
        
        if avg_performance > 10:
            return TrendDirection.STRONG_UP
        elif avg_performance > 3:
            return TrendDirection.UP
        elif avg_performance < -10:
            return TrendDirection.STRONG_DOWN
        elif avg_performance < -3:
            return TrendDirection.DOWN
        else:
            return TrendDirection.SIDEWAYS
    
    def _determine_market_phase(self, sector_performances: List[SectorPerformance]) -> RotationPhase:
        """Determine current market cycle phase."""
        # Simplified logic based on sector performance patterns
        tech_perf = next((sp for sp in sector_performances if sp.sector == SectorCategory.TECHNOLOGY), None)
        energy_perf = next((sp for sp in sector_performances if sp.sector == SectorCategory.ENERGY), None)
        
        if tech_perf and energy_perf:
            if float(tech_perf.performance_3m) > float(energy_perf.performance_3m):
                return RotationPhase.EARLY_CYCLE
            else:
                return RotationPhase.LATE_CYCLE
        
        return RotationPhase.MID_CYCLE
    
    def _determine_volatility_regime(self, sector_performances: List[SectorPerformance]) -> str:
        """Determine current volatility regime."""
        if not sector_performances:
            return "normal"
        
        avg_volatility = statistics.mean(float(sp.volatility) for sp in sector_performances)
        
        if avg_volatility > 30:
            return "high"
        elif avg_volatility > 20:
            return "elevated"
        elif avg_volatility < 15:
            return "low"
        else:
            return "normal"
    
    def _generate_comparison_insights(
        self,
        sector_performances: Dict[SectorCategory, SectorPerformance],
        timeframe: str
    ) -> List[str]:
        """Generate insights from sector comparison."""
        insights = []
        
        # Find best and worst performers
        performances = list(sector_performances.values())
        if not performances:
            return insights
        
        performance_attr = f"performance_{timeframe}"
        best_perf = max(performances, key=lambda x: getattr(x, performance_attr, 0))
        worst_perf = min(performances, key=lambda x: getattr(x, performance_attr, 0))
        
        best_return = getattr(best_perf, performance_attr, 0)
        worst_return = getattr(worst_perf, performance_attr, 0)
        
        insights.append(
            f"{best_perf.sector} leads with {best_return:.1f}% return over {timeframe}"
        )
        insights.append(
            f"{worst_perf.sector} lags with {worst_return:.1f}% return over {timeframe}"
        )
        
        # Performance spread
        spread = float(best_return - worst_return)
        insights.append(
            f"Performance spread of {spread:.1f}% indicates {'high' if spread > 20 else 'moderate'} sector dispersion"
        )
        
        return insights
    
    def _generate_comparison_recommendations(
        self,
        sector_performances: Dict[SectorCategory, SectorPerformance],
        performance_ranking: List[Dict[str, Any]],
        valuation_ranking: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate investment recommendations from sector comparison."""
        recommendations = []
        
        if performance_ranking:
            top_performer = performance_ranking[0]['sector']
            recommendations.append(
                f"Consider overweighting {top_performer} based on strong momentum"
            )
        
        if valuation_ranking:
            best_value = valuation_ranking[0]['sector']
            recommendations.append(
                f"Consider {best_value} for value-oriented allocation"
            )
        
        recommendations.append(
            "Diversify across multiple sectors to manage risk"
        )
        
        return recommendations