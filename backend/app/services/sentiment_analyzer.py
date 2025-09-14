"""
Sentiment analysis service for news and social media data.
Integrates with NewsAPI and Reddit API to analyze market sentiment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
import re

import aiohttp
import praw
from newsapi import NewsApiClient
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import numpy as np

from ..models.sentiment import (
    SentimentData, NewsItem, SocialMediaPost, SentimentAnalysisResult,
    SentimentAlert, SentimentConflict, TrendDirection, SentimentSource
)
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyzes sentiment from news articles and social media posts.
    Combines multiple sentiment analysis approaches for accuracy.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.news_client = None
        self.reddit_client = None
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Initialize API clients
        self._initialize_clients()
        
        # Financial keywords for relevance scoring
        self.financial_keywords = {
            'positive': ['profit', 'growth', 'earnings', 'revenue', 'bullish', 'buy', 'upgrade', 
                        'outperform', 'strong', 'beat', 'exceed', 'rally', 'surge', 'gain'],
            'negative': ['loss', 'decline', 'bearish', 'sell', 'downgrade', 'underperform', 
                        'weak', 'miss', 'fall', 'drop', 'crash', 'plunge', 'concern'],
            'neutral': ['hold', 'maintain', 'stable', 'unchanged', 'flat', 'sideways']
        }
        
        # Subreddits for financial sentiment
        self.financial_subreddits = [
            'investing', 'stocks', 'SecurityAnalysis', 'ValueInvesting',
            'StockMarket', 'financialindependence', 'SecurityAnalysis'
        ]
    
    def _initialize_clients(self):
        """Initialize API clients for news and social media."""
        try:
            # Initialize NewsAPI client
            if hasattr(self.settings, 'NEWS_API_KEY') and self.settings.NEWS_API_KEY:
                self.news_client = NewsApiClient(api_key=self.settings.NEWS_API_KEY)
                logger.info("NewsAPI client initialized successfully")
            else:
                logger.warning("NEWS_API_KEY not found in settings")
            
            # Initialize Reddit client
            if (hasattr(self.settings, 'REDDIT_CLIENT_ID') and 
                hasattr(self.settings, 'REDDIT_CLIENT_SECRET')):
                self.reddit_client = praw.Reddit(
                    client_id=self.settings.REDDIT_CLIENT_ID,
                    client_secret=self.settings.REDDIT_CLIENT_SECRET,
                    user_agent="settlers-of-stock/1.0"
                )
                logger.info("Reddit client initialized successfully")
            else:
                logger.warning("Reddit API credentials not found in settings")
                
        except Exception as e:
            logger.error(f"Error initializing API clients: {e}")
    
    async def analyze_stock_sentiment(
        self, 
        symbol: str, 
        days_back: int = 7,
        include_social: bool = True
    ) -> SentimentAnalysisResult:
        """
        Perform comprehensive sentiment analysis for a stock symbol.
        
        Args:
            symbol: Stock symbol to analyze
            days_back: Number of days to look back for news/posts
            include_social: Whether to include social media analysis
            
        Returns:
            Complete sentiment analysis result
        """
        logger.info(f"Starting sentiment analysis for {symbol}")
        
        try:
            # Fetch news and social media data concurrently
            tasks = [self._fetch_news_data(symbol, days_back)]
            
            if include_social:
                tasks.append(self._fetch_social_data(symbol, days_back))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            news_items = results[0] if not isinstance(results[0], Exception) else []
            social_posts = results[1] if len(results) > 1 and not isinstance(results[1], Exception) else []
            
            # Analyze sentiment for each data source
            news_sentiment = self._analyze_news_sentiment(news_items)
            social_sentiment = self._analyze_social_sentiment(social_posts) if social_posts else Decimal('0')
            
            # Calculate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(
                news_sentiment, social_sentiment, len(news_items), len(social_posts)
            )
            
            # Analyze trends
            trend_direction, trend_strength = self._analyze_sentiment_trend(
                news_items + social_posts
            )
            
            # Calculate confidence and volatility
            confidence_score = self._calculate_confidence_score(news_items, social_posts)
            volatility = self._calculate_sentiment_volatility(news_items + social_posts)
            
            # Create sentiment data
            sentiment_data = SentimentData(
                symbol=symbol,
                overall_sentiment=overall_sentiment,
                news_sentiment=news_sentiment,
                social_sentiment=social_sentiment,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                volatility=volatility,
                news_articles_count=len(news_items),
                social_posts_count=len(social_posts),
                data_freshness=datetime.now(),
                confidence_score=confidence_score,
                sources=[SentimentSource.NEWS, SentimentSource.REDDIT] if social_posts else [SentimentSource.NEWS],
                source_weights={
                    'news': Decimal('0.6') if social_posts else Decimal('1.0'),
                    'social': Decimal('0.4') if social_posts else Decimal('0.0')
                }
            )
            
            # Generate alerts for significant sentiment changes
            alerts = await self._generate_sentiment_alerts(symbol, sentiment_data)
            
            return SentimentAnalysisResult(
                symbol=symbol,
                sentiment_data=sentiment_data,
                recent_news=news_items[:10],  # Limit to most recent 10
                recent_social_posts=social_posts[:10],
                sentiment_alerts=alerts,
                conflicts=[],  # Will be populated by analysis engine
                analysis_timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis for {symbol}: {e}")
            # Return empty result with error indication
            return SentimentAnalysisResult(
                symbol=symbol,
                sentiment_data=SentimentData(
                    symbol=symbol,
                    overall_sentiment=Decimal('0'),
                    news_sentiment=Decimal('0'),
                    social_sentiment=Decimal('0'),
                    trend_direction=TrendDirection.STABLE,
                    trend_strength=Decimal('0'),
                    volatility=Decimal('0'),
                    news_articles_count=0,
                    social_posts_count=0,
                    data_freshness=datetime.now(),
                    confidence_score=Decimal('0'),
                    sources=[],
                    source_weights={}
                )
            )
    
    async def _fetch_news_data(self, symbol: str, days_back: int) -> List[NewsItem]:
        """Fetch recent news articles for a stock symbol."""
        if not self.news_client:
            logger.warning("NewsAPI client not available")
            return []
        
        try:
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_back)
            
            # Search for news articles
            articles = self.news_client.get_everything(
                q=f'"{symbol}" OR stock OR shares',
                language='en',
                sort_by='publishedAt',
                from_param=from_date.strftime('%Y-%m-%d'),
                to=to_date.strftime('%Y-%m-%d'),
                page_size=50
            )
            
            news_items = []
            for article in articles.get('articles', []):
                try:
                    # Analyze sentiment for the article
                    text = f"{article.get('title', '')} {article.get('description', '')}"
                    sentiment_score = self._analyze_text_sentiment(text)
                    relevance_score = self._calculate_relevance_score(text, symbol)
                    
                    # Only include relevant articles
                    if relevance_score > 0.3:
                        news_item = NewsItem(
                            id=f"news_{hash(article.get('url', ''))}",
                            title=article.get('title', ''),
                            summary=article.get('description', ''),
                            url=article.get('url', ''),
                            source=article.get('source', {}).get('name', 'Unknown'),
                            author=article.get('author'),
                            published_at=datetime.fromisoformat(
                                article.get('publishedAt', '').replace('Z', '+00:00')
                            ),
                            sentiment_score=sentiment_score,
                            relevance_score=relevance_score,
                            symbols=[symbol],
                            keywords=self._extract_financial_keywords(text)
                        )
                        news_items.append(news_item)
                        
                except Exception as e:
                    logger.warning(f"Error processing news article: {e}")
                    continue
            
            logger.info(f"Fetched {len(news_items)} relevant news articles for {symbol}")
            return sorted(news_items, key=lambda x: x.published_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching news data for {symbol}: {e}")
            return []
    
    async def _fetch_social_data(self, symbol: str, days_back: int) -> List[SocialMediaPost]:
        """Fetch recent social media posts from Reddit."""
        if not self.reddit_client:
            logger.warning("Reddit client not available")
            return []
        
        try:
            social_posts = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Search across financial subreddits
            for subreddit_name in self.financial_subreddits:
                try:
                    subreddit = self.reddit_client.subreddit(subreddit_name)
                    
                    # Search for posts mentioning the symbol
                    for submission in subreddit.search(f"{symbol}", time_filter="week", limit=20):
                        created_time = datetime.fromtimestamp(submission.created_utc)
                        
                        if created_time < cutoff_date:
                            continue
                        
                        # Analyze post content
                        text = f"{submission.title} {submission.selftext}"
                        sentiment_score = self._analyze_text_sentiment(text)
                        relevance_score = self._calculate_relevance_score(text, symbol)
                        
                        if relevance_score > 0.4:  # Higher threshold for social media
                            social_post = SocialMediaPost(
                                id=f"reddit_{submission.id}",
                                platform="reddit",
                                title=submission.title,
                                content=submission.selftext[:500],  # Limit content length
                                author=str(submission.author) if submission.author else "Unknown",
                                subreddit=subreddit_name,
                                score=submission.score,
                                comments_count=submission.num_comments,
                                created_at=created_time,
                                sentiment_score=sentiment_score,
                                relevance_score=relevance_score,
                                symbols=[symbol]
                            )
                            social_posts.append(social_post)
                            
                except Exception as e:
                    logger.warning(f"Error fetching from subreddit {subreddit_name}: {e}")
                    continue
            
            logger.info(f"Fetched {len(social_posts)} relevant social media posts for {symbol}")
            return sorted(social_posts, key=lambda x: x.created_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Error fetching social media data for {symbol}: {e}")
            return []
    
    def _analyze_text_sentiment(self, text: str) -> Decimal:
        """
        Analyze sentiment of text using multiple approaches.
        Combines VADER and TextBlob for better accuracy.
        """
        if not text or not text.strip():
            return Decimal('0')
        
        try:
            # VADER sentiment (good for social media)
            vader_scores = self.vader_analyzer.polarity_scores(text)
            vader_compound = vader_scores['compound']
            
            # TextBlob sentiment (good for formal text)
            blob = TextBlob(text)
            textblob_polarity = blob.sentiment.polarity
            
            # Combine scores with weights
            # VADER is better for informal text, TextBlob for formal
            combined_score = (vader_compound * 0.6) + (textblob_polarity * 0.4)
            
            # Apply financial keyword boost
            keyword_boost = self._calculate_keyword_sentiment_boost(text)
            final_score = combined_score + keyword_boost
            
            # Clamp to [-1, 1] range
            final_score = max(-1, min(1, final_score))
            
            return Decimal(str(round(final_score, 3)))
            
        except Exception as e:
            logger.warning(f"Error analyzing text sentiment: {e}")
            return Decimal('0')
    
    def _calculate_keyword_sentiment_boost(self, text: str) -> float:
        """Calculate sentiment boost based on financial keywords."""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.financial_keywords['positive'] if word in text_lower)
        negative_count = sum(1 for word in self.financial_keywords['negative'] if word in text_lower)
        
        # Calculate boost (max ±0.2)
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0
        
        boost = (positive_count - negative_count) / total_keywords * 0.2
        return boost
    
    def _calculate_relevance_score(self, text: str, symbol: str) -> Decimal:
        """Calculate how relevant the text is to the stock symbol."""
        if not text:
            return Decimal('0')
        
        text_lower = text.lower()
        symbol_lower = symbol.lower()
        
        relevance_score = 0.0
        
        # Direct symbol mention
        if symbol_lower in text_lower:
            relevance_score += 0.5
        
        # Financial keywords
        financial_word_count = sum(
            1 for word_list in self.financial_keywords.values()
            for word in word_list
            if word in text_lower
        )
        relevance_score += min(financial_word_count * 0.1, 0.4)
        
        # Stock-related terms
        stock_terms = ['stock', 'share', 'equity', 'investment', 'trading', 'market']
        stock_term_count = sum(1 for term in stock_terms if term in text_lower)
        relevance_score += min(stock_term_count * 0.05, 0.2)
        
        return Decimal(str(min(relevance_score, 1.0)))
    
    def _extract_financial_keywords(self, text: str) -> List[str]:
        """Extract financial keywords from text."""
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        for word_list in self.financial_keywords.values():
            for word in word_list:
                if word in text_lower:
                    found_keywords.append(word)
        
        return list(set(found_keywords))  # Remove duplicates
    
    def _analyze_news_sentiment(self, news_items: List[NewsItem]) -> Decimal:
        """Calculate overall news sentiment."""
        if not news_items:
            return Decimal('0')
        
        # Weight recent news more heavily
        total_weighted_sentiment = Decimal('0')
        total_weight = Decimal('0')
        
        now = datetime.now()
        
        for item in news_items:
            # Calculate time-based weight (more recent = higher weight)
            hours_old = (now - item.published_at).total_seconds() / 3600
            time_weight = max(0.1, 1.0 - (hours_old / 168))  # Decay over 1 week
            
            # Apply relevance weight
            relevance_weight = float(item.relevance_score)
            
            # Combined weight
            weight = Decimal(str(time_weight * relevance_weight))
            
            total_weighted_sentiment += item.sentiment_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return Decimal('0')
        
        return total_weighted_sentiment / total_weight
    
    def _analyze_social_sentiment(self, social_posts: List[SocialMediaPost]) -> Decimal:
        """Calculate overall social media sentiment."""
        if not social_posts:
            return Decimal('0')
        
        # Weight posts by engagement (score/upvotes)
        total_weighted_sentiment = Decimal('0')
        total_weight = Decimal('0')
        
        for post in social_posts:
            # Use post score as weight (with minimum weight)
            engagement_weight = max(1, post.score or 1)
            relevance_weight = float(post.relevance_score)
            
            weight = Decimal(str(engagement_weight * relevance_weight))
            
            total_weighted_sentiment += post.sentiment_score * weight
            total_weight += weight
        
        if total_weight == 0:
            return Decimal('0')
        
        return total_weighted_sentiment / total_weight
    
    def _calculate_overall_sentiment(
        self, 
        news_sentiment: Decimal, 
        social_sentiment: Decimal,
        news_count: int,
        social_count: int
    ) -> Decimal:
        """Calculate overall sentiment combining news and social media."""
        if news_count == 0 and social_count == 0:
            return Decimal('0')
        
        # Weight based on data availability and reliability
        news_weight = Decimal('0.7') if news_count > 0 else Decimal('0')
        social_weight = Decimal('0.3') if social_count > 0 else Decimal('0')
        
        # Adjust weights if only one source is available
        total_weight = news_weight + social_weight
        if total_weight > 0:
            news_weight = news_weight / total_weight
            social_weight = social_weight / total_weight
        
        overall = (news_sentiment * news_weight) + (social_sentiment * social_weight)
        return overall
    
    def _analyze_sentiment_trend(
        self, 
        items: List[NewsItem | SocialMediaPost]
    ) -> Tuple[TrendDirection, Decimal]:
        """Analyze sentiment trend over time."""
        if len(items) < 3:
            return TrendDirection.STABLE, Decimal('0')
        
        # Sort by timestamp
        sorted_items = sorted(items, key=lambda x: x.published_at if hasattr(x, 'published_at') else x.created_at)
        
        # Calculate sentiment over time periods
        now = datetime.now()
        recent_items = [item for item in sorted_items 
                       if (now - (item.published_at if hasattr(item, 'published_at') else item.created_at)).days <= 2]
        older_items = [item for item in sorted_items 
                      if (now - (item.published_at if hasattr(item, 'published_at') else item.created_at)).days > 2]
        
        if not recent_items or not older_items:
            return TrendDirection.STABLE, Decimal('0')
        
        recent_sentiment = sum(item.sentiment_score for item in recent_items) / len(recent_items)
        older_sentiment = sum(item.sentiment_score for item in older_items) / len(older_items)
        
        sentiment_change = recent_sentiment - older_sentiment
        change_magnitude = abs(sentiment_change)
        
        # Determine trend direction
        if change_magnitude < Decimal('0.1'):
            direction = TrendDirection.STABLE
        elif sentiment_change > 0:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.DECLINING
        
        # Check for volatility
        if change_magnitude > Decimal('0.3'):
            direction = TrendDirection.VOLATILE
        
        return direction, min(change_magnitude, Decimal('1'))
    
    def _calculate_confidence_score(
        self, 
        news_items: List[NewsItem], 
        social_posts: List[SocialMediaPost]
    ) -> Decimal:
        """Calculate confidence in sentiment analysis."""
        total_items = len(news_items) + len(social_posts)
        
        if total_items == 0:
            return Decimal('0')
        
        # Base confidence on data volume
        volume_score = min(total_items / 20, 1.0)  # Max confidence at 20+ items
        
        # Adjust for data quality
        high_relevance_items = sum(
            1 for item in news_items if item.relevance_score > Decimal('0.7')
        ) + sum(
            1 for item in social_posts if item.relevance_score > Decimal('0.7')
        )
        
        quality_score = high_relevance_items / total_items if total_items > 0 else 0
        
        # Combine scores
        confidence = (volume_score * 0.6) + (quality_score * 0.4)
        return Decimal(str(round(confidence, 3)))
    
    def _calculate_sentiment_volatility(
        self, 
        items: List[NewsItem | SocialMediaPost]
    ) -> Decimal:
        """Calculate sentiment volatility."""
        if len(items) < 2:
            return Decimal('0')
        
        sentiments = [float(item.sentiment_score) for item in items]
        volatility = np.std(sentiments) if len(sentiments) > 1 else 0
        
        return Decimal(str(round(volatility, 3)))
    
    async def _generate_sentiment_alerts(
        self, 
        symbol: str, 
        sentiment_data: SentimentData
    ) -> List[SentimentAlert]:
        """Generate alerts for significant sentiment changes."""
        alerts = []
        
        # This would typically compare with historical data
        # For now, generate alerts based on extreme values
        
        if abs(sentiment_data.overall_sentiment) > Decimal('0.7'):
            alert_type = "sentiment_spike" if sentiment_data.overall_sentiment > 0 else "sentiment_drop"
            
            alert = SentimentAlert(
                symbol=symbol,
                alert_type=alert_type,
                current_sentiment=sentiment_data.overall_sentiment,
                previous_sentiment=Decimal('0'),  # Would be from historical data
                change_magnitude=abs(sentiment_data.overall_sentiment),
                trigger_time=datetime.now(),
                description=f"Strong {'positive' if sentiment_data.overall_sentiment > 0 else 'negative'} sentiment detected",
                confidence=sentiment_data.confidence_score
            )
            alerts.append(alert)
        
        return alerts
    
    async def detect_sentiment_conflicts(
        self, 
        symbol: str, 
        sentiment_score: Decimal, 
        fundamental_score: Decimal
    ) -> List[SentimentConflict]:
        """Detect conflicts between sentiment and fundamental analysis."""
        conflicts = []
        
        # Define conflict threshold
        conflict_threshold = Decimal('0.5')
        
        # Check for significant divergence
        divergence = abs(sentiment_score - Decimal(str(fundamental_score)))
        
        if divergence > conflict_threshold:
            if sentiment_score > 0 and fundamental_score < 0:
                conflict_type = "bullish_sentiment_bearish_fundamentals"
                explanation = "Market sentiment is positive but fundamental analysis suggests caution"
            elif sentiment_score < 0 and fundamental_score > 0:
                conflict_type = "bearish_sentiment_bullish_fundamentals"
                explanation = "Market sentiment is negative but fundamentals appear strong"
            else:
                return conflicts  # No significant conflict
            
            conflict = SentimentConflict(
                symbol=symbol,
                sentiment_score=sentiment_score,
                fundamental_score=Decimal(str(fundamental_score)),
                conflict_severity=min(divergence, Decimal('1.0')),  # Cap at 1.0
                conflict_type=conflict_type,
                explanation=explanation,
                detected_at=datetime.now()
            )
            conflicts.append(conflict)
        
        return conflicts
# Global sentiment analyzer instance
sentiment_analyzer = SentimentAnalyzer()