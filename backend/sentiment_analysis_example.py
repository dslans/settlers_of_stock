#!/usr/bin/env python3
"""
Sentiment Analysis Example for Settlers of Stock

This example demonstrates how to use the sentiment analysis system to:
1. Analyze news and social media sentiment for stocks
2. Detect conflicts between sentiment and fundamental analysis
3. Generate sentiment alerts and trend analysis
4. Integrate sentiment data into investment decisions

Usage:
    python sentiment_analysis_example.py [SYMBOL]
    
Example:
    python sentiment_analysis_example.py AAPL
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.sentiment_analyzer import SentimentAnalyzer
from app.models.sentiment import (
    NewsItem, SocialMediaPost, SentimentAnalysisResult, 
    TrendDirection, SentimentSource
)


class SentimentAnalysisDemo:
    """Demonstration of sentiment analysis capabilities."""
    
    def __init__(self):
        self.analyzer = SentimentAnalyzer()
    
    async def run_comprehensive_demo(self, symbol: str = "AAPL"):
        """Run a comprehensive sentiment analysis demonstration."""
        print(f"🔍 Sentiment Analysis Demo for {symbol}")
        print("=" * 50)
        
        # Create mock data for demonstration
        mock_data = self._create_mock_data(symbol)
        
        # Patch the analyzer to use mock data
        from unittest.mock import patch
        
        async def mock_fetch_news(s, d):
            return mock_data['news']
        
        async def mock_fetch_social(s, d):
            return mock_data['social']
        
        with patch.object(self.analyzer, '_fetch_news_data', side_effect=mock_fetch_news), \
             patch.object(self.analyzer, '_fetch_social_data', side_effect=mock_fetch_social):
            
            # 1. Basic Sentiment Analysis
            await self._demo_basic_sentiment_analysis(symbol)
            
            # 2. Sentiment Trend Analysis
            await self._demo_trend_analysis(symbol)
            
            # 3. Conflict Detection
            await self._demo_conflict_detection(symbol)
            
            # 4. Data Source Analysis
            await self._demo_data_source_analysis(symbol)
            
            # 5. Investment Decision Integration
            await self._demo_investment_integration(symbol)
    
    async def _demo_basic_sentiment_analysis(self, symbol: str):
        """Demonstrate basic sentiment analysis functionality."""
        print("\n📊 1. Basic Sentiment Analysis")
        print("-" * 30)
        
        result = await self.analyzer.analyze_stock_sentiment(symbol)
        sentiment_data = result.sentiment_data
        
        print(f"Symbol: {symbol}")
        print(f"Overall Sentiment: {float(sentiment_data.overall_sentiment):.3f}")
        print(f"Sentiment Label: {self._get_sentiment_label(sentiment_data.overall_sentiment)}")
        print(f"News Sentiment: {float(sentiment_data.news_sentiment):.3f}")
        print(f"Social Sentiment: {float(sentiment_data.social_sentiment):.3f}")
        print(f"Confidence Score: {float(sentiment_data.confidence_score):.3f}")
        print(f"Data Sources: {', '.join(sentiment_data.sources)}")
        print(f"News Articles: {sentiment_data.news_articles_count}")
        print(f"Social Posts: {sentiment_data.social_posts_count}")
        
        # Show top news headlines
        print(f"\n📰 Top News Headlines:")
        for i, news in enumerate(result.recent_news[:3], 1):
            sentiment_label = self._get_sentiment_label(news.sentiment_score)
            print(f"  {i}. {news.title}")
            print(f"     Source: {news.source} | Sentiment: {sentiment_label} ({float(news.sentiment_score):.2f})")
        
        # Show top social posts
        print(f"\n💬 Top Social Media Posts:")
        for i, post in enumerate(result.recent_social_posts[:3], 1):
            sentiment_label = self._get_sentiment_label(post.sentiment_score)
            print(f"  {i}. {post.title}")
            print(f"     Platform: {post.platform} | Score: {post.score} | Sentiment: {sentiment_label} ({float(post.sentiment_score):.2f})")
    
    async def _demo_trend_analysis(self, symbol: str):
        """Demonstrate sentiment trend analysis."""
        print("\n📈 2. Sentiment Trend Analysis")
        print("-" * 30)
        
        result = await self.analyzer.analyze_stock_sentiment(symbol)
        sentiment_data = result.sentiment_data
        
        print(f"Trend Direction: {sentiment_data.trend_direction.value}")
        print(f"Trend Strength: {float(sentiment_data.trend_strength):.3f}")
        print(f"Volatility: {float(sentiment_data.volatility):.3f}")
        
        # Interpret trend
        trend_interpretation = self._interpret_trend(
            sentiment_data.trend_direction, 
            sentiment_data.trend_strength
        )
        print(f"Interpretation: {trend_interpretation}")
        
        # Show alerts if any
        if result.sentiment_alerts:
            print(f"\n🚨 Sentiment Alerts ({len(result.sentiment_alerts)}):")
            for alert in result.sentiment_alerts:
                print(f"  • {alert.alert_type}: {alert.description}")
                print(f"    Confidence: {float(alert.confidence):.2f}")
    
    async def _demo_conflict_detection(self, symbol: str):
        """Demonstrate sentiment vs fundamental conflict detection."""
        print("\n⚠️  3. Sentiment vs Fundamental Conflicts")
        print("-" * 40)
        
        result = await self.analyzer.analyze_stock_sentiment(symbol)
        sentiment_score = result.sentiment_data.overall_sentiment
        
        # Simulate different fundamental scenarios
        scenarios = [
            ("Strong Fundamentals", Decimal('0.8')),
            ("Weak Fundamentals", Decimal('-0.6')),
            ("Neutral Fundamentals", Decimal('0.1'))
        ]
        
        for scenario_name, fundamental_score in scenarios:
            conflicts = await self.analyzer.detect_sentiment_conflicts(
                symbol, sentiment_score, fundamental_score
            )
            
            print(f"\nScenario: {scenario_name}")
            print(f"Sentiment Score: {float(sentiment_score):.2f}")
            print(f"Fundamental Score: {float(fundamental_score):.2f}")
            
            if conflicts:
                conflict = conflicts[0]
                print(f"⚠️  CONFLICT DETECTED: {conflict.conflict_type}")
                print(f"Severity: {float(conflict.conflict_severity):.2f}")
                print(f"Explanation: {conflict.explanation}")
            else:
                print("✅ No conflicts detected - sentiment and fundamentals align")
    
    async def _demo_data_source_analysis(self, symbol: str):
        """Demonstrate analysis of different data sources."""
        print("\n📊 4. Data Source Analysis")
        print("-" * 30)
        
        result = await self.analyzer.analyze_stock_sentiment(symbol)
        
        # Analyze news vs social sentiment
        news_sentiment = result.sentiment_data.news_sentiment
        social_sentiment = result.sentiment_data.social_sentiment
        
        print(f"News Sentiment: {float(news_sentiment):.3f}")
        print(f"Social Sentiment: {float(social_sentiment):.3f}")
        print(f"Difference: {float(abs(news_sentiment - social_sentiment)):.3f}")
        
        # Source reliability analysis
        source_weights = result.sentiment_data.source_weights
        print(f"\nSource Weights:")
        for source, weight in source_weights.items():
            print(f"  {source.title()}: {float(weight):.2f}")
        
        # Data quality metrics
        print(f"\nData Quality Metrics:")
        print(f"  Confidence Score: {float(result.sentiment_data.confidence_score):.3f}")
        print(f"  Data Freshness: {result.sentiment_data.data_freshness.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Volatility: {float(result.sentiment_data.volatility):.3f}")
        
        # Recommend data source focus
        if abs(news_sentiment - social_sentiment) > 0.3:
            if news_sentiment > social_sentiment:
                print(f"\n💡 Recommendation: Focus on news sentiment (more positive)")
            else:
                print(f"\n💡 Recommendation: Focus on social sentiment (more positive)")
        else:
            print(f"\n💡 Recommendation: News and social sentiment are aligned")
    
    async def _demo_investment_integration(self, symbol: str):
        """Demonstrate how to integrate sentiment into investment decisions."""
        print("\n💰 5. Investment Decision Integration")
        print("-" * 40)
        
        result = await self.analyzer.analyze_stock_sentiment(symbol)
        sentiment_data = result.sentiment_data
        
        # Create investment recommendation based on sentiment
        recommendation = self._generate_investment_recommendation(sentiment_data)
        
        print(f"Investment Recommendation: {recommendation['action']}")
        print(f"Confidence: {recommendation['confidence']:.1f}%")
        print(f"Risk Level: {recommendation['risk_level']}")
        print(f"Reasoning: {recommendation['reasoning']}")
        
        # Position sizing based on sentiment confidence
        position_size = self._calculate_position_size(sentiment_data)
        print(f"\nSuggested Position Size: {position_size:.1f}% of portfolio")
        
        # Risk management
        risk_factors = self._identify_risk_factors(sentiment_data, result.sentiment_alerts)
        if risk_factors:
            print(f"\n⚠️  Risk Factors to Monitor:")
            for factor in risk_factors:
                print(f"  • {factor}")
        
        # Entry/exit signals
        signals = self._generate_trading_signals(sentiment_data)
        print(f"\nTrading Signals:")
        for signal_type, signal_strength in signals.items():
            print(f"  {signal_type}: {signal_strength}")
    
    def _create_mock_data(self, symbol: str) -> Dict:
        """Create realistic mock data for demonstration."""
        now = datetime.now()
        
        # Mock news data with varied sentiment
        news_items = [
            NewsItem(
                id="news_1",
                title=f"{symbol} reports strong quarterly earnings, beats expectations",
                summary=f"{symbol} delivered better than expected results with revenue growth of 15%",
                url="https://example.com/news1",
                source="Financial Times",
                published_at=now - timedelta(hours=2),
                sentiment_score=Decimal('0.85'),
                relevance_score=Decimal('0.95'),
                symbols=[symbol],
                keywords=["earnings", "beats", "strong", "growth"]
            ),
            NewsItem(
                id="news_2",
                title=f"Analysts upgrade {symbol} with higher price target",
                summary=f"Multiple analysts raise price targets for {symbol} citing strong fundamentals",
                url="https://example.com/news2",
                source="Bloomberg",
                published_at=now - timedelta(hours=4),
                sentiment_score=Decimal('0.7'),
                relevance_score=Decimal('0.9'),
                symbols=[symbol],
                keywords=["upgrade", "analysts", "price", "target"]
            ),
            NewsItem(
                id="news_3",
                title=f"{symbol} faces regulatory scrutiny in Europe",
                summary=f"European regulators announce investigation into {symbol}'s business practices",
                url="https://example.com/news3",
                source="Reuters",
                published_at=now - timedelta(hours=8),
                sentiment_score=Decimal('-0.4'),
                relevance_score=Decimal('0.8'),
                symbols=[symbol],
                keywords=["regulatory", "scrutiny", "investigation"]
            ),
            NewsItem(
                id="news_4",
                title=f"{symbol} announces new product launch",
                summary=f"{symbol} unveils innovative new product line expected to drive growth",
                url="https://example.com/news4",
                source="TechCrunch",
                published_at=now - timedelta(hours=12),
                sentiment_score=Decimal('0.6'),
                relevance_score=Decimal('0.85'),
                symbols=[symbol],
                keywords=["product", "launch", "innovative", "growth"]
            )
        ]
        
        # Mock social media data
        social_posts = [
            SocialMediaPost(
                id="reddit_1",
                platform="reddit",
                title=f"{symbol} earnings call was incredible!",
                content=f"Just finished listening to {symbol} earnings call. Management sounds very confident about future growth. Loading up on more shares!",
                author="growth_investor",
                subreddit="stocks",
                score=156,
                comments_count=43,
                created_at=now - timedelta(hours=3),
                sentiment_score=Decimal('0.9'),
                relevance_score=Decimal('0.9'),
                symbols=[symbol]
            ),
            SocialMediaPost(
                id="reddit_2",
                platform="reddit",
                title=f"Concerned about {symbol} valuation",
                content=f"{symbol} P/E ratio is getting quite high. Might be time to take some profits. What's everyone's thoughts?",
                author="value_seeker",
                subreddit="investing",
                score=89,
                comments_count=67,
                created_at=now - timedelta(hours=6),
                sentiment_score=Decimal('-0.3'),
                relevance_score=Decimal('0.75'),
                symbols=[symbol]
            ),
            SocialMediaPost(
                id="reddit_3",
                platform="reddit",
                title=f"{symbol} technical analysis",
                content=f"Looking at {symbol} charts, we're approaching a key resistance level. If we break through, could see significant upside.",
                author="chart_master",
                subreddit="SecurityAnalysis",
                score=234,
                comments_count=78,
                created_at=now - timedelta(hours=1),
                sentiment_score=Decimal('0.5'),
                relevance_score=Decimal('0.8'),
                symbols=[symbol]
            )
        ]
        
        return {
            'news': news_items,
            'social': social_posts
        }
    
    def _get_sentiment_label(self, sentiment_score) -> str:
        """Convert sentiment score to human-readable label."""
        if sentiment_score >= 0.7:
            return "Very Positive"
        elif sentiment_score >= 0.3:
            return "Positive"
        elif sentiment_score >= -0.3:
            return "Neutral"
        elif sentiment_score >= -0.7:
            return "Negative"
        else:
            return "Very Negative"
    
    def _interpret_trend(self, direction: TrendDirection, strength: Decimal) -> str:
        """Interpret sentiment trend for human understanding."""
        if direction == TrendDirection.IMPROVING:
            if strength > 0.7:
                return "Strong positive momentum building"
            elif strength > 0.4:
                return "Moderate positive trend developing"
            else:
                return "Slight improvement in sentiment"
        elif direction == TrendDirection.DECLINING:
            if strength > 0.7:
                return "Strong negative momentum building"
            elif strength > 0.4:
                return "Moderate negative trend developing"
            else:
                return "Slight decline in sentiment"
        elif direction == TrendDirection.VOLATILE:
            return "High volatility - sentiment changing rapidly"
        else:
            return "Sentiment remains stable"
    
    def _generate_investment_recommendation(self, sentiment_data) -> Dict:
        """Generate investment recommendation based on sentiment."""
        overall_sentiment = float(sentiment_data.overall_sentiment)
        confidence = float(sentiment_data.confidence_score)
        
        if overall_sentiment >= 0.6 and confidence >= 0.7:
            return {
                "action": "BUY",
                "confidence": confidence * 100,
                "risk_level": "Moderate",
                "reasoning": "Strong positive sentiment with high confidence"
            }
        elif overall_sentiment >= 0.3 and confidence >= 0.6:
            return {
                "action": "HOLD/ACCUMULATE",
                "confidence": confidence * 100,
                "risk_level": "Low-Moderate",
                "reasoning": "Positive sentiment trend with good confidence"
            }
        elif overall_sentiment <= -0.6 and confidence >= 0.7:
            return {
                "action": "SELL/AVOID",
                "confidence": confidence * 100,
                "risk_level": "High",
                "reasoning": "Strong negative sentiment with high confidence"
            }
        elif overall_sentiment <= -0.3 and confidence >= 0.6:
            return {
                "action": "REDUCE/HOLD",
                "confidence": confidence * 100,
                "risk_level": "Moderate-High",
                "reasoning": "Negative sentiment trend developing"
            }
        else:
            return {
                "action": "HOLD",
                "confidence": confidence * 100,
                "risk_level": "Moderate",
                "reasoning": "Mixed or uncertain sentiment signals"
            }
    
    def _calculate_position_size(self, sentiment_data) -> float:
        """Calculate suggested position size based on sentiment confidence."""
        confidence = float(sentiment_data.confidence_score)
        sentiment_strength = abs(float(sentiment_data.overall_sentiment))
        
        # Base position size on confidence and sentiment strength
        base_size = 5.0  # 5% base position
        confidence_multiplier = confidence * 2  # 0-2x multiplier
        sentiment_multiplier = sentiment_strength * 1.5  # 0-1.5x multiplier
        
        position_size = base_size * confidence_multiplier * sentiment_multiplier
        return min(position_size, 15.0)  # Cap at 15% of portfolio
    
    def _identify_risk_factors(self, sentiment_data, alerts) -> List[str]:
        """Identify risk factors based on sentiment analysis."""
        risk_factors = []
        
        if float(sentiment_data.volatility) > 0.5:
            risk_factors.append("High sentiment volatility - expect price swings")
        
        if float(sentiment_data.confidence_score) < 0.5:
            risk_factors.append("Low confidence in sentiment data - verify with other sources")
        
        if sentiment_data.news_articles_count < 3:
            risk_factors.append("Limited news coverage - may lack market attention")
        
        if abs(float(sentiment_data.news_sentiment - sentiment_data.social_sentiment)) > 0.4:
            risk_factors.append("Divergence between news and social sentiment")
        
        if alerts:
            risk_factors.append(f"Active sentiment alerts ({len(alerts)}) - monitor closely")
        
        return risk_factors
    
    def _generate_trading_signals(self, sentiment_data) -> Dict[str, str]:
        """Generate trading signals based on sentiment."""
        signals = {}
        
        # Entry signal
        if sentiment_data.trend_direction == TrendDirection.IMPROVING:
            if float(sentiment_data.trend_strength) > 0.6:
                signals["Entry Signal"] = "Strong Buy"
            else:
                signals["Entry Signal"] = "Buy"
        elif sentiment_data.trend_direction == TrendDirection.DECLINING:
            signals["Entry Signal"] = "Wait/Avoid"
        else:
            signals["Entry Signal"] = "Neutral"
        
        # Exit signal
        if float(sentiment_data.overall_sentiment) < -0.5:
            signals["Exit Signal"] = "Consider Selling"
        elif float(sentiment_data.volatility) > 0.7:
            signals["Exit Signal"] = "Take Profits"
        else:
            signals["Exit Signal"] = "Hold"
        
        return signals


async def main():
    """Main function to run the sentiment analysis demo."""
    # Get symbol from command line or use default
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    symbol = symbol.upper()
    
    print("🚀 Settlers of Stock - Sentiment Analysis Demo")
    print("=" * 50)
    print(f"Analyzing sentiment for: {symbol}")
    print("Note: This demo uses mock data for demonstration purposes")
    
    demo = SentimentAnalysisDemo()
    await demo.run_comprehensive_demo(symbol)
    
    print("\n" + "=" * 50)
    print("📚 Key Takeaways:")
    print("• Sentiment analysis combines news and social media data")
    print("• Trend analysis helps identify momentum shifts")
    print("• Conflict detection reveals sentiment vs fundamental divergence")
    print("• Multiple data sources provide comprehensive market view")
    print("• Integration with investment decisions requires confidence scoring")
    print("\n🎯 Next Steps:")
    print("• Set up NewsAPI and Reddit API keys for live data")
    print("• Integrate with your existing fundamental analysis")
    print("• Customize sentiment thresholds for your strategy")
    print("• Monitor sentiment alerts for trading opportunities")


if __name__ == "__main__":
    asyncio.run(main())