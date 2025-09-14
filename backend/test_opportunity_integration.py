#!/usr/bin/env python3
"""
Simple integration test for the opportunity search functionality.
This test bypasses the main app configuration issues.
"""

import asyncio
import sys
import os
from decimal import Decimal
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.models.opportunity import (
    OpportunitySearchFilters, InvestmentOpportunity, OpportunityScore,
    OpportunityType, RiskLevel, MarketCapCategory
)
from app.services.opportunity_search import OpportunitySearchService


async def test_opportunity_search_basic():
    """Test basic opportunity search functionality."""
    print("Testing opportunity search basic functionality...")
    
    try:
        # Create service instance
        service = OpportunitySearchService()
        print("✓ OpportunitySearchService created successfully")
        
        # Test market cap thresholds
        thresholds = service.market_cap_thresholds
        assert MarketCapCategory.LARGE_CAP in thresholds
        assert thresholds[MarketCapCategory.LARGE_CAP] == (10_000_000_000, 200_000_000_000)
        print("✓ Market cap thresholds configured correctly")
        
        # Test stock universe retrieval
        symbols = await service._get_popular_symbols()
        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "AAPL" in symbols
        print(f"✓ Popular symbols retrieved: {len(symbols)} symbols")
        
        # Test filter creation
        filters = OpportunitySearchFilters(
            market_cap_categories=[MarketCapCategory.LARGE_CAP],
            sectors=["Technology"],
            pe_ratio_max=Decimal("30"),
            limit=5
        )
        print("✓ Filters created successfully")
        
        # Test opportunity score calculation
        from app.models.stock import MarketData
        from app.models.fundamental import FundamentalData
        
        market_data = MarketData(
            symbol="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=75000000,
            high_52_week=Decimal("180.00"),
            low_52_week=Decimal("120.00"),
            avg_volume=80000000,
            market_cap=2500000000000,
            pe_ratio=Decimal("25.5"),
            timestamp=datetime.now()
        )
        
        fundamental_data = FundamentalData(
            symbol="AAPL",
            pe_ratio=Decimal("25.5"),
            pb_ratio=Decimal("6.8"),
            roe=Decimal("0.31"),
            debt_to_equity=Decimal("0.45"),
            revenue_growth=Decimal("0.08"),
            profit_margin=Decimal("0.25"),
            eps=Decimal("6.15"),
            dividend=Decimal("0.92"),
            dividend_yield=Decimal("0.006"),
            quarter="Q4",
            year=2024,
            last_updated=datetime.now()
        )
        
        scores = service._calculate_opportunity_scores(market_data, fundamental_data, None)
        assert isinstance(scores, OpportunityScore)
        assert 0 <= scores.overall_score <= 100
        print(f"✓ Opportunity scores calculated: {scores.overall_score}/100")
        
        # Test opportunity type identification
        opportunity_types = service._identify_opportunity_types(
            market_data, fundamental_data, None, scores
        )
        assert isinstance(opportunity_types, list)
        assert len(opportunity_types) > 0
        assert all(isinstance(ot, OpportunityType) for ot in opportunity_types)
        print(f"✓ Opportunity types identified: {[ot.value for ot in opportunity_types]}")
        
        # Test risk assessment
        risk_level = service._assess_risk_level(market_data, fundamental_data, None)
        assert isinstance(risk_level, RiskLevel)
        print(f"✓ Risk level assessed: {risk_level.value}")
        
        # Test reason generation
        reasons = service._generate_reasons(market_data, fundamental_data, None, opportunity_types)
        assert isinstance(reasons, list)
        assert len(reasons) > 0
        print(f"✓ Reasons generated: {len(reasons)} reasons")
        
        # Test price target calculation
        targets = service._calculate_price_targets(market_data.price, fundamental_data, None)
        assert isinstance(targets, dict)
        assert "short" in targets
        assert "medium" in targets
        assert "long" in targets
        print(f"✓ Price targets calculated: Short={targets['short']}, Medium={targets['medium']}, Long={targets['long']}")
        
        print("\n🎉 All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_opportunity_filters():
    """Test opportunity filtering functionality."""
    print("\nTesting opportunity filtering functionality...")
    
    try:
        service = OpportunitySearchService()
        
        # Test market data filtering
        from app.models.stock import MarketData
        
        market_data = MarketData(
            symbol="AAPL",
            price=Decimal("150.25"),
            change=Decimal("2.50"),
            change_percent=Decimal("1.69"),
            volume=75000000,
            high_52_week=Decimal("180.00"),
            low_52_week=Decimal("120.00"),
            avg_volume=80000000,
            market_cap=2500000000000,
            pe_ratio=Decimal("25.5"),
            timestamp=datetime.now()
        )
        
        # Test market cap filtering
        filters = OpportunitySearchFilters(market_cap_min=1000000000000)  # 1T
        assert service._passes_market_filters(market_data, filters)
        print("✓ Market cap minimum filter works")
        
        filters = OpportunitySearchFilters(market_cap_max=3000000000000)  # 3T
        assert service._passes_market_filters(market_data, filters)
        print("✓ Market cap maximum filter works")
        
        filters = OpportunitySearchFilters(market_cap_min=3000000000000)  # 3T (too high)
        assert not service._passes_market_filters(market_data, filters)
        print("✓ Market cap filtering correctly excludes stocks")
        
        # Test volume filtering
        filters = OpportunitySearchFilters(volume_min=50000000)
        assert service._passes_market_filters(market_data, filters)
        print("✓ Volume filtering works")
        
        print("✓ All filtering tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Filter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("Starting Opportunity Search Integration Tests")
    print("=" * 50)
    
    success = True
    
    # Run basic functionality tests
    success &= await test_opportunity_search_basic()
    
    # Run filtering tests
    success &= await test_opportunity_filters()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The opportunity search engine is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)