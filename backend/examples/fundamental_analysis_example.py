"""
Example demonstrating the Fundamental Analysis Engine.
Shows how to use the FundamentalAnalyzer for stock analysis.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.fundamental_analyzer import FundamentalAnalyzer, FundamentalAnalysisException
from app.services.data_aggregation import DataAggregationService


async def demonstrate_fundamental_analysis():
    """Demonstrate fundamental analysis capabilities."""
    
    print("🏢 Settlers of Stock - Fundamental Analysis Engine Demo")
    print("=" * 60)
    
    # Initialize the analyzer
    analyzer = FundamentalAnalyzer()
    
    # Test symbols
    test_symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in test_symbols:
        print(f"\n📊 Analyzing {symbol}...")
        print("-" * 40)
        
        try:
            # 1. Basic Fundamental Analysis
            print("1️⃣ Fetching fundamental data...")
            fundamental_data = await analyzer.analyze_fundamentals(symbol)
            
            print(f"   Symbol: {fundamental_data.symbol}")
            if fundamental_data.pe_ratio:
                print(f"   P/E Ratio: {fundamental_data.pe_ratio}")
            if fundamental_data.pb_ratio:
                print(f"   P/B Ratio: {fundamental_data.pb_ratio}")
            if fundamental_data.roe:
                print(f"   ROE: {fundamental_data.roe:.2%}")
            if fundamental_data.debt_to_equity:
                print(f"   Debt-to-Equity: {fundamental_data.debt_to_equity}")
            if fundamental_data.profit_margin:
                print(f"   Profit Margin: {fundamental_data.profit_margin:.2%}")
            
            # 2. Company Health Assessment
            print("\n2️⃣ Assessing company health...")
            health_assessment = await analyzer.assess_company_health(symbol)
            
            print(f"   Overall Score: {health_assessment.overall_score}/100")
            print(f"   Rating: {health_assessment.rating}")
            
            if health_assessment.strengths:
                print("   💪 Strengths:")
                for strength in health_assessment.strengths[:3]:  # Show top 3
                    print(f"      • {strength}")
            
            if health_assessment.weaknesses:
                print("   ⚠️  Weaknesses:")
                for weakness in health_assessment.weaknesses[:3]:  # Show top 3
                    print(f"      • {weakness}")
            
            # 3. Industry Comparison
            print("\n3️⃣ Comparing to industry peers...")
            try:
                industry_comparison = await analyzer.compare_to_industry(symbol)
                
                print(f"   Industry: {industry_comparison.industry}")
                print(f"   Sector: {industry_comparison.sector}")
                print(f"   Peer Companies: {', '.join(industry_comparison.peer_symbols[:5])}")
                
                if industry_comparison.percentile_rankings:
                    print("   📈 Percentile Rankings:")
                    for metric, percentile in industry_comparison.percentile_rankings.items():
                        print(f"      {metric}: {percentile}th percentile")
                
                if industry_comparison.relative_performance:
                    print("   📊 Relative Performance:")
                    for metric, performance in industry_comparison.relative_performance.items():
                        emoji = "🟢" if "Above" in performance else "🔴" if "Below" in performance else "🟡"
                        print(f"      {metric}: {performance} {emoji}")
            
            except Exception as e:
                print(f"   ⚠️  Industry comparison failed: {e}")
            
            # 4. Demonstrate Individual Ratio Calculations
            print("\n4️⃣ Individual ratio calculations:")
            
            # Example calculations with sample data
            if fundamental_data.eps and fundamental_data.pe_ratio:
                estimated_price = float(fundamental_data.eps) * float(fundamental_data.pe_ratio)
                print(f"   Estimated Price (EPS × P/E): ${estimated_price:.2f}")
            
            if fundamental_data.net_income and fundamental_data.total_equity:
                calculated_roe = analyzer.calculate_roe(fundamental_data.net_income, fundamental_data.total_equity)
                if calculated_roe:
                    print(f"   Calculated ROE: {calculated_roe:.2%}")
            
            if fundamental_data.total_debt is not None and fundamental_data.total_equity:
                calculated_de = analyzer.calculate_debt_to_equity(fundamental_data.total_debt, fundamental_data.total_equity)
                if calculated_de:
                    print(f"   Calculated D/E Ratio: {calculated_de}")
        
        except FundamentalAnalysisException as e:
            print(f"   ❌ Analysis failed: {e.message}")
            if e.suggestions:
                print("   💡 Suggestions:")
                for suggestion in e.suggestions:
                    print(f"      • {suggestion}")
        
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Fundamental Analysis Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("• Financial ratio calculations (P/E, P/B, ROE, D/E)")
    print("• Company health scoring and assessment")
    print("• Industry peer comparison and rankings")
    print("• Error handling and graceful degradation")
    print("• Real-time data integration with yfinance")


async def demonstrate_ratio_calculations():
    """Demonstrate individual ratio calculation methods."""
    
    print("\n🧮 Individual Ratio Calculation Examples")
    print("=" * 50)
    
    analyzer = FundamentalAnalyzer()
    
    # Example data
    examples = [
        {
            "name": "High-Growth Tech Company",
            "price": 150.00,
            "eps": 5.00,
            "book_value": 25.00,
            "net_income": 10000000000,  # $10B
            "total_equity": 50000000000,  # $50B
            "total_debt": 15000000000,  # $15B
        },
        {
            "name": "Value Stock",
            "price": 45.00,
            "eps": 4.50,
            "book_value": 40.00,
            "net_income": 2000000000,  # $2B
            "total_equity": 20000000000,  # $20B
            "total_debt": 8000000000,  # $8B
        },
        {
            "name": "Struggling Company",
            "price": 12.00,
            "eps": 0.50,
            "book_value": 15.00,
            "net_income": 100000000,  # $100M
            "total_equity": 5000000000,  # $5B
            "total_debt": 12000000000,  # $12B
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print("-" * 30)
        
        # Calculate ratios
        pe_ratio = analyzer.calculate_pe_ratio(example['price'], example['eps'])
        pb_ratio = analyzer.calculate_pb_ratio(example['price'], example['book_value'])
        roe = analyzer.calculate_roe(example['net_income'], example['total_equity'])
        debt_to_equity = analyzer.calculate_debt_to_equity(example['total_debt'], example['total_equity'])
        
        print(f"Stock Price: ${example['price']:.2f}")
        print(f"P/E Ratio: {pe_ratio:.2f}" if pe_ratio else "P/E Ratio: N/A")
        print(f"P/B Ratio: {pb_ratio:.2f}" if pb_ratio else "P/B Ratio: N/A")
        print(f"ROE: {roe:.2%}" if roe else "ROE: N/A")
        print(f"Debt-to-Equity: {debt_to_equity:.2f}" if debt_to_equity else "D/E Ratio: N/A")
        
        # Interpretation
        if pe_ratio:
            if pe_ratio < 15:
                print("📊 P/E Analysis: Potentially undervalued or slow growth")
            elif pe_ratio > 30:
                print("📊 P/E Analysis: High growth expectations or overvalued")
            else:
                print("📊 P/E Analysis: Reasonable valuation")
        
        if roe:
            if roe > 0.15:
                print("💪 ROE Analysis: Strong profitability")
            elif roe > 0.10:
                print("👍 ROE Analysis: Good profitability")
            else:
                print("⚠️  ROE Analysis: Below average profitability")
        
        if debt_to_equity:
            if debt_to_equity < 0.3:
                print("💪 D/E Analysis: Conservative debt levels")
            elif debt_to_equity < 0.6:
                print("👍 D/E Analysis: Moderate debt levels")
            else:
                print("⚠️  D/E Analysis: High debt levels - monitor closely")


if __name__ == "__main__":
    print("Starting Fundamental Analysis Engine Demo...")
    
    try:
        # Run the main demonstration
        asyncio.run(demonstrate_fundamental_analysis())
        
        # Run ratio calculation examples
        asyncio.run(demonstrate_ratio_calculations())
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()