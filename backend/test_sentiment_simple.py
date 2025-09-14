#!/usr/bin/env python3
"""
Simple test script for sentiment analyzer functionality.
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.sentiment_analyzer import SentimentAnalyzer
from app.models.sentiment import NewsItem, SocialMediaPost


async def test_sentiment_analyzer():
    """Test basic sentiment analyzer functionality."""
    print("Testing SentimentAnalyzer...")
    
    # Create analyzer instance
    analyzer = SentimentAnalyzer()
    
    # Test text sentiment analysis
    print("\n1. Testing text sentiment analysis:")
    
    positive_text = "This stock is performing excellently with strong growth and profits"
    positive_sentiment = analyzer._analyze_text_sentiment(positive_text)
    print(f"Positive text sentiment: {positive_sentiment}")
    assert positive_sentiment > 0, "Positive text should have positive sentiment"
    
    negative_text = "The company is facing losses and declining performance"
    negative_sentiment = analyzer._analyze_text_sentiment(negative_text)
    print(f"Negative text sentiment: {negative_sentiment}")
    assert negative_sentiment < 0, "Negative text should have negative sentiment"
    
    neutral_text = "The company reported quarterly results"
    neutral_sentiment = analyzer._analyze_text_sentiment(neutral_text)
    print(f"Neutral text sentiment: {neutral_sentiment}")
    assert abs(neutral_sentiment) < 0.5, "Neutral text should have moderate sentiment"
    
    # Test relevance scoring
    print("\n2. Testing relevance scoring:")
    
    relevant_text = "AAPL stock price increased after strong earnings report"
    relevance = analyzer._calculate_relevance_score(relevant_text, "AAPL")
    print(f"Relevant text relevance: {relevance}")
    assert relevance > Decimal('0.5'), "Relevant text should have high relevance"
    
    irrelevant_text = "The weather is nice today"
    irrelevance = analyzer._calculate_relevance_score(irrelevant_text, "AAPL")
    print(f"Irrelevant text relevance: {irrelevance}")
    assert irrelevance < Decimal('0.3'), "Irrelevant text should have low relevance"
    
    # Test keyword extraction
    print("\n3. Testing keyword extraction:")
    
    keyword_text = "The company showed strong profit growth and beat earnings expectations"
    keywords = analyzer._extract_financial_keywords(keyword_text)
    print(f"Extracted keywords: {keywords}")
    assert "profit" in keywords, "Should extract 'profit' keyword"
    assert "growth" in keywords, "Should extract 'growth' keyword"
    assert "beat" in keywords, "Should extract 'beat' keyword"
    
    # Test news sentiment aggregation
    print("\n4. Testing news sentiment aggregation:")
    
    sample_news = [
        NewsItem(
            id="news_1",
            title="AAPL stock surges on strong earnings",
            summary="Apple reports better than expected results",
            url="https://example.com/news1",
            source="Financial Times",
            published_at=datetime.now() - timedelta(hours=2),
            sentiment_score=Decimal('0.8'),
            relevance_score=Decimal('0.9'),
            symbols=["AAPL"],
            keywords=["earnings", "surge", "strong"]
        ),
        NewsItem(
            id="news_2",
            title="AAPL faces regulatory concerns",
            summary="New regulations may impact Apple's business",
            url="https://example.com/news2",
            source="Reuters",
            published_at=datetime.now() - timedelta(hours=6),
            sentiment_score=Decimal('-0.4'),
            relevance_score=Decimal('0.7'),
            symbols=["AAPL"],
            keywords=["regulatory", "concerns"]
        )
    ]
    
    news_sentiment = analyzer._analyze_news_sentiment(sample_news)
    print(f"Aggregated news sentiment: {news_sentiment}")
    assert news_sentiment > 0, "Should be positive overall (recent positive news weighted more)"
    
    # Test social media sentiment aggregation
    print("\n5. Testing social media sentiment aggregation:")
    
    sample_social = [
        SocialMediaPost(
            id="reddit_1",
            platform="reddit",
            title="AAPL to the moon!",
            content="Just bought more AAPL shares, this stock is going up!",
            author="investor123",
            subreddit="stocks",
            score=25,
            comments_count=10,
            created_at=datetime.now() - timedelta(hours=1),
            sentiment_score=Decimal('0.7'),
            relevance_score=Decimal('0.8'),
            symbols=["AAPL"]
        ),
        SocialMediaPost(
            id="reddit_2",
            platform="reddit",
            title="Worried about AAPL",
            content="AAPL might be overvalued, considering selling",
            author="trader456",
            subreddit="investing",
            score=15,
            comments_count=5,
            created_at=datetime.now() - timedelta(hours=4),
            sentiment_score=Decimal('-0.3'),
            relevance_score=Decimal('0.6'),
            symbols=["AAPL"]
        )
    ]
    
    social_sentiment = analyzer._analyze_social_sentiment(sample_social)
    print(f"Aggregated social sentiment: {social_sentiment}")
    assert social_sentiment > 0, "Should be positive (higher engagement on positive post)"
    
    # Test overall sentiment calculation
    print("\n6. Testing overall sentiment calculation:")
    
    overall_sentiment = analyzer._calculate_overall_sentiment(
        news_sentiment, social_sentiment, len(sample_news), len(sample_social)
    )
    print(f"Overall sentiment: {overall_sentiment}")
    assert overall_sentiment > 0, "Overall sentiment should be positive"
    
    # Test sentiment trend analysis
    print("\n7. Testing sentiment trend analysis:")
    
    all_items = sample_news + sample_social
    direction, strength = analyzer._analyze_sentiment_trend(all_items)
    print(f"Trend direction: {direction}, strength: {strength}")
    
    # Test confidence calculation
    print("\n8. Testing confidence calculation:")
    
    confidence = analyzer._calculate_confidence_score(sample_news, sample_social)
    print(f"Confidence score: {confidence}")
    assert 0 <= confidence <= 1, "Confidence should be between 0 and 1"
    
    # Test volatility calculation
    print("\n9. Testing volatility calculation:")
    
    volatility = analyzer._calculate_sentiment_volatility(all_items)
    print(f"Sentiment volatility: {volatility}")
    assert volatility >= 0, "Volatility should be non-negative"
    
    # Test conflict detection
    print("\n10. Testing conflict detection:")
    
    conflicts = await analyzer.detect_sentiment_conflicts(
        "AAPL", Decimal('0.7'), Decimal('-0.6')
    )
    print(f"Detected conflicts: {len(conflicts)}")
    if conflicts:
        print(f"Conflict type: {conflicts[0].conflict_type}")
        assert conflicts[0].conflict_type == "bullish_sentiment_bearish_fundamentals"
    
    print("\n✅ All sentiment analyzer tests passed!")


if __name__ == "__main__":
    asyncio.run(test_sentiment_analyzer())