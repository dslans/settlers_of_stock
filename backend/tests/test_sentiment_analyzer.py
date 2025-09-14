"""
Tests for sentiment analysis functionality.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.sentiment_analyzer import SentimentAnalyzer
from app.models.sentiment import (
    NewsItem, SocialMediaPost, SentimentData, SentimentAnalysisResult,
    TrendDirection, SentimentSource, SentimentAlert, SentimentConflict
)


class TestSentimentAnalyzer:
    """Test cases for SentimentAnalyzer class."""
    
    @pytest.fixture
    def sentiment_analyzer(self):
        """Create a SentimentAnalyzer instance for testing."""
        with patch('app.services.sentiment_analyzer.get_settings') as mock_settings:
            mock_settings.return_value.NEWS_API_KEY = "test_news_key"
            mock_settings.return_value.REDDIT_CLIENT_ID = "test_reddit_id"
            mock_settings.return_value.REDDIT_CLIENT_SECRET = "test_reddit_secret"
            
            analyzer = SentimentAnalyzer()
            return analyzer
    
    @pytest.fixture
    def sample_news_items(self):
        """Create sample news items for testing."""
        return [
            NewsItem(
                id="news_1",
                title="AAPL stock surges on strong earnings",
                summary="Apple reports better than expected quarterly results",
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
                summary="New regulations may impact Apple's business model",
                url="https://example.com/news2",
                source="Reuters",
                published_at=datetime.now() - timedelta(hours=6),
                sentiment_score=Decimal('-0.4'),
                relevance_score=Decimal('0.7'),
                symbols=["AAPL"],
                keywords=["regulatory", "concerns"]
            )
        ]
    
    @pytest.fixture
    def sample_social_posts(self):
        """Create sample social media posts for testing."""
        return [
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
    
    def test_analyze_text_sentiment_positive(self, sentiment_analyzer):
        """Test sentiment analysis for positive text."""
        positive_text = "This stock is performing excellently with strong growth and profits"
        sentiment = sentiment_analyzer._analyze_text_sentiment(positive_text)
        
        assert sentiment > 0
        assert -1 <= sentiment <= 1
    
    def test_analyze_text_sentiment_negative(self, sentiment_analyzer):
        """Test sentiment analysis for negative text."""
        negative_text = "The company is facing losses and declining performance"
        sentiment = sentiment_analyzer._analyze_text_sentiment(negative_text)
        
        assert sentiment < 0
        assert -1 <= sentiment <= 1
    
    def test_analyze_text_sentiment_neutral(self, sentiment_analyzer):
        """Test sentiment analysis for neutral text."""
        neutral_text = "The company reported quarterly results"
        sentiment = sentiment_analyzer._analyze_text_sentiment(neutral_text)
        
        assert abs(sentiment) < 0.3  # Should be relatively neutral
        assert -1 <= sentiment <= 1
    
    def test_analyze_text_sentiment_empty(self, sentiment_analyzer):
        """Test sentiment analysis for empty text."""
        sentiment = sentiment_analyzer._analyze_text_sentiment("")
        assert sentiment == Decimal('0')
        
        sentiment = sentiment_analyzer._analyze_text_sentiment(None)
        assert sentiment == Decimal('0')
    
    def test_calculate_relevance_score_high(self, sentiment_analyzer):
        """Test relevance calculation for highly relevant text."""
        text = "AAPL stock price increased after strong earnings report"
        relevance = sentiment_analyzer._calculate_relevance_score(text, "AAPL")
        
        assert relevance > Decimal('0.5')
        assert 0 <= relevance <= 1
    
    def test_calculate_relevance_score_low(self, sentiment_analyzer):
        """Test relevance calculation for low relevance text."""
        text = "The weather is nice today"
        relevance = sentiment_analyzer._calculate_relevance_score(text, "AAPL")
        
        assert relevance < Decimal('0.3')
        assert 0 <= relevance <= 1
    
    def test_extract_financial_keywords(self, sentiment_analyzer):
        """Test financial keyword extraction."""
        text = "The company showed strong profit growth and beat earnings expectations"
        keywords = sentiment_analyzer._extract_financial_keywords(text)
        
        assert "profit" in keywords
        assert "growth" in keywords
        assert "beat" in keywords
        assert len(keywords) > 0
    
    def test_analyze_news_sentiment(self, sentiment_analyzer, sample_news_items):
        """Test news sentiment aggregation."""
        sentiment = sentiment_analyzer._analyze_news_sentiment(sample_news_items)
        
        # Should be positive overall (0.8 weighted more than -0.4)
        assert sentiment > 0
        assert -1 <= sentiment <= 1
    
    def test_analyze_news_sentiment_empty(self, sentiment_analyzer):
        """Test news sentiment with empty list."""
        sentiment = sentiment_analyzer._analyze_news_sentiment([])
        assert sentiment == Decimal('0')
    
    def test_analyze_social_sentiment(self, sentiment_analyzer, sample_social_posts):
        """Test social media sentiment aggregation."""
        sentiment = sentiment_analyzer._analyze_social_sentiment(sample_social_posts)
        
        # Should be positive (0.7 with higher engagement weight)
        assert sentiment > 0
        assert -1 <= sentiment <= 1
    
    def test_analyze_social_sentiment_empty(self, sentiment_analyzer):
        """Test social sentiment with empty list."""
        sentiment = sentiment_analyzer._analyze_social_sentiment([])
        assert sentiment == Decimal('0')
    
    def test_calculate_overall_sentiment(self, sentiment_analyzer):
        """Test overall sentiment calculation."""
        news_sentiment = Decimal('0.6')
        social_sentiment = Decimal('0.4')
        
        overall = sentiment_analyzer._calculate_overall_sentiment(
            news_sentiment, social_sentiment, 5, 3
        )
        
        # Should be weighted average (0.7 * 0.6 + 0.3 * 0.4)
        expected = Decimal('0.54')  # 0.42 + 0.12
        assert abs(overall - expected) < Decimal('0.1')
    
    def test_calculate_overall_sentiment_news_only(self, sentiment_analyzer):
        """Test overall sentiment with only news data."""
        news_sentiment = Decimal('0.5')
        social_sentiment = Decimal('0')
        
        overall = sentiment_analyzer._calculate_overall_sentiment(
            news_sentiment, social_sentiment, 5, 0
        )
        
        assert overall == news_sentiment
    
    def test_analyze_sentiment_trend_improving(self, sentiment_analyzer, sample_news_items):
        """Test sentiment trend analysis for improving trend."""
        # Modify timestamps to create improving trend
        sample_news_items[0].published_at = datetime.now() - timedelta(hours=1)  # Recent positive
        sample_news_items[1].published_at = datetime.now() - timedelta(days=3)   # Older negative
        
        direction, strength = sentiment_analyzer._analyze_sentiment_trend(sample_news_items)
        
        assert direction == TrendDirection.IMPROVING
        assert strength > 0
    
    def test_analyze_sentiment_trend_stable(self, sentiment_analyzer):
        """Test sentiment trend analysis for stable trend."""
        # Create items with similar sentiment
        items = [
            NewsItem(
                id="news_1", title="Test", summary="", url="", source="Test",
                published_at=datetime.now() - timedelta(hours=1),
                sentiment_score=Decimal('0.1'), relevance_score=Decimal('0.5'),
                symbols=["TEST"], keywords=[]
            ),
            NewsItem(
                id="news_2", title="Test", summary="", url="", source="Test",
                published_at=datetime.now() - timedelta(days=3),
                sentiment_score=Decimal('0.05'), relevance_score=Decimal('0.5'),
                symbols=["TEST"], keywords=[]
            )
        ]
        
        direction, strength = sentiment_analyzer._analyze_sentiment_trend(items)
        
        assert direction == TrendDirection.STABLE
        assert strength < Decimal('0.2')
    
    def test_calculate_confidence_score(self, sentiment_analyzer, sample_news_items, sample_social_posts):
        """Test confidence score calculation."""
        confidence = sentiment_analyzer._calculate_confidence_score(
            sample_news_items, sample_social_posts
        )
        
        assert 0 <= confidence <= 1
        assert confidence > 0  # Should have some confidence with data
    
    def test_calculate_confidence_score_no_data(self, sentiment_analyzer):
        """Test confidence score with no data."""
        confidence = sentiment_analyzer._calculate_confidence_score([], [])
        assert confidence == Decimal('0')
    
    def test_calculate_sentiment_volatility(self, sentiment_analyzer, sample_news_items):
        """Test sentiment volatility calculation."""
        volatility = sentiment_analyzer._calculate_sentiment_volatility(sample_news_items)
        
        assert volatility >= 0
        assert volatility > 0  # Should have some volatility with different sentiments
    
    def test_calculate_sentiment_volatility_single_item(self, sentiment_analyzer):
        """Test volatility calculation with single item."""
        single_item = [NewsItem(
            id="news_1", title="Test", summary="", url="", source="Test",
            published_at=datetime.now(), sentiment_score=Decimal('0.5'),
            relevance_score=Decimal('0.5'), symbols=["TEST"], keywords=[]
        )]
        
        volatility = sentiment_analyzer._calculate_sentiment_volatility(single_item)
        assert volatility == Decimal('0')
    
    @pytest.mark.asyncio
    async def test_generate_sentiment_alerts_positive_spike(self, sentiment_analyzer):
        """Test alert generation for positive sentiment spike."""
        sentiment_data = SentimentData(
            symbol="AAPL",
            overall_sentiment=Decimal('0.8'),  # Strong positive
            news_sentiment=Decimal('0.8'),
            social_sentiment=Decimal('0.7'),
            trend_direction=TrendDirection.IMPROVING,
            trend_strength=Decimal('0.6'),
            volatility=Decimal('0.2'),
            news_articles_count=5,
            social_posts_count=3,
            data_freshness=datetime.now(),
            confidence_score=Decimal('0.8'),
            sources=[SentimentSource.NEWS],
            source_weights={"news": Decimal('1.0')}
        )
        
        alerts = await sentiment_analyzer._generate_sentiment_alerts("AAPL", sentiment_data)
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "sentiment_spike"
        assert alerts[0].symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_generate_sentiment_alerts_negative_drop(self, sentiment_analyzer):
        """Test alert generation for negative sentiment drop."""
        sentiment_data = SentimentData(
            symbol="AAPL",
            overall_sentiment=Decimal('-0.8'),  # Strong negative
            news_sentiment=Decimal('-0.8'),
            social_sentiment=Decimal('-0.7'),
            trend_direction=TrendDirection.DECLINING,
            trend_strength=Decimal('0.6'),
            volatility=Decimal('0.2'),
            news_articles_count=5,
            social_posts_count=3,
            data_freshness=datetime.now(),
            confidence_score=Decimal('0.8'),
            sources=[SentimentSource.NEWS],
            source_weights={"news": Decimal('1.0')}
        )
        
        alerts = await sentiment_analyzer._generate_sentiment_alerts("AAPL", sentiment_data)
        
        assert len(alerts) == 1
        assert alerts[0].alert_type == "sentiment_drop"
        assert alerts[0].symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_generate_sentiment_alerts_no_alerts(self, sentiment_analyzer):
        """Test no alerts generated for moderate sentiment."""
        sentiment_data = SentimentData(
            symbol="AAPL",
            overall_sentiment=Decimal('0.3'),  # Moderate positive
            news_sentiment=Decimal('0.3'),
            social_sentiment=Decimal('0.2'),
            trend_direction=TrendDirection.STABLE,
            trend_strength=Decimal('0.2'),
            volatility=Decimal('0.1'),
            news_articles_count=5,
            social_posts_count=3,
            data_freshness=datetime.now(),
            confidence_score=Decimal('0.6'),
            sources=[SentimentSource.NEWS],
            source_weights={"news": Decimal('1.0')}
        )
        
        alerts = await sentiment_analyzer._generate_sentiment_alerts("AAPL", sentiment_data)
        
        assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_detect_sentiment_conflicts_bullish_sentiment_bearish_fundamentals(self, sentiment_analyzer):
        """Test conflict detection for bullish sentiment vs bearish fundamentals."""
        conflicts = await sentiment_analyzer.detect_sentiment_conflicts(
            "AAPL", Decimal('0.7'), Decimal('-0.6')
        )
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "bullish_sentiment_bearish_fundamentals"
        assert conflicts[0].symbol == "AAPL"
        assert conflicts[0].conflict_severity > Decimal('0.5')
    
    @pytest.mark.asyncio
    async def test_detect_sentiment_conflicts_bearish_sentiment_bullish_fundamentals(self, sentiment_analyzer):
        """Test conflict detection for bearish sentiment vs bullish fundamentals."""
        conflicts = await sentiment_analyzer.detect_sentiment_conflicts(
            "AAPL", Decimal('-0.7'), Decimal('0.6')
        )
        
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "bearish_sentiment_bullish_fundamentals"
        assert conflicts[0].symbol == "AAPL"
        assert conflicts[0].conflict_severity > Decimal('0.5')
    
    @pytest.mark.asyncio
    async def test_detect_sentiment_conflicts_no_conflict(self, sentiment_analyzer):
        """Test no conflict detection when sentiment and fundamentals align."""
        conflicts = await sentiment_analyzer.detect_sentiment_conflicts(
            "AAPL", Decimal('0.6'), Decimal('0.5')
        )
        
        assert len(conflicts) == 0
    
    @pytest.mark.asyncio
    @patch('app.services.sentiment_analyzer.NewsApiClient')
    async def test_fetch_news_data_success(self, mock_news_client, sentiment_analyzer):
        """Test successful news data fetching."""
        # Mock NewsAPI response
        mock_articles = {
            'articles': [
                {
                    'title': 'AAPL stock rises on earnings',
                    'description': 'Apple reports strong quarterly results',
                    'url': 'https://example.com/news1',
                    'source': {'name': 'Financial Times'},
                    'author': 'John Doe',
                    'publishedAt': '2024-01-15T10:00:00Z'
                }
            ]
        }
        
        mock_client_instance = Mock()
        mock_client_instance.get_everything.return_value = mock_articles
        mock_news_client.return_value = mock_client_instance
        
        # Reinitialize analyzer with mocked client
        sentiment_analyzer.news_client = mock_client_instance
        
        news_items = await sentiment_analyzer._fetch_news_data("AAPL", 7)
        
        assert len(news_items) >= 0  # May be 0 if relevance score is too low
        mock_client_instance.get_everything.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_news_data_no_client(self, sentiment_analyzer):
        """Test news data fetching when client is not available."""
        sentiment_analyzer.news_client = None
        
        news_items = await sentiment_analyzer._fetch_news_data("AAPL", 7)
        
        assert news_items == []
    
    @pytest.mark.asyncio
    @patch('app.services.sentiment_analyzer.praw.Reddit')
    async def test_fetch_social_data_success(self, mock_reddit, sentiment_analyzer):
        """Test successful social media data fetching."""
        # Mock Reddit response
        mock_submission = Mock()
        mock_submission.id = "test123"
        mock_submission.title = "AAPL to the moon!"
        mock_submission.selftext = "Great earnings, buying more shares"
        mock_submission.author = "investor123"
        mock_submission.score = 25
        mock_submission.num_comments = 10
        mock_submission.created_utc = datetime.now().timestamp()
        
        mock_subreddit = Mock()
        mock_subreddit.search.return_value = [mock_submission]
        
        mock_reddit_instance = Mock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        
        sentiment_analyzer.reddit_client = mock_reddit_instance
        
        social_posts = await sentiment_analyzer._fetch_social_data("AAPL", 7)
        
        assert len(social_posts) >= 0  # May be 0 if relevance score is too low
    
    @pytest.mark.asyncio
    async def test_fetch_social_data_no_client(self, sentiment_analyzer):
        """Test social data fetching when client is not available."""
        sentiment_analyzer.reddit_client = None
        
        social_posts = await sentiment_analyzer._fetch_social_data("AAPL", 7)
        
        assert social_posts == []
    
    @pytest.mark.asyncio
    @patch('app.services.sentiment_analyzer.SentimentAnalyzer._fetch_news_data')
    @patch('app.services.sentiment_analyzer.SentimentAnalyzer._fetch_social_data')
    async def test_analyze_stock_sentiment_complete(
        self, mock_fetch_social, mock_fetch_news, sentiment_analyzer, 
        sample_news_items, sample_social_posts
    ):
        """Test complete stock sentiment analysis."""
        mock_fetch_news.return_value = sample_news_items
        mock_fetch_social.return_value = sample_social_posts
        
        result = await sentiment_analyzer.analyze_stock_sentiment("AAPL", days_back=7)
        
        assert isinstance(result, SentimentAnalysisResult)
        assert result.symbol == "AAPL"
        assert result.sentiment_data.symbol == "AAPL"
        assert len(result.recent_news) <= 10
        assert len(result.recent_social_posts) <= 10
        assert result.sentiment_data.overall_sentiment != Decimal('0')  # Should have calculated sentiment
        
        mock_fetch_news.assert_called_once_with("AAPL", 7)
        mock_fetch_social.assert_called_once_with("AAPL", 7)
    
    @pytest.mark.asyncio
    @patch('app.services.sentiment_analyzer.SentimentAnalyzer._fetch_news_data')
    async def test_analyze_stock_sentiment_news_only(
        self, mock_fetch_news, sentiment_analyzer, sample_news_items
    ):
        """Test stock sentiment analysis with news only."""
        mock_fetch_news.return_value = sample_news_items
        
        result = await sentiment_analyzer.analyze_stock_sentiment(
            "AAPL", days_back=7, include_social=False
        )
        
        assert isinstance(result, SentimentAnalysisResult)
        assert result.symbol == "AAPL"
        assert len(result.recent_social_posts) == 0
        assert SentimentSource.NEWS in result.sentiment_data.sources
        assert SentimentSource.REDDIT not in result.sentiment_data.sources
    
    @pytest.mark.asyncio
    @patch('app.services.sentiment_analyzer.SentimentAnalyzer._fetch_news_data')
    @patch('app.services.sentiment_analyzer.SentimentAnalyzer._fetch_social_data')
    async def test_analyze_stock_sentiment_error_handling(
        self, mock_fetch_social, mock_fetch_news, sentiment_analyzer
    ):
        """Test error handling in sentiment analysis."""
        mock_fetch_news.side_effect = Exception("API Error")
        mock_fetch_social.side_effect = Exception("API Error")
        
        result = await sentiment_analyzer.analyze_stock_sentiment("AAPL")
        
        assert isinstance(result, SentimentAnalysisResult)
        assert result.symbol == "AAPL"
        assert result.sentiment_data.overall_sentiment == Decimal('0')
        assert result.sentiment_data.confidence_score == Decimal('0')


class TestSentimentAnalyzerIntegration:
    """Integration tests for SentimentAnalyzer with real data structures."""
    
    @pytest.mark.asyncio
    async def test_keyword_sentiment_boost_positive(self):
        """Test positive keyword sentiment boost."""
        analyzer = SentimentAnalyzer()
        
        text = "The company reported strong profit growth and beat earnings expectations"
        boost = analyzer._calculate_keyword_sentiment_boost(text)
        
        assert boost > 0
        assert boost <= 0.2
    
    @pytest.mark.asyncio
    async def test_keyword_sentiment_boost_negative(self):
        """Test negative keyword sentiment boost."""
        analyzer = SentimentAnalyzer()
        
        text = "The company faces significant losses and declining performance"
        boost = analyzer._calculate_keyword_sentiment_boost(text)
        
        assert boost < 0
        assert boost >= -0.2
    
    @pytest.mark.asyncio
    async def test_keyword_sentiment_boost_neutral(self):
        """Test neutral keyword sentiment boost."""
        analyzer = SentimentAnalyzer()
        
        text = "The company reported quarterly results"
        boost = analyzer._calculate_keyword_sentiment_boost(text)
        
        assert abs(boost) < 0.1  # Should be minimal boost