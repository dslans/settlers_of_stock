"""
Comprehensive integration tests for API endpoints and database operations.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from app.models.user import User
from app.models.watchlist import Watchlist, WatchlistItem
from app.models.alert import Alert
from tests.test_factories import (
    MarketDataFactory, FundamentalDataFactory, TechnicalDataFactory,
    AnalysisResultFactory, NewsItemFactory
)


@pytest.mark.integration
class TestUserWorkflow:
    """Integration tests for complete user workflows."""
    
    def test_complete_user_registration_and_verification_workflow(self, client, db_session):
        """Test complete user registration and verification process."""
        
        # Step 1: Register new user
        registration_data = {
            "email": "integration@example.com",
            "password": "IntegrationTest123!",
            "confirm_password": "IntegrationTest123!",
            "full_name": "Integration Test User",
            "preferences": {
                "risk_tolerance": "moderate",
                "investment_horizon": "medium"
            }
        }
        
        response = client.post("/api/auth/register", json=registration_data)
        assert response.status_code == 201
        
        user_data = response.json()
        assert user_data["email"] == registration_data["email"]
        assert user_data["full_name"] == registration_data["full_name"]
        assert "id" in user_data
        
        # Verify user exists in database
        user = db_session.query(User).filter(User.email == registration_data["email"]).first()
        assert user is not None
        assert user.is_verified == False  # Should be unverified initially
        
        # Step 2: Attempt login before verification (should fail)
        login_response = client.post("/api/auth/login", json={
            "email": registration_data["email"],
            "password": registration_data["password"]
        })
        assert login_response.status_code == 400
        
        # Step 3: Verify user (simulate email verification)
        user.is_verified = True
        db_session.commit()
        
        # Step 4: Login after verification
        login_response = client.post("/api/auth/login", json={
            "email": registration_data["email"],
            "password": registration_data["password"]
        })
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        
        # Step 5: Access protected endpoint
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_response = client.get("/api/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile_data = profile_response.json()
        assert profile_data["email"] == registration_data["email"]

    def test_complete_stock_analysis_workflow(self, client, auth_headers):
        """Test complete stock analysis workflow."""
        
        with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_market, \
             patch('app.services.data_aggregation.DataAggregationService.get_fundamental_data') as mock_fundamental, \
             patch('app.services.analysis_engine.AnalysisEngine.perform_combined_analysis') as mock_analysis:
            
            # Mock data
            mock_market.return_value = MarketDataFactory(symbol="AAPL")
            mock_fundamental.return_value = FundamentalDataFactory(symbol="AAPL")
            mock_analysis.return_value = AnalysisResultFactory(symbol="AAPL")
            
            # Step 1: Get basic stock information
            stock_response = client.get("/api/stocks/AAPL", headers=auth_headers)
            assert stock_response.status_code == 200
            
            stock_data = stock_response.json()
            assert stock_data["symbol"] == "AAPL"
            assert "price" in stock_data
            assert "change" in stock_data
            
            # Step 2: Request detailed analysis
            analysis_response = client.post(
                "/api/analysis/AAPL",
                json={"analysis_types": ["fundamental", "technical", "sentiment"]},
                headers=auth_headers
            )
            assert analysis_response.status_code == 200
            
            analysis_data = analysis_response.json()
            assert analysis_data["symbol"] == "AAPL"
            assert "recommendation" in analysis_data
            assert "confidence" in analysis_data
            assert "reasoning" in analysis_data
            
            # Step 3: Get historical analysis
            with patch('app.services.bigquery_service.BigQueryService.get_historical_analysis') as mock_historical:
                mock_historical.return_value = {
                    "symbol": "AAPL",
                    "performance_metrics": {
                        "total_return": 0.15,
                        "volatility": 0.25,
                        "sharpe_ratio": 0.6
                    }
                }
                
                historical_response = client.get(
                    "/api/historical/AAPL?period=1Y",
                    headers=auth_headers
                )
                assert historical_response.status_code == 200

    def test_complete_watchlist_management_workflow(self, client, auth_headers, test_user):
        """Test complete watchlist management workflow."""
        
        # Step 1: Create new watchlist
        watchlist_data = {
            "name": "Integration Test Watchlist",
            "description": "Test watchlist for integration testing",
            "is_default": False
        }
        
        create_response = client.post("/api/watchlists", json=watchlist_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        watchlist = create_response.json()
        watchlist_id = watchlist["id"]
        assert watchlist["name"] == watchlist_data["name"]
        
        # Step 2: Add stocks to watchlist
        stock_data = {
            "symbol": "AAPL",
            "company_name": "Apple Inc.",
            "notes": "Tech giant",
            "target_price": 200.00
        }
        
        add_stock_response = client.post(
            f"/api/watchlists/{watchlist_id}/items",
            json=stock_data,
            headers=auth_headers
        )
        assert add_stock_response.status_code == 201
        
        # Step 3: Get watchlist with items
        get_response = client.get(f"/api/watchlists/{watchlist_id}", headers=auth_headers)
        assert get_response.status_code == 200
        
        watchlist_with_items = get_response.json()
        assert len(watchlist_with_items["items"]) == 1
        assert watchlist_with_items["items"][0]["symbol"] == "AAPL"
        
        # Step 4: Update watchlist item
        update_data = {
            "notes": "Updated notes",
            "target_price": 220.00
        }
        
        item_id = watchlist_with_items["items"][0]["id"]
        update_response = client.put(
            f"/api/watchlists/{watchlist_id}/items/{item_id}",
            json=update_data,
            headers=auth_headers
        )
        assert update_response.status_code == 200
        
        # Step 5: Delete watchlist item
        delete_item_response = client.delete(
            f"/api/watchlists/{watchlist_id}/items/{item_id}",
            headers=auth_headers
        )
        assert delete_item_response.status_code == 204
        
        # Step 6: Delete watchlist
        delete_watchlist_response = client.delete(f"/api/watchlists/{watchlist_id}", headers=auth_headers)
        assert delete_watchlist_response.status_code == 204

    def test_complete_alert_management_workflow(self, client, auth_headers):
        """Test complete alert management workflow."""
        
        # Step 1: Create price alert
        alert_data = {
            "symbol": "AAPL",
            "alert_type": "price_above",
            "condition_value": 200.00,
            "message": "AAPL reached target price"
        }
        
        create_response = client.post("/api/alerts", json=alert_data, headers=auth_headers)
        assert create_response.status_code == 201
        
        alert = create_response.json()
        alert_id = alert["id"]
        assert alert["symbol"] == "AAPL"
        assert alert["is_active"] == True
        
        # Step 2: Get all alerts
        get_alerts_response = client.get("/api/alerts", headers=auth_headers)
        assert get_alerts_response.status_code == 200
        
        alerts = get_alerts_response.json()
        assert len(alerts) >= 1
        assert any(a["id"] == alert_id for a in alerts)
        
        # Step 3: Update alert
        update_data = {
            "condition_value": 210.00,
            "message": "Updated alert message"
        }
        
        update_response = client.put(f"/api/alerts/{alert_id}", json=update_data, headers=auth_headers)
        assert update_response.status_code == 200
        
        updated_alert = update_response.json()
        assert updated_alert["condition_value"] == 210.00
        
        # Step 4: Deactivate alert
        deactivate_response = client.patch(f"/api/alerts/{alert_id}/deactivate", headers=auth_headers)
        assert deactivate_response.status_code == 200
        
        deactivated_alert = deactivate_response.json()
        assert deactivated_alert["is_active"] == False
        
        # Step 5: Delete alert
        delete_response = client.delete(f"/api/alerts/{alert_id}", headers=auth_headers)
        assert delete_response.status_code == 204


@pytest.mark.integration
class TestChatWorkflow:
    """Integration tests for chat functionality."""
    
    def test_complete_chat_session_workflow(self, client, auth_headers):
        """Test complete chat session workflow."""
        
        with patch('app.services.vertex_ai_service.VertexAIService.generate_stock_analysis_response') as mock_ai, \
             patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_market:
            
            mock_market.return_value = MarketDataFactory(symbol="AAPL")
            mock_ai.return_value = "Apple Inc. (AAPL) is currently trading at $150.00, up 2.5% today. The stock shows strong fundamentals with a P/E ratio of 25.5 and solid revenue growth."
            
            # Step 1: Start chat session
            chat_data = {
                "message": "Tell me about AAPL",
                "context": {}
            }
            
            chat_response = client.post("/api/chat", json=chat_data, headers=auth_headers)
            assert chat_response.status_code == 200
            
            response_data = chat_response.json()
            assert "response" in response_data
            assert "context" in response_data
            assert "AAPL" in response_data["response"]
            
            # Step 2: Follow-up question with context
            followup_data = {
                "message": "What about its technical indicators?",
                "context": response_data["context"]
            }
            
            with patch('app.services.analysis_engine.AnalysisEngine.perform_technical_analysis') as mock_technical:
                mock_technical.return_value = TechnicalDataFactory(symbol="AAPL")
                
                followup_response = client.post("/api/chat", json=followup_data, headers=auth_headers)
                assert followup_response.status_code == 200
                
                followup_data = followup_response.json()
                assert "technical" in followup_data["response"].lower()

    def test_chat_with_educational_content(self, client, auth_headers):
        """Test chat integration with educational content."""
        
        with patch('app.services.education_service.EducationService.get_concept_explanation') as mock_education:
            mock_education.return_value = {
                "concept": "P/E Ratio",
                "explanation": "Price-to-Earnings ratio measures how much investors are willing to pay per dollar of earnings.",
                "example": "A P/E ratio of 20 means investors pay $20 for every $1 of annual earnings."
            }
            
            chat_data = {
                "message": "What is P/E ratio?",
                "context": {}
            }
            
            response = client.post("/api/chat", json=chat_data, headers=auth_headers)
            assert response.status_code == 200
            
            response_data = response.json()
            assert "P/E" in response_data["response"]
            assert "educational_content" in response_data


@pytest.mark.integration
class TestDataIntegration:
    """Integration tests for data services and external APIs."""
    
    def test_data_aggregation_service_integration(self):
        """Test data aggregation service with mocked external APIs."""
        from app.services.data_aggregation import DataAggregationService
        
        service = DataAggregationService()
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock yfinance response
            mock_info = {
                'symbol': 'AAPL',
                'currentPrice': 150.00,
                'regularMarketChange': 3.75,
                'regularMarketChangePercent': 2.56,
                'volume': 50000000,
                'fiftyTwoWeekHigh': 180.00,
                'fiftyTwoWeekLow': 120.00,
                'averageVolume': 45000000
            }
            
            mock_ticker_instance = MagicMock()
            mock_ticker_instance.info = mock_info
            mock_ticker.return_value = mock_ticker_instance
            
            # Test market data retrieval
            market_data = service.get_market_data("AAPL")
            
            assert market_data is not None
            assert market_data["symbol"] == "AAPL"
            assert market_data["price"] == 150.00

    def test_cache_integration(self):
        """Test Redis cache integration."""
        from app.core.cache import get_cache_client
        
        cache = get_cache_client()
        
        # Test cache operations
        test_key = "integration_test_key"
        test_data = {"symbol": "AAPL", "price": 150.00}
        
        # Set data
        cache.setex(test_key, 60, json.dumps(test_data))
        
        # Get data
        cached_data = cache.get(test_key)
        assert cached_data is not None
        
        parsed_data = json.loads(cached_data)
        assert parsed_data["symbol"] == "AAPL"
        assert parsed_data["price"] == 150.00
        
        # Clean up
        cache.delete(test_key)

    def test_database_transaction_integrity(self, db_session, test_user):
        """Test database transaction integrity."""
        
        # Test successful transaction
        watchlist = Watchlist(
            user_id=test_user.id,
            name="Transaction Test",
            description="Testing transaction integrity"
        )
        
        db_session.add(watchlist)
        db_session.flush()  # Get ID without committing
        
        item = WatchlistItem(
            watchlist_id=watchlist.id,
            symbol="TEST",
            company_name="Test Company"
        )
        
        db_session.add(item)
        db_session.commit()
        
        # Verify both objects were saved
        saved_watchlist = db_session.query(Watchlist).filter(Watchlist.id == watchlist.id).first()
        saved_item = db_session.query(WatchlistItem).filter(WatchlistItem.watchlist_id == watchlist.id).first()
        
        assert saved_watchlist is not None
        assert saved_item is not None
        assert saved_item.symbol == "TEST"
        
        # Test rollback on error
        try:
            db_session.begin()
            
            # Create another watchlist
            error_watchlist = Watchlist(
                user_id=test_user.id,
                name="Error Test",
                description="This should be rolled back"
            )
            db_session.add(error_watchlist)
            db_session.flush()
            
            # Simulate an error
            raise Exception("Simulated error")
            
        except Exception:
            db_session.rollback()
        
        # Verify rollback worked
        error_watchlist_check = db_session.query(Watchlist).filter(
            Watchlist.name == "Error Test"
        ).first()
        assert error_watchlist_check is None


@pytest.mark.integration
class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""
    
    def test_websocket_connection_and_messaging(self, client):
        """Test WebSocket connection and real-time messaging."""
        
        with client.websocket_connect("/ws") as websocket:
            # Send test message
            test_message = {
                "type": "stock_query",
                "symbol": "AAPL",
                "message": "Get current price for AAPL"
            }
            
            websocket.send_json(test_message)
            
            # Receive response
            response = websocket.receive_json()
            
            assert "type" in response
            assert "data" in response
            
            # Test connection close
            websocket.close()

    def test_websocket_authentication(self, client, test_user_token):
        """Test WebSocket authentication."""
        
        # Test with valid token
        with client.websocket_connect(f"/ws?token={test_user_token}") as websocket:
            # Send authenticated message
            test_message = {
                "type": "user_query",
                "message": "Get my watchlists"
            }
            
            websocket.send_json(test_message)
            response = websocket.receive_json()
            
            assert response["type"] != "error"
            websocket.close()
        
        # Test with invalid token
        with pytest.raises(Exception):  # Should raise connection error
            with client.websocket_connect("/ws?token=invalid_token") as websocket:
                pass


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Integration tests for error handling across the system."""
    
    def test_api_error_handling_chain(self, client, auth_headers):
        """Test error handling propagation through the API chain."""
        
        # Test invalid stock symbol
        response = client.get("/api/stocks/INVALID_SYMBOL", headers=auth_headers)
        assert response.status_code == 404
        
        error_data = response.json()
        assert "detail" in error_data
        assert "suggestions" in error_data
        
        # Test malformed request data
        response = client.post(
            "/api/analysis/AAPL",
            json={"invalid_field": "invalid_value"},
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error
        
        # Test unauthorized access
        response = client.get("/api/auth/me")  # No auth headers
        assert response.status_code == 401

    def test_service_error_recovery(self, client, auth_headers):
        """Test service error recovery mechanisms."""
        
        with patch('app.services.data_aggregation.DataAggregationService.get_market_data') as mock_data:
            # Simulate primary data source failure
            mock_data.side_effect = Exception("Primary data source unavailable")
            
            # The service should handle the error gracefully
            response = client.get("/api/stocks/AAPL", headers=auth_headers)
            
            # Should return error response, not crash
            assert response.status_code in [500, 503, 404]  # Acceptable error codes
            
            error_data = response.json()
            assert "detail" in error_data