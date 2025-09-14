# Sentiment Analysis System

The Settlers of Stock sentiment analysis system provides comprehensive market sentiment analysis by integrating news articles and social media data to help inform investment decisions.

## Features

### 📊 Core Functionality
- **Multi-source Analysis**: Combines news articles (NewsAPI) and social media posts (Reddit)
- **Real-time Sentiment Scoring**: Uses VADER and TextBlob for accurate sentiment analysis
- **Trend Detection**: Identifies sentiment momentum and direction changes
- **Conflict Detection**: Alerts when sentiment diverges from fundamental analysis
- **Confidence Scoring**: Provides reliability metrics for sentiment data

### 🔍 Analysis Components
1. **Text Sentiment Analysis**: Advanced NLP processing with financial keyword weighting
2. **Relevance Scoring**: Filters content based on stock symbol relevance
3. **Time-weighted Aggregation**: Recent data weighted more heavily
4. **Volatility Measurement**: Tracks sentiment stability over time
5. **Alert Generation**: Automatic notifications for significant sentiment changes

## Quick Start

### 1. Installation

```bash
# Install required packages
uv pip install newsapi-python praw vaderSentiment textblob

# Download NLTK data (required for TextBlob)
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"
```

### 2. Configuration

Add API credentials to your `.env` file:

```env
# NewsAPI (get free key at https://newsapi.org/)
NEWS_API_KEY=your_news_api_key_here

# Reddit API (create app at https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

### 3. Basic Usage

```python
from app.services.sentiment_analyzer import SentimentAnalyzer

# Initialize analyzer
analyzer = SentimentAnalyzer()

# Analyze sentiment for a stock
result = await analyzer.analyze_stock_sentiment("AAPL")

print(f"Overall Sentiment: {result.sentiment_data.overall_sentiment}")
print(f"Confidence: {result.sentiment_data.confidence_score}")
print(f"Trend: {result.sentiment_data.trend_direction}")
```

### 4. Run Demo

```bash
# Run comprehensive demo
python sentiment_analysis_example.py AAPL

# Test with different symbols
python sentiment_analysis_example.py TSLA
python sentiment_analysis_example.py MSFT
```

## API Endpoints

### Sentiment Analysis
```http
GET /api/v1/analysis/sentiment/{symbol}
```

Parameters:
- `days_back` (optional): Number of days to analyze (1-30, default: 7)
- `include_social` (optional): Include social media analysis (default: true)

### Sentiment Summary
```http
GET /api/v1/analysis/sentiment/{symbol}/summary
```

Returns quick sentiment overview with key metrics.

### Conflict Detection
```http
GET /api/v1/analysis/sentiment/{symbol}/conflicts
```

Detects conflicts between sentiment and fundamental analysis.

## Data Models

### SentimentData
Core sentiment metrics for a stock:
- `overall_sentiment`: Combined sentiment score (-1 to 1)
- `news_sentiment`: News-based sentiment
- `social_sentiment`: Social media sentiment
- `trend_direction`: IMPROVING, DECLINING, STABLE, or VOLATILE
- `confidence_score`: Reliability of the analysis (0 to 1)

### NewsItem
Individual news article with sentiment:
- `title`, `summary`, `url`, `source`
- `sentiment_score`: Article sentiment (-1 to 1)
- `relevance_score`: Relevance to stock (0 to 1)
- `keywords`: Extracted financial terms

### SocialMediaPost
Social media post with sentiment:
- `title`, `content`, `platform`, `author`
- `sentiment_score`: Post sentiment (-1 to 1)
- `score`: Engagement metrics (upvotes, likes)

## Advanced Features

### 1. Sentiment Trend Analysis

```python
# Analyze sentiment trends over time
result = await analyzer.analyze_stock_sentiment("AAPL", days_back=14)

trend_direction = result.sentiment_data.trend_direction
trend_strength = result.sentiment_data.trend_strength

if trend_direction == TrendDirection.IMPROVING:
    print(f"Positive momentum building (strength: {trend_strength})")
```

### 2. Conflict Detection

```python
# Detect sentiment vs fundamental conflicts
conflicts = await analyzer.detect_sentiment_conflicts(
    symbol="AAPL",
    sentiment_score=Decimal('0.8'),  # Positive sentiment
    fundamental_score=Decimal('-0.6')  # Negative fundamentals
)

for conflict in conflicts:
    print(f"Conflict: {conflict.conflict_type}")
    print(f"Severity: {conflict.conflict_severity}")
```

### 3. Custom Analysis

```python
# Analyze specific text
sentiment = analyzer._analyze_text_sentiment(
    "Company reports strong earnings growth and beats expectations"
)

# Calculate relevance
relevance = analyzer._calculate_relevance_score(
    "AAPL stock price surges on iPhone sales", "AAPL"
)

# Extract financial keywords
keywords = analyzer._extract_financial_keywords(
    "Strong profit growth and revenue beat expectations"
)
```

## Investment Integration

### Position Sizing
Use sentiment confidence to determine position sizes:

```python
def calculate_position_size(sentiment_data):
    confidence = float(sentiment_data.confidence_score)
    sentiment_strength = abs(float(sentiment_data.overall_sentiment))
    
    base_size = 5.0  # 5% base position
    multiplier = confidence * sentiment_strength
    
    return min(base_size * multiplier * 2, 15.0)  # Cap at 15%
```

### Risk Management
Monitor sentiment volatility and conflicts:

```python
def assess_sentiment_risk(sentiment_data, alerts):
    risk_level = "LOW"
    
    if float(sentiment_data.volatility) > 0.5:
        risk_level = "HIGH"  # High volatility
    elif len(alerts) > 0:
        risk_level = "MEDIUM"  # Active alerts
    elif float(sentiment_data.confidence_score) < 0.5:
        risk_level = "MEDIUM"  # Low confidence
    
    return risk_level
```

### Trading Signals
Generate entry/exit signals:

```python
def generate_signals(sentiment_data):
    sentiment = float(sentiment_data.overall_sentiment)
    trend = sentiment_data.trend_direction
    
    if sentiment > 0.6 and trend == TrendDirection.IMPROVING:
        return "STRONG_BUY"
    elif sentiment < -0.6 and trend == TrendDirection.DECLINING:
        return "STRONG_SELL"
    else:
        return "HOLD"
```

## Testing

### Unit Tests
```bash
# Run sentiment analyzer tests
python -m pytest tests/test_sentiment_analyzer.py -v

# Run simple functionality tests
python test_sentiment_simple.py
```

### Integration Tests
```bash
# Run integration tests with mock data
python test_sentiment_integration.py
```

## Configuration Options

### Sentiment Thresholds
Customize sentiment interpretation:

```python
# In SentimentAnalyzer.__init__()
self.sentiment_thresholds = {
    'very_positive': 0.7,
    'positive': 0.3,
    'neutral': 0.0,
    'negative': -0.3,
    'very_negative': -0.7
}
```

### Data Source Weights
Adjust importance of different sources:

```python
# News vs social media weighting
news_weight = 0.7  # 70% news
social_weight = 0.3  # 30% social media
```

### Financial Keywords
Extend keyword lists for better relevance:

```python
self.financial_keywords = {
    'positive': ['profit', 'growth', 'earnings', 'revenue', 'bullish'],
    'negative': ['loss', 'decline', 'bearish', 'sell', 'downgrade'],
    'neutral': ['hold', 'maintain', 'stable', 'unchanged']
}
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure NEWS_API_KEY and Reddit credentials are set
   - Check API key validity and rate limits

2. **Low Confidence Scores**
   - Increase `days_back` parameter for more data
   - Check if stock symbol has sufficient news coverage

3. **Empty Results**
   - Verify stock symbol is correct and actively traded
   - Check if APIs are accessible from your network

### Performance Optimization

1. **Caching**: Implement Redis caching for frequent requests
2. **Batch Processing**: Analyze multiple stocks concurrently
3. **Rate Limiting**: Respect API rate limits to avoid blocks

## Roadmap

### Planned Features
- [ ] Twitter/X integration
- [ ] Analyst report sentiment analysis
- [ ] Multi-language support
- [ ] Real-time sentiment streaming
- [ ] Machine learning sentiment models
- [ ] Sector-wide sentiment analysis

### Integration Opportunities
- [ ] Portfolio-level sentiment scoring
- [ ] Alert system integration
- [ ] Backtesting framework
- [ ] Risk management system
- [ ] Trading bot integration

## Support

For questions or issues:
1. Check the test files for usage examples
2. Review the API documentation
3. Run the demo script for comprehensive examples
4. Examine the source code for implementation details

## License

This sentiment analysis system is part of the Settlers of Stock project and follows the same licensing terms.