"""
Earnings calendar and corporate events API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import date, datetime, timedelta

from ..core.database import get_db
from ..core.dependencies import get_current_user
from ..models.user import User
from ..models.earnings import (
    EarningsCalendarFilter, EventCalendarFilter,
    EarningsCalendarResponse, EventCalendarResponse,
    EarningsEventResponse, CorporateEventResponse,
    EarningsImpactAnalysis, EventType, EventImpact
)
from ..services.earnings_service import EarningsService, EarningsServiceException

router = APIRouter(prefix="/earnings", tags=["earnings"])


@router.get("/calendar", response_model=EarningsCalendarResponse)
async def get_earnings_calendar(
    symbols: Optional[str] = Query(None, description="Comma-separated list of stock symbols"),
    start_date: Optional[date] = Query(None, description="Start date for earnings events"),
    end_date: Optional[date] = Query(None, description="End date for earnings events"),
    confirmed_only: bool = Query(False, description="Only return confirmed earnings events"),
    impact_levels: Optional[str] = Query(None, description="Comma-separated list of impact levels (high,medium,low)"),
    has_estimates: Optional[bool] = Query(None, description="Filter by whether events have estimates"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get earnings calendar with optional filtering.
    
    Returns upcoming and historical earnings events with estimates and actuals.
    """
    try:
        # Parse query parameters
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        impact_level_list = None
        if impact_levels:
            impact_level_list = [
                EventImpact(level.strip().lower()) 
                for level in impact_levels.split(",") 
                if level.strip().lower() in [e.value for e in EventImpact]
            ]
        
        # Set default date range if not provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today() + timedelta(days=90)
        
        # Create filter
        filters = EarningsCalendarFilter(
            symbols=symbol_list,
            start_date=start_date,
            end_date=end_date,
            confirmed_only=confirmed_only,
            impact_levels=impact_level_list,
            has_estimates=has_estimates
        )
        
        # Get earnings calendar
        earnings_service = EarningsService()
        calendar = await earnings_service.get_earnings_calendar(
            db=db,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return calendar
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve earnings calendar: {str(e)}"
        )


@router.get("/events", response_model=EventCalendarResponse)
async def get_corporate_events_calendar(
    symbols: Optional[str] = Query(None, description="Comma-separated list of stock symbols"),
    event_types: Optional[str] = Query(None, description="Comma-separated list of event types"),
    start_date: Optional[date] = Query(None, description="Start date for events"),
    end_date: Optional[date] = Query(None, description="End date for events"),
    confirmed_only: bool = Query(False, description="Only return confirmed events"),
    impact_levels: Optional[str] = Query(None, description="Comma-separated list of impact levels"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get corporate events calendar (dividends, splits, etc.) with optional filtering.
    """
    try:
        # Parse query parameters
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
        
        event_type_list = None
        if event_types:
            event_type_list = [
                EventType(event_type.strip().lower()) 
                for event_type in event_types.split(",") 
                if event_type.strip().lower() in [e.value for e in EventType]
            ]
        
        impact_level_list = None
        if impact_levels:
            impact_level_list = [
                EventImpact(level.strip().lower()) 
                for level in impact_levels.split(",") 
                if level.strip().lower() in [e.value for e in EventImpact]
            ]
        
        # Set default date range if not provided
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today() + timedelta(days=90)
        
        # Create filter
        filters = EventCalendarFilter(
            symbols=symbol_list,
            event_types=event_type_list,
            start_date=start_date,
            end_date=end_date,
            confirmed_only=confirmed_only,
            impact_levels=impact_level_list
        )
        
        # Get corporate events calendar
        earnings_service = EarningsService()
        calendar = await earnings_service.get_corporate_events_calendar(
            db=db,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return calendar
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve corporate events calendar: {str(e)}"
        )


@router.get("/{symbol}/upcoming", response_model=List[EarningsEventResponse])
async def get_upcoming_earnings_for_symbol(
    symbol: str,
    days_ahead: int = Query(90, ge=1, le=365, description="Number of days ahead to look for earnings"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get upcoming earnings events for a specific stock symbol.
    """
    try:
        symbol = symbol.upper()
        
        # Create filter for upcoming earnings
        filters = EarningsCalendarFilter(
            symbols=[symbol],
            start_date=date.today(),
            end_date=date.today() + timedelta(days=days_ahead)
        )
        
        earnings_service = EarningsService()
        calendar = await earnings_service.get_earnings_calendar(
            db=db,
            filters=filters,
            limit=10,
            offset=0
        )
        
        return calendar.events
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve upcoming earnings for {symbol}: {str(e)}"
        )


@router.get("/{symbol}/events", response_model=List[CorporateEventResponse])
async def get_corporate_events_for_symbol(
    symbol: str,
    days_ahead: int = Query(90, ge=1, le=365, description="Number of days ahead to look for events"),
    event_types: Optional[str] = Query(None, description="Comma-separated list of event types to filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get corporate events for a specific stock symbol.
    """
    try:
        symbol = symbol.upper()
        
        # Parse event types
        event_type_list = None
        if event_types:
            event_type_list = [
                EventType(event_type.strip().lower()) 
                for event_type in event_types.split(",") 
                if event_type.strip().lower() in [e.value for e in EventType]
            ]
        
        # Create filter for corporate events
        filters = EventCalendarFilter(
            symbols=[symbol],
            event_types=event_type_list,
            start_date=date.today() - timedelta(days=30),  # Include recent past events
            end_date=date.today() + timedelta(days=days_ahead)
        )
        
        earnings_service = EarningsService()
        calendar = await earnings_service.get_corporate_events_calendar(
            db=db,
            filters=filters,
            limit=20,
            offset=0
        )
        
        return calendar.events
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve corporate events for {symbol}: {str(e)}"
        )


@router.get("/{symbol}/impact-analysis", response_model=EarningsImpactAnalysis)
async def get_earnings_impact_analysis(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get earnings impact analysis for a stock symbol.
    
    Provides historical earnings performance patterns and predictions for upcoming earnings.
    """
    try:
        symbol = symbol.upper()
        
        earnings_service = EarningsService()
        analysis = await earnings_service.get_earnings_impact_analysis(
            db=db,
            symbol=symbol
        )
        
        return analysis
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve earnings impact analysis for {symbol}: {str(e)}"
        )


@router.post("/{symbol}/fetch-data")
async def fetch_earnings_data(
    symbol: str,
    days_ahead: int = Query(90, ge=1, le=365, description="Number of days ahead to fetch data"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch and store earnings data for a specific symbol from external sources.
    
    This endpoint triggers data fetching from yfinance and other sources.
    """
    try:
        symbol = symbol.upper()
        
        earnings_service = EarningsService()
        
        # Fetch earnings data
        earnings_events = await earnings_service.fetch_earnings_data_for_symbol(
            db=db,
            symbol=symbol,
            days_ahead=days_ahead
        )
        
        # Fetch corporate events
        corporate_events = await earnings_service.fetch_corporate_events_for_symbol(
            db=db,
            symbol=symbol,
            days_ahead=days_ahead
        )
        
        return {
            "message": f"Successfully fetched data for {symbol}",
            "earnings_events_count": len(earnings_events),
            "corporate_events_count": len(corporate_events),
            "earnings_events": earnings_events,
            "corporate_events": corporate_events
        }
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch earnings data for {symbol}: {str(e)}"
        )


@router.get("/today", response_model=EarningsCalendarResponse)
async def get_todays_earnings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get today's earnings events.
    """
    try:
        today = date.today()
        
        filters = EarningsCalendarFilter(
            start_date=today,
            end_date=today,
            confirmed_only=True
        )
        
        earnings_service = EarningsService()
        calendar = await earnings_service.get_earnings_calendar(
            db=db,
            filters=filters,
            limit=50,
            offset=0
        )
        
        return calendar
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve today's earnings: {str(e)}"
        )


@router.get("/this-week", response_model=EarningsCalendarResponse)
async def get_this_weeks_earnings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get this week's earnings events.
    """
    try:
        today = date.today()
        # Get start of week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        filters = EarningsCalendarFilter(
            start_date=start_of_week,
            end_date=end_of_week
        )
        
        earnings_service = EarningsService()
        calendar = await earnings_service.get_earnings_calendar(
            db=db,
            filters=filters,
            limit=100,
            offset=0
        )
        
        return calendar
        
    except EarningsServiceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": e.message,
                "error_type": e.error_type,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve this week's earnings: {str(e)}"
        )