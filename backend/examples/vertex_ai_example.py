"""
Example script demonstrating Vertex AI integration for stock analysis.
This script shows how to use the VertexAI service for generating conversational responses.
"""

import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vertex_ai_service import VertexAIService, AnalysisResult, ConversationContext

async def main():
    """
    Demonstrate Vertex AI service functionality
    """
    print("🤖 Vertex AI Stock Analysis Example")
    print("=" * 50)
    
    # Check if GCP project ID is set
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        print("❌ Error: GCP_PROJECT_ID environment variable not set")
        print("Please set your Google Cloud Project ID:")
        print("export GCP_PROJECT_ID=your-project-id")
        return
    
    try:
        # Initialize Vertex AI service
        print(f"🔧 Initializing Vertex AI service for project: {project_id}")
        vertex_ai_service = VertexAIService(project_id=project_id)
        print("✅ Vertex AI service initialized successfully")
        
        # Create sample analysis result
        print("\n📊 Creating sample analysis result...")
        analysis_result = AnalysisResult(
            symbol="AAPL",
            recommendation="BUY",
            confidence=85,
            reasoning=[
                "Strong quarterly earnings growth of 15%",
                "Technical indicators showing bullish momentum",
                "Market-leading position in smartphone segment",
                "Healthy balance sheet with strong cash flow"
            ],
            risks=[
                "Potential market volatility due to economic uncertainty",
                "Increased competition in the smartphone market",
                "Supply chain disruptions could impact production"
            ],
            targets={
                "short_term": 180.0,
                "medium_term": 200.0,
                "long_term": 220.0
            },
            analysis_type="combined"
        )
        print(f"✅ Analysis result created for {analysis_result.symbol}")
        
        # Create conversation context
        print("\n💬 Creating conversation context...")
        context = ConversationContext(
            user_id="demo_user",
            current_stocks=["AAPL"],
            user_preferences={
                "risk_tolerance": "moderate",
                "investment_horizon": "medium"
            }
        )
        print("✅ Conversation context created")
        
        # Test 1: Generate stock analysis response
        print("\n🎯 Test 1: Generating stock analysis response...")
        user_query = "What do you think about Apple stock? Should I buy it?"
        
        try:
            response = await vertex_ai_service.generate_stock_analysis_response(
                analysis_result, user_query, context
            )
            print(f"✅ Generated response:")
            print(f"📝 Query: {user_query}")
            print(f"🤖 Response: {response}")
            print()
        except Exception as e:
            print(f"❌ Error generating analysis response: {e}")
        
        # Test 2: Explain technical indicator
        print("🎯 Test 2: Explaining technical indicator...")
        try:
            explanation = await vertex_ai_service.explain_technical_indicator(
                "RSI", 70.5, "AAPL", context
            )
            print(f"✅ Technical indicator explanation:")
            print(f"📊 Indicator: RSI = 70.5 for AAPL")
            print(f"🤖 Explanation: {explanation}")
            print()
        except Exception as e:
            print(f"❌ Error explaining technical indicator: {e}")
        
        # Test 3: Handle follow-up question
        print("🎯 Test 3: Handling follow-up question...")
        follow_up_query = "What are the main risks I should be aware of?"
        
        try:
            follow_up_response = await vertex_ai_service.handle_follow_up_question(
                follow_up_query, context
            )
            print(f"✅ Follow-up response:")
            print(f"📝 Follow-up: {follow_up_query}")
            print(f"🤖 Response: {follow_up_response}")
            print()
        except Exception as e:
            print(f"❌ Error handling follow-up: {e}")
        
        # Test 4: Generate market summary
        print("🎯 Test 4: Generating market summary...")
        market_data = [
            {"symbol": "AAPL", "change": 2.5, "change_percent": 1.4, "volume": 50000000},
            {"symbol": "GOOGL", "change": -1.2, "change_percent": -0.8, "volume": 30000000},
            {"symbol": "MSFT", "change": 0.8, "change_percent": 0.3, "volume": 25000000},
            {"symbol": "TSLA", "change": -5.2, "change_percent": -2.1, "volume": 75000000}
        ]
        
        try:
            market_summary = await vertex_ai_service.generate_market_summary(market_data, context)
            print(f"✅ Market summary:")
            print(f"📈 Market Data: {len(market_data)} stocks")
            print(f"🤖 Summary: {market_summary}")
            print()
        except Exception as e:
            print(f"❌ Error generating market summary: {e}")
        
        # Test 5: Service statistics
        print("🎯 Test 5: Service statistics...")
        active_sessions = vertex_ai_service.get_active_sessions_count()
        print(f"✅ Active chat sessions: {active_sessions}")
        
        # Clean up
        print("\n🧹 Cleaning up...")
        vertex_ai_service.clear_chat_session("demo_user")
        print("✅ Demo chat session cleared")
        
        print("\n🎉 All tests completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        print("Please check your GCP credentials and project configuration.")

def print_setup_instructions():
    """Print setup instructions for running the example"""
    print("\n📋 Setup Instructions:")
    print("1. Set up Google Cloud credentials:")
    print("   gcloud auth application-default login")
    print("2. Set your project ID:")
    print("   export GCP_PROJECT_ID=your-project-id")
    print("3. Enable Vertex AI API in your GCP project")
    print("4. Run this example:")
    print("   python examples/vertex_ai_example.py")

if __name__ == "__main__":
    # Check if running in interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print_setup_instructions()
    else:
        # Run the main demonstration
        asyncio.run(main())