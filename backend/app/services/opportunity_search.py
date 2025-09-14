"""
Investment Opportunity Search Service.

This service provides stock screening capabilities to identify investment opportunities
based on fundamental, technical, and performance criteria. It combines multiple
analysis engines to rank and filter stocks according to user-defined criteria.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf

from ..models.opportunity import (
    OpportunitySearchFilters, InvestmentOpportunity, OpportunitySearchResult,
    OpportunityScore, OpportunityType, RiskLevel, MarketCapCategory, OpportunityRanking
)
from ..models.stock import MarketData, Stock
from ..models.fundamental import FundamentalData
from ..models.technical import TechnicalData, TimeFrame
from .data_aggregation import DataAggregationService, DataAggregationException
from .fundamental_analyzer import FundamentalAnalyzer
from .technical_analyzer import TechnicalAnalyzer
from .analysis_engine import AnalysisEngine


# Configure logging
logger = logging.getLogger(__name__)


class OpportunitySearchException(Exception):
    """Custom exception for opportunity search errors."""
    
    def __init__(self, message: str, error_type: str = "SEARCH_ERROR", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class OpportunitySearchService:
    """
    Investment Opportunity Search Service.
    
    Provides comprehensive stock screening and opportunity identification
    capabilities with filtering, ranking, and detailed analysis.
    """
    
    def __init__(
        self,
        data_service: Optional[DataAggregationService] = None,
        fundamental_analyzer: Optional[FundamentalAnalyzer] = None,
        technical_analyzer: Optional[TechnicalAnalyzer] = None,
        analysis_engine: Optional[AnalysisEngine] = None
    ):
        """Initialize the opportunity search service."""
        self.data_service = data_service or DataAggregationService()
        self.fundamental_analyzer = fundamental_analyzer or FundamentalAnalyzer(self.data_service)
        self.technical_analyzer = technical_analyzer or TechnicalAnalyzer(self.data_service)
        self.analysis_engine = analysis_engine or AnalysisEngine()
        self.executor = ThreadPoolExecutor(max_workers=8)
        
        # Market cap thresholds (in USD)
        self.market_cap_thresholds = {
            MarketCapCategory.MEGA_CAP: (200_000_000_000, None),
            MarketCapCategory.LARGE_CAP: (10_000_000_000, 200_000_000_000),
            MarketCapCategory.MID_CAP: (2_000_000_000, 10_000_000_000),
            MarketCapCategory.SMALL_CAP: (300_000_000, 2_000_000_000),
            MarketCapCategory.MICRO_CAP: (None, 300_000_000)
        }
        
        # Popular stock universes for screening
        self.stock_universes = {
            'sp500': self._get_sp500_symbols,
            'nasdaq100': self._get_nasdaq100_symbols,
            'russell2000': self._get_russell2000_symbols,
            'popular': self._get_popular_symbols
        }
    
    async def search_opportunities(
        self,
        filters: OpportunitySearchFilters,
        ranking: Optional[OpportunityRanking] = None,
        universe: str = 'popular'
    ) -> OpportunitySearchResult:
        """
        Search for investment opportunities based on specified filters.
        
        Args:
            filters: Search filters and criteria
            ranking: Ranking preferences for results
            universe: Stock universe to search ('sp500', 'nasdaq100', 'popular')
            
        Returns:
            OpportunitySearchResult with matching opportunities
            
        Raises:
            OpportunitySearchException: If search cannot be performed
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting opportunity search with {len(filters.dict(exclude_none=True))} filters")
            
            # Get stock universe to search
            symbols = await self._get_stock_universe(universe)
            logger.info(f"Searching {len(symbols)} symbols from {universe} universe")
            
            # Apply initial filters to reduce search space
            filtered_symbols = await self._apply_initial_filters(symbols, filters)
            logger.info(f"After initial filtering: {len(filtered_symbols)} symbols remain")
            
            if not filtered_symbols:
                return OpportunitySearchResult(
                    opportunities=[],
                    total_found=0,
                    filters_applied=filters,
                    search_timestamp=start_time,
                    execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    stats={'symbols_screened': len(symbols), 'symbols_analyzed': 0}
                )
            
            # Analyze opportunities in batches
            opportunities = await self._analyze_opportunities(filtered_symbols, filters)
            logger.info(f"Found {len(opportunities)} potential opportunities")
            
            # Rank and sort opportunities
            if ranking:
                opportunities = self._rank_opportunities(opportunities, ranking)
            else:
                opportunities.sort(key=lambda x: x.scores.overall_score, reverse=True)
            
            # Apply final filters and limits
            final_opportunities = self._apply_final_filters(opportunities, filters)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = OpportunitySearchResult(
                opportunities=final_opportunities[:filters.limit],
                total_found=len(final_opportunities),
                filters_applied=filters,
                search_timestamp=start_time,
                execution_time_ms=execution_time,
                stats={
                    'symbols_screened': len(symbols),
                    'symbols_analyzed': len(filtered_symbols),
                    'opportunities_found': len(final_opportunities),
                    'execution_time_ms': execution_time
                }
            )
            
            logger.info(f"Opportunity search completed in {execution_time}ms, found {len(final_opportunities)} opportunities")
            return result
            
        except Exception as e:
            logger.error(f"Opportunity search failed: {e}")
            if isinstance(e, OpportunitySearchException):
                raise e
            raise OpportunitySearchException(
                f"Failed to search for opportunities: {str(e)}",
                error_type="SEARCH_FAILED",
                suggestions=[
                    "Try with fewer filters",
                    "Check filter values are reasonable",
                    "Try again later"
                ]
            )
    
    async def get_opportunity_details(self, symbol: str) -> InvestmentOpportunity:
        """
        Get detailed opportunity analysis for a specific symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Detailed investment opportunity analysis
        """
        try:
            logger.info(f"Getting detailed opportunity analysis for {symbol}")
            
            # Get comprehensive analysis
            analysis_result = await self.analysis_engine.analyze_stock(
                symbol,
                include_fundamental=True,
                include_technical=True,
                include_sentiment=True
            )
            
            # Convert to opportunity format
            opportunity = await self._create_opportunity_from_analysis(analysis_result)
            
            logger.info(f"Generated detailed opportunity analysis for {symbol}")
            return opportunity
            
        except Exception as e:
            logger.error(f"Failed to get opportunity details for {symbol}: {e}")
            raise OpportunitySearchException(
                f"Failed to analyze opportunity for {symbol}: {str(e)}",
                error_type="ANALYSIS_FAILED",
                suggestions=[
                    "Verify symbol exists",
                    "Try again later",
                    "Check if market data is available"
                ]
            )
    
    async def get_sector_opportunities(
        self,
        sector: str,
        limit: int = 10,
        min_market_cap: Optional[int] = None
    ) -> List[InvestmentOpportunity]:
        """
        Find top opportunities within a specific sector.
        
        Args:
            sector: Sector name to search
            limit: Maximum number of opportunities to return
            min_market_cap: Minimum market cap filter
            
        Returns:
            List of top opportunities in the sector
        """
        filters = OpportunitySearchFilters(
            sectors=[sector],
            market_cap_min=min_market_cap,
            limit=limit
        )
        
        result = await self.search_opportunities(filters)
        return result.opportunities
    
    async def get_trending_opportunities(
        self,
        timeframe: str = '1d',
        limit: int = 20
    ) -> List[InvestmentOpportunity]:
        """
        Find opportunities based on recent price momentum.
        
        Args:
            timeframe: Timeframe for momentum ('1d', '1w', '1m')
            limit: Maximum number of opportunities to return
            
        Returns:
            List of trending opportunities
        """
        # Set momentum filters based on timeframe
        filters = OpportunitySearchFilters(
            opportunity_types=[OpportunityType.MOMENTUM],
            limit=limit
        )
        
        if timeframe == '1d':
            filters.price_change_1d_min = Decimal('2.0')  # At least 2% gain
        elif timeframe == '1w':
            filters.price_change_1w_min = Decimal('5.0')  # At least 5% gain
        elif timeframe == '1m':
            filters.price_change_1m_min = Decimal('10.0')  # At least 10% gain
        
        result = await self.search_opportunities(filters)
        return result.opportunities
    
    # Private helper methods
    
    async def _get_stock_universe(self, universe: str) -> List[str]:
        """Get list of symbols for the specified universe."""
        if universe in self.stock_universes:
            return await self.stock_universes[universe]()
        else:
            logger.warning(f"Unknown universe '{universe}', using popular stocks")
            return await self._get_popular_symbols()
    
    async def _get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 symbols."""
        try:
            # This would typically come from a data provider or cached list
            # For now, return a subset of popular large-cap stocks
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
                'UNH', 'JNJ', 'JPM', 'V', 'PG', 'HD', 'MA', 'DIS', 'PYPL', 'ADBE',
                'NFLX', 'CRM', 'CMCSA', 'XOM', 'ABT', 'VZ', 'KO', 'PFE', 'NKE',
                'TMO', 'ABBV', 'ACN', 'COST', 'AVGO', 'DHR', 'TXN', 'NEE', 'LIN',
                'WMT', 'BMY', 'QCOM', 'HON', 'UPS', 'LOW', 'ORCL', 'IBM', 'AMD',
                'SBUX', 'CVX', 'MDT', 'AMGN', 'BA', 'CAT', 'GS', 'BLK', 'AXP'
            ]
        except Exception as e:
            logger.warning(f"Failed to get S&P 500 symbols: {e}")
            return await self._get_popular_symbols()
    
    async def _get_nasdaq100_symbols(self) -> List[str]:
        """Get NASDAQ 100 symbols."""
        try:
            return [
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA',
                'PYPL', 'ADBE', 'NFLX', 'CRM', 'INTC', 'CMCSA', 'PEP', 'AVGO',
                'TXN', 'QCOM', 'COST', 'SBUX', 'INTU', 'AMAT', 'BKNG', 'ISRG',
                'AMD', 'MU', 'GILD', 'MDLZ', 'ADP', 'CSX', 'REGN', 'ATVI', 'FISV',
                'MELI', 'LRCX', 'ADI', 'KLAC', 'MRNA', 'ORLY', 'WDAY', 'NXPI',
                'SNPS', 'CDNS', 'MCHP', 'CTAS', 'PAYX', 'ASML', 'MNST', 'LULU'
            ]
        except Exception as e:
            logger.warning(f"Failed to get NASDAQ 100 symbols: {e}")
            return await self._get_popular_symbols()
    
    async def _get_russell2000_symbols(self) -> List[str]:
        """Get Russell 2000 symbols (small-cap)."""
        try:
            # Sample of small-cap stocks
            return [
                'ROKU', 'PENN', 'PLUG', 'SPCE', 'CLOV', 'WISH', 'SOFI', 'PLTR',
                'BB', 'NOK', 'SNDL', 'TLRY', 'ACB', 'HEXO', 'CGC', 'CRON',
                'RIOT', 'MARA', 'SQ', 'HOOD', 'COIN', 'RBLX', 'UPST', 'AFRM',
                'OPEN', 'LCID', 'RIVN', 'F', 'GM', 'FORD', 'NIO', 'XPEV', 'LI'
            ]
        except Exception as e:
            logger.warning(f"Failed to get Russell 2000 symbols: {e}")
            return await self._get_popular_symbols()
    
    async def _get_popular_symbols(self) -> List[str]:
        """Get popular/commonly traded symbols."""
        return [
            # Large tech
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
            # Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BRK-B', 'V', 'MA', 'AXP',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'BMY', 'MRK', 'ABT', 'TMO', 'DHR',
            # Consumer
            'WMT', 'HD', 'PG', 'KO', 'PEP', 'NKE', 'SBUX', 'MCD', 'DIS',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'FDX', 'LMT', 'RTX',
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'VLO', 'PSX',
            # Growth/Momentum
            'CRM', 'ADBE', 'PYPL', 'SQ', 'ROKU', 'ZOOM', 'DOCU', 'SHOP'
        ]
    
    async def _apply_initial_filters(
        self,
        symbols: List[str],
        filters: OpportunitySearchFilters
    ) -> List[str]:
        """Apply initial filters to reduce the symbol universe."""
        if not symbols:
            return []
        
        # For now, return all symbols as we'll filter during analysis
        # In a production system, this would apply basic filters like
        # market cap, sector, etc. using cached data
        return symbols
    
    async def _analyze_opportunities(
        self,
        symbols: List[str],
        filters: OpportunitySearchFilters
    ) -> List[InvestmentOpportunity]:
        """Analyze symbols to identify opportunities."""
        opportunities = []
        
        # Process symbols in batches to avoid overwhelming the system
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_opportunities = await self._analyze_batch(batch, filters)
            opportunities.extend(batch_opportunities)
            
            # Add small delay between batches to be respectful to data sources
            if i + batch_size < len(symbols):
                await asyncio.sleep(0.1)
        
        return opportunities
    
    async def _analyze_batch(
        self,
        symbols: List[str],
        filters: OpportunitySearchFilters
    ) -> List[InvestmentOpportunity]:
        """Analyze a batch of symbols."""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self._analyze_single_symbol(symbol, filters))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        opportunities = []
        for result in results:
            if isinstance(result, InvestmentOpportunity):
                opportunities.append(result)
            elif isinstance(result, Exception):
                logger.debug(f"Failed to analyze symbol: {result}")
        
        return opportunities
    
    async def _analyze_single_symbol(
        self,
        symbol: str,
        filters: OpportunitySearchFilters
    ) -> Optional[InvestmentOpportunity]:
        """Analyze a single symbol for opportunities."""
        try:
            # Get market data first for basic filtering
            market_data = await self.data_service.get_market_data(symbol)
            
            # Apply market data filters
            if not self._passes_market_filters(market_data, filters):
                return None
            
            # Get fundamental and technical analysis
            fundamental_task = asyncio.create_task(
                self._safe_fundamental_analysis(symbol)
            )
            technical_task = asyncio.create_task(
                self._safe_technical_analysis(symbol)
            )
            
            fundamental_data, technical_data = await asyncio.gather(
                fundamental_task, technical_task
            )
            
            # Apply fundamental filters
            if fundamental_data and not self._passes_fundamental_filters(fundamental_data, filters):
                return None
            
            # Apply technical filters
            if technical_data and not self._passes_technical_filters(technical_data, filters):
                return None
            
            # Create opportunity if it passes all filters
            opportunity = await self._create_opportunity(
                symbol, market_data, fundamental_data, technical_data, filters
            )
            
            return opportunity
            
        except Exception as e:
            logger.debug(f"Failed to analyze {symbol}: {e}")
            return None
    
    def _passes_market_filters(self, market_data: MarketData, filters: OpportunitySearchFilters) -> bool:
        """Check if market data passes filters."""
        # Market cap filters
        if market_data.market_cap:
            if filters.market_cap_min and market_data.market_cap < filters.market_cap_min:
                return False
            if filters.market_cap_max and market_data.market_cap > filters.market_cap_max:
                return False
            
            # Market cap category filters
            if filters.market_cap_categories:
                market_cap = market_data.market_cap
                passes_category = False
                for category in filters.market_cap_categories:
                    min_cap, max_cap = self.market_cap_thresholds[category]
                    if (min_cap is None or market_cap >= min_cap) and \
                       (max_cap is None or market_cap <= max_cap):
                        passes_category = True
                        break
                if not passes_category:
                    return False
        
        # Volume filters
        if filters.volume_min and market_data.volume < filters.volume_min:
            return False
        if filters.avg_volume_min and market_data.avg_volume and market_data.avg_volume < filters.avg_volume_min:
            return False
        
        return True
    
    def _passes_fundamental_filters(self, fundamental_data: FundamentalData, filters: OpportunitySearchFilters) -> bool:
        """Check if fundamental data passes filters."""
        # P/E ratio filters
        if fundamental_data.pe_ratio:
            if filters.pe_ratio_min and fundamental_data.pe_ratio < filters.pe_ratio_min:
                return False
            if filters.pe_ratio_max and fundamental_data.pe_ratio > filters.pe_ratio_max:
                return False
        
        # P/B ratio filters
        if fundamental_data.pb_ratio:
            if filters.pb_ratio_min and fundamental_data.pb_ratio < filters.pb_ratio_min:
                return False
            if filters.pb_ratio_max and fundamental_data.pb_ratio > filters.pb_ratio_max:
                return False
        
        # ROE filters
        if fundamental_data.roe:
            if filters.roe_min and fundamental_data.roe < filters.roe_min:
                return False
        
        # Debt-to-equity filters
        if fundamental_data.debt_to_equity:
            if filters.debt_to_equity_max and fundamental_data.debt_to_equity > filters.debt_to_equity_max:
                return False
        
        # Profit margin filters
        if fundamental_data.profit_margin:
            if filters.profit_margin_min and fundamental_data.profit_margin < filters.profit_margin_min:
                return False
        
        # Revenue growth filters
        if fundamental_data.revenue_growth:
            if filters.revenue_growth_min and fundamental_data.revenue_growth < filters.revenue_growth_min:
                return False
        
        return True
    
    def _passes_technical_filters(self, technical_data: TechnicalData, filters: OpportunitySearchFilters) -> bool:
        """Check if technical data passes filters."""
        # RSI filters
        if technical_data.rsi:
            if filters.rsi_min and technical_data.rsi < filters.rsi_min:
                return False
            if filters.rsi_max and technical_data.rsi > filters.rsi_max:
                return False
        
        # Moving average filters
        if filters.price_above_sma_20 is not None and technical_data.sma_20:
            # This would require current price comparison
            pass
        
        if filters.price_above_sma_50 is not None and technical_data.sma_50:
            # This would require current price comparison
            pass
        
        return True
    
    async def _create_opportunity(
        self,
        symbol: str,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData],
        filters: OpportunitySearchFilters
    ) -> InvestmentOpportunity:
        """Create an investment opportunity from analysis data."""
        # Get basic stock info
        stock_info = await self.data_service.get_stock_info(symbol)
        
        # Calculate scores
        scores = self._calculate_opportunity_scores(
            market_data, fundamental_data, technical_data
        )
        
        # Identify opportunity types
        opportunity_types = self._identify_opportunity_types(
            market_data, fundamental_data, technical_data, scores
        )
        
        # Filter by requested opportunity types
        if filters.opportunity_types:
            if not any(ot in filters.opportunity_types for ot in opportunity_types):
                return None
        
        # Assess risk level
        risk_level = self._assess_risk_level(
            market_data, fundamental_data, technical_data
        )
        
        # Filter by risk level
        if filters.max_risk_level:
            risk_order = [RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.VERY_HIGH]
            if risk_order.index(risk_level) > risk_order.index(filters.max_risk_level):
                return None
        
        # Generate reasons, risks, and catalysts
        reasons = self._generate_reasons(market_data, fundamental_data, technical_data, opportunity_types)
        risks = self._generate_risks(market_data, fundamental_data, technical_data, risk_level)
        catalysts = self._generate_catalysts(market_data, fundamental_data, technical_data)
        
        # Calculate price targets
        price_targets = self._calculate_price_targets(
            market_data.price, fundamental_data, technical_data
        )
        
        # Create key metrics
        key_metrics = self._create_key_metrics(market_data, fundamental_data, technical_data)
        
        opportunity = InvestmentOpportunity(
            symbol=symbol,
            name=stock_info.name,
            sector=stock_info.sector,
            industry=stock_info.industry,
            current_price=market_data.price,
            market_cap=market_data.market_cap,
            volume=market_data.volume,
            opportunity_types=opportunity_types,
            risk_level=risk_level,
            scores=scores,
            key_metrics=key_metrics,
            reasons=reasons,
            risks=risks,
            catalysts=catalysts,
            price_target_short=price_targets.get('short'),
            price_target_medium=price_targets.get('medium'),
            price_target_long=price_targets.get('long'),
            last_updated=datetime.now(),
            data_freshness={
                'market': market_data.timestamp,
                'fundamental': fundamental_data.last_updated if fundamental_data else None,
                'technical': technical_data.timestamp if technical_data else None
            }
        )
        
        return opportunity
    
    def _calculate_opportunity_scores(
        self,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData]
    ) -> OpportunityScore:
        """Calculate detailed opportunity scores."""
        fundamental_score = None
        technical_score = None
        value_score = 50
        quality_score = 50
        momentum_score = 50
        
        # Calculate fundamental score
        if fundamental_data:
            fundamental_score = fundamental_data.calculate_health_score()
            
            # Value score based on valuation metrics
            value_components = []
            if fundamental_data.pe_ratio:
                # Lower P/E is better for value (inverse scoring)
                pe_score = max(0, 100 - (float(fundamental_data.pe_ratio) - 10) * 2)
                value_components.append(min(100, max(0, pe_score)))
            
            if fundamental_data.pb_ratio:
                # Lower P/B is better for value
                pb_score = max(0, 100 - (float(fundamental_data.pb_ratio) - 1) * 20)
                value_components.append(min(100, max(0, pb_score)))
            
            if value_components:
                value_score = sum(value_components) / len(value_components)
            
            # Quality score based on profitability and financial health
            quality_components = []
            if fundamental_data.roe:
                roe_score = min(100, float(fundamental_data.roe) * 400)  # 25% ROE = 100 points
                quality_components.append(roe_score)
            
            if fundamental_data.profit_margin:
                margin_score = min(100, float(fundamental_data.profit_margin) * 400)  # 25% margin = 100 points
                quality_components.append(margin_score)
            
            if fundamental_data.debt_to_equity is not None:
                # Lower debt is better
                debt_score = max(0, 100 - float(fundamental_data.debt_to_equity) * 50)
                quality_components.append(debt_score)
            
            if quality_components:
                quality_score = sum(quality_components) / len(quality_components)
        
        # Calculate technical score
        if technical_data:
            technical_score = technical_data.calculate_technical_score(market_data.price)
            
            # Momentum score based on technical indicators
            momentum_components = []
            
            if technical_data.rsi:
                # RSI between 50-70 is good momentum
                rsi = float(technical_data.rsi)
                if 50 <= rsi <= 70:
                    momentum_components.append(80 + (rsi - 50))
                elif 30 <= rsi < 50:
                    momentum_components.append(40 + (rsi - 30))
                else:
                    momentum_components.append(max(0, 100 - abs(rsi - 60) * 2))
            
            if technical_data.sma_20 and technical_data.sma_50:
                # Price above moving averages is positive momentum
                current_price = float(market_data.price)
                sma_20 = float(technical_data.sma_20)
                sma_50 = float(technical_data.sma_50)
                
                if current_price > sma_20 > sma_50:
                    momentum_components.append(90)
                elif current_price > sma_20:
                    momentum_components.append(70)
                elif current_price > sma_50:
                    momentum_components.append(60)
                else:
                    momentum_components.append(30)
            
            if momentum_components:
                momentum_score = sum(momentum_components) / len(momentum_components)
        
        # Calculate overall score
        scores = []
        weights = []
        
        if fundamental_score:
            scores.append(fundamental_score)
            weights.append(0.4)
        
        if technical_score:
            scores.append(technical_score)
            weights.append(0.3)
        
        scores.extend([value_score, quality_score, momentum_score])
        weights.extend([0.1, 0.1, 0.1])
        
        # Normalize weights
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
            overall_score = sum(score * weight for score, weight in zip(scores, weights))
        else:
            overall_score = 50
        
        return OpportunityScore(
            overall_score=int(overall_score),
            fundamental_score=int(fundamental_score) if fundamental_score else None,
            technical_score=int(technical_score) if technical_score else None,
            momentum_score=int(momentum_score),
            value_score=int(value_score),
            quality_score=int(quality_score)
        )
    
    def _identify_opportunity_types(
        self,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData],
        scores: OpportunityScore
    ) -> List[OpportunityType]:
        """Identify the types of opportunities present."""
        opportunity_types = []
        
        # Value opportunity
        if scores.value_score >= 70:
            opportunity_types.append(OpportunityType.UNDERVALUED)
        
        # Growth opportunity
        if fundamental_data and fundamental_data.revenue_growth and fundamental_data.revenue_growth > Decimal('0.15'):
            opportunity_types.append(OpportunityType.GROWTH)
        
        # Quality opportunity
        if scores.quality_score >= 80:
            opportunity_types.append(OpportunityType.DIVIDEND)  # High quality often pays dividends
        
        # Momentum opportunity
        if scores.momentum_score >= 75:
            opportunity_types.append(OpportunityType.MOMENTUM)
        
        # Technical breakout
        if technical_data and technical_data.rsi and 30 <= technical_data.rsi <= 40:
            opportunity_types.append(OpportunityType.OVERSOLD)
        
        # Default to undervalued if no specific types identified
        if not opportunity_types:
            opportunity_types.append(OpportunityType.UNDERVALUED)
        
        return opportunity_types
    
    def _assess_risk_level(
        self,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData]
    ) -> RiskLevel:
        """Assess the risk level of the opportunity."""
        risk_score = 0  # 0 = low risk, 100 = very high risk
        
        # Market cap risk (smaller = higher risk)
        if market_data.market_cap:
            if market_data.market_cap < 300_000_000:  # Micro cap
                risk_score += 30
            elif market_data.market_cap < 2_000_000_000:  # Small cap
                risk_score += 20
            elif market_data.market_cap < 10_000_000_000:  # Mid cap
                risk_score += 10
        
        # Fundamental risk factors
        if fundamental_data:
            if fundamental_data.debt_to_equity and fundamental_data.debt_to_equity > Decimal('1.0'):
                risk_score += 20
            
            if fundamental_data.profit_margin and fundamental_data.profit_margin < Decimal('0.05'):
                risk_score += 15
        
        # Technical risk factors
        if technical_data:
            if technical_data.rsi:
                rsi = float(technical_data.rsi)
                if rsi > 80 or rsi < 20:  # Extreme levels
                    risk_score += 15
        
        # Determine risk level
        if risk_score >= 60:
            return RiskLevel.VERY_HIGH
        elif risk_score >= 40:
            return RiskLevel.HIGH
        elif risk_score >= 20:
            return RiskLevel.MODERATE
        else:
            return RiskLevel.LOW
    
    def _generate_reasons(
        self,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData],
        opportunity_types: List[OpportunityType]
    ) -> List[str]:
        """Generate reasons why this is an opportunity."""
        reasons = []
        
        # Fundamental reasons
        if fundamental_data:
            if fundamental_data.roe and fundamental_data.roe > Decimal('0.20'):
                reasons.append(f"Strong return on equity of {fundamental_data.roe:.1%}")
            
            if fundamental_data.revenue_growth and fundamental_data.revenue_growth > Decimal('0.10'):
                reasons.append(f"Solid revenue growth of {fundamental_data.revenue_growth:.1%}")
            
            if fundamental_data.debt_to_equity and fundamental_data.debt_to_equity < Decimal('0.30'):
                reasons.append(f"Conservative debt level (D/E: {fundamental_data.debt_to_equity:.2f})")
            
            if fundamental_data.pe_ratio and fundamental_data.pe_ratio < Decimal('20'):
                reasons.append(f"Attractive valuation (P/E: {fundamental_data.pe_ratio:.1f})")
        
        # Technical reasons
        if technical_data:
            if technical_data.rsi and 30 <= technical_data.rsi <= 50:
                reasons.append("RSI indicates potential oversold recovery")
            
            if technical_data.support_levels:
                reasons.append("Strong technical support levels identified")
        
        # Market reasons
        if market_data.volume > (market_data.avg_volume or 0) * 1.5:
            reasons.append("Above-average trading volume indicates interest")
        
        # Default reason if none found
        if not reasons:
            reasons.append("Meets screening criteria for investment consideration")
        
        return reasons
    
    def _generate_risks(
        self,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData],
        risk_level: RiskLevel
    ) -> List[str]:
        """Generate key risks to consider."""
        risks = ["Market volatility and economic uncertainty"]
        
        # Market cap specific risks
        if market_data.market_cap and market_data.market_cap < 2_000_000_000:
            risks.append("Small-cap stock with higher volatility risk")
        
        # Fundamental risks
        if fundamental_data:
            if fundamental_data.debt_to_equity and fundamental_data.debt_to_equity > Decimal('0.80'):
                risks.append("High debt levels may limit financial flexibility")
            
            if fundamental_data.profit_margin and fundamental_data.profit_margin < Decimal('0.05'):
                risks.append("Low profit margins indicate operational challenges")
        
        # Technical risks
        if technical_data:
            if technical_data.resistance_levels:
                risks.append("Technical resistance levels may limit upside")
        
        return risks
    
    def _generate_catalysts(
        self,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData]
    ) -> List[str]:
        """Generate potential catalysts."""
        catalysts = []
        
        if fundamental_data:
            if fundamental_data.revenue_growth and fundamental_data.revenue_growth > Decimal('0.15'):
                catalysts.append("Continued revenue growth momentum")
            
            catalysts.append("Upcoming earnings announcement")
        
        if technical_data:
            if technical_data.resistance_levels:
                catalysts.append("Technical breakout above resistance")
        
        catalysts.extend([
            "Positive industry developments",
            "Broader market recovery"
        ])
        
        return catalysts
    
    def _calculate_price_targets(
        self,
        current_price: Decimal,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData]
    ) -> Dict[str, Decimal]:
        """Calculate price targets for different timeframes."""
        targets = {}
        
        # Simple target calculation based on current price
        # In a real system, this would use more sophisticated models
        
        # Short-term (3 months) - conservative
        targets['short'] = current_price * Decimal('1.10')  # 10% upside
        
        # Medium-term (6 months) - moderate
        targets['medium'] = current_price * Decimal('1.20')  # 20% upside
        
        # Long-term (12 months) - optimistic
        targets['long'] = current_price * Decimal('1.35')  # 35% upside
        
        # Adjust based on fundamental strength
        if fundamental_data:
            health_score = fundamental_data.calculate_health_score()
            if health_score and health_score > 80:
                # Increase targets for high-quality companies
                for timeframe in targets:
                    targets[timeframe] *= Decimal('1.05')
        
        return targets
    
    def _create_key_metrics(
        self,
        market_data: MarketData,
        fundamental_data: Optional[FundamentalData],
        technical_data: Optional[TechnicalData]
    ) -> Dict[str, Any]:
        """Create key metrics dictionary."""
        metrics = {
            'current_price': market_data.price,
            'market_cap': market_data.market_cap,
            'volume': market_data.volume
        }
        
        if fundamental_data:
            if fundamental_data.pe_ratio:
                metrics['pe_ratio'] = fundamental_data.pe_ratio
            if fundamental_data.roe:
                metrics['roe'] = fundamental_data.roe
            if fundamental_data.debt_to_equity:
                metrics['debt_to_equity'] = fundamental_data.debt_to_equity
            if fundamental_data.revenue_growth:
                metrics['revenue_growth'] = fundamental_data.revenue_growth
        
        if technical_data:
            if technical_data.rsi:
                metrics['rsi'] = technical_data.rsi
        
        return metrics
    
    async def _safe_fundamental_analysis(self, symbol: str) -> Optional[FundamentalData]:
        """Safely perform fundamental analysis."""
        try:
            return await self.fundamental_analyzer.analyze_fundamentals(symbol)
        except Exception:
            return None
    
    async def _safe_technical_analysis(self, symbol: str) -> Optional[TechnicalData]:
        """Safely perform technical analysis."""
        try:
            return await self.technical_analyzer.analyze_technical(symbol, TimeFrame.ONE_DAY)
        except Exception:
            return None
    
    def _apply_final_filters(
        self,
        opportunities: List[InvestmentOpportunity],
        filters: OpportunitySearchFilters
    ) -> List[InvestmentOpportunity]:
        """Apply final filters to opportunities."""
        filtered = []
        
        for opportunity in opportunities:
            # Score filter
            if filters.min_score and opportunity.scores.overall_score < filters.min_score:
                continue
            
            # Sector filters
            if filters.sectors and opportunity.sector not in filters.sectors:
                continue
            
            if filters.exclude_sectors and opportunity.sector in filters.exclude_sectors:
                continue
            
            filtered.append(opportunity)
        
        return filtered
    
    def _rank_opportunities(
        self,
        opportunities: List[InvestmentOpportunity],
        ranking: OpportunityRanking
    ) -> List[InvestmentOpportunity]:
        """Rank opportunities based on specified criteria."""
        # Calculate weighted scores
        for opportunity in opportunities:
            weighted_score = (
                (opportunity.scores.fundamental_score or 50) * ranking.fundamental_weight +
                (opportunity.scores.technical_score or 50) * ranking.technical_weight +
                opportunity.scores.momentum_score * ranking.momentum_weight +
                opportunity.scores.value_score * ranking.value_weight
            )
            opportunity.scores.overall_score = int(weighted_score)
        
        # Sort by the specified field
        reverse = ranking.sort_order == "desc"
        
        if ranking.sort_by == "overall_score":
            opportunities.sort(key=lambda x: x.scores.overall_score, reverse=reverse)
        elif ranking.sort_by == "market_cap":
            opportunities.sort(key=lambda x: x.market_cap or 0, reverse=reverse)
        elif ranking.sort_by == "current_price":
            opportunities.sort(key=lambda x: x.current_price, reverse=reverse)
        else:
            # Default to overall score
            opportunities.sort(key=lambda x: x.scores.overall_score, reverse=reverse)
        
        return opportunities
    
    async def _create_opportunity_from_analysis(self, analysis_result) -> InvestmentOpportunity:
        """Create opportunity from existing analysis result."""
        # This would convert an AnalysisResult to an InvestmentOpportunity
        # For now, return a placeholder
        raise NotImplementedError("This method needs to be implemented based on AnalysisResult structure")