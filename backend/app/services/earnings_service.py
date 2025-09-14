"""
Earnings calendar and corporate events service.
Handles data fetching, storage, and analysis of earnings and corporate events.
"""

import yfinance as yf
import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
import requests
import json

from ..models.earnings import (
    EarningsEvent, CorporateEvent, EarningsHistoricalPerformance,
    EarningsEventCreate, EarningsEventResponse, EarningsEventUpdate,
    CorporateEventCreate, CorporateEventResponse,
    EarningsCalendarFilter, EventCalendarFilter,
    EarningsCalendarResponse, EventCalendarResponse,
    EarningsImpactAnalysis, EarningsHistoricalPerformanceResponse,
    EventType, EarningsConfidence, EventImpact
)
from ..models.stock import MarketData
from ..services.data_aggregation import DataAggregationService
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EarningsServiceException(Exception):
    """Custom exception for earnings service errors."""
    
    def __init__(self, message: str, error_type: str = "GENERAL", suggestions: List[str] = None):
        self.message = message
        self.error_type = error_type
        self.suggestions = suggestions or []
        super().__init__(self.message)


class EarningsService:
    """Service for managing earnings calendar and corporate events."""
    
    def __init__(self, data_service: Optional[DataAggregationService] = None):
        """Initialize earnings service."""
        self.data_service = data_service or DataAggregationService()
        self.cache_ttl = {
            'earnings_data': 3600,  # 1 hour for earnings data
            'corporate_events': 1800,  # 30 minutes for corporate events
            'historical_performance': 86400  # 24 hours for historical data
        }
    
    # Earnings Calendar Methods
    
    async def get_earnings_calendar(
        self,
        db: AsyncSession,
        filters: EarningsCalendarFilter,
        limit: int = 100,
        offset: int = 0
    ) -> EarningsCalendarResponse:
        """
        Get earnings calendar with filtering options.
        
        Args:
            db: Database session
            filters: Filter criteria
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            EarningsCalendarResponse with filtered events
        """
        try:
            # Build query
            query = select(EarningsEvent)
            
            # Apply filters
            conditions = []
            
            if filters.symbols:
                conditions.append(EarningsEvent.symbol.in_(filters.symbols))
            
            if filters.start_date:
                conditions.append(EarningsEvent.earnings_date >= filters.start_date)
            
            if filters.end_date:
                conditions.append(EarningsEvent.earnings_date <= filters.end_date)
            
            if filters.confirmed_only:
                conditions.append(EarningsEvent.is_confirmed == True)
            
            if filters.impact_levels:
                conditions.append(EarningsEvent.impact_level.in_(filters.impact_levels))
            
            if filters.has_estimates is not None:
                if filters.has_estimates:
                    conditions.append(EarningsEvent.eps_estimate.isnot(None))
                else:
                    conditions.append(EarningsEvent.eps_estimate.is_(None))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Order by earnings date
            query = query.order_by(asc(EarningsEvent.earnings_date))
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await db.execute(query)
            events = result.scalars().all()
            
            # Convert to response models
            event_responses = []
            for event in events:
                response = await self._convert_to_earnings_response(event)
                event_responses.append(response)
            
            # Get total count
            count_query = select(EarningsEvent)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            count_result = await db.execute(count_query)
            total_events = len(count_result.scalars().all())
            
            # Count upcoming events
            upcoming_count = sum(1 for event in event_responses if event.is_upcoming)
            
            # Determine date range
            date_range = {
                "start_date": filters.start_date,
                "end_date": filters.end_date
            }
            
            return EarningsCalendarResponse(
                total_events=total_events,
                upcoming_events=upcoming_count,
                events=event_responses,
                date_range=date_range
            )
            
        except Exception as e:
            logger.error(f"Failed to get earnings calendar: {e}")
            raise EarningsServiceException(
                f"Failed to retrieve earnings calendar: {str(e)}",
                error_type="DATABASE_ERROR"
            )
    
    async def get_corporate_events_calendar(
        self,
        db: AsyncSession,
        filters: EventCalendarFilter,
        limit: int = 100,
        offset: int = 0
    ) -> EventCalendarResponse:
        """
        Get corporate events calendar with filtering options.
        
        Args:
            db: Database session
            filters: Filter criteria
            limit: Maximum number of events to return
            offset: Number of events to skip
            
        Returns:
            EventCalendarResponse with filtered events
        """
        try:
            # Build query
            query = select(CorporateEvent)
            
            # Apply filters
            conditions = []
            
            if filters.symbols:
                conditions.append(CorporateEvent.symbol.in_(filters.symbols))
            
            if filters.event_types:
                conditions.append(CorporateEvent.event_type.in_(filters.event_types))
            
            if filters.start_date:
                conditions.append(CorporateEvent.event_date >= filters.start_date)
            
            if filters.end_date:
                conditions.append(CorporateEvent.event_date <= filters.end_date)
            
            if filters.confirmed_only:
                conditions.append(CorporateEvent.is_confirmed == True)
            
            if filters.impact_levels:
                conditions.append(CorporateEvent.impact_level.in_(filters.impact_levels))
            
            if conditions:
                query = query.where(and_(*conditions))
            
            # Order by event date
            query = query.order_by(asc(CorporateEvent.event_date))
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            result = await db.execute(query)
            events = result.scalars().all()
            
            # Convert to response models
            event_responses = []
            for event in events:
                response = await self._convert_to_corporate_event_response(event)
                event_responses.append(response)
            
            # Get total count
            count_query = select(CorporateEvent)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            
            count_result = await db.execute(count_query)
            total_events = len(count_result.scalars().all())
            
            # Count upcoming events
            upcoming_count = sum(1 for event in event_responses if event.is_upcoming)
            
            # Get unique event types
            event_types = list(set(event.event_type for event in events))
            
            # Determine date range
            date_range = {
                "start_date": filters.start_date,
                "end_date": filters.end_date
            }
            
            return EventCalendarResponse(
                total_events=total_events,
                upcoming_events=upcoming_count,
                events=event_responses,
                date_range=date_range,
                event_types=event_types
            )
            
        except Exception as e:
            logger.error(f"Failed to get corporate events calendar: {e}")
            raise EarningsServiceException(
                f"Failed to retrieve corporate events calendar: {str(e)}",
                error_type="DATABASE_ERROR"
            )
    
    async def fetch_earnings_data_for_symbol(
        self,
        db: AsyncSession,
        symbol: str,
        days_ahead: int = 90
    ) -> List[EarningsEventResponse]:
        """
        Fetch and store earnings data for a specific symbol.
        
        Args:
            db: Database session
            symbol: Stock ticker symbol
            days_ahead: Number of days ahead to fetch earnings data
            
        Returns:
            List of earnings events for the symbol
        """
        symbol = symbol.upper()
        
        try:
            # Fetch earnings data from yfinance
            earnings_data = await self._fetch_earnings_from_yfinance(symbol)
            
            # Store or update earnings events in database
            stored_events = []
            for earnings_info in earnings_data:
                event = await self._store_or_update_earnings_event(db, earnings_info)
                if event:
                    response = await self._convert_to_earnings_response(event)
                    stored_events.append(response)
            
            await db.commit()
            
            logger.info(f"Fetched and stored {len(stored_events)} earnings events for {symbol}")
            return stored_events
            
        except Exception as e:
            logger.error(f"Failed to fetch earnings data for {symbol}: {e}")
            await db.rollback()
            raise EarningsServiceException(
                f"Failed to fetch earnings data for {symbol}: {str(e)}",
                error_type="DATA_FETCH_ERROR",
                suggestions=["Verify symbol exists", "Try again later"]
            )
    
    async def fetch_corporate_events_for_symbol(
        self,
        db: AsyncSession,
        symbol: str,
        days_ahead: int = 90
    ) -> List[CorporateEventResponse]:
        """
        Fetch and store corporate events for a specific symbol.
        
        Args:
            db: Database session
            symbol: Stock ticker symbol
            days_ahead: Number of days ahead to fetch events
            
        Returns:
            List of corporate events for the symbol
        """
        symbol = symbol.upper()
        
        try:
            # Fetch corporate events from yfinance
            events_data = await self._fetch_corporate_events_from_yfinance(symbol)
            
            # Store or update corporate events in database
            stored_events = []
            for event_info in events_data:
                event = await self._store_or_update_corporate_event(db, event_info)
                if event:
                    response = await self._convert_to_corporate_event_response(event)
                    stored_events.append(response)
            
            await db.commit()
            
            logger.info(f"Fetched and stored {len(stored_events)} corporate events for {symbol}")
            return stored_events
            
        except Exception as e:
            logger.error(f"Failed to fetch corporate events for {symbol}: {e}")
            await db.rollback()
            raise EarningsServiceException(
                f"Failed to fetch corporate events for {symbol}: {str(e)}",
                error_type="DATA_FETCH_ERROR",
                suggestions=["Verify symbol exists", "Try again later"]
            )
    
    async def get_earnings_impact_analysis(
        self,
        db: AsyncSession,
        symbol: str
    ) -> EarningsImpactAnalysis:
        """
        Analyze historical earnings impact and predict upcoming earnings impact.
        
        Args:
            db: Database session
            symbol: Stock ticker symbol
            
        Returns:
            EarningsImpactAnalysis with historical patterns and predictions
        """
        symbol = symbol.upper()
        
        try:
            # Get upcoming earnings
            upcoming_query = select(EarningsEvent).where(
                and_(
                    EarningsEvent.symbol == symbol,
                    EarningsEvent.earnings_date >= datetime.now()
                )
            ).order_by(asc(EarningsEvent.earnings_date)).limit(1)
            
            upcoming_result = await db.execute(upcoming_query)
            upcoming_earnings = upcoming_result.scalar_one_or_none()
            
            # Get historical performance data
            historical_query = select(EarningsHistoricalPerformance).where(
                EarningsHistoricalPerformance.symbol == symbol
            ).order_by(desc(EarningsHistoricalPerformance.created_at))
            
            historical_result = await db.execute(historical_query)
            historical_data = historical_result.scalars().all()
            
            # Convert to response models
            upcoming_response = None
            if upcoming_earnings:
                upcoming_response = await self._convert_to_earnings_response(upcoming_earnings)
            
            historical_responses = [
                EarningsHistoricalPerformanceResponse.from_orm(perf)
                for perf in historical_data
            ]
            
            # Calculate analysis metrics
            analysis_metrics = await self._calculate_earnings_impact_metrics(historical_data)
            
            return EarningsImpactAnalysis(
                symbol=symbol,
                upcoming_earnings=upcoming_response,
                historical_performance=historical_responses,
                **analysis_metrics
            )
            
        except Exception as e:
            logger.error(f"Failed to get earnings impact analysis for {symbol}: {e}")
            raise EarningsServiceException(
                f"Failed to analyze earnings impact for {symbol}: {str(e)}",
                error_type="ANALYSIS_ERROR"
            )
    
    # Private helper methods
    
    async def _fetch_earnings_from_yfinance(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch earnings data from yfinance."""
        loop = asyncio.get_event_loop()
        
        def _fetch_sync():
            try:
                ticker = yf.Ticker(symbol)
                
                # Get earnings calendar
                calendar = ticker.calendar
                earnings_data = []
                
                if calendar is not None and not calendar.empty:
                    for index, row in calendar.iterrows():
                        earnings_info = {
                            'symbol': symbol,
                            'company_name': ticker.info.get('longName', symbol),
                            'earnings_date': index,
                            'eps_estimate': row.get('Earnings Estimate'),
                            'revenue_estimate': row.get('Revenue Estimate'),
                            'fiscal_quarter': self._determine_fiscal_quarter(index),
                            'fiscal_year': index.year,
                            'confidence': EarningsConfidence.MEDIUM,
                            'impact_level': EventImpact.MEDIUM,
                            'is_confirmed': True
                        }
                        earnings_data.append(earnings_info)
                
                # Also try to get earnings dates from info
                earnings_date = ticker.info.get('earningsDate')
                if earnings_date and not earnings_data:
                    # Convert timestamp to datetime if needed
                    if isinstance(earnings_date, (int, float)):
                        earnings_date = datetime.fromtimestamp(earnings_date)
                    
                    earnings_info = {
                        'symbol': symbol,
                        'company_name': ticker.info.get('longName', symbol),
                        'earnings_date': earnings_date,
                        'confidence': EarningsConfidence.LOW,
                        'impact_level': EventImpact.MEDIUM,
                        'is_confirmed': False
                    }
                    earnings_data.append(earnings_info)
                
                return earnings_data
                
            except Exception as e:
                logger.warning(f"Failed to fetch earnings from yfinance for {symbol}: {e}")
                return []
        
        return await loop.run_in_executor(None, _fetch_sync)
    
    async def _fetch_corporate_events_from_yfinance(self, symbol: str) -> List[Dict[str, Any]]:
        """Fetch corporate events from yfinance."""
        loop = asyncio.get_event_loop()
        
        def _fetch_sync():
            try:
                ticker = yf.Ticker(symbol)
                events_data = []
                
                # Get dividends
                dividends = ticker.dividends
                if not dividends.empty:
                    for date, amount in dividends.tail(10).items():  # Last 10 dividends
                        event_info = {
                            'symbol': symbol,
                            'company_name': ticker.info.get('longName', symbol),
                            'event_type': EventType.DIVIDEND,
                            'event_date': date,
                            'dividend_amount': float(amount),
                            'impact_level': EventImpact.LOW,
                            'is_confirmed': True,
                            'description': f"Dividend payment of ${amount:.2f} per share"
                        }
                        events_data.append(event_info)
                
                # Get stock splits
                splits = ticker.splits
                if not splits.empty:
                    for date, ratio in splits.tail(5).items():  # Last 5 splits
                        event_info = {
                            'symbol': symbol,
                            'company_name': ticker.info.get('longName', symbol),
                            'event_type': EventType.STOCK_SPLIT,
                            'event_date': date,
                            'split_factor': float(ratio),
                            'split_ratio': f"{ratio}:1" if ratio > 1 else f"1:{1/ratio}",
                            'impact_level': EventImpact.HIGH,
                            'is_confirmed': True,
                            'description': f"Stock split {ratio}:1"
                        }
                        events_data.append(event_info)
                
                return events_data
                
            except Exception as e:
                logger.warning(f"Failed to fetch corporate events from yfinance for {symbol}: {e}")
                return []
        
        return await loop.run_in_executor(None, _fetch_sync)
    
    async def _store_or_update_earnings_event(
        self,
        db: AsyncSession,
        earnings_info: Dict[str, Any]
    ) -> Optional[EarningsEvent]:
        """Store or update earnings event in database."""
        try:
            # Check if event already exists
            existing_query = select(EarningsEvent).where(
                and_(
                    EarningsEvent.symbol == earnings_info['symbol'],
                    EarningsEvent.earnings_date == earnings_info['earnings_date']
                )
            )
            
            result = await db.execute(existing_query)
            existing_event = result.scalar_one_or_none()
            
            if existing_event:
                # Update existing event
                for key, value in earnings_info.items():
                    if hasattr(existing_event, key) and value is not None:
                        setattr(existing_event, key, value)
                existing_event.updated_at = datetime.utcnow()
                return existing_event
            else:
                # Create new event
                new_event = EarningsEvent(**earnings_info)
                db.add(new_event)
                await db.flush()  # Get the ID
                return new_event
                
        except Exception as e:
            logger.error(f"Failed to store earnings event: {e}")
            return None
    
    async def _store_or_update_corporate_event(
        self,
        db: AsyncSession,
        event_info: Dict[str, Any]
    ) -> Optional[CorporateEvent]:
        """Store or update corporate event in database."""
        try:
            # Check if event already exists
            existing_query = select(CorporateEvent).where(
                and_(
                    CorporateEvent.symbol == event_info['symbol'],
                    CorporateEvent.event_type == event_info['event_type'],
                    CorporateEvent.event_date == event_info['event_date']
                )
            )
            
            result = await db.execute(existing_query)
            existing_event = result.scalar_one_or_none()
            
            if existing_event:
                # Update existing event
                for key, value in event_info.items():
                    if hasattr(existing_event, key) and value is not None:
                        setattr(existing_event, key, value)
                existing_event.updated_at = datetime.utcnow()
                return existing_event
            else:
                # Create new event
                new_event = CorporateEvent(**event_info)
                db.add(new_event)
                await db.flush()  # Get the ID
                return new_event
                
        except Exception as e:
            logger.error(f"Failed to store corporate event: {e}")
            return None
    
    async def _convert_to_earnings_response(self, event: EarningsEvent) -> EarningsEventResponse:
        """Convert database model to response model."""
        # Calculate days until earnings
        days_until = None
        is_upcoming = False
        if event.earnings_date:
            days_until = (event.earnings_date.date() - date.today()).days
            is_upcoming = days_until >= 0
        
        # Check if has estimates and actuals
        has_estimates = event.eps_estimate is not None or event.revenue_estimate is not None
        has_actuals = event.eps_actual is not None or event.revenue_actual is not None
        
        return EarningsEventResponse(
            id=event.id,
            symbol=event.symbol,
            company_name=event.company_name,
            earnings_date=event.earnings_date,
            report_time=event.report_time,
            fiscal_quarter=event.fiscal_quarter,
            fiscal_year=event.fiscal_year,
            eps_estimate=event.eps_estimate,
            eps_estimate_high=event.eps_estimate_high,
            eps_estimate_low=event.eps_estimate_low,
            eps_estimate_count=event.eps_estimate_count,
            revenue_estimate=event.revenue_estimate,
            revenue_estimate_high=event.revenue_estimate_high,
            revenue_estimate_low=event.revenue_estimate_low,
            eps_actual=event.eps_actual,
            revenue_actual=event.revenue_actual,
            eps_surprise=event.eps_surprise,
            revenue_surprise=event.revenue_surprise,
            confidence=event.confidence,
            impact_level=event.impact_level,
            is_confirmed=event.is_confirmed,
            notes=event.notes,
            created_at=event.created_at,
            updated_at=event.updated_at,
            days_until_earnings=days_until,
            is_upcoming=is_upcoming,
            has_estimates=has_estimates,
            has_actuals=has_actuals
        )
    
    async def _convert_to_corporate_event_response(self, event: CorporateEvent) -> CorporateEventResponse:
        """Convert database model to response model."""
        # Calculate days until event
        days_until = None
        is_upcoming = False
        if event.event_date:
            days_until = (event.event_date.date() - date.today()).days
            is_upcoming = days_until >= 0
        
        return CorporateEventResponse(
            id=event.id,
            symbol=event.symbol,
            company_name=event.company_name,
            event_type=event.event_type,
            event_date=event.event_date,
            ex_date=event.ex_date,
            record_date=event.record_date,
            payment_date=event.payment_date,
            dividend_amount=event.dividend_amount,
            split_ratio=event.split_ratio,
            split_factor=event.split_factor,
            description=event.description,
            impact_level=event.impact_level,
            is_confirmed=event.is_confirmed,
            created_at=event.created_at,
            updated_at=event.updated_at,
            days_until_event=days_until,
            is_upcoming=is_upcoming
        )
    
    def _determine_fiscal_quarter(self, date: datetime) -> str:
        """Determine fiscal quarter from date."""
        month = date.month
        if month in [1, 2, 3]:
            return "Q1"
        elif month in [4, 5, 6]:
            return "Q2"
        elif month in [7, 8, 9]:
            return "Q3"
        else:
            return "Q4"
    
    async def _calculate_earnings_impact_metrics(
        self,
        historical_data: List[EarningsHistoricalPerformance]
    ) -> Dict[str, Any]:
        """Calculate earnings impact analysis metrics."""
        if not historical_data:
            return {
                'avg_price_change_1d': None,
                'avg_price_change_1w': None,
                'avg_volume_change': None,
                'beat_rate': None,
                'volatility_increase': None,
                'expected_volatility': "unknown",
                'risk_level': "unknown",
                'key_metrics_to_watch': []
            }
        
        # Calculate averages
        price_changes_1d = [p.price_change_1d for p in historical_data if p.price_change_1d is not None]
        price_changes_1w = [p.price_change_1w for p in historical_data if p.price_change_1w is not None]
        volume_changes = [p.volume_change for p in historical_data if p.volume_change is not None]
        beats = [p.beat_estimate for p in historical_data if p.beat_estimate is not None]
        
        avg_price_change_1d = Decimal(str(sum(price_changes_1d) / len(price_changes_1d))) if price_changes_1d else None
        avg_price_change_1w = Decimal(str(sum(price_changes_1w) / len(price_changes_1w))) if price_changes_1w else None
        avg_volume_change = Decimal(str(sum(volume_changes) / len(volume_changes))) if volume_changes else None
        beat_rate = Decimal(str(sum(beats) / len(beats) * 100)) if beats else None
        
        # Calculate volatility
        volatility_increase = None
        if price_changes_1d:
            volatility = sum(abs(change) for change in price_changes_1d) / len(price_changes_1d)
            volatility_increase = Decimal(str(volatility))
        
        # Determine expected volatility and risk level
        expected_volatility = "medium"
        risk_level = "medium"
        
        if volatility_increase:
            if volatility_increase > 5:
                expected_volatility = "high"
                risk_level = "high"
            elif volatility_increase < 2:
                expected_volatility = "low"
                risk_level = "low"
        
        # Key metrics to watch
        key_metrics = ["EPS", "Revenue", "Guidance"]
        if beat_rate and beat_rate < 50:
            key_metrics.append("Analyst Expectations")
        if avg_volume_change and avg_volume_change > 50:
            key_metrics.append("Trading Volume")
        
        return {
            'avg_price_change_1d': avg_price_change_1d,
            'avg_price_change_1w': avg_price_change_1w,
            'avg_volume_change': avg_volume_change,
            'beat_rate': beat_rate,
            'volatility_increase': volatility_increase,
            'expected_volatility': expected_volatility,
            'risk_level': risk_level,
            'key_metrics_to_watch': key_metrics
        }