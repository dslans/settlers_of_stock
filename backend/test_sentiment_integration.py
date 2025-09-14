#!/usr/bin/env python3
"""
Integration test for sentiment analysis API endpoints.
"""

import asyncio
import sys
import os
from unittest.mock import Mock, patch
from decimal import Decimal
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.sentiment_analyzer import SentimentAnalyzer
from app.models.sentiment import NewsItem, SocialMediaPost, SentimentAnalysisResult, SentimentData, TrendDirection, SentimentSource


async def test_full_sentiment_analysis():
    """Test the complete sentiment analysis workflow."""
    print("Testing complete sentiment analysis workflow...")
    
    # Create analyzer
    analyzer = SentimentAnalyzer()
    
    # Mock the API calls since we don't have real API keys
    with patch.object(analyzer, '_fetch_news_data') as mock_news, \
         patch.object(analyzer, '_fetch_social_data') as mock_social:
        
        # Mock news data
        mock_news_items = [
            NewsItem(
                id="news_1",
                title="AAPL reports strong Q4 earnings, beats expectations",
                summary="Apple Inc. reported better than expected quarterly results with strong iPhone sales",
                url="https://example.com/news1",
                source="Financial Times",
                published_at=datetime.now() - timedelta(hours=2),
                sentiment_score=Decimal('0.8'),
                relevance_score=Decimal('0.9'),
                symbols=["AAPL"],
                keywords=["earnings", "beats", "strong", "iPhone"]
            ),
            NewsItem(
                id="news_2",
                title="Apple faces supply chain challenges",
                summary="Apple may face production delays due to supply chain issues",
                url="https://example.com/news2",
                source="Reuters",
                published_at=datetime.now() - timedelta(hours=8),
                sentiment_score=Decimal('-0.3'),
                relevance_score=Decimal('0.8'),
                symbols=["AAPL"],
                keywords=["challenges", "delays", "supply"]
            ),
            NewsItem(
                id="news_3",
                title="AAPL stock upgraded by analysts",
                summary="Multiple analysts upgrade Apple stock with higher price targets",
                url="https://example.com/news3",
                source="Bloomberg",
                published_at=datetime.now() - timedelta(hours=4),
                sentiment_score=Decimal('0.6'),
                relevance_score=Decimal('0.95'),
                symbols=["AAPL"],
                keywords=["upgraded", "analysts", "price", "targets"]
            )
        ]
        
        # Mock social media data
        mock_social_posts = [
            SocialMediaPost(
                id="reddit_1",
                platform="reddit",
                title="AAPL earnings call was amazing!",
                content="Just listened to the AAPL earnings call. Revenue growth is incredible, buying more shares tomorrow!",
                author="investor_pro",
                subreddit="stocks",
                score=45,
                comments_count=23,
                created_at=datetime.now() - timedelta(hours=3),
                sentiment_score=Decimal('0.9'),
                relevance_score=Decimal('0.85'),
                symbols=["AAPL"]
            ),
            SocialMediaPost(
                id="reddit_2",
                platform="reddit",
                title="Thoughts on AAPL valuation?",
                content="AAPL seems overvalued at current levels. P/E ratio is getting high. What do you think?",
                author="value_hunter",
                subreddit="investing",
                score=28,
                comments_count=15,
                created_at=datetime.now() - timedelta(hours=6),
                sentiment_score=Decimal('-0.2'),
                relevance_score=Decimal('0.7'),
                symbols=["AAPL"]
            ),
            SocialMediaPost(
                id="reddit_3",
                platform="reddit",
                title="AAPL long term outlook",
                content="Despite short term volatility, AAPL has strong fundamentals and great products. Holding long term.",
                author="long_term_investor",
                subreddit="SecurityAnalysis",
                score=67,
                comments_count=31,
                created_at=datetime.now() - timedelta(hours=1),
                sentiment_score=Decimal('0.5'),
                relevance_score=Decimal('0.8'),
                symbols=["AAPL"]
            )
        ]
        
        mock_news.return_value = mock_news_items
        mock_social.return_value = mock_social_posts
        
        # Perform sentiment analysis
        result = await analyzer.analyze_stock_sentiment("AAPL", days_back=7, include_social=True)
        
        # Verify result structure
        assert isinstance(result, SentimentAnalysisResult)
        assert result.symbol == "AAPL"
        assert isinstance(result.sentiment_data, SentimentData)
        
        # Verify sentiment data
        sentiment_data = result.sentiment_data
        print(f"Overall sentiment: {sentiment_data.overall_sentiment}")
        print(f"News sentiment: {sentiment_data.news_sentiment}")
        print(f"Social sentiment: {sentiment_data.social_sentiment}")
        print(f"Trend direction: {sentiment_data.trend_direction}")
        print(f"Confidence score: {sentiment_data.confidence_score}")
        
        # Verify sentiment is positive (more positive news and social posts)
        assert sentiment_data.overall_sentiment > 0, "Overall sentiment should be positive"
        assert sentiment_data.news_sentiment > 0, "News sentiment should be positive"
        assert sentiment_data.social_sentiment > 0, "Social sentiment should be positive"
        
        # Verify data counts
        assert sentiment_data.news_articles_count == 3
        assert sentiment_data.social_posts_count == 3
        
        # Verify sources
        assert SentimentSource.NEWS in sentiment_data.sources
        assert SentimentSource.REDDIT in sentiment_data.sources
        
        # Verify recent items are included
        assert len(result.recent_news) <= 10
        assert len(result.recent_social_posts) <= 10
        assert len(result.recent_news) > 0
        assert len(result.recent_social_posts) > 0
        
        # Verify confidence is reasonable
        assert 0 <= sentiment_data.confidence_score <= 1
        assert sentiment_data.confidence_score > 0.3  # Should have decent confidence with this much data
        
        print("✅ Complete sentiment analysis test passed!")


async def test_sentiment_analysis_news_only():
    """Test sentiment analysis with news only."""
    print("Testing sentiment analysis with news only...")
    
    analyzer = SentimentAnalyzer()
    
    with patch.object(analyzer, '_fetch_news_data') as mock_news:
        mock_news_items = [
            NewsItem(
                id="news_1",
                title="Stock market rally continues",
                summary="Markets show strong performance across sectors",
                url="https://example.com/news1",
                source="MarketWatch",
                published_at=datetime.now() - timedelta(hours=1),
                sentiment_score=Decimal('0.7'),
                relevance_score=Decimal('0.6'),
                symbols=["TSLA"],
                keywords=["rally", "strong", "performance"]
            )
        ]
        
        mock_news.return_value = mock_news_items
        
        # Analyze with social media disabled
        result = await analyzer.analyze_stock_sentiment("TSLA", include_social=False)
        
        assert result.symbol == "TSLA"
        assert result.sentiment_data.news_articles_count == 1
        assert result.sentiment_data.social_posts_count == 0
        assert len(result.recent_social_posts) == 0
        assert SentimentSource.NEWS in result.sentiment_data.sources
        assert SentimentSource.REDDIT not in result.sentiment_data.sources
        
        print("✅ News-only sentiment analysis test passed!")


async def test_sentiment_conflict_detection():
    """Test sentiment conflict detection."""
    print("Testing sentiment conflict detection...")
    
    analyzer = SentimentAnalyzer()
    
    # Test bullish sentiment vs bearish fundamentals
    conflicts = await analyzer.detect_sentiment_conflicts(
        "TSLA", Decimal('0.8'), Decimal('-0.7')
    )
    
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "bullish_sentiment_bearish_fundamentals"
    assert conflicts[0].symbol == "TSLA"
    assert conflicts[0].conflict_severity > Decimal('0.5')
    
    # Test bearish sentiment vs bullish fundamentals
    conflicts = await analyzer.detect_sentiment_conflicts(
        "MSFT", Decimal('-0.6'), Decimal('0.8')
    )
    
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "bearish_sentiment_bullish_fundamentals"
    assert conflicts[0].symbol == "MSFT"
    
    # Test no conflict (aligned sentiment and fundamentals)
    conflicts = await analyzer.detect_sentiment_conflicts(
        "GOOGL", Decimal('0.5'), Decimal('0.6')
    )
    
    assert len(conflicts) == 0
    
    print("✅ Sentiment conflict detection test passed!")


async def test_error_handling():
    """Test error handling in sentiment analysis."""
    print("Testing error handling...")
    
    analyzer = SentimentAnalyzer()
    
    # Mock API failures
    with patch.object(analyzer, '_fetch_news_data') as mock_news, \
         patch.object(analyzer, '_fetch_social_data') as mock_social:
        
        mock_news.side_effect = Exception("News API error")
        mock_social.side_effect = Exception("Social API error")
        
        # Should return empty result without crashing
        result = await analyzer.analyze_stock_sentiment("ERROR")
        
        assert result.symbol == "ERROR"
        assert result.sentiment_data.overall_sentiment == Decimal('0')
        assert result.sentiment_data.confidence_score == Decimal('0')
        assert result.sentiment_data.news_articles_count == 0
        assert result.sentiment_data.social_posts_count == 0
        
        print("✅ Error handling test passed!")


async def main():
    """Run all integration tests."""
    print("Running sentiment analysis integration tests...\n")
    
    await test_full_sentiment_analysis()
    print()
    await test_sentiment_analysis_news_only()
    print()
    await test_sentiment_conflict_detection()
    print()
    await test_error_handling()
    
    print("\n🎉 All sentiment analysis integration tests passed!")


if __name__ == "__main__":
    asyncio.run(main())