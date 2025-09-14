#!/usr/bin/env python3
"""
Example script demonstrating the DataAggregationService functionality.
This script shows how to use the service to fetch stock data with caching and error handling.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.data_aggregation import DataAggregationService, DataAggregationException


async def main():
    """Demonstrate DataAggregationService functionality."""
    print("🏛️ Settlers of Stock - Data Aggregation Service Demo")
    print("=" * 60)
    
    # Initialize the service (without Redis for this demo)
    service = DataAggregationService(redis_client=None)
    
    # Test symbols - mix of valid and invalid
    test_symbols = ['AAPL', 'GOOGL', 'MSFT', 'INVALID_SYMBOL', 'TSLA']
    
    print("\n📊 Testing individual stock data fetching:")
    print("-" * 40)
    
    for symbol in test_symbols[:4]:  # Test first 4 symbols individually
        try:
            print(f"\n🔍 Fetching data for {symbol}...")
            market_data = await service.get_market_data(symbol, use_cache=False)
            
            print(f"✅ {symbol} - ${market_data.price:.2f}")
            print(f"   Change: ${market_data.change:.2f} ({market_data.change_percent:.2f}%)")
            print(f"   Volume: {market_data.volume:,}")
            if market_data.market_cap:
                print(f"   Market Cap: ${market_data.market_cap:,}")
            
        except DataAggregationException as e:
            print(f"❌ {symbol} - Error: {e.message}")
            if e.suggestions:
                print(f"   Suggestions: {', '.join(e.suggestions)}")
        except Exception as e:
            print(f"💥 {symbol} - Unexpected error: {e}")
    
    print(f"\n📈 Testing multiple symbols fetch:")
    print("-" * 40)
    
    try:
        # Test fetching multiple symbols at once
        valid_symbols = ['AAPL', 'GOOGL', 'MSFT']
        results = await service.get_multiple_market_data(valid_symbols)
        
        print(f"✅ Successfully fetched data for {len(results)} symbols:")
        for symbol, data in results.items():
            print(f"   {symbol}: ${data.price:.2f} ({data.change_percent:+.2f}%)")
    
    except Exception as e:
        print(f"❌ Multiple fetch error: {e}")
    
    print(f"\n🏢 Testing stock info fetching:")
    print("-" * 40)
    
    try:
        stock_info = await service.get_stock_info('AAPL', use_cache=False)
        print(f"✅ {stock_info.symbol} - {stock_info.name}")
        print(f"   Exchange: {stock_info.exchange}")
        print(f"   Sector: {stock_info.sector}")
        print(f"   Industry: {stock_info.industry}")
        
    except DataAggregationException as e:
        print(f"❌ Stock info error: {e.message}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
    
    print(f"\n🔍 Testing symbol validation:")
    print("-" * 40)
    
    validation_symbols = ['AAPL', 'INVALID123', 'GOOGL']
    for symbol in validation_symbols:
        try:
            is_valid = await service.validate_symbol(symbol)
            status = "✅ Valid" if is_valid else "❌ Invalid"
            print(f"   {symbol}: {status}")
        except Exception as e:
            print(f"   {symbol}: ❓ Could not validate - {e}")
    
    print(f"\n📊 Cache statistics:")
    print("-" * 40)
    stats = service.get_cache_stats()
    if "error" in stats:
        print(f"   Cache not available: {stats['error']}")
    else:
        print(f"   Market data entries: {stats.get('market_data_entries', 0)}")
        print(f"   Stock info entries: {stats.get('stock_info_entries', 0)}")
        print(f"   Invalid symbols cached: {stats.get('invalid_symbols', 0)}")
    
    print(f"\n🎯 Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        sys.exit(1)