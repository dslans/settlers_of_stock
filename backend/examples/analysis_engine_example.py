"""
Example usage of the Analysis Engine.

This script demonstrates how to use the AnalysisEngine to perform
comprehensive stock analysis combining fundamental and technical analysis.
"""

import asyncio
import sys
import os
from decimal import Decimal

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.analysis_engine import AnalysisEngine
from app.models.analysis import Recommendation, RiskLevel


async def demonstrate_analysis_engine():
    """Demonstrate the analysis engine capabilities."""
    print("Analysis Engine Demonstration")
    print("=" * 50)
    
    # Create analysis engine
    engine = AnalysisEngine()
    
    # Example stocks to analyze
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    for symbol in symbols:
        print(f"\n📊 Analyzing {symbol}...")
        print("-" * 30)
        
        try:
            # Perform comprehensive analysis
            result = await engine.analyze_stock(symbol)
            
            # Display results
            print(f"🎯 Recommendation: {result.recommendation.value}")
            print(f"📈 Confidence: {result.confidence}%")
            print(f"⚖️  Overall Score: {result.overall_score}/100")
            print(f"⚠️  Risk Level: {result.risk_level.value}")
            
            if result.fundamental_score:
                print(f"📊 Fundamental Score: {result.fundamental_score}/100")
            
            if result.technical_score:
                print(f"📈 Technical Score: {result.technical_score}/100")
            
            # Show key insights
            if result.strengths:
                print(f"\n✅ Key Strengths:")
                for i, strength in enumerate(result.strengths[:3], 1):
                    print(f"   {i}. {strength}")
            
            if result.risks:
                print(f"\n⚠️  Key Risks:")
                for i, risk in enumerate(result.risks[:3], 1):
                    print(f"   {i}. {risk}")
            
            # Show price targets
            if result.price_targets:
                print(f"\n🎯 Price Targets:")
                for target in result.price_targets:
                    print(f"   {target.timeframe}: ${target.target} (confidence: {target.confidence}%)")
                    print(f"      Rationale: {target.rationale}")
            
            # Show recommendation summary
            print(f"\n📋 Summary: {result.get_recommendation_summary()}")
            print(f"🛡️  Risk: {result.get_risk_summary()}")
            
        except Exception as e:
            print(f"❌ Failed to analyze {symbol}: {e}")
    
    print("\n" + "=" * 50)
    print("Analysis Engine Demonstration Complete!")


async def demonstrate_component_analysis():
    """Demonstrate individual analysis components."""
    print("\n\nComponent Analysis Demonstration")
    print("=" * 50)
    
    engine = AnalysisEngine()
    symbol = "AAPL"
    
    print(f"Analyzing {symbol} with different configurations...\n")
    
    # Fundamental-only analysis
    print("🏢 Fundamental Analysis Only:")
    print("-" * 30)
    try:
        result_fund = await engine.analyze_stock(symbol, include_technical=False)
        print(f"   Recommendation: {result_fund.recommendation.value}")
        print(f"   Confidence: {result_fund.confidence}%")
        print(f"   Fundamental Score: {result_fund.fundamental_score}/100")
        print(f"   Technical Score: {result_fund.technical_score or 'N/A'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Technical-only analysis
    print("\n📈 Technical Analysis Only:")
    print("-" * 30)
    try:
        result_tech = await engine.analyze_stock(symbol, include_fundamental=False)
        print(f"   Recommendation: {result_tech.recommendation.value}")
        print(f"   Confidence: {result_tech.confidence}%")
        print(f"   Fundamental Score: {result_tech.fundamental_score or 'N/A'}")
        print(f"   Technical Score: {result_tech.technical_score}/100")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Combined analysis
    print("\n🔄 Combined Analysis:")
    print("-" * 30)
    try:
        result_combined = await engine.analyze_stock(symbol)
        print(f"   Recommendation: {result_combined.recommendation.value}")
        print(f"   Confidence: {result_combined.confidence}%")
        print(f"   Fundamental Score: {result_combined.fundamental_score}/100")
        print(f"   Technical Score: {result_combined.technical_score}/100")
        print(f"   Combined Score: {result_combined.overall_score}/100")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def demonstrate_risk_assessment():
    """Demonstrate risk assessment capabilities."""
    print("\n\nRisk Assessment Demonstration")
    print("=" * 50)
    
    engine = AnalysisEngine()
    
    # Test with different types of stocks
    test_cases = [
        ("AAPL", "Large-cap tech stock"),
        ("TSLA", "High-growth volatile stock"),
        ("JNJ", "Defensive dividend stock")
    ]
    
    for symbol, description in test_cases:
        print(f"\n🔍 {symbol} ({description}):")
        print("-" * 40)
        
        try:
            result = await engine.analyze_stock(symbol)
            
            print(f"   Risk Level: {result.risk_level.value}")
            print(f"   Risk Summary: {result.get_risk_summary()}")
            
            # Show key risk factors
            if 'overall_risk_score' in result.risk_factors:
                risk_score = result.risk_factors['overall_risk_score']
                print(f"   Risk Score: {risk_score}/100")
            
            # Show specific risk factors
            risk_details = []
            if 'debt_ratio' in result.risk_factors:
                risk_details.append(f"Debt Ratio: {result.risk_factors['debt_ratio']:.2f}")
            if 'volatility' in result.risk_factors:
                risk_details.append(f"Volatility: {result.risk_factors['volatility']:.1%}")
            if 'pe_ratio' in result.risk_factors:
                risk_details.append(f"P/E Ratio: {result.risk_factors['pe_ratio']:.1f}")
            
            if risk_details:
                print(f"   Risk Factors: {', '.join(risk_details)}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


async def main():
    """Run all demonstrations."""
    try:
        await demonstrate_analysis_engine()
        await demonstrate_component_analysis()
        await demonstrate_risk_assessment()
        
        print("\n🎉 All demonstrations completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting Analysis Engine Examples...")
    print("Note: This requires internet access for real market data.\n")
    
    asyncio.run(main())