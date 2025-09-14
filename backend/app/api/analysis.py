"""
Analysis API endpoints for stock analysis and recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging

from ..services.analysis_engine import AnalysisEngine, AnalysisEngineException
from ..services.sentiment_analyzer import SentimentAnalyzer
from ..models.analysis import AnalysisResult
from ..models.sentiment import SentimentAnalysisResult, SentimentConflict
from ..core.dependencies import get_current_user
from ..models.user import User

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/analysis", tags=["analysis"])

# Create analysis engine and sentiment analyzer instances
analysis_engine = AnalysisEngine()
sentiment_analyzer = SentimentAnalyzer()


@router.get("/stock/{symbol}", response_model=AnalysisResult)
async def analyze_stock(
    symbol: str,
    include_fundamental: bool = Query(True, description="Include fundamental analysis"),
    include_technical: bool = Query(True, description="Include technical analysis"),
    timeframe: str = Query("1D", description="Technical analysis timeframe"),
    current_user: User = Depends(get_current_user)
):
    """
    Perform comprehensive stock analysis.
    
    Args:
        symbol: Stock ticker symbol
        include_fundamental: Whether to include fundamental analysis
        include_technical: Whether to include technical analysis
        timeframe: Technical analysis timeframe (1D, 1W, 1M, etc.)
        current_user: Current authenticated user
        
    Returns:
        AnalysisResult with comprehensive analysis and recommendation
        
    Raises:
        HTTPException: If analysis fails or symbol is invalid
    """
    try:
        logger.info(f"User {current_user.email} requested analysis for {symbol}")
        
        # Validate symbol
        symbol = symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Validate timeframe
        valid_timeframes = ["1D", "1W", "1M", "3M", "6M", "1Y", "2Y"]
        if timeframe not in valid_timeframes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
            )
        
        # Perform analysis
        result = await analysis_engine.analyze_stock(
            symbol=symbol,
            include_fundamental=include_fundamental,
            include_technical=include_technical,
            timeframe=timeframe
        )
        
        logger.info(f"Analysis completed for {symbol}: {result.recommendation} ({result.confidence}%)")
        return result
        
    except AnalysisEngineException as e:
        logger.error(f"Analysis engine error for {symbol}: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.error_type,
                "message": e.message,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error analyzing {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during analysis"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for the analysis service.
    
    Returns:
        dict: Service health status
    """
    try:
        # Basic health check - could be expanded to check dependencies
        return {
            "status": "healthy",
            "service": "analysis_engine",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service unavailable"
        )


@router.get("/recommendations/{symbol}")
async def get_recommendations_summary(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a quick recommendations summary for a stock.
    
    Args:
        symbol: Stock ticker symbol
        current_user: Current authenticated user
        
    Returns:
        dict: Quick recommendation summary
    """
    try:
        logger.info(f"User {current_user.email} requested recommendation summary for {symbol}")
        
        # Perform quick analysis
        result = await analysis_engine.analyze_stock(symbol)
        
        # Return summary
        summary = {
            "symbol": result.symbol,
            "recommendation": result.recommendation,
            "confidence": result.confidence,
            "risk_level": result.risk_level,
            "summary": result.get_recommendation_summary(),
            "risk_summary": result.get_risk_summary(),
            "key_strengths": result.strengths[:3],  # Top 3 strengths
            "key_risks": result.risks[:3],  # Top 3 risks
            "price_targets": [
                {
                    "timeframe": target.timeframe,
                    "target": float(target.target),
                    "confidence": target.confidence
                }
                for target in result.price_targets
            ]
        }
        
        return summary
        
    except AnalysisEngineException as e:
        logger.error(f"Analysis engine error for {symbol}: {e.message}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.error_type,
                "message": e.message,
                "suggestions": e.suggestions
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error getting recommendations for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during analysis"
        )


@router.get("/sentiment/{symbol}", response_model=SentimentAnalysisResult)
async def analyze_sentiment(
    symbol: str,
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back for sentiment data"),
    include_social: bool = Query(True, description="Include social media sentiment analysis"),
    current_user: User = Depends(get_current_user)
):
    """
    Perform sentiment analysis for a stock symbol.
    
    Args:
        symbol: Stock ticker symbol
        days_back: Number of days to look back for news and social media data
        include_social: Whether to include social media analysis
        current_user: Current authenticated user
        
    Returns:
        SentimentAnalysisResult with comprehensive sentiment analysis
        
    Raises:
        HTTPException: If analysis fails or symbol is invalid
    """
    try:
        logger.info(f"User {current_user.email} requested sentiment analysis for {symbol}")
        
        # Validate symbol
        symbol = symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Perform sentiment analysis
        result = await sentiment_analyzer.analyze_stock_sentiment(
            symbol=symbol,
            days_back=days_back,
            include_social=include_social
        )
        
        logger.info(f"Sentiment analysis completed for {symbol}: {result.sentiment_data.overall_sentiment}")
        return result
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during sentiment analysis"
        )


@router.get("/sentiment/{symbol}/conflicts")
async def detect_sentiment_conflicts(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Detect conflicts between sentiment and fundamental analysis.
    
    Args:
        symbol: Stock ticker symbol
        current_user: Current authenticated user
        
    Returns:
        List of detected conflicts between sentiment and fundamentals
        
    Raises:
        HTTPException: If analysis fails or symbol is invalid
    """
    try:
        logger.info(f"User {current_user.email} requested sentiment conflict analysis for {symbol}")
        
        # Validate symbol
        symbol = symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Get sentiment analysis
        sentiment_result = await sentiment_analyzer.analyze_stock_sentiment(symbol)
        sentiment_score = sentiment_result.sentiment_data.overall_sentiment
        
        # Get fundamental analysis (simplified - would normally get from analysis engine)
        try:
            analysis_result = await analysis_engine.analyze_stock(symbol, include_technical=False)
            # Convert recommendation to score for comparison
            fundamental_score = {
                "BUY": 0.7,
                "HOLD": 0.0,
                "SELL": -0.7
            }.get(analysis_result.recommendation, 0.0)
        except Exception:
            # If fundamental analysis fails, use neutral score
            fundamental_score = 0.0
        
        # Detect conflicts
        conflicts = await sentiment_analyzer.detect_sentiment_conflicts(
            symbol, sentiment_score, fundamental_score
        )
        
        logger.info(f"Conflict analysis completed for {symbol}: {len(conflicts)} conflicts found")
        return {
            "symbol": symbol,
            "sentiment_score": float(sentiment_score),
            "fundamental_score": fundamental_score,
            "conflicts": conflicts,
            "analysis_timestamp": sentiment_result.analysis_timestamp
        }
        
    except Exception as e:
        logger.error(f"Error in conflict analysis for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during conflict analysis"
        )


@router.get("/sentiment/{symbol}/summary")
async def get_sentiment_summary(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get a quick sentiment summary for a stock.
    
    Args:
        symbol: Stock ticker symbol
        current_user: Current authenticated user
        
    Returns:
        dict: Quick sentiment summary
    """
    try:
        logger.info(f"User {current_user.email} requested sentiment summary for {symbol}")
        
        # Validate symbol
        symbol = symbol.upper().strip()
        if not symbol or len(symbol) > 10:
            raise HTTPException(
                status_code=400,
                detail="Invalid stock symbol format"
            )
        
        # Get sentiment analysis
        result = await sentiment_analyzer.analyze_stock_sentiment(symbol)
        sentiment_data = result.sentiment_data
        
        # Create summary
        summary = {
            "symbol": symbol,
            "overall_sentiment": float(sentiment_data.overall_sentiment),
            "sentiment_label": _get_sentiment_label(sentiment_data.overall_sentiment),
            "news_sentiment": float(sentiment_data.news_sentiment),
            "social_sentiment": float(sentiment_data.social_sentiment),
            "trend_direction": sentiment_data.trend_direction,
            "trend_strength": float(sentiment_data.trend_strength),
            "confidence_score": float(sentiment_data.confidence_score),
            "data_freshness": sentiment_data.data_freshness,
            "news_count": sentiment_data.news_articles_count,
            "social_posts_count": sentiment_data.social_posts_count,
            "volatility": float(sentiment_data.volatility),
            "alerts_count": len(result.sentiment_alerts),
            "top_news": [
                {
                    "title": news.title,
                    "source": news.source,
                    "sentiment": float(news.sentiment_score),
                    "published_at": news.published_at
                }
                for news in result.recent_news[:3]  # Top 3 news items
            ]
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting sentiment summary for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during sentiment summary"
        )


def _get_sentiment_label(sentiment_score) -> str:
    """Convert sentiment score to human-readable label."""
    if sentiment_score >= 0.5:
        return "Very Positive"
    elif sentiment_score >= 0.2:
        return "Positive"
    elif sentiment_score >= -0.2:
        return "Neutral"
    elif sentiment_score >= -0.5:
        return "Negative"
    else:
        return "Very Negative"