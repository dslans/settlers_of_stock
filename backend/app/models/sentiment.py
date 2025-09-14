"""
Sentiment analysis data models for news and social media sentiment.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SentimentSource(str, Enum):
    """Sources of sentiment data."""
    NEWS = "news"
    REDDIT = "reddit"
    TWITTER = "twitter"
    ANALYST = "analyst"
    COMBINED = "combined"


class TrendDirection(str, Enum):
    """Direction of sentiment trend."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"


class NewsItem(BaseModel):
    """Individual news article with sentiment analysis."""
    id: str
    title: str
    summary: Optional[str] = None
    url: str
    source: str
    author: Optional[str] = None
    published_at: datetime
    sentiment_score: Decimal = Field(..., ge=-1, le=1, description="Sentiment score from -1 (negative) to 1 (positive)")
    relevance_score: Decimal = Field(..., ge=0, le=1, description="Relevance to the stock from 0 to 1")
    symbols: List[str] = Field(default_factory=list, description="Stock symbols mentioned in the article")
    keywords: List[str] = Field(default_factory=list, description="Key financial terms extracted")
    
    @validator('sentiment_score', 'relevance_score', pre=True)
    def convert_to_decimal(cls, v):
        """Convert float values to Decimal for precision."""
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class SocialMediaPost(BaseModel):
    """Social media post with sentiment analysis."""
    id: str
    platform: str  # reddit, twitter, etc.
    title: Optional[str] = None
    content: str
    author: str
    subreddit: Optional[str] = None  # for Reddit posts
    score: Optional[int] = None  # upvotes/likes
    comments_count: Optional[int] = None
    created_at: datetime
    sentiment_score: Decimal = Field(..., ge=-1, le=1)
    relevance_score: Decimal = Field(..., ge=0, le=1)
    symbols: List[str] = Field(default_factory=list)
    
    @validator('sentiment_score', 'relevance_score', pre=True)
    def convert_to_decimal(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class SentimentData(BaseModel):
    """Aggregated sentiment data for a stock symbol."""
    symbol: str
    overall_sentiment: Decimal = Field(..., ge=-1, le=1, description="Overall sentiment score")
    news_sentiment: Decimal = Field(..., ge=-1, le=1, description="News-based sentiment")
    social_sentiment: Decimal = Field(..., ge=-1, le=1, description="Social media sentiment")
    analyst_sentiment: Optional[Decimal] = Field(None, ge=-1, le=1, description="Analyst sentiment")
    
    # Trend analysis
    trend_direction: TrendDirection
    trend_strength: Decimal = Field(..., ge=0, le=1, description="Strength of the trend")
    volatility: Decimal = Field(..., ge=0, description="Sentiment volatility measure")
    
    # Data quality metrics
    news_articles_count: int = Field(ge=0)
    social_posts_count: int = Field(ge=0)
    data_freshness: datetime = Field(description="When the data was last updated")
    confidence_score: Decimal = Field(..., ge=0, le=1, description="Confidence in sentiment accuracy")
    
    # Source breakdown
    sources: List[SentimentSource] = Field(default_factory=list)
    source_weights: Dict[str, Decimal] = Field(default_factory=dict)
    
    @validator('overall_sentiment', 'news_sentiment', 'social_sentiment', 'analyst_sentiment', 
              'trend_strength', 'volatility', 'confidence_score', pre=True)
    def convert_to_decimal(cls, v):
        if v is not None and isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class SentimentAlert(BaseModel):
    """Alert for significant sentiment changes."""
    symbol: str
    alert_type: str  # "sentiment_spike", "sentiment_drop", "trend_reversal"
    current_sentiment: Decimal
    previous_sentiment: Decimal
    change_magnitude: Decimal
    trigger_time: datetime
    description: str
    confidence: Decimal = Field(..., ge=0, le=1)


class SentimentConflict(BaseModel):
    """Detected conflict between sentiment and fundamental analysis."""
    symbol: str
    sentiment_score: Decimal
    fundamental_score: Decimal
    conflict_severity: Decimal = Field(..., ge=0, le=1)
    conflict_type: str  # "bullish_sentiment_bearish_fundamentals", etc.
    explanation: str
    detected_at: datetime
    
    @validator('sentiment_score', 'fundamental_score', 'conflict_severity', pre=True)
    def convert_to_decimal(cls, v):
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return v


class SentimentAnalysisResult(BaseModel):
    """Complete sentiment analysis result for a stock."""
    symbol: str
    sentiment_data: SentimentData
    recent_news: List[NewsItem] = Field(default_factory=list)
    recent_social_posts: List[SocialMediaPost] = Field(default_factory=list)
    sentiment_alerts: List[SentimentAlert] = Field(default_factory=list)
    conflicts: List[SentimentConflict] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }