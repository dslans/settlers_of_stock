"""
Test data factories using factory_boy for consistent test data generation.
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
from decimal import Decimal
import random

from app.models.user import User
from app.models.stock import Stock
from app.models.watchlist import Watchlist, WatchlistItem
from app.models.alert import Alert
from app.models.analysis import AnalysisResult
from app.schemas.auth import UserCreate


class UserFactory(factory.Factory):
    """Factory for creating test users."""
    
    class Meta:
        model = User
    
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker('name')
    hashed_password = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"  # "secret"
    is_active = True
    is_verified = True
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    preferences = {
        "risk_tolerance": "moderate",
        "investment_horizon": "medium",
        "preferred_analysis": ["fundamental", "technical"],
        "notification_settings": {
            "email_alerts": True,
            "push_notifications": True,
            "price_alerts": True,
            "news_alerts": False
        },
        "display_settings": {
            "theme": "light",
            "currency": "USD",
            "chart_type": "candlestick"
        }
    }


class UserCreateFactory(factory.Factory):
    """Factory for creating UserCreate schemas."""
    
    class Meta:
        model = UserCreate
    
    email = factory.Sequence(lambda n: f"newuser{n}@example.com")
    password = "TestPassword123!"
    confirm_password = "TestPassword123!"
    full_name = factory.Faker('name')
    preferences = {
        "risk_tolerance": fuzzy.FuzzyChoice(["conservative", "moderate", "aggressive"]),
        "investment_horizon": fuzzy.FuzzyChoice(["short", "medium", "long"])
    }


class StockFactory(factory.Factory):
    """Factory for creating test stocks."""
    
    class Meta:
        model = Stock
    
    symbol = factory.Sequence(lambda n: f"TEST{n}")
    name = factory.Faker('company')
    exchange = fuzzy.FuzzyChoice(["NYSE", "NASDAQ", "AMEX"])
    sector = fuzzy.FuzzyChoice([
        "Technology", "Healthcare", "Financial Services", 
        "Consumer Cyclical", "Industrials", "Energy"
    ])
    industry = factory.Faker('bs')
    market_cap = fuzzy.FuzzyInteger(1000000, 1000000000000)
    last_updated = factory.LazyFunction(datetime.utcnow)


class WatchlistFactory(factory.Factory):
    """Factory for creating test watchlists."""
    
    class Meta:
        model = Watchlist
    
    name = factory.Faker('word')
    description = factory.Faker('sentence')
    is_default = False
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)


class WatchlistItemFactory(factory.Factory):
    """Factory for creating test watchlist items."""
    
    class Meta:
        model = WatchlistItem
    
    symbol = factory.Sequence(lambda n: f"STOCK{n}")
    company_name = factory.Faker('company')
    notes = factory.Faker('sentence')
    target_price = fuzzy.FuzzyDecimal(50.0, 500.0, 2)
    entry_price = fuzzy.FuzzyDecimal(40.0, 450.0, 2)
    shares_owned = fuzzy.FuzzyDecimal(1.0, 1000.0, 2)
    added_at = factory.LazyFunction(datetime.utcnow)


class AlertFactory(factory.Factory):
    """Factory for creating test alerts."""
    
    class Meta:
        model = Alert
    
    symbol = factory.Sequence(lambda n: f"ALERT{n}")
    alert_type = fuzzy.FuzzyChoice(["price_above", "price_below", "volume_spike", "technical_breakout"])
    condition_value = fuzzy.FuzzyDecimal(50.0, 500.0, 2)
    is_active = True
    created_at = factory.LazyFunction(datetime.utcnow)
    triggered_at = None


class MarketDataFactory(factory.Factory):
    """Factory for creating test market data."""
    
    class Meta:
        model = dict
    
    symbol = factory.Sequence(lambda n: f"MKT{n}")
    price = fuzzy.FuzzyDecimal(50.0, 500.0, 2)
    change = fuzzy.FuzzyDecimal(-10.0, 10.0, 2)
    change_percent = fuzzy.FuzzyDecimal(-5.0, 5.0, 2)
    volume = fuzzy.FuzzyInteger(100000, 10000000)
    high_52_week = factory.LazyAttribute(lambda obj: obj.price * Decimal('1.2'))
    low_52_week = factory.LazyAttribute(lambda obj: obj.price * Decimal('0.8'))
    avg_volume = fuzzy.FuzzyInteger(1000000, 50000000)
    timestamp = factory.LazyFunction(datetime.utcnow)


class FundamentalDataFactory(factory.Factory):
    """Factory for creating test fundamental data."""
    
    class Meta:
        model = dict
    
    symbol = factory.Sequence(lambda n: f"FUND{n}")
    pe_ratio = fuzzy.FuzzyDecimal(10.0, 30.0, 2)
    pb_ratio = fuzzy.FuzzyDecimal(1.0, 5.0, 2)
    roe = fuzzy.FuzzyDecimal(0.1, 0.3, 3)
    debt_to_equity = fuzzy.FuzzyDecimal(0.1, 2.0, 2)
    revenue_growth = fuzzy.FuzzyDecimal(-0.1, 0.3, 3)
    profit_margin = fuzzy.FuzzyDecimal(0.05, 0.25, 3)
    eps = fuzzy.FuzzyDecimal(1.0, 10.0, 2)
    dividend = fuzzy.FuzzyDecimal(0.0, 5.0, 2)
    dividend_yield = fuzzy.FuzzyDecimal(0.0, 0.05, 4)
    quarter = "Q4"
    year = 2024


class TechnicalDataFactory(factory.Factory):
    """Factory for creating test technical data."""
    
    class Meta:
        model = dict
    
    symbol = factory.Sequence(lambda n: f"TECH{n}")
    timeframe = fuzzy.FuzzyChoice(["1D", "1W", "1M", "3M", "1Y"])
    sma_20 = fuzzy.FuzzyDecimal(50.0, 500.0, 2)
    sma_50 = fuzzy.FuzzyDecimal(50.0, 500.0, 2)
    ema_12 = fuzzy.FuzzyDecimal(50.0, 500.0, 2)
    ema_26 = fuzzy.FuzzyDecimal(50.0, 500.0, 2)
    rsi = fuzzy.FuzzyDecimal(20.0, 80.0, 2)
    macd = fuzzy.FuzzyDecimal(-5.0, 5.0, 3)
    macd_signal = fuzzy.FuzzyDecimal(-5.0, 5.0, 3)
    bollinger_upper = fuzzy.FuzzyDecimal(100.0, 600.0, 2)
    bollinger_lower = fuzzy.FuzzyDecimal(40.0, 400.0, 2)
    support_levels = factory.LazyFunction(lambda: [random.uniform(50, 200) for _ in range(3)])
    resistance_levels = factory.LazyFunction(lambda: [random.uniform(200, 400) for _ in range(3)])
    timestamp = factory.LazyFunction(datetime.utcnow)


class AnalysisResultFactory(factory.Factory):
    """Factory for creating test analysis results."""
    
    class Meta:
        model = dict
    
    symbol = factory.Sequence(lambda n: f"ANAL{n}")
    analysis_type = fuzzy.FuzzyChoice(["fundamental", "technical", "sentiment", "combined"])
    score = fuzzy.FuzzyInteger(0, 100)
    recommendation = fuzzy.FuzzyChoice(["BUY", "SELL", "HOLD"])
    confidence = fuzzy.FuzzyInteger(60, 95)
    reasoning = factory.LazyFunction(lambda: [
        "Strong financial metrics",
        "Positive technical indicators",
        "Favorable market sentiment"
    ])
    risks = factory.LazyFunction(lambda: [
        "Market volatility",
        "Sector rotation risk",
        "Economic uncertainty"
    ])
    targets = {
        "short_term": fuzzy.FuzzyDecimal(100.0, 200.0, 2),
        "medium_term": fuzzy.FuzzyDecimal(150.0, 250.0, 2),
        "long_term": fuzzy.FuzzyDecimal(200.0, 300.0, 2)
    }
    timestamp = factory.LazyFunction(datetime.utcnow)


class NewsItemFactory(factory.Factory):
    """Factory for creating test news items."""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: f"news-{n}")
    title = factory.Faker('sentence')
    summary = factory.Faker('paragraph')
    url = factory.Faker('url')
    source = factory.Faker('company')
    published_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(hours=random.randint(1, 24)))
    sentiment = fuzzy.FuzzyDecimal(-1.0, 1.0, 3)
    relevance_score = fuzzy.FuzzyDecimal(0.5, 1.0, 2)
    symbols = factory.LazyFunction(lambda: [f"SYM{i}" for i in range(1, random.randint(2, 4))])